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
import torch

# 🔒 Force GPU execution
if not torch.cuda.is_available():
    raise SystemError("❌ GPU not detected. LYRA requires CUDA to run Whisper models.")

device_name = torch.cuda.get_device_name(0)
torch.backends.cudnn.benchmark = True
print(f"[LYRA] 🚀 GPU Ready: {device_name}")

# ✅ FIX: Do NOT set default dtype to float16 - breaks Whisper
# Whisper will use FP16 internally when fp16=True is passed


# ═══════════════════════════════════════════════════════════════════════════
# EMOTIONAL ANALYZER CLASS
# ═══════════════════════════════════════════════════════════════════════════
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

        for emotion, lang_phrases in self.emotion_phrases.items():
            for lang, phrases in lang_phrases.items():
                for phrase in phrases:
                    if phrase in text_lower:
                        return emotion

        emotion_scores = {'happy': 0, 'sad': 0, 'okay': 0}

        for emotion, lang_keywords in self.emotion_keywords.items():
            for lang, keywords in lang_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        emotion_scores[emotion] += 1

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


# ═══════════════════════════════════════════════════════════════════════════
# MAIN VOICE ASSISTANT CLASS
# ═══════════════════════════════════════════════════════════════════════════
class VoiceAssistant:
    def __init__(self, username="User", profile_manager=None, db_manager=None, gui=None):
        self.current_user = username
        self.profile_manager = profile_manager
        self.db = db_manager
        self.gui = gui
        self.current_language = DEFAULT_LANGUAGE

        # Core modules
        self.audio_handler = AudioHandler()
        self.speech_recognizer = SpeechRecognizer()
        self.tts = TTSEngine()
        self.command_processor = CommandProcessor()
        self.emotion_analyzer = EmotionalAnalyzer()

        # Feature modules
        self.app_controller = AppController()
        self.utils = UtilityFeatures()
        self.custom_commands = CustomCommandsManager(self.db)

        # Features
        self.reminder_manager = ReminderManager(self.db)
        self.calendar_manager = CalendarManager(self.db)
        self.notes_manager = NotesManager(self.db)
        self.email_handler = EmailHandler()
        self.whatsapp_handler = WhatsAppHandler()

        # State management
        self.assistant_state = "ready"
        self.is_continuous_listening = False
        self.state_lock = threading.Lock()
        self.mic_enabled = True
        self.mode = "PASSIVE"
        
        # Thread for processing audio segments
        self.processing_thread = None
        self.stop_processing = threading.Event()

        if self.gui:
            self._start_gui_reminder_listener()

    def _is_noise_or_unintended(self, text):
        """Check if text appears to be noise or unintended speech"""
        text = text.lower().strip()

        noise_patterns = [
            r'^[uhm]+$',
            r'^[a-z]\s*$',
            r'^\W+$',
            r'^(ha|haha|hehe|lol)+$',
            r'^\d+\s*\d*$',
            r'^(yes|no|okay|ok|yeah|yep|sure|right|wrong)$',
        ]

        for pattern in noise_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True

        words = text.split()
        if len(words) <= 2 and len(text) < 10:
            command_starters = ['open', 'close', 'play', 'stop', 'show', 'tell', 'what', 'how', 'when', 'where']
            if not any(word in command_starters for word in words):
                return True

        return False

    def set_language(self, language):
        """Set the current language"""
        self.current_language = language
        
        # ✅ NEW: Tell Whisper about language preference
        if hasattr(self.speech_recognizer, 'set_preferred_language'):
            self.speech_recognizer.set_preferred_language(language)
        
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

    # ═══════════════════════════════════════════════════════════════════════════
    # ✅ CONTINUOUS LISTENING WITH QUEUE-BASED AUDIO PROCESSING
    # ═══════════════════════════════════════════════════════════════════════════
    
    def start_continuous_listening(self):
        """Start continuous listening mode using queue-based audio capture"""
        if self.is_continuous_listening:
            print("[LYRA] Already in continuous listening mode")
            return
            
        self.is_continuous_listening = True
        self.stop_processing.clear()
        
        # Start audio capture thread (VAD-based segmentation)
        self.audio_handler.start_listening()
        
        # Start processing thread (consumes audio segments from queue)
        self.processing_thread = threading.Thread(target=self._audio_processing_loop, daemon=True)
        self.processing_thread.start()
        
        with self.state_lock:
            self.assistant_state = "ready"
        
        if self.gui:
            self.gui.update_state_signal.emit("ready")
        
        print("[LYRA] ✅ Continuous listening started - Queue-based audio processing")

    def _audio_processing_loop(self):
        """Main loop that processes audio segments from the queue"""
        print("[LYRA] 🎧 Audio processing loop started")
        
        while not self.stop_processing.is_set():
            try:
                # Get next audio segment from queue (blocks with timeout)
                audio_segment = self.audio_handler.get_next_audio_segment(timeout=1)
                
                if audio_segment is None:
                    continue
                
                # Check if we're ready to process
                with self.state_lock:
                    if self.assistant_state != "ready":
                        print("[LYRA] ⏸️ Not ready, skipping segment")
                        continue
                    
                    # Transition to listening state
                    self.assistant_state = "listening"
                
                if self.gui:
                    self.gui.update_state_signal.emit("listening")
                
                print("[LYRA] 🎤 Processing audio segment...")
                
                # Process the audio segment
                self._process_audio_segment(audio_segment)
                
            except Exception as e:
                print(f"[LYRA] ❌ Error in processing loop: {e}")
                import traceback
                traceback.print_exc()
                
                # Reset to ready state
                with self.state_lock:
                    self.assistant_state = "ready"
                if self.gui:
                    self.gui.update_state_signal.emit("ready")
        
        print("[LYRA] 🛑 Audio processing loop stopped")

    def _process_audio_segment(self, audio_data):
        """Process audio with Alexa-like conversational fluency"""
        try:
            if not self.speech_recognizer.is_loaded():
                print("[LYRA] ⚠️ Whisper not loaded yet")
                with self.state_lock:
                    self.assistant_state = "ready"
                if self.gui:
                    self.gui.update_state_signal.emit("ready")
                return

            print("[LYRA] 🧠 Transcribing...")
            
            # Transcribe without forcing language (let Whisper detect)
            result = self.speech_recognizer.transcribe(audio_data, language=None)
            
            command_text = result.get('text', '').strip()
            detected_language = result.get('language', 'en')
            confidence = result.get('confidence', 0.0)
            model_used = result.get('model', 'unknown')

            print(f"[LYRA] 📝 {detected_language} | {model_used} | {confidence:.2f}")
            
            if command_text:
                print(f"[LYRA] 💬 '{command_text}'")

            # Filter: minimum length and confidence
            min_length = 2 if detected_language == 'en' else 1
            min_conf = 0.18 if detected_language in ['kn', 'hi'] else 0.22
            
            if (command_text and 
                len(command_text) > min_length and
                confidence > min_conf and
                not self._is_noise_or_unintended(command_text)):

                # ✅ Alexa-like flow: Quick acknowledgment
                if self.gui:
                    self.gui.add_message_signal.emit("You", command_text)

                with self.state_lock:
                    self.assistant_state = "talking"
                if self.gui:
                    self.gui.update_state_signal.emit("talking")

                try:
                    # Process command
                    response = self.process_text(command_text, language=detected_language)
                    
                    if not response:
                        # Natural fallback responses
                        fallbacks = {
                            "en": "I'm not sure how to help with that.",
                            "hi": "मुझे समझ नहीं आया।",
                            "kn": "ನನಗೆ ಅರ್ಥವಾಗಲಿಲ್ಲ।"
                        }
                        response = fallbacks.get(detected_language, fallbacks["en"])
                    
                    print(f"[LYRA] 💡 {response}")
                except Exception as e:
                    print(f"[LYRA] ❌ {e}")
                    errors = {
                        "en": "Sorry, I encountered an error.",
                        "hi": "क्षमा करें, कुछ गड़बड़ हो गई।",
                        "kn": "ಕ್ಷಮಿಸಿ, ದೋಷ ಸಂಭವಿಸಿದೆ।"
                    }
                    response = errors.get(detected_language, errors["en"])

                # Display and speak response
                if self.gui:
                    self.gui.add_message_signal.emit("LYRA", response)

                try:
                    self.tts.set_language(detected_language)
                    self.tts.speak(response)
                except Exception as tts_error:
                    print(f"[LYRA] 🔇 TTS error: {tts_error}")

                time.sleep(1.2)  # Brief pause for natural flow

            else:
                # Silently filter noise
                if command_text:
                    reasons = []
                    if len(command_text) <= min_length:
                        reasons.append("short")
                    if confidence <= min_conf:
                        reasons.append(f"conf:{confidence:.2f}")
                    if self._is_noise_or_unintended(command_text):
                        reasons.append("noise")
                    
                    if reasons:
                        print(f"[LYRA] 🔇 Filtered ({', '.join(reasons)})")

            # Return to ready
            with self.state_lock:
                self.assistant_state = "ready"
            if self.gui:
                self.gui.update_state_signal.emit("ready")

        except Exception as e:
            print(f"[LYRA] ❌ {e}")
            import traceback
            traceback.print_exc()

            with self.state_lock:
                self.assistant_state = "ready"
            if self.gui:
                self.gui.update_state_signal.emit("ready")

    def stop_continuous_listening(self):
        """Stop continuous listening mode"""
        self.is_continuous_listening = False
        self.stop_processing.set()
        
        # Stop audio handler
        self.audio_handler.stop_continuous_recording()
        
        # Wait for processing thread to finish
        if self.processing_thread:
            self.processing_thread.join(timeout=2)
            self.processing_thread = None

        with self.state_lock:
            self.assistant_state = "ready"

        if self.gui:
            self.gui.update_state_signal.emit("ready")

        print("[LYRA] 🛑 Continuous listening stopped")

    def _detect_language_unicode(self, text):
        """Detect language using Unicode ranges"""
        text = text.strip()
        if not text:
            return 'en'

        kannada_count = 0
        hindi_count = 0
        english_count = 0

        for char in text:
            code = ord(char)
            if 0x0C80 <= code <= 0x0CFF:
                kannada_count += 1
            elif 0x0900 <= code <= 0x097F:
                hindi_count += 1
            elif ord('a') <= code <= ord('z') or ord('A') <= code <= ord('Z'):
                english_count += 1

        max_count = max(kannada_count, hindi_count, english_count)

        if max_count == 0:
            return 'en'
        elif kannada_count == max_count:
            return 'kn'
        elif hindi_count == max_count:
            return 'hi'
        else:
            return 'en'

    def process_text(self, text, language=None):
        """Process text command"""
        user_id = getattr(self.profile_manager, "current_user_id", None)
        lang = language or self.current_language

        original_text = text.strip()
        detected_lang = self._detect_language_unicode(original_text)

        processing_text = original_text

        if detected_lang != 'en':
            try:
                from core.translation_engine import get_translation_engine
                translator = get_translation_engine()

                if translator.is_available():
                    processing_text = translator.translate_to_english(original_text, detected_lang)
                    print(f"🔄 Translation: {detected_lang} -> en")
                else:
                    print(f"⚠️ Translation unavailable")
                    processing_text = original_text

            except Exception as e:
                print(f"⚠️ Translation error: {e}")
                processing_text = original_text

        emotion = self.emotion_analyzer.detect_emotion(processing_text)

        if emotion != 'neutral' and len(processing_text.split()) < 15:
            is_command = False

            cmd_result = self.command_processor.process_command(processing_text)
            if cmd_result.get('intent') and cmd_result.get('confidence', 0) > 0.6:
                is_command = True

            if not is_command:
                response = self.emotion_analyzer.get_emotional_response(emotion, detected_lang)
                if detected_lang != 'en':
                    try:
                        from core.translation_engine import get_translation_engine
                        translator = get_translation_engine()
                        if translator.is_available():
                            response = translator.translate_from_english(response, detected_lang)
                    except Exception:
                        pass
                return response

        if self.custom_commands and user_id:
            custom_cmd = self.custom_commands.match_custom_command(user_id, processing_text)
            if custom_cmd:
                success, result = self.custom_commands.execute_custom_command(custom_cmd)
                if success and isinstance(result, str):
                    if detected_lang != 'en':
                        try:
                            from core.translation_engine import get_translation_engine
                            translator = get_translation_engine()
                            if translator.is_available():
                                result = translator.translate_from_english(result, detected_lang)
                        except Exception:
                            pass
                    return result

        cmd_result = self.command_processor.process_command(processing_text)
        response = self.route_to_feature_module(cmd_result, detected_lang)

        if detected_lang != 'en' and response:
            try:
                from core.translation_engine import get_translation_engine
                translator = get_translation_engine()
                if translator.is_available():
                    response = translator.translate_from_english(response, detected_lang)
            except Exception as e:
                print(f"⚠️ Response translation failed: {e}")

        if detected_lang != 'en':
            self.tts.set_language(detected_lang)

        return response

    def route_to_feature_module(self, cmd_result, language=None):
        """Route detected intent to appropriate feature module - COMPLETE VERSION"""
        intent = cmd_result.get('intent')
        entities = cmd_result.get('entities', {})
        user_id = getattr(self.profile_manager, "current_user_id", None)
        lang = language or self.current_language
        original_text = cmd_result.get('original_text', '')

        if intent == 'get_time':
            return self.utils.get_current_time(lang)

        elif intent == 'get_date':
            return self.utils.get_current_date(lang)

        elif intent == 'get_weather':
            city = entities.get('city', 'Bengaluru')
            return self.utils.get_weather(city, lang)

        elif intent == 'tell_joke':
            # Check if it's a "bored" or "entertain me" request
            bored_keywords = ['bored', 'bore', 'entertain', 'बोर', 'मजा', 'ಬೋರ್', 'ಮಜೇದಾರ']
            if any(keyword in original_text.lower() for keyword in bored_keywords):
                return self.utils.entertain_me(lang)
            else:
                return self.utils.tell_joke(lang)

        elif intent == 'get_news':
            return self.utils.get_news(lang)

        elif intent == 'open_app':
            app_name = entities.get('app_name', entities.get('entity_0', ''))
            print(f"📱 Opening app: '{app_name}'")
            if app_name:
                success, msg = self.app_controller.open_app(app_name)
                return msg
            return {
                'en': "Which app would you like me to open?",
                'hi': "कौन सा ऐप खोलूं?",
                'kn': "ಯಾವ ಆ್ಯಪ್ ತೆರೆಯಲಿ?"
            }.get(lang, "Which app would you like me to open?")

        elif intent == 'close_app':
            app_name = entities.get('app_name', entities.get('entity_0', ''))
            print(f"📱 Closing app: '{app_name}'")
            if app_name:
                success, msg = self.app_controller.close_app(app_name)
                return msg
            return {
                'en': "Which app would you like me to close?",
                'hi': "कौन सा ऐप बंद करूं?",
                'kn': "ಯಾವ ಆ್ಯಪ್ ಮುಚ್ಚಲಿ?"
            }.get(lang, "Which app would you like me to close?")

        elif intent == 'create_reminder' and user_id:
            task = entities.get('task') or entities.get('entity_0') or "Reminder"
            time_text = entities.get('time') or entities.get('entity_1') or "later"
            due_time = self.reminder_manager.parse_reminder_time(f"{task} at {time_text}")
            self.reminder_manager.create_reminder(user_id, task, due_datetime=due_time)
            
            responses = {
                'en': f"Reminder set: {task} at {due_time.strftime('%I:%M %p, %d-%b-%Y')}",
                'hi': f"रिमाइंडर सेट किया गया: {task} {due_time.strftime('%I:%M %p, %d-%b-%Y')} पर",
                'kn': f"ಜ್ಞಾಪನೆ ಸೆಟ್ ಮಾಡಲಾಗಿದೆ: {task} {due_time.strftime('%I:%M %p, %d-%b-%Y')}"
            }
            return responses.get(lang, responses['en'])

        elif intent == 'create_note' and user_id:
            content = entities.get('entity_0', '')
            if content:
                success, msg = self.notes_manager.create_note(user_id, "Quick Note", content, language=lang)
                return msg
            return {
                'en': "What would you like to note down?",
                'hi': "आप क्या लिखना चाहते हैं?",
                'kn': "ನೀವು ಏನು ಬರೆಯಲು ಬಯಸುತ್ತೀರಿ?"
            }.get(lang, "What would you like to note down?")

        elif intent == 'search_note' and user_id:
            search_term = entities.get('entity_0', '')
            if search_term:
                success, msg, notes = self.notes_manager.search_notes(user_id, search_term, language=lang)
                if success and notes:
                    # Return first few notes
                    note_titles = [note['title'] for note in notes[:3]]
                    titles_str = ', '.join(note_titles)
                    return f"{msg}. {titles_str}"
                return msg
            return {
                'en': "What notes are you looking for?",
                'hi': "आप कौन से नोट खोज रहे हैं?",
                'kn': "ನೀವು ಯಾವ ನೋಟ್‌ಗಳನ್ನು ಹುಡುಕುತ್ತಿದ್ದೀರಿ?"
            }.get(lang, "What notes are you looking for?")

        elif intent == 'create_event' and user_id:
            title = entities.get('entity_0', 'Event')
            time_str = original_text
            
            print(f"📅 Creating event: '{title}' from text: '{time_str}'")
            
            # Open calendar
            try:
                success, msg = self.calendar_manager.open_calendar()
            except:
                pass
            
            # Save to database with proper datetime parsing
            try:
                success, msg = self.calendar_manager.create_event(
                    user_id, 
                    title, 
                    start_datetime=time_str,
                    language=lang
                )
                return msg
            except Exception as e:
                print(f"⚠️ Calendar error: {e}")
                responses = {
                    'en': f"Opening calendar to create: {title}",
                    'hi': f"कैलेंडर खोल रहे हैं: {title}",
                    'kn': f"ಕ್ಯಾಲೆಂಡರ್ ತೆರೆಯುತ್ತಿದೆ: {title}"
                }
                return responses.get(lang, responses['en'])

        elif intent == 'send_email':
            recipient = entities.get('recipient', entities.get('entity_0', ''))
            content = entities.get('content', entities.get('entity_1', ''))
            if recipient:
                success, msg = self.email_handler.send_email(recipient, "Message from LYRA", content)
                return msg
            return {
                'en': "Who would you like to send an email to?",
                'hi': "किसको ईमेल भेजना है?",
                'kn': "ಯಾರಿಗೆ ಇಮೇಲ್ ಕಳುಹಿಸಬೇಕು?"
            }.get(lang, "Who would you like to send an email to?")

        elif intent == 'send_whatsapp':
            contact = entities.get('contact', entities.get('entity_1', ''))
            message = entities.get('message', entities.get('entity_0', 'Hello from LYRA!'))
            
            print(f"📱 WhatsApp - Contact: '{contact}', Message: '{message}'")
            
            if contact:
                success, msg = self.whatsapp_handler.send_message(contact, message)
                return msg
            return {
                'en': "Who would you like to send a WhatsApp message to?",
                'hi': "किसको व्हाट्सएप भेजना है?",
                'kn': "ಯಾರಿಗೆ ವಾಟ್ಸಪ್ ಕಳುಹಿಸಬೇಕು?"
            }.get(lang, "Who would you like to send a WhatsApp message to?")

        elif intent == 'read_pdf':
            file_path = entities.get('entity_0', '')
            if file_path:
                # Initialize PDF reader
                from features.pdf_reader import PDFReader
                pdf_reader = PDFReader()
                success, content = pdf_reader.read_pdf_summary(file_path, max_chars=500, language=lang)
                return content
            return {
                'en': "Which PDF file would you like me to read?",
                'hi': "कौन सी पीडीएफ फाइल पढ़ूं?",
                'kn': "ಯಾವ ಪಿಡಿಎಫ್ ಫೈಲ್ ಓದಲಿ?"
            }.get(lang, "Which PDF file would you like me to read?")

        # Conversational fallback
        else:
            # Check if it's a greeting
            greetings = ['hello', 'hi', 'hey', 'namaste', 'namaskar', 'namaskara', 'hola']
            if any(g in original_text.lower() for g in greetings):
                responses = {
                    'en': "Hello! How can I help you today?",
                    'hi': "नमस्ते! मैं आपकी कैसे मदद कर सकता हूं?",
                    'kn': "ನಮಸ್ಕಾರ! ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?"
                }
                return responses.get(lang, responses['en'])
            
            # Check if asking about capabilities
            capability_words = ['what can you do', 'help', 'capabilities', 'functions', 'features']
            if any(w in original_text.lower() for w in capability_words):
                responses = {
                    'en': "I can help with time, weather, opening apps, reminders, notes, calendar, WhatsApp, email, jokes, and more. Just ask!",
                    'hi': "मैं समय, मौसम, ऐप्स खोलने, रिमाइंडर, नोट्स, कैलेंडर, व्हाट्सएप, ईमेल, जोक्स और बहुत कुछ में मदद कर सकता हूं।",
                    'kn': "ನಾನು ಸಮಯ, ಹವಾಮಾನ, ಅಪ್ಲಿಕೇಶನ್‌ಗಳು, ಜ್ಞಾಪನೆಗಳು, ನೋಟ್‌ಗಳು, ಕ್ಯಾಲೆಂಡರ್, ವಾಟ್ಸಪ್, ಇಮೇಲ್, ಹಾಸ್ಯಗಳು ಮತ್ತು ಹೆಚ್ಚಿನದನ್ನು ಮಾಡಬಲ್ಲೆ."
                }
                return responses.get(lang, responses['en'])
            
            # Default: didn't understand
            responses = {
                'en': "I didn't quite catch that. Could you try rephrasing?",
                'hi': "मुझे समझ नहीं आया। क्या आप दूसरे तरीके से कह सकते हैं?",
                'kn': "ನನಗೆ ಅರ್ಥವಾಗಲಿಲ್ಲ। ದಯವಿಟ್ಟು ಮತ್ತೆ ಹೇಳಬಹುದೇ?"
            }
            return responses.get(lang, responses['en'])

# ═══════════════════════════════════════════════════════════════════════════
# WHISPER LOADER THREAD
# ═══════════════════════════════════════════════════════════════════════════
class WhisperLoaderThread(QThread):
    """Background thread to load Whisper models"""
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, speech_recognizer):
        super().__init__()
        self.speech_recognizer = speech_recognizer

    def run(self):
        """Models are already loaded in __init__, just signal completion"""
        try:
            if self.speech_recognizer.is_loaded():
                print("[LYRA] ✅ All Whisper models already loaded on GPU")
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


# ═══════════════════════════════════════════════════════════════════════════
# MAIN FUNCTION
# ═══════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 80)
    print("🎤 LYRA - Linguistic Yielded Responsive Assistant")
    print("=" * 80)
    print("\n✅ FEATURES:")
    print("   1. Continuous VAD-based audio capture")
    print("   2. GPU Whisper (tiny → base/medium)")
    print("   3. Multi-language support (EN/HI/KN)")
    print("=" * 80 + "\n")

    app = QApplication(sys.argv)

    db = DatabaseManager()
    profile_mgr = ProfileManager()

    try:
        face_rec = FaceRecognition()
        print("✅ Face recognition initialized")
    except Exception as e:
        print(f"⚠️ Face recognition failed: {e}")
        face_rec = None

    login_window = LoginWindow(face_rec)
    if login_window.exec_() != QDialog.Accepted:
        print("❌ Login cancelled")
        return

    username = login_window.get_authenticated_user()
    if not username:
        print("❌ No authenticated user")
        QMessageBox.warning(None, "Login Error", "Authentication failed.")
        return

    print(f"✅ User: {username}")

    success, preferences = profile_mgr.login(username)
    if not success:
        print(f"⚠️ Failed to load profile for {username}")

    main_window = VoiceAssistantGUI(None)
    assistant = VoiceAssistant(username, profile_mgr, db, gui=main_window)
    main_window.assistant = assistant

    main_window.show()

    main_window.add_message("LYRA", "🔄 Loading Whisper models...")
    main_window.statusBar().showMessage("Loading Whisper...")
    QApplication.processEvents()

    def on_whisper_loaded():
        """Called when Whisper finishes loading"""
        print("✅ Whisper models loaded on GPU")
        main_window.statusBar().showMessage("Ready")

        greeting = f"Welcome {username}. I'm LYRA. Continuous listening is active!"
        main_window.add_message("LYRA", greeting)
        
        try:
            assistant.tts.speak(greeting)
        except Exception as e:
            print(f"⚠️ TTS error: {e}")

        print("\n🎤 Starting continuous listening...")
        try:
            assistant.start_continuous_listening()
            main_window.set_continuous_mode(True)
            print("✅ Continuous listening active!\n")
        except Exception as e:
            print(f"⚠️ Could not start continuous listening: {e}\n")

    def on_whisper_error(error_msg):
        """Called if Whisper loading fails"""
        print(f"❌ Whisper failed: {error_msg}")
        main_window.statusBar().showMessage("Speech recognition unavailable")
        main_window.add_message("LYRA", f"⚠️ Speech recognition failed: {error_msg}")

    loader_thread = WhisperLoaderThread(assistant.speech_recognizer)
    loader_thread.finished.connect(on_whisper_loaded)
    loader_thread.error.connect(on_whisper_error)
    loader_thread.start()

    print("=" * 80)
    print("🚀 LYRA ready!")
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