# main.py - Clean Architecture: ASR → Command Processor → Feature Modules
# speech → text → intent → feature → system call

from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
import sys, os
from datetime import datetime, timedelta
import time
import re
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import VoiceAssistantGUI
from gui.login_window import LoginWindow
from core.audio_handler import AudioHandler
from core.speech_recognition import SpeechRecognizer
from core.tts_engine import TTSEngine
from core.command_processor import CommandProcessor
from features.app_controller import AppController
from features.utility_features import UtilityFeatures
from auth.profile_manager import ProfileManager
from database.db_manager import DatabaseManager
from features.custom_commands import CustomCommandsManager
from features.reminder_manager import ReminderManager
from features.calendar_manager import CalendarManager
from features.email_handler import EmailHandler
from features.whatsapp_handler import WhatsAppHandler
from features.notes_manager import NotesManager
from auth.face_recognition import FaceRecognition
from config import DEFAULT_LANGUAGE


# ═══════════════════════════════════════════════════════════════════
# FEATURE 2: EMOTIONAL ANALYZER CLASS
# ═══════════════════════════════════════════════════════════════════
class EmotionalAnalyzer:
    """Analyze emotional tone from text input in English, Hindi, and Kannada"""

    def __init__(self):
        self.emotion_keywords = {
            'happy': {
                'en': ['happy', 'great', 'awesome', 'wonderful', 'excited', 'fantastic',
                       'excellent', 'good', 'joy', 'glad', 'amazing', 'perfect', 'love',
                       'thrilled', 'delighted', 'cheerful', 'super', 'yay', 'woohoo'],
                'hi': ['खुश', 'बढ़िया', 'शानदार', 'अच्छा', 'उत्साहित', 'प्रसन्न', 'मस्त',
                       'धन्यवाद', 'अद्भुत', 'मजा', 'बहुत अच्छा', 'सुखी', 'खुशी'],
                'kn': ['ಸಂತೋಷ', 'ಒಳ್ಳೆಯದು', 'ಅದ್ಭುತ', 'ಉತ್ತಮ', 'ಸಂತಸ', 'ಸುಖ', 'ಮೆಚ್ಚು',
                       'ಅದ್ಬುತ', 'ಚೆನ್ನಾಗಿದೆ', 'ಖುಷಿ', 'ರೋಮಾಂಚಕ']
            },
            'sad': {
                'en': ['sad', 'unhappy', 'depressed', 'down', 'upset', 'disappointed',
                       'terrible', 'bad', 'awful', 'cry', 'miserable', 'gloomy', 'hurt',
                       'lonely', 'pain', 'sorry', 'worried', 'stressed', 'anxious'],
                'hi': ['दुखी', 'उदास', 'खराब', 'निराश', 'परेशान', 'बुरा', 'रोना', 'चिंता',
                       'तकलीफ', 'दर्द', 'अकेला', 'घबराहट', 'तनाव', 'मुश्किल'],
                'kn': ['ದುಃಖ', 'ನೊಂದ', 'ಕೆಟ್ಟದ್ದು', 'ನಿರಾಶೆ', 'ಚಿಂತೆ', 'ತೊಂದರೆ', 'ನೋವು',
                       'ಏಕಾಂಗಿ', 'ಕಷ್ಟ', 'ಬೇಸರ']
            },
            'okay': {
                'en': ['okay', 'ok', 'fine', 'alright', 'average', 'normal', 'so-so',
                       'sure', 'yes', 'yeah', 'right', 'understood', 'got it'],
                'hi': ['ठीक', 'ओके', 'सामान्य', 'चलेगा', 'हां', 'समझ गया', 'हो गया', 'अच्छा'],
                'kn': ['ಸರಿ', 'ಓಕೆ', 'ಚೆನ್ನಾಗಿದೆ', 'ಸಾಮಾನ್ಯ', 'ಹೌದು', 'ಅರ್ಥವಾಯಿತು']
            }
        }

        # Contextual phrases for better detection
        self.emotion_phrases = {
            'happy': {
                'en': ["i'm happy", "feeling great", "i feel good", "i'm excited", "this is great"],
                'hi': ["मैं खुश हूं", "अच्छा लग रहा है", "बहुत अच्छा", "मजा आ रहा"],
                'kn': ["ನಾನು ಸಂತೋಷವಾಗಿದ್ದೇನೆ", "ಚೆನ್ನಾಗಿ ಅನಿಸುತ್ತಿದೆ", "ತುಂಬಾ ಚೆನ್ನಾಗಿದೆ"]
            },
            'sad': {
                'en': ["i'm sad", "feeling down", "not good", "i'm upset", "feeling bad"],
                'hi': ["मैं दुखी हूं", "अच्छा नहीं लग रहा", "परेशान हूं", "उदास हूं"],
                'kn': ["ನಾನು ದುಃಖವಾಗಿದ್ದೇನೆ", "ಒಳ್ಳೆಯದಿಲ್ಲ", "ಚಿಂತೆಯಾಗಿದೆ"]
            },
            'okay': {
                'en': ["i'm okay", "it's fine", "alright", "all good"],
                'hi': ["मैं ठीक हूं", "सब ठीक है", "चलेगा"],
                'kn': ["ನಾನು ಸರಿಯಾಗಿದ್ದೇನೆ", "ಎಲ್ಲಾ ಚೆನ್ನಾಗಿದೆ"]
            }
        }

    def detect_emotion(self, text):
        """Detect emotion from text - returns: happy, sad, okay, or neutral"""
        text_lower = text.lower().strip()

        # First check for contextual phrases (more accurate)
        for emotion, lang_phrases in self.emotion_phrases.items():
            for lang, phrases in lang_phrases.items():
                for phrase in phrases:
                    if phrase in text_lower:
                        return emotion

        # Then check for individual keywords
        emotion_scores = {'happy': 0, 'sad': 0, 'okay': 0}

        for emotion, lang_keywords in self.emotion_keywords.items():
            for lang, keywords in lang_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        emotion_scores[emotion] += 1

        # Return emotion with highest score, or neutral if no emotions detected
        max_emotion = max(emotion_scores, key=emotion_scores.get)
        if emotion_scores[max_emotion] > 0:
            return max_emotion

        return 'neutral'

    def get_emotional_response(self, emotion, language='en'):
        """Get appropriate empathetic response based on emotion"""
        responses = {
            'happy': {
                'en': "That's wonderful! I'm so glad to hear that! 😊 How can I assist you today?",
                'hi': "यह बहुत अच्छा है! मुझे यह सुनकर बहुत खुशी हुई! 😊 मैं आज आपकी कैसे मदद कर सकता हूं?",
                'kn': "ಅದು ಅದ್ಭುತವಾಗಿದೆ! ಅದನ್ನು ಕೇಳಲು ನನಗೆ ತುಂಬಾ ಸಂತೋಷವಾಗಿದೆ! 😊 ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?"
            },
            'sad': {
                'en': "I'm sorry to hear that. 😔 I'm here for you. Is there anything I can do to help or cheer you up?",
                'hi': "मुझे यह सुनकर दुख हुआ। 😔 मैं आपके लिए यहां हूं। क्या मैं कुछ मदद कर सकता हूं या आपको खुश कर सकता हूं?",
                'kn': "ಅದನ್ನು ಕೇಳಲು ನನಗೆ ವಿಷಾದವಾಗಿದೆ। 😔 ನಾನು ನಿಮಗಾಗಿ ಇಲ್ಲಿದ್ದೇನೆ। ನಾನು ಏನಾದರೂ ಸಹಾಯ ಮಾಡಬಹುದೇ ಅಥವಾ ನಿಮ್ಮನ್ನು ಸಂತೋಷಪಡಿಸಬಹುದೇ?"
            },
            'okay': {
                'en': "Okay, got it. 👍 What would you like me to do for you?",
                'hi': "ठीक है, समझ गया। 👍 आप चाहते हैं कि मैं आपके लिए क्या करूं?",
                'kn': "ಸರಿ, ಅರ್ಥವಾಯಿತು। 👍 ನಾನು ನಿಮಗಾಗಿ ಏನು ಮಾಡಬೇಕೆಂದು ಬಯಸುತ್ತೀರಿ?"
            },
            'neutral': {
                'en': "I'm listening. How can I help you?",
                'hi': "मैं सुन रहा हूं। मैं आपकी कैसे मदद कर सकता हूं?",
                'kn': "ನಾನು ಕೇಳುತ್ತಿದ್ದೇನೆ। ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?"
            }
        }

        return responses.get(emotion, responses['neutral']).get(language, responses[emotion]['en'])


# ═══════════════════════════════════════════════════════════════════
# MAIN VOICE ASSISTANT CLASS - CLEAN ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════
class VoiceAssistant:
    def __init__(self, username="User", profile_manager=None, db_manager=None, gui=None):
        self.current_user = username
        self.profile_manager = profile_manager
        self.db = db_manager
        self.gui = gui
        self.current_language = DEFAULT_LANGUAGE

        # Core modules - CLEAN ARCHITECTURE
        self.audio_handler = AudioHandler()
        self.speech_recognizer = SpeechRecognizer(model_name='base', lazy_load=True)
        self.tts = TTSEngine()
        self.command_processor = CommandProcessor()  # INTENT DETECTION ONLY

        # Feature modules - SYSTEM CALLS HAPPEN HERE
        self.app_controller = AppController()
        self.utils = UtilityFeatures()
        self.custom_commands = CustomCommandsManager(self.db)

        # ✅ FEATURE 2: Emotional analyzer
        self.emotion_analyzer = EmotionalAnalyzer()

        # Features - DATABASE OPERATIONS
        self.reminder_manager = ReminderManager(self.db)
        self.calendar_manager = CalendarManager(self.db)
        self.notes_manager = NotesManager(self.db)
        self.email_handler = EmailHandler()
        self.whatsapp_handler = WhatsAppHandler()

        # ✅ FEATURE 3: Voice isolation state management
        self.assistant_state = "ready"
        self.is_continuous_listening = False
        self.state_lock = threading.Lock()

        # Start reminder notification thread
        if self.gui:
            self._start_gui_reminder_listener()

    def _is_noise_or_unintended(self, text):
        """Check if text appears to be noise or unintended speech"""
        text = text.lower().strip()

        # Common noise patterns
        noise_patterns = [
            r'^[uhm]+$',  # Just "uh", "hmm", etc.
            r'^[a-z]\s*$',  # Single letters
            r'^\W+$',  # Only punctuation
            r'^(ha|haha|hehe|lol)+$',  # Laughter without context
            r'^\d+\s*\d*$',  # Just numbers
            r'^(yes|no|okay|ok|yeah|yep|sure|right|wrong)$',  # Single words without context
        ]

        for pattern in noise_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True

        # Check for very short phrases that are likely fragments
        words = text.split()
        if len(words) <= 2 and len(text) < 10:
            # Allow common command starters
            command_starters = ['open', 'close', 'play', 'stop', 'show', 'tell', 'what', 'how', 'when', 'where']
            if not any(word in command_starters for word in words):
                return True

        return False

    def set_language(self, language):
        """Set the current language"""
        self.current_language = language
        if self.gui:
            self.gui.update_language_display(language)

    def _start_gui_reminder_listener(self):
        """Background thread for reminder notifications"""
        def listener():
            while True:
                try:
                    user_id = getattr(self.profile_manager, "current_user_id", None)
                    if not user_id:
                        time.sleep(5)
                        continue

                    now = datetime.now()
                    reminders = self.reminder_manager.get_due_reminders(user_id, now)

                    for rem in reminders:
                        msg = f"⏰ Reminder: {rem['title']}"
                        if rem['description']:
                            msg += f" - {rem['description']}"

                        if self.gui:
                            self.gui.reminder_signal.emit(msg)

                        self.reminder_manager.mark_notified(rem["reminder_id"])

                    time.sleep(10)

                except Exception as e:
                    print(f"Reminder Listener Error: {e}")
                    time.sleep(10)

        threading.Thread(target=listener, daemon=True).start()

    # ═══════════════════════════════════════════════════════════════════
    # ✅ FEATURE 1: CONTINUOUS LISTENING WITH VOICE ISOLATION
    # ═══════════════════════════════════════════════════════════════════
    def start_continuous_listening(self):
        """Start continuous listening mode with direct voice detection"""
        self.is_continuous_listening = True
        self.voice_activity_counter = 0
        self.silence_counter = 0

        def continuous_callback(audio_data):
            """Callback for continuous audio processing with direct detection"""
            try:
                # More sensitive voice activity detection for natural speech
                has_voice = self.audio_handler.detect_voice_activity(audio_data, threshold=0.008, min_duration=0.15)

                with self.state_lock:
                    current_state = self.assistant_state

                # Direct detection logic - no complex state management
                if has_voice:
                    self.voice_activity_counter += 1
                    self.silence_counter = 0

                    # If we detect voice and we're ready, start processing immediately
                    if current_state == "ready" and self.voice_activity_counter >= 1:
                        with self.state_lock:
                            self.assistant_state = "listening"
                        if self.gui:
                            self.gui.update_state_signal.emit("listening")
                        print("🎤 Voice detected - Processing immediately")
                        self._process_voice_command(audio_data)

                else:
                    self.silence_counter += 1
                    self.voice_activity_counter = 0

                    # Quick return to ready state after brief silence
                    if self.silence_counter >= 3 and current_state == "listening":
                        with self.state_lock:
                            self.assistant_state = "ready"
                        if self.gui:
                            self.gui.update_state_signal.emit("ready")
                        print("🔇 Silence detected - Back to READY mode")

            except Exception as e:
                error_msg = f"Continuous listening error: {e}"
                print(f"❌ {error_msg}")
                import traceback
                traceback.print_exc()

                # Reset to ready state on error
                with self.state_lock:
                    self.assistant_state = "ready"
                if self.gui:
                    self.gui.update_state_signal.emit("ready")

        # Start continuous recording with shorter chunks for more responsive detection
        self.audio_handler.start_continuous_recording(continuous_callback, chunk_duration=2)

        # Start in READY state
        with self.state_lock:
            self.assistant_state = "ready"

        if self.gui:
            self.gui.update_state_signal.emit("ready")

        print("🎤 Continuous listening started - Direct voice detection enabled")

    def _process_voice_command(self, audio_data):
        """Process voice command when voice activity is confirmed"""
        try:
            # Transcribe audio
            if not self.speech_recognizer.is_loaded():
                print("⚠️ Whisper model not loaded yet, skipping audio processing")
                return

            result = self.speech_recognizer.transcribe(audio_data, language=self.current_language)
            command_text = result.get('text', '').strip()
            detected_language = result.get('language', self.current_language)

            # Enhanced filtering: check confidence, length, and content
            confidence = result.get('confidence', 0.0)
            if (command_text and
                len(command_text) > 4 and
                confidence > 0.4 and
                not self._is_noise_or_unintended(command_text)):

                print(f"🎤 Heard (confidence: {confidence:.2f}, lang: {detected_language}): {command_text}")

                # Update GUI using signal (thread-safe)
                if self.gui:
                    self.gui.add_message_signal.emit("You (voice)", command_text)

                # Transition to TALKING state
                with self.state_lock:
                    self.assistant_state = "talking"

                if self.gui:
                    self.gui.update_state_signal.emit("talking")

                # Process command with error handling
                try:
                    response = self.process_text(command_text, language=detected_language)
                    if not response:
                        response = "I processed your command but didn't get a response."
                    print(f"✅ Response (in {detected_language}): {response}")
                except Exception as cmd_error:
                    error_msg = f"Error processing command: {str(cmd_error)}"
                    print(f"❌ {error_msg}")
                    # Provide error message in detected language
                    error_responses = {
                        "en": f"Sorry, I encountered an error: {str(cmd_error)}",
                        "hi": f"क्षमा करें, मुझे एक त्रुटि मिली: {str(cmd_error)}",
                        "kn": f"ಕ್ಷಮಿಸಿ, ನನಗೆ ಒಂದು ದೋಷ ಸಿಕ್ಕಿದೆ: {str(cmd_error)}"
                    }
                    response = error_responses.get(detected_language, error_responses["en"])

                # Update GUI using signal (thread-safe) and speak
                if self.gui:
                    self.gui.add_message_signal.emit("LYRA", response)

                # Speak response in detected language
                try:
                    self.tts.set_language(detected_language)
                    self.tts.speak(response)
                except Exception as tts_error:
                    print(f"⚠️ TTS error: {tts_error}")

                # Return to READY state after speaking
                time.sleep(1.5)

                with self.state_lock:
                    self.assistant_state = "ready"

                if self.gui:
                    self.gui.update_state_signal.emit("ready")

                # Reset counters
                self.voice_activity_counter = 0
                self.silence_counter = 0

            else:
                # Filtered out - show reason for debugging
                if command_text:
                    reason = []
                    if len(command_text) <= 4:
                        reason.append("too short")
                    if confidence <= 0.4:
                        reason.append(f"low confidence ({confidence:.2f})")
                    if self._is_noise_or_unintended(command_text):
                        reason.append("unintended content")

                    print(f"🔇 Filtered out: '{command_text}' - {', '.join(reason)}")

        except Exception as e:
            error_msg = f"Voice processing error: {e}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()

            # Reset to ready state on error
            with self.state_lock:
                self.assistant_state = "ready"
            if self.gui:
                self.gui.update_state_signal.emit("ready")

    def stop_continuous_listening(self):
        """Stop continuous listening mode"""
        self.is_continuous_listening = False
        self.audio_handler.stop_continuous_recording()

        # ✅ FEATURE 3: Return to READY state
        with self.state_lock:
            self.assistant_state = "ready"

        if self.gui:
            self.gui.update_state_signal.emit("ready")

        print("🛑 Continuous listening stopped - Returned to READY state")

    def _detect_language_unicode(self, text):
        """
        Detect language using Unicode ranges (production-grade)
        Kannada: 0C80–0CFF, Hindi (Devanagari): 0900–097F
        """
        text = text.strip()
        if not text:
            return 'en'

        # Count characters in each Unicode range
        kannada_count = 0
        hindi_count = 0
        english_count = 0

        for char in text:
            code = ord(char)
            if 0x0C80 <= code <= 0x0CFF:  # Kannada Unicode range
                kannada_count += 1
            elif 0x0900 <= code <= 0x097F:  # Devanagari (Hindi) Unicode range
                hindi_count += 1
            elif ord('a') <= code <= ord('z') or ord('A') <= code <= ord('Z'):
                english_count += 1

        # Determine language by majority vote
        max_count = max(kannada_count, hindi_count, english_count)

        if max_count == 0:  # No recognizable characters
            return 'en'
        elif kannada_count == max_count:
            return 'kn'
        elif hindi_count == max_count:
            return 'hi'
        else:
            return 'en'

    # ═══════════════════════════════════════════════════════════════════
    # ✅ FEATURE 2: TEXT PROCESSING WITH EMOTIONAL ANALYSIS
    # ═══════════════════════════════════════════════════════════════════
    def process_text(self, text, language=None):
        """Process text command - CLEAN ARCHITECTURE: route to command processor"""
        user_id = getattr(self.profile_manager, "current_user_id", None)
        lang = language or self.current_language

        # ═══════════════════════════════════════════════════════════════════
        # PRODUCTION-CRITICAL: TRANSLATION BRIDGE
        # ═══════════════════════════════════════════════════════════════════
        original_text = text.strip()
        detected_lang = self._detect_language_unicode(original_text)

        # CRITICAL: CommandProcessor MUST only see ENGLISH
        processing_text = original_text

        # Translate non-English to English for command processing
        if detected_lang != 'en':
            try:
                from core.translation_engine import get_translation_engine
                translator = get_translation_engine()

                if translator.is_available():
                    processing_text = translator.translate_to_english(original_text, detected_lang)
                    print(f"🔄 TRANSLATION BRIDGE: {detected_lang} -> en: '{original_text}' -> '{processing_text}'")
                else:
                    print(f"⚠️ Translation unavailable, processing {detected_lang} text directly")
                    processing_text = original_text

            except Exception as e:
                print(f"⚠️ Translation bridge error: {e}, using original text")
                processing_text = original_text

        # ✅ FEATURE 2: Check for emotional content FIRST (in English)
        emotion = self.emotion_analyzer.detect_emotion(processing_text)

        # If text is purely emotional, respond with empathy
        if emotion != 'neutral' and len(processing_text.split()) < 15:
            is_command = False

            # Check if there's actually a command in the text (in English)
            cmd_result = self.command_processor.process_command(processing_text)
            if cmd_result.get('intent') and cmd_result.get('confidence', 0) > 0.6:
                is_command = True

            # If no command detected, return emotional response
            if not is_command:
                response = self.emotion_analyzer.get_emotional_response(emotion, detected_lang)
                # Translate response back if needed
                if detected_lang != 'en':
                    try:
                        from core.translation_engine import get_translation_engine
                        translator = get_translation_engine()
                        if translator.is_available():
                            response = translator.translate_from_english(response, detected_lang)
                    except Exception:
                        pass
                return response

        # Check custom commands (in English)
        if self.custom_commands and user_id:
            custom_cmd = self.custom_commands.match_custom_command(user_id, processing_text)
            if custom_cmd:
                success, result = self.custom_commands.execute_custom_command(custom_cmd)
                if success and isinstance(result, str):
                    # Translate response back if needed
                    if detected_lang != 'en':
                        try:
                            from core.translation_engine import get_translation_engine
                            translator = get_translation_engine()
                            if translator.is_available():
                                result = translator.translate_from_english(result, detected_lang)
                        except Exception:
                            pass
                    return result

        # CLEAN ARCHITECTURE: Route to command processor for intent detection
        # CRITICAL: CommandProcessor ONLY sees ENGLISH
        cmd_result = self.command_processor.process_command(processing_text)
        response = self.route_to_feature_module(cmd_result, detected_lang)

        # Translate response back to original language
        if detected_lang != 'en' and response:
            try:
                from core.translation_engine import get_translation_engine
                translator = get_translation_engine()
                if translator.is_available():
                    response = translator.translate_from_english(response, detected_lang)
                    print(f"🔄 RESPONSE TRANSLATION: en -> {detected_lang}: '{response}'")
            except Exception as e:
                print(f"⚠️ Response translation failed: {e}")

        # Set TTS language for response
        if detected_lang != 'en':
            self.tts.set_language(detected_lang)

        return response

    def route_to_feature_module(self, cmd_result, language=None):
        """Route detected intent to appropriate feature module - CLEAN ARCHITECTURE"""
        intent = cmd_result.get('intent')
        entities = cmd_result.get('entities', {})
        user_id = getattr(self.profile_manager, "current_user_id", None)
        lang = language or self.current_language

        # Route to feature modules based on intent
        if intent == 'get_time':
            return self.utils.get_current_time(lang)

        elif intent == 'get_date':
            return self.utils.get_current_date(lang)

        elif intent == 'get_weather':
            city = entities.get('city', 'Bengaluru')
            return self.utils.get_weather(city, lang)

        elif intent == 'tell_joke':
            return self.utils.tell_joke(lang)

        elif intent == 'get_news':
            return self.utils.get_news(lang)

        elif intent == 'open_app':
            app_name = entities.get('app_name', entities.get('entity_0', ''))
            if app_name:
                success, msg = self.app_controller.open_app(app_name)
                return msg

        elif intent == 'close_app':
            app_name = entities.get('app_name', entities.get('entity_0', ''))
            if app_name:
                success, msg = self.app_controller.close_app(app_name)
                return msg

        elif intent == 'create_reminder' and user_id:
            task = entities.get('task') or entities.get('entity_0') or "Reminder"
            time_text = entities.get('time') or entities.get('entity_1') or "later"
            due_time = self.reminder_manager.parse_reminder_time(f"{task} at {time_text}")
            self.reminder_manager.create_reminder(user_id, task, due_datetime=due_time)
            return f"Reminder set: {task} at {due_time.strftime('%I:%M %p, %d-%b-%Y')}"

        elif intent == 'create_note' and user_id:
            content = entities.get('entity_0', '')
            if content:
                self.notes_manager.create_note(user_id, "Quick Note", content)
                responses = {
                    "en": f"Note created: {content[:50]}...",
                    "hi": f"नोट बनाया गया: {content[:50]}...",
                    "kn": f"ನೋಟ್ ರಚಿಸಲಾಗಿದೆ: {content[:50]}..."
                }
                return responses.get(lang, responses["en"])

        elif intent == 'create_event' and user_id:
            title = entities.get('entity_0', 'Event')
            responses = {
                "en": f"Event created: {title}",
                "hi": f"इवेंट बनाया गया: {title}",
                "kn": f"ಈವೆಂಟ್ ರಚಿಸಲಾಗಿದೆ: {title}"
            }
            return responses.get(lang, responses["en"])

        elif intent == 'send_email':
            recipient = entities.get('recipient', entities.get('entity_0', ''))
            content = entities.get('content', entities.get('entity_1', ''))
            if recipient:
                success, msg = self.email_handler.send_email(recipient, "Message from LYRA", content)
                return msg

        elif intent == 'send_whatsapp':
            contact = entities.get('entity_0', '')
            message = entities.get('entity_1', 'Hello from LYRA!')
            if contact:
                success, msg = self.whatsapp_handler.send_message(contact, message)
                return msg

        elif intent == 'read_pdf':
            file_path = entities.get('entity_0', '')
            if file_path:
                success, msg = self.utils.read_pdf(file_path)
                return msg

        # Unknown command
        responses = {
            "en": "I didn't understand that command. Please try again.",
            "hi": "मुझे वह कमांड समझ नहीं आया। कृपया पुनः प्रयास करें।",
            "kn": "ನನಗೆ ಆ ಆಜ್ಞೆ ಅರ್ಥವಾಗಲಿಲ್ಲ। ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ।"
        }
        return responses.get(lang, responses["en"])


# ═══════════════════════════════════════════════════════════════════
# WHISPER LOADER THREAD - Loads model in background without blocking GUI
# ═══════════════════════════════════════════════════════════════════
class WhisperLoaderThread(QThread):
    """Background thread to load Whisper model without blocking GUI"""
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, speech_recognizer):
        super().__init__()
        self.speech_recognizer = speech_recognizer

    def run(self):
        """Load Whisper model in background"""
        try:
            self.speech_recognizer._load_model()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


# ═══════════════════════════════════════════════════════════════════
# MAIN FUNCTION - INITIALIZES EVERYTHING WITH FACE RECOGNITION FIX
# ═══════════════════════════════════════════════════════════════════
def main():
    print("=" * 80)
    print("🎤 LYRA - Linguistic Yielded Responsive Assistant (Windows)")
    print("=" * 80)
    print("\n✅ NEW FEATURES ENABLED:")
    print("   1. Continuous listening (mic always on)")
    print("   2. Emotional analysis (happy/sad/okay in English/Hindi/Kannada)")
    print("   3. Voice isolation (ready → listening → talking stages)")
    print("=" * 80 + "\n")

    app = QApplication(sys.argv)

    # Initialize core components
    db = DatabaseManager()
    profile_mgr = ProfileManager()

    # ✅ FIX: Properly initialize FaceRecognition (was causing NoneType error)
    try:
        face_rec = FaceRecognition()
        print("✅ Face recognition initialized successfully")
    except Exception as e:
        print(f"⚠️ Face recognition initialization failed: {e}")
        print("   Continuing without face recognition...")
        face_rec = None

    # Login with proper face_rec object
    login_window = LoginWindow(face_rec)
    if login_window.exec_() != QDialog.Accepted:
        print("❌ Login cancelled by user")
        return

    username = login_window.get_authenticated_user()
    if not username:
        print("❌ No authenticated user")
        QMessageBox.warning(None, "Login Error", "Authentication failed. Please try again.")
        return

    print(f"✅ User authenticated: {username}")

    # Login to profile
    success, preferences = profile_mgr.login(username)
    if not success:
        print(f"⚠️ Failed to load profile for {username}")

    # Create main window and assistant
    main_window = VoiceAssistantGUI(None)
    assistant = VoiceAssistant(username, profile_mgr, db, gui=main_window)
    main_window.assistant = assistant

    # Show window immediately so user sees it (before Whisper loads)
    main_window.show()

    # Show loading message
    main_window.add_message("LYRA", "🔄 Initializing speech recognition... Please wait.")
    main_window.statusBar().showMessage("Loading Whisper model... This may take a moment.")
    QApplication.processEvents()  # Process events to show the window immediately

    # Load Whisper in background thread
    def on_whisper_loaded():
        """Called when Whisper finishes loading"""
        print("✅ Whisper model loaded successfully")
        main_window.statusBar().showMessage("Ready - Click mic or type a command")

        # Greeting with information about continuous mode
        greeting_responses = {
            "en": f"Welcome back {username}. I'm LYRA, ready to assist you. Continuous listening mode is now active. Just speak naturally, and I'll respond!",
            "hi": f"स्वागत है {username}। मैं LYRA हूं, आपकी मदद के लिए तैयार। निरंतर सुनने का मोड अब सक्रिय है। बस स्वाभाविक रूप से बोलें, और मैं जवाब दूंगा!",
            "kn": f"ಸ್ವಾಗತ {username}। ನಾನು LYRA, ನಿಮಗೆ ಸಹಾಯ ಮಾಡಲು ಸಿದ್ಧ। ನಿರಂತರ ಆಲಿಸುವ ಮೋಡ್ ಈಗ ಸಕ್ರಿಯವಾಗಿದೆ। ನೈಸರ್ಗಿಕವಾಗಿ ಮಾತನಾಡಿ, ನಾನು ಪ್ರತಿಕ್ರಿಯಿಸುತ್ತೇನೆ!"
        }

        main_window.add_message("LYRA", greeting_responses[DEFAULT_LANGUAGE])
        try:
            assistant.tts.speak(greeting_responses[DEFAULT_LANGUAGE])
        except Exception as e:
            print(f"⚠️ TTS error: {e}")

        # ✅ FEATURE 1: Start continuous listening automatically after Whisper loads
        print("\n🎤 Starting continuous listening mode...")
        try:
            assistant.start_continuous_listening()
            main_window.set_continuous_mode(True)
            print("✅ Continuous listening active! Speak naturally.\n")
        except Exception as e:
            print(f"⚠️ Could not start continuous listening: {e}")
            print("   You can still use the microphone button or type commands.\n")

    def on_whisper_error(error_msg):
        """Called if Whisper loading fails"""
        print(f"❌ Whisper loading failed: {error_msg}")
        main_window.statusBar().showMessage("Speech recognition unavailable - You can still type commands")
        main_window.add_message("LYRA", f"⚠️ Speech recognition initialization failed: {error_msg}. You can still type commands.")

        # Show greeting anyway
        greeting_responses = {
            "en": f"Welcome back {username}. I'm LYRA, ready to assist you. (Note: Voice recognition unavailable - you can type commands)",
            "hi": f"स्वागत है {username}। मैं LYRA हूं, आपकी मदद के लिए तैयार। (नोट: आवाज पहचान उपलब्ध नहीं - आप कमांड टाइप कर सकते हैं)",
            "kn": f"ಸ್ವಾಗತ {username}। ನಾನು LYRA, ನಿಮಗೆ ಸಹಾಯ ಮಾಡಲು ಸಿದ್ಧ। (ಗಮನಿಸಿ: ಧ್ವನಿ ಗುರುತಿಸುವಿಕೆ ಲಭ್ಯವಿಲ್ಲ - ನೀವು ಆಜ್ಞೆಗಳನ್ನು ಟೈಪ್ ಮಾಡಬಹುದು)"
        }
        main_window.add_message("LYRA", greeting_responses[DEFAULT_LANGUAGE])

    # Start loading Whisper in background
    loader_thread = WhisperLoaderThread(assistant.speech_recognizer)
    loader_thread.finished.connect(on_whisper_loaded)
    loader_thread.error.connect(on_whisper_error)
    loader_thread.start()

    print("=" * 80)
    print("🚀 LYRA is ready! All features loaded successfully.")
    print("=" * 80 + "\n")

    sys.exit(app.exec_())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
