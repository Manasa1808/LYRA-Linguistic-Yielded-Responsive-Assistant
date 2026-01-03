"""
Enhanced Speech Recognition Module for LYRA Voice Assistant
Fixes: Proper Kannada/Hindi decoding, no hallucinations, stable language detection
"""

import whisper
import numpy as np
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    """
    Enhanced speech recognizer with:
    - Proper multilingual decoding (no nonsense text)
    - Hallucination filtering
    - Confidence-based validation
    - Noise suppression
    """
    
    def __init__(self, model_name='base', lazy_load=True):
        """
        Initialize speech recognizer
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            lazy_load: If True, load model on first use
        """
        self.model_name = model_name
        self.model = None
        self._loading = False
        self.lazy_load = lazy_load
        
        # Supported languages
        self.supported_languages = ['en', 'hi', 'kn']
        
        # Store last detected language for response translation
        self.last_detected_language = 'en'
        self.last_original_text = ''
        
        if not lazy_load:
            self._load_model()
    
    def _load_model(self):
        """Load the Whisper model"""
        if self.model is None and not self._loading:
            self._loading = True
            try:
                logger.info(f"Loading Whisper model: {self.model_name}")
                print(f"Loading Whisper model: {self.model_name}")
                self.model = whisper.load_model(self.model_name)
                logger.info("✅ Whisper model loaded successfully")
                print("✅ Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                print(f"❌ Failed to load Whisper model: {e}")
                raise
            finally:
                self._loading = False
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None
    
    def _preprocess_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Preprocess audio: normalize, trim silence
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            Preprocessed audio
        """
        # Ensure float32
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        # Normalize to [-1, 1]
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val
        
        # Trim silence from start and end
        threshold = 0.01
        non_silent = np.abs(audio_data) > threshold
        
        if np.any(non_silent):
            start_idx = np.argmax(non_silent)
            end_idx = len(audio_data) - np.argmax(non_silent[::-1])
            audio_data = audio_data[start_idx:end_idx]
        
        return audio_data
    
    def _is_hallucination(self, text: str, segments: list) -> bool:
        """
        Detect hallucinations (repeated phrases, "la la la", etc.)
        
        Args:
            text: Transcribed text
            segments: Whisper segments
            
        Returns:
            True if likely hallucination
        """
        if not text or len(text.strip()) < 3:
            return True
        
        text_lower = text.lower().strip()
        
        # Check for common hallucination patterns
        hallucination_patterns = [
            'la la la', 'na na na', 'da da da',
            'thank you for watching', 'please subscribe',
            'like and subscribe', 'thanks for watching',
            'music playing', '[music]', '(music)',
            'applause', '[applause]', '(applause)'
        ]
        
        for pattern in hallucination_patterns:
            if pattern in text_lower:
                return True
        
        # Check for excessive repetition
        words = text_lower.split()
        if len(words) > 3:
            # Check if more than 50% of words are repeated
            unique_words = set(words)
            if len(unique_words) / len(words) < 0.5:
                return True
        
        # Check segment-level no_speech_prob
        if segments:
            avg_no_speech = sum(seg.get('no_speech_prob', 0) for seg in segments) / len(segments)
            if avg_no_speech > 0.8:  # High probability of no speech
                return True
        
        return False
    
    def transcribe(self, audio_data: np.ndarray, language: Optional[str] = None) -> Dict:
        """
        Transcribe audio with enhanced multilingual support
        
        Args:
            audio_data: Audio data as numpy array
            language: Optional language hint (ignored for auto-detection)
            
        Returns:
            Dictionary with:
                - text: Transcribed text
                - language: Detected language code
                - confidence: Confidence score (0-1)
                - is_valid: Whether transcription is valid (not hallucination)
        """
        # Lazy load model if needed
        if self.model is None:
            self._load_model()
        
        try:
            # Preprocess audio
            audio_data = self._preprocess_audio(audio_data)
            
            # Check if audio is too short or too quiet
            if len(audio_data) < 1600:  # Less than 0.1 seconds at 16kHz
                return {
                    'text': '',
                    'language': 'en',
                    'confidence': 0.0,
                    'is_valid': False,
                    'reason': 'Audio too short'
                }
            
            # Transcribe with Whisper
            # CRITICAL: Must output native Unicode script (Kannada/Hindi), NOT romanized
            result = self.model.transcribe(
                audio_data,
                language=None,  # Auto-detect language (will detect kn, hi, en)
                task='transcribe',  # MUST be 'transcribe' not 'translate'
                fp16=False,  # Prevent tensor errors
                verbose=False,
                word_timestamps=True,  # Get word-level timestamps
                condition_on_previous_text=False,  # Prevent context bleeding
                temperature=0.0,  # Deterministic output
                compression_ratio_threshold=2.4,  # Filter out low-quality
                logprob_threshold=-1.0,  # Filter low confidence
                no_speech_threshold=0.6,  # Filter silence
                # CRITICAL: These settings ensure native script output
                initial_prompt=None,  # No English bias
                suppress_tokens="-1"  # Don't suppress any tokens
            )
            
            # Extract results
            raw_text = result.get('text', '').strip()
            detected_lang = result.get('language', 'en')
            segments = result.get('segments', [])
            
            # Map Whisper language codes to system codes
            lang_map = {
                'en': 'en',
                'hi': 'hi',
                'kn': 'kn',
                'mr': 'hi',  # Marathi -> Hindi
                'te': 'hi',  # Telugu -> Hindi
                'ta': 'hi',  # Tamil -> Hindi
            }
            system_lang = lang_map.get(detected_lang, 'en')
            
            # CRITICAL: If Whisper outputs romanized text for Kannada/Hindi,
            # apply phonetic normalization
            if system_lang in ['hi', 'kn'] and self._is_romanized(raw_text):
                logger.warning(f"Detected romanized output for {system_lang}: '{raw_text}'")
                # Apply phonetic normalization
                from core.multilingual_processor import MultilingualTextProcessor
                processor = MultilingualTextProcessor()
                raw_text = processor.normalize_phonetic(raw_text)
                logger.info(f"Phonetic normalized: '{raw_text}'")
                # Treat as English since it's romanized
                system_lang = 'en'
            
            # Calculate confidence
            confidence = self._calculate_confidence(segments)
            
            # Check for hallucinations
            is_hallucination = self._is_hallucination(raw_text, segments)
            
            # Validate transcription
            is_valid = (
                len(raw_text) > 0 and
                confidence > 0.3 and
                not is_hallucination
            )
            
            if not is_valid:
                reason = 'hallucination' if is_hallucination else 'low confidence'
                logger.debug(f"Invalid transcription: {reason}")
                return {
                    'text': '',
                    'language': system_lang,
                    'confidence': confidence,
                    'is_valid': False,
                    'reason': reason
                }
            
            logger.info(f"Transcribed: '{raw_text}' (lang: {detected_lang} -> {system_lang}, confidence: {confidence:.2f})")
            
            return {
                'text': raw_text,
                'language': system_lang,
                'original_language': detected_lang,
                'confidence': confidence,
                'is_valid': True,
                'segments': segments
            }
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            print(f"❌ Transcription error: {e}")
            return {
                'text': '',
                'language': 'en',
                'confidence': 0.0,
                'is_valid': False,
                'reason': f'error: {str(e)}'
            }
    
    def _calculate_confidence(self, segments: list) -> float:
        """
        Calculate confidence from segments
        
        Args:
            segments: Whisper segments
            
        Returns:
            Confidence score (0-1)
        """
        if not segments:
            return 0.5
        
        try:
            # Use average of (1 - no_speech_prob) and avg_logprob
            no_speech_probs = []
            avg_logprobs = []
            
            for seg in segments:
                no_speech_probs.append(seg.get('no_speech_prob', 0.5))
                avg_logprobs.append(seg.get('avg_logprob', -1.0))
            
            # Confidence from no_speech_prob (lower is better)
            avg_no_speech = sum(no_speech_probs) / len(no_speech_probs)
            speech_confidence = 1.0 - avg_no_speech
            
            # Confidence from avg_logprob (higher is better, typically -1.0 to 0.0)
            avg_logprob = sum(avg_logprobs) / len(avg_logprobs)
            logprob_confidence = max(0.0, min(1.0, (avg_logprob + 1.0)))
            
            # Combined confidence
            confidence = (speech_confidence + logprob_confidence) / 2.0
            
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.warning(f"Confidence calculation error: {e}")
            return 0.5
    
    def _is_romanized(self, text: str) -> bool:
        """
        Check if text is romanized (Latin characters) instead of native script
        
        Args:
            text: Text to check
            
        Returns:
            True if text appears to be romanized
        """
        if not text:
            return False
        
        # Count Latin characters
        latin_count = sum(1 for c in text if c.isascii() and c.isalpha())
        total_alpha = sum(1 for c in text if c.isalpha())
        
        if total_alpha == 0:
            return False
        
        # If more than 80% Latin characters, it's romanized
        return (latin_count / total_alpha) > 0.8
    
    def detect_language(self, audio_data: np.ndarray) -> tuple:
        """
        Detect language from audio
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Tuple of (language_code, confidence)
        """
        # Lazy load model if needed
        if self.model is None:
            self._load_model()
        
        try:
            # Preprocess audio
            audio_data = self._preprocess_audio(audio_data)
            
            # Prepare audio for language detection
            audio_tensor = whisper.pad_or_trim(audio_data)
            mel = whisper.log_mel_spectrogram(audio_tensor).to(self.model.device)
            
            # Detect language
            _, probs = self.model.detect_language(mel)
            
            # Get most likely language
            detected_lang = max(probs, key=probs.get)
            confidence = probs[detected_lang]
            
            # Map to system language
            lang_map = {
                'en': 'en',
                'hi': 'hi',
                'kn': 'kn',
                'mr': 'hi',
                'te': 'hi',
                'ta': 'hi',
            }
            system_lang = lang_map.get(detected_lang, 'en')
            
            logger.info(f"Detected language: {detected_lang} -> {system_lang} (confidence: {confidence:.2f})")
            
            return system_lang, confidence
            
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return 'en', 0.5
    
    def preprocess_for_command(self, text: str, detected_language: str = None) -> tuple:
        """
        Preprocess text for command processing
        CRITICAL: Translates non-English to English automatically
        This method should be called by main.py before sending to command_processor
        
        Args:
            text: Input text (any language)
            detected_language: Optional language hint
            
        Returns:
            Tuple of (english_text, original_language, original_text)
        """
        from core.multilingual_processor import MultilingualTextProcessor
        from core.translation_engine import get_translation_engine
        
        processor = MultilingualTextProcessor()
        translator = get_translation_engine()
        
        # Clean and normalize
        cleaned_text = processor.clean_text(text)
        
        # Detect language if not provided
        if detected_language is None:
            detected_language = processor.detect_language(cleaned_text)
        
        # Store for response translation
        self.last_detected_language = detected_language
        self.last_original_text = cleaned_text
        
        logger.info(f"Preprocessing: detected language = {detected_language}")
        
        # If not English, translate to English
        if detected_language != 'en':
            if translator.is_available():
                try:
                    english_text = translator.translate_to_english(cleaned_text, detected_language)
                    logger.info(f"Translated {detected_language} -> en: '{cleaned_text}' -> '{english_text}'")
                    return english_text, detected_language, cleaned_text
                except Exception as e:
                    logger.error(f"Translation failed: {e}")
                    return cleaned_text, detected_language, cleaned_text
            else:
                logger.warning("Translation not available")
                return cleaned_text, detected_language, cleaned_text
        else:
            # Already English - apply phonetic normalization
            normalized = processor.normalize_phonetic(cleaned_text)
            if normalized != cleaned_text:
                logger.info(f"Phonetic normalized: '{cleaned_text}' -> '{normalized}'")
            return normalized, 'en', cleaned_text
    
    def translate_response(self, response: str, target_language: str = None) -> str:
        """
        Translate response back to user's language
        
        Args:
            response: English response
            target_language: Target language (if None, uses last detected)
            
        Returns:
            Translated response
        """
        from core.translation_engine import get_translation_engine
        
        if target_language is None:
            target_language = self.last_detected_language
        
        if target_language == 'en':
            return response
        
        translator = get_translation_engine()
        if translator.is_available():
            try:
                translated = translator.translate_from_english(response, target_language)
                logger.info(f"Response translated en -> {target_language}: '{response}' -> '{translated}'")
                return translated
            except Exception as e:
                logger.error(f"Response translation failed: {e}")
                return response
        else:
            return response
