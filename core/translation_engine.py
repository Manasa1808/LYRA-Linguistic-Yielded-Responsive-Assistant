"""
Enhanced Translation Engine for LYRA Voice Assistant
Handles robust translation between English, Kannada, and Hindi
"""

import logging
from typing import Optional, Dict
from functools import lru_cache
import time

logger = logging.getLogger(__name__)

# Try to import googletrans
try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False
    logger.warning("googletrans not available. Install with: pip install googletrans==4.0.0rc1")


class TranslationEngine:
    """
    Enhanced translation engine with:
    - Robust error handling
    - Retry logic
    - Translation validation
    - Caching for performance
    """
    
    def __init__(self):
        self.translator = None
        self.supported_languages = ['en', 'hi', 'kn']
        self.max_retries = 3
        self.retry_delay = 0.5  # seconds
        
        if GOOGLETRANS_AVAILABLE:
            try:
                self.translator = Translator()
                logger.info("✅ Translation engine initialized successfully")
                print("✅ Translation engine initialized")
            except Exception as e:
                logger.error(f"Failed to initialize translator: {e}")
                self.translator = None
        else:
            logger.warning("⚠️ Translation unavailable - googletrans not installed")
            print("⚠️ Translation unavailable - install googletrans")
    
    @lru_cache(maxsize=1000)
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text with retry logic and validation
        
        Args:
            text: Text to translate
            source_lang: Source language code (en, hi, kn)
            target_lang: Target language code (en, hi, kn)
            
        Returns:
            Translated text, or original text if translation fails
        """
        # No translation needed if same language
        if source_lang == target_lang:
            return text
        
        # Return original if translator not available
        if not self.translator:
            logger.warning(f"Translation unavailable: {source_lang} -> {target_lang}")
            return text
        
        # Validate languages
        if source_lang not in self.supported_languages or target_lang not in self.supported_languages:
            logger.warning(f"Unsupported language pair: {source_lang} -> {target_lang}")
            return text
        
        # Validate text
        if not text or not text.strip():
            return text
        
        # Try translation with retries
        for attempt in range(self.max_retries):
            try:
                # Perform translation
                result = self.translator.translate(text, src=source_lang, dest=target_lang)
                translated_text = result.text
                
                # Validate translation
                if translated_text and translated_text.strip():
                    logger.info(f"Translated ({source_lang} -> {target_lang}): '{text}' -> '{translated_text}'")
                    return translated_text
                else:
                    logger.warning(f"Empty translation result, attempt {attempt + 1}/{self.max_retries}")
                    
            except Exception as e:
                logger.error(f"Translation error (attempt {attempt + 1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    # Reinitialize translator on error
                    try:
                        self.translator = Translator()
                    except:
                        pass
        
        # If all retries failed, return original text
        logger.error(f"Translation failed after {self.max_retries} attempts, returning original text")
        return text
    
    def translate_to_english(self, text: str, source_lang: str) -> str:
        """
        Translate text to English for command processing
        CRITICAL: Command processor MUST receive English text only
        
        Args:
            text: Text to translate
            source_lang: Source language code (en, hi, kn)
            
        Returns:
            English translation
        """
        if source_lang == 'en':
            return text
        
        logger.info(f"Translating to English from {source_lang}: '{text}'")
        english_text = self.translate(text, source_lang, 'en')
        logger.info(f"English result: '{english_text}'")
        
        return english_text
    
    def translate_from_english(self, text: str, target_lang: str) -> str:
        """
        Translate English response back to user's language
        CRITICAL: User MUST hear response in their spoken language
        
        Args:
            text: English text to translate
            target_lang: Target language code (en, hi, kn)
            
        Returns:
            Translated text
        """
        if target_lang == 'en':
            return text
        
        logger.info(f"Translating from English to {target_lang}: '{text}'")
        translated_text = self.translate(text, 'en', target_lang)
        logger.info(f"{target_lang} result: '{translated_text}'")
        
        return translated_text
    
    def is_available(self) -> bool:
        """Check if translation is available"""
        return self.translator is not None
    
    def clear_cache(self):
        """Clear translation cache"""
        self.translate.cache_clear()
        logger.info("Translation cache cleared")
    
    def validate_translation(self, original: str, translated: str, source_lang: str, target_lang: str) -> bool:
        """
        Validate translation quality
        
        Args:
            original: Original text
            translated: Translated text
            source_lang: Source language
            target_lang: Target language
            
        Returns:
            True if translation seems valid
        """
        # Basic validation checks
        if not translated or not translated.strip():
            return False
        
        # Check if translation is same as original (might indicate failure)
        if original.strip() == translated.strip():
            # This is OK if languages are same, but suspicious otherwise
            if source_lang != target_lang:
                logger.warning(f"Translation unchanged: '{original}' -> '{translated}'")
                return False
        
        # Check length ratio (translated text shouldn't be too different in length)
        length_ratio = len(translated) / len(original) if len(original) > 0 else 0
        if length_ratio < 0.3 or length_ratio > 3.0:
            logger.warning(f"Suspicious length ratio: {length_ratio}")
            return False
        
        return True


# Singleton instance
_translation_engine = None

def get_translation_engine() -> TranslationEngine:
    """Get or create translation engine singleton"""
    global _translation_engine
    if _translation_engine is None:
        _translation_engine = TranslationEngine()
    return _translation_engine
