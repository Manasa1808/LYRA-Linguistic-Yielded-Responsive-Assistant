"""
Enhanced Multilingual Processor for LYRA Voice Assistant
Handles robust language detection and minimal text processing
CRITICAL: Includes Unicode normalization for Kannada/Hindi
CRITICAL: Includes phonetic keyword mapping for romanized ASR output
"""

import re
import logging
import unicodedata
from typing import Optional, List, Dict, Tuple

logger = logging.getLogger(__name__)


class MultilingualTextProcessor:
    """
    Enhanced text processor with:
    - Robust language detection
    - Minimal text cleaning (no corruption)
    - Validation utilities
    - Phonetic keyword mapping for romanized ASR
    """
    
    def __init__(self):
        # Language detection patterns (Unicode ranges)
        self.lang_patterns = {
            'kn': re.compile(r'[\u0C80-\u0CFF]'),  # Kannada Unicode range
            'hi': re.compile(r'[\u0900-\u097F]'),  # Devanagari (Hindi) Unicode range
            'en': re.compile(r'[a-zA-Z]')          # English (Latin alphabet)
        }
        
        # Language names for logging
        self.lang_names = {
            'en': 'English',
            'hi': 'Hindi',
            'kn': 'Kannada'
        }
        
        # Phonetic keyword mapping for romanized ASR output
        # Maps common romanized words to English equivalents
        self.phonetic_map = {
            # App names
            'calculator': 'calculator',
            'calc': 'calculator',
            'kalkulater': 'calculator',
            'kalkulator': 'calculator',
            
            'notepad': 'notepad',
            'nota': 'notepad',
            'notpad': 'notepad',
            'note': 'notepad',
            'pad': 'notepad',
            
            'browser': 'browser',
            'brove': 'browser',
            'brave': 'brave',
            'brav': 'brave',
            'chrome': 'chrome',
            'krom': 'chrome',
            
            # Actions
            'open': 'open',
            'therey': 'open',
            'tere': 'open',
            'kholo': 'open',
            'kolo': 'open',
            
            'close': 'close',
            'band': 'close',
            'bund': 'close',
            
            # Common words
            'please': 'please',
            'dayavittu': 'please',
            'kripya': 'please',
        }
    
    def detect_language(self, text: str) -> str:
        """
        Robust language detection from text using character analysis
        
        Args:
            text: Input text
            
        Returns:
            Language code: 'en', 'hi', or 'kn'
        """
        if not text or not text.strip():
            return 'en'
        
        text = text.strip()
        
        # Count characters for each language
        counts = {'kn': 0, 'hi': 0, 'en': 0}
        total_chars = 0
        
        for char in text:
            # Skip whitespace and punctuation
            if char.isspace() or not char.isalnum():
                continue
                
            total_chars += 1
            
            # Check which language this character belongs to
            for lang, pattern in self.lang_patterns.items():
                if pattern.match(char):
                    counts[lang] += 1
                    break
        
        # If very short or no alphanumeric characters, default to English
        if total_chars < 2:
            logger.debug(f"Text too short for language detection: '{text}'")
            return 'en'
        
        # Calculate percentages
        percentages = {lang: (count / total_chars * 100) if total_chars > 0 else 0 
                      for lang, count in counts.items()}
        
        # Get language with highest percentage
        detected_lang = max(percentages, key=percentages.get)
        detected_percentage = percentages[detected_lang]
        
        # Require at least 30% of characters to be from detected language
        # This prevents misdetection on mixed or ambiguous text
        if detected_percentage < 30:
            logger.debug(f"No clear language winner (max: {detected_percentage:.1f}%), defaulting to English")
            return 'en'
        
        logger.info(f"Detected language: {self.lang_names[detected_lang]} ({detected_percentage:.1f}% confidence)")
        logger.debug(f"Language distribution: {percentages}")
        
        return detected_lang
    
    def normalize_unicode(self, text: str) -> str:
        """
        Normalize Unicode text to NFC form
        CRITICAL: Required for proper Kannada/Hindi text processing
        
        Args:
            text: Input text (may be in NFD, NFKC, etc.)
            
        Returns:
            NFC normalized text
        """
        if not text:
            return ""
        
        # Normalize to NFC (Canonical Composition)
        # This ensures consistent Unicode representation
        normalized = unicodedata.normalize('NFC', text)
        
        return normalized
    
    def clean_text(self, text: str) -> str:
        """
        Minimal text cleaning with Unicode normalization
        CRITICAL: Normalizes Unicode FIRST, then cleans whitespace
        
        Args:
            text: Input text
            
        Returns:
            Cleaned and normalized text
        """
        if not text:
            return ""
        
        # Step 1: Normalize Unicode (NFC form)
        text = self.normalize_unicode(text)
        
        # Step 2: Only remove excessive whitespace
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def is_valid_text(self, text: str, min_length: int = 2) -> bool:
        """
        Check if text is valid (not just noise or punctuation)
        
        Args:
            text: Input text
            min_length: Minimum length for valid text
            
        Returns:
            True if valid text, False otherwise
        """
        if not text or not text.strip():
            return False
        
        text = text.strip()
        
        # Check minimum length
        if len(text) < min_length:
            return False
        
        # Check if it's just punctuation or numbers
        if re.match(r'^[\W\d]+$', text):
            return False
        
        # Check if it has at least some alphanumeric characters
        alphanumeric_count = sum(1 for c in text if c.isalnum())
        if alphanumeric_count < min_length:
            return False
        
        return True
    
    def extract_command_keywords(self, text: str, language: str) -> List[str]:
        """
        Extract potential command keywords from text
        Useful for debugging and analysis
        
        Args:
            text: Input text
            language: Language code
            
        Returns:
            List of keywords
        """
        # Clean text
        text = self.clean_text(text)
        
        # Split into words
        words = text.split()
        
        # Remove very short words (likely articles, etc.)
        keywords = [word for word in words if len(word) > 2]
        
        return keywords
    
    def detect_mixed_language(self, text: str) -> Dict[str, float]:
        """
        Detect if text contains mixed languages and their proportions
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with language percentages
        """
        if not text or not text.strip():
            return {'en': 100.0}
        
        text = text.strip()
        
        # Count characters for each language
        counts = {'kn': 0, 'hi': 0, 'en': 0}
        total_chars = 0
        
        for char in text:
            if char.isspace() or not char.isalnum():
                continue
                
            total_chars += 1
            
            for lang, pattern in self.lang_patterns.items():
                if pattern.match(char):
                    counts[lang] += 1
                    break
        
        if total_chars == 0:
            return {'en': 100.0}
        
        # Calculate percentages
        percentages = {lang: (count / total_chars * 100) 
                      for lang, count in counts.items()}
        
        # Filter out languages with 0%
        percentages = {lang: pct for lang, pct in percentages.items() if pct > 0}
        
        return percentages
    
    def normalize_phonetic(self, text: str) -> str:
        """
        Normalize romanized/phonetic text to proper English
        CRITICAL: For handling romanized ASR output
        
        Args:
            text: Romanized text (e.g., "calculator therey")
            
        Returns:
            Normalized English text (e.g., "open calculator")
        """
        if not text:
            return ""
        
        text = text.lower().strip()
        words = text.split()
        normalized_words = []
        
        for word in words:
            # Check if word is in phonetic map
            if word in self.phonetic_map:
                normalized_words.append(self.phonetic_map[word])
            else:
                # Keep original word
                normalized_words.append(word)
        
        result = ' '.join(normalized_words)
        logger.info(f"Phonetic normalization: '{text}' -> '{result}'")
        return result
    
    def process_text_with_translation(self, text: str) -> Tuple[str, str, str]:
        """
        Process text with automatic language detection and translation
        CRITICAL: This method can be called by main.py to get automatic translation
        
        Args:
            text: Input text (any language)
            
        Returns:
            Tuple of (english_text, detected_language, original_text)
        """
        # Clean and normalize
        original_text = self.clean_text(text)
        
        # Detect language
        detected_lang = self.detect_language(original_text)
        
        # If not English, try to translate
        if detected_lang != 'en':
            try:
                from core.translation_engine import get_translation_engine
                translator = get_translation_engine()
                
                if translator.is_available():
                    english_text = translator.translate_to_english(original_text, detected_lang)
                    logger.info(f"Translated {detected_lang} -> en: '{original_text}' -> '{english_text}'")
                    return english_text, detected_lang, original_text
                else:
                    logger.warning("Translation not available, returning original text")
                    return original_text, detected_lang, original_text
            except Exception as e:
                logger.error(f"Translation error: {e}")
                return original_text, detected_lang, original_text
        else:
            # Already English or romanized - try phonetic normalization
            normalized = self.normalize_phonetic(original_text)
            return normalized, 'en', original_text
    
    def normalize_for_comparison(self, text: str) -> str:
        """
        Normalize text for comparison purposes
        (e.g., comparing user input with command patterns)
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = self.clean_text(text)
        
        # Remove common punctuation
        text = re.sub(r'[.,!?;:]', '', text)
        
        return text


# Deprecated classes kept for backward compatibility
class MultilingualIntentMapper:
    """DEPRECATED: Use translation_engine instead"""
    
    def __init__(self):
        logger.warning("MultilingualIntentMapper is deprecated. Use translation_engine instead.")
    
    def map_to_intent(self, text: str, language: str) -> Optional[str]:
        """Deprecated - returns None"""
        return None


class MultilingualResponseGenerator:
    """DEPRECATED: Use translation_engine instead"""
    
    def __init__(self):
        logger.warning("MultilingualResponseGenerator is deprecated. Use translation_engine instead.")
    
    def get_response(self, intent: str, language: str, **kwargs) -> str:
        """Deprecated - returns empty string"""
        return ""
