"""
Enhanced Text-to-Speech Engine for LYRA Voice Assistant
Fixes: Proper language-native pronunciation for Kannada, Hindi, English
Uses language-specific neural voices, not English phonetics for all languages
"""

import os
import tempfile
import logging
import asyncio
import platform
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import TTS libraries
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logger.warning("edge-tts not available. Install with: pip install edge-tts")

try:
    from gtts import gTTS
    import pygame
    pygame.mixer.init()
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    logger.warning("gTTS or pygame not available. Install with: pip install gTTS pygame")

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logger.warning("pyttsx3 not available. Install with: pip install pyttsx3")


class TTSEngine:
    """
    Enhanced TTS engine with language-native pronunciation
    CRITICAL: Uses separate voice models for each language
    - Kannada text → Kannada voice (not English voice reading Kannada)
    - Hindi text → Hindi voice
    - English text → English voice
    """
    
    def __init__(self, rate: int = 150, volume: float = 0.9):
        """
        Initialize TTS engine
        
        Args:
            rate: Speech rate (words per minute) for pyttsx3
            volume: Volume level (0.0 to 1.0)
        """
        self.rate = rate
        self.volume = volume
        self.current_language = 'en'
        self.platform = platform.system()
        
        # Edge-TTS voice mapping (LANGUAGE-NATIVE NEURAL VOICES)
        # CRITICAL: Each language uses its native voice model
        self.edge_voices = {
            'en': 'en-US-AriaNeural',      # Native English voice
            'hi': 'hi-IN-SwaraNeural',     # Native Hindi voice (NOT English reading Hindi)
            'kn': 'kn-IN-SapnaNeural'      # Native Kannada voice (NOT English reading Kannada)
        }
        
        # gTTS language codes (also language-native)
        self.gtts_langs = {
            'en': 'en',  # English TTS
            'hi': 'hi',  # Hindi TTS (native pronunciation)
            'kn': 'kn'   # Kannada TTS (native pronunciation)
        }
        
        # Initialize pyttsx3 if available (limited language support)
        self.pyttsx3_engine = None
        if PYTTSX3_AVAILABLE:
            try:
                self.pyttsx3_engine = pyttsx3.init()
                self.pyttsx3_engine.setProperty('rate', self.rate)
                self.pyttsx3_engine.setProperty('volume', self.volume)
                logger.info("✅ pyttsx3 initialized")
            except Exception as e:
                logger.warning(f"pyttsx3 initialization failed: {e}")
                self.pyttsx3_engine = None
        
        # Log available backends
        backends = []
        if EDGE_TTS_AVAILABLE:
            backends.append("edge-tts (neural, language-native)")
        if GTTS_AVAILABLE:
            backends.append("gTTS (language-native)")
        if self.pyttsx3_engine:
            backends.append("pyttsx3 (limited)")
        
        logger.info(f"TTS backends available: {', '.join(backends) if backends else 'None'}")
        print(f"TTS backends: {', '.join(backends) if backends else 'None'}")
    
    def speak(self, text: str, language: Optional[str] = None):
        """
        Speak text using language-native TTS
        CRITICAL: Uses the correct voice model for each language
        
        Args:
            text: Text to speak
            language: Language code (en, hi, kn). If None, uses current_language
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to TTS")
            return
        
        # Use provided language or current language
        lang = language or self.current_language
        
        # Validate language
        if lang not in ['en', 'hi', 'kn']:
            logger.warning(f"Unsupported language: {lang}, defaulting to English")
            lang = 'en'
        
        logger.info(f"Speaking ({lang}): {text[:50]}...")
        print(f"🔊 Speaking ({lang}): {text[:50]}...")
        
        # Try backends in priority order
        # Priority: edge-tts (best) > gTTS (good) > pyttsx3 (fallback)
        
        # 1. Try edge-tts (BEST - neural, language-native voices)
        if EDGE_TTS_AVAILABLE and lang in self.edge_voices:
            try:
                success = self._speak_edge_tts(text, lang)
                if success:
                    logger.info(f"✅ Spoke using edge-tts ({lang} native voice)")
                    return
            except Exception as e:
                logger.warning(f"edge-tts failed: {e}")
        
        # 2. Try gTTS (GOOD - language-native pronunciation)
        if GTTS_AVAILABLE and lang in self.gtts_langs:
            try:
                success = self._speak_gtts(text, lang)
                if success:
                    logger.info(f"✅ Spoke using gTTS ({lang} native voice)")
                    return
            except Exception as e:
                logger.warning(f"gTTS failed: {e}")
        
        # 3. Fallback to pyttsx3 (LIMITED - mainly English)
        if self.pyttsx3_engine:
            try:
                success = self._speak_pyttsx3(text, lang)
                if success:
                    logger.info(f"✅ Spoke using pyttsx3 (limited {lang} support)")
                    return
            except Exception as e:
                logger.warning(f"pyttsx3 failed: {e}")
        
        # If all backends failed
        logger.error(f"❌ All TTS backends failed for language: {lang}")
        print(f"❌ TTS Error: Could not speak text in {lang}")
    
    def _speak_edge_tts(self, text: str, language: str) -> bool:
        """
        Speak using edge-tts (LANGUAGE-NATIVE neural voices)
        
        Args:
            text: Text to speak
            language: Language code
            
        Returns:
            True if successful, False otherwise
        """
        try:
            voice = self.edge_voices.get(language)
            if not voice:
                return False
            
            logger.info(f"Using edge-tts voice: {voice} for language: {language}")
            
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_filename = temp_file.name
            
            # Generate speech asynchronously
            async def generate_speech():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(temp_filename)
            
            # Run async function
            asyncio.run(generate_speech())
            
            # Play the audio using pygame
            if GTTS_AVAILABLE:  # Use pygame from gTTS
                pygame.mixer.music.load(temp_filename)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
            
            # Clean up
            try:
                os.unlink(temp_filename)
            except:
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"edge-tts error: {e}")
            return False
    
    def _speak_gtts(self, text: str, language: str) -> bool:
        """
        Speak using gTTS (LANGUAGE-NATIVE pronunciation)
        
        Args:
            text: Text to speak
            language: Language code
            
        Returns:
            True if successful, False otherwise
        """
        try:
            tts_lang = self.gtts_langs.get(language, 'en')
            
            logger.info(f"Using gTTS language: {tts_lang} for language: {language}")
            
            # Generate speech with language-native pronunciation
            tts = gTTS(text=text, lang=tts_lang, slow=False)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_filename = temp_file.name
                tts.save(temp_filename)
            
            # Play the audio
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            
            # Clean up
            try:
                os.unlink(temp_filename)
            except:
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"gTTS error: {e}")
            return False
    
    def _speak_pyttsx3(self, text: str, language: str) -> bool:
        """
        Speak using pyttsx3 (LIMITED language support, mainly English)
        WARNING: pyttsx3 has poor support for Hindi/Kannada
        
        Args:
            text: Text to speak
            language: Language code
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.pyttsx3_engine:
                return False
            
            # pyttsx3 has very limited language support
            # It will try to speak but pronunciation may be poor for non-English
            logger.warning(f"Using pyttsx3 for {language} - pronunciation may be poor")
            
            self.pyttsx3_engine.say(text)
            self.pyttsx3_engine.runAndWait()
            
            return True
            
        except Exception as e:
            logger.error(f"pyttsx3 error: {e}")
            return False
    
    def set_language(self, language_code: str):
        """
        Set the current language for TTS
        
        Args:
            language_code: Language code (en, hi, kn)
        """
        if language_code in ['en', 'hi', 'kn']:
            self.current_language = language_code
            logger.info(f"TTS language set to: {language_code}")
        else:
            logger.warning(f"Unsupported language: {language_code}, keeping {self.current_language}")
    
    def stop(self):
        """Stop any ongoing speech"""
        try:
            if GTTS_AVAILABLE:
                pygame.mixer.music.stop()
            if self.pyttsx3_engine:
                self.pyttsx3_engine.stop()
        except Exception as e:
            logger.warning(f"Error stopping TTS: {e}")
    
    def get_available_backends(self) -> list:
        """Get list of available TTS backends"""
        backends = []
        if EDGE_TTS_AVAILABLE:
            backends.append('edge-tts')
        if GTTS_AVAILABLE:
            backends.append('gTTS')
        if self.pyttsx3_engine:
            backends.append('pyttsx3')
        return backends
    
    def test_voice(self, language: str):
        """
        Test TTS voice for a specific language
        
        Args:
            language: Language code to test
        """
        test_phrases = {
            'en': 'Hello, this is a test of the English voice.',
            'hi': 'नमस्ते, यह हिंदी आवाज का परीक्षण है।',
            'kn': 'ನಮಸ್ಕಾರ, ಇದು ಕನ್ನಡ ಧ್ವನಿಯ ಪರೀಕ್ಷೆ.'
        }
        
        phrase = test_phrases.get(language, test_phrases['en'])
        print(f"\nTesting {language} voice...")
        print(f"Phrase: {phrase}")
        self.speak(phrase, language)
