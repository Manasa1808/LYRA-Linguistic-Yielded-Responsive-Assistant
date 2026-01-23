# gui/main_window.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
from features.custom_commands import CustomCommandsGUI
from config import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from gui.settings_window import SettingsWindow

class VoiceAssistantGUI(QMainWindow):
    reminder_signal = pyqtSignal(str)
    # Signals for thread-safe GUI updates from background threads
    add_message_signal = pyqtSignal(str, str)  # sender, message
    update_state_signal = pyqtSignal(str)  # state: "ready", "listening", "talking"
    
    def __init__(self, assistant=None):
        super().__init__()
        self.assistant = assistant
        self.is_listening = False
        self.is_continuous_mode = False
        self.current_language = DEFAULT_LANGUAGE
        self.reminder_signal.connect(self._on_reminder)
        self.add_message_signal.connect(self._add_message_thread_safe)
        self.update_state_signal.connect(self._update_state_thread_safe)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('LYRA - Linguistic Yielded Responsive Assistant')
        # Windows optimized size (larger for better visibility)
        self.setGeometry(80, 50, 1350, 900)
        
        self.apply_dark_theme()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        top_bar = self.create_top_bar()
        main_layout.addWidget(top_bar)
        
        content_layout = QHBoxLayout()
        
        sidebar = self.create_sidebar()
        content_layout.addWidget(sidebar)
        
        main_area = self.create_main_area()
        content_layout.addWidget(main_area, stretch=1)
        
        main_layout.addLayout(content_layout)
        
        self.statusBar().showMessage('Ready - Click mic or type a command')
    
    def apply_dark_theme(self):
        dark_stylesheet = """
            QMainWindow { background-color: #1e1e1e; }
            QWidget { 
                background-color: #1e1e1e; 
                color: #ffffff; 
                font-family: 'Segoe UI', Arial, sans-serif; 
                font-size: 14px; 
            }
            QPushButton { 
                background-color: #0078d4; 
                color: white; 
                border: none; 
                padding: 12px 24px; 
                border-radius: 6px; 
                font-weight: bold; 
                min-height: 38px;
            }
            QPushButton:hover { background-color: #106ebe; }
            QPushButton:pressed { background-color: #005a9e; }
            QPushButton#micButton { 
                background-color: #0078d4; 
                border-radius: 32px; 
                font-size: 20px; 
            }
            QPushButton#micButton:hover { background-color: #106ebe; }
            QPushButton#micButton[listening="true"] { background-color: #e81123; }
            QLineEdit, QTextEdit { 
                background-color: #2d2d2d; 
                border: 1px solid #3d3d3d; 
                border-radius: 6px; 
                padding: 12px; 
                color: #ffffff; 
                font-size: 14px;
            }
            QListWidget { 
                background-color: #2d2d2d; 
                border: 1px solid #3d3d3d; 
                border-radius: 6px; 
            }
            QListWidget::item:selected { background-color: #0078d4; }
            QLabel#voiceViz { 
                background-color: #2d2d2d; 
                border-radius: 12px; 
                font-size: 19px; 
                color: #0078d4; 
                padding: 12px; 
            }
            QComboBox { 
                background-color: #2d2d2d; 
                border: 1px solid #3d3d3d; 
                border-radius: 6px; 
                padding: 10px; 
                color: white; 
                min-height: 35px; 
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { 
                background-color: #2d2d2d; 
                selection-background-color: #0078d4; 
            }
            QStatusBar { 
                background-color: #252525; 
                color: #ffffff; 
                font-size: 13px; 
                padding: 6px;
            }
        """
        self.setStyleSheet(dark_stylesheet)

    def create_top_bar(self):
        top_bar = QWidget()
        top_bar.setFixedHeight(75)  # Windows adjusted height
        layout = QHBoxLayout()
        top_bar.setLayout(layout)
        
        title = QLabel('🎤 LYRA Voice Assistant')
        title.setStyleSheet('font-size: 27px; font-weight: bold; color: #0078d4;')
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Language selector
        lang_label = QLabel('Language:')
        lang_label.setStyleSheet('font-size: 15px;')
        layout.addWidget(lang_label)
        
        self.language_combo = QComboBox()
        self.language_combo.setMinimumWidth(190)
        for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
            self.language_combo.addItem(lang_name, lang_code)
        self.language_combo.currentIndexChanged.connect(self.change_language)
        layout.addWidget(self.language_combo)
        
        self.user_label = QLabel('User: Admin')
        self.user_label.setStyleSheet('font-size: 15px; padding: 10px;')
        if self.assistant and hasattr(self.assistant, 'current_user'):
            self.user_label.setText(f"User: {self.assistant.current_user}")
        layout.addWidget(self.user_label)
        
        settings_btn = QPushButton('⚙️ Settings')
        settings_btn.setMinimumWidth(130)
        settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(settings_btn)
        
        return top_bar

    def change_language(self):
        """Handle language change - FORCE LOCK"""
        lang_code = self.language_combo.currentData()
        self.current_language = lang_code
        
        if self.assistant:
            # ✅ CRITICAL: Force language lock in Whisper
            self.assistant.set_language(lang_code)
            
            # ✅ CRITICAL: Set TTS language BEFORE speaking
            self.assistant.tts.set_language(lang_code)
            
            messages = {
                "en": f"Language changed to English",
                "hi": f"भाषा हिन्दी में बदल गई",
                "kn": f"ಭಾಷೆ ಕನ್ನಡಕ್ಕೆ ಬದಲಾಗಿದೆ"
            }
            
            msg = messages.get(lang_code, messages["en"])
            self.add_message("LYRA", msg)
            
            # ✅ FIX: Speak in the CORRECT language (not English for Kannada)
            try:
                self.assistant.tts.speak(msg, language=lang_code)
            except Exception as e:
                print(f"TTS error: {e}")

    def update_language_display(self, language):
        """Update UI language display"""
        self.current_language = language
        idx = self.language_combo.findData(language)
        if idx >= 0:
            self.language_combo.setCurrentIndex(idx)

    def create_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(240)  # Windows adjusted width
        layout = QVBoxLayout()
        sidebar.setLayout(layout)
        
        features = [
            ('🎙️ Voice Control', self.show_voice_control),
            ('📝 Notes', self.show_notes),
            ('📅 Calendar', self.show_calendar),
            ('⏰ Reminders', self.show_reminders),
            ('✉️ Email', self.show_email),
            ('💬 WhatsApp', self.show_whatsapp),
            ('📱 Apps', self.show_apps),
            ('⚡ Custom Commands', self.show_custom_commands),
        ]
        
        for text, callback in features:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setStyleSheet('text-align: left; padding: 18px; font-size: 15px;')
            btn.setMinimumHeight(50)
            layout.addWidget(btn)
        
        layout.addStretch()
        return sidebar

    def create_main_area(self):
        main_area = QWidget()
        layout = QVBoxLayout()
        main_area.setLayout(layout)
        
        self.voice_viz = QLabel()
        self.voice_viz.setObjectName('voiceViz')
        self.voice_viz.setFixedHeight(170)  # Windows adjusted
        self.voice_viz.setAlignment(Qt.AlignCenter)
        self.voice_viz.setText('🎤 Click microphone to speak or type a command below')
        layout.addWidget(self.voice_viz)
        
        self.conversation_text = QTextEdit()
        self.conversation_text.setReadOnly(True)
        self.conversation_text.setPlaceholderText('Your conversation will appear here...')
        self.conversation_text.setStyleSheet('font-size: 14px; line-height: 1.6;')
        layout.addWidget(self.conversation_text)
        
        input_layout = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText('Type a command and press Enter...')
        self.command_input.setMinimumHeight(50)  # Windows adjusted
        self.command_input.returnPressed.connect(self.process_text_command)
        input_layout.addWidget(self.command_input)
        
        self.mic_btn = QPushButton('🎤')
        self.mic_btn.setObjectName('micButton')
        self.mic_btn.setFixedSize(64, 64)  # Windows adjusted - larger button
        self.mic_btn.clicked.connect(self.toggle_listening)
        input_layout.addWidget(self.mic_btn)
        
        layout.addLayout(input_layout)
        return main_area

    def add_message(self, sender, message):
        current_text = self.conversation_text.toPlainText()
        timestamp = QTime.currentTime().toString('hh:mm:ss')
        new_message = f"[{timestamp}] {sender}: {message}\n"
        self.conversation_text.setPlainText(current_text + new_message)
        
        scrollbar = self.conversation_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def process_text_command(self):
        command_text = self.command_input.text().strip()
        if not command_text:
            return
            
        self.command_input.clear()
        self.add_message("You", command_text)
        
        if self.assistant:
            response = self.assistant.process_text(command_text)
            self.add_message("LYRA", response)
            self.assistant.tts.speak(response)

    def toggle_listening(self):
        """
        ✅ FIX: Mic button works in BOTH modes:
        - Continuous mode: Shows info message
        - Manual mode: Records single command
        """
        if not self.assistant:
            QMessageBox.warning(self, "Error", "Voice assistant not initialized")
            return
        
        # If in continuous mode, just inform user
        if self.is_continuous_mode:
            self.add_message("LYRA", "Continuous listening is already active. Just speak naturally!")
            return
        
        # Manual single-shot mode
        if not self.is_listening:
            self.is_listening = True
            self.mic_btn.setProperty("listening", "true")
            self.mic_btn.style().unpolish(self.mic_btn)
            self.mic_btn.style().polish(self.mic_btn)
            self.mic_btn.setText('⏹️')
            self.voice_viz.setText('🔴 Listening... Speak now!')
            self.statusBar().showMessage('Listening for voice commands...')
            QTimer.singleShot(100, self.start_voice_recording)
        else:
            self.stop_listening()

    def start_voice_recording(self):
        """
        ✅ FIX: Works in manual mode - gets next segment from queue
        """
        if self.is_continuous_mode:
            # In continuous mode, audio is already being processed
            self.stop_listening()
            return
        
        # Manual mode: get next audio segment
        if self.assistant:
            try:
                self.voice_viz.setText('🔄 Waiting for speech...')
                
                # Wait for next audio segment from queue (timeout 6 seconds)
                audio_segment = self.assistant.audio_handler.get_next_audio_segment(timeout=6)
                
                if audio_segment is not None:
                    self.voice_viz.setText('🔄 Processing...')
                    
                    # Transcribe without forcing language
                    result = self.assistant.speech_recognizer.transcribe(audio_segment, language=None)
                    command_text = result.get('text', '').strip()
                    detected_lang = result.get('language', 'en')
                    
                    if command_text:
                        self.add_message("You (voice)", command_text)
                        response = self.assistant.process_text(command_text, language=detected_lang)
                        self.add_message("LYRA", response)
                        self.assistant.tts.set_language(detected_lang)
                        self.assistant.tts.speak(response)
                    else:
                        self.add_message("LYRA", "No speech detected")
                else:
                    self.add_message("LYRA", "No audio captured (timeout - please speak after clicking mic)")
                    
            except Exception as e:
                self.add_message("LYRA", f"Voice error: {str(e)}")
                import traceback
                traceback.print_exc()
            finally:
                self.stop_listening()

    def stop_listening(self):
        self.is_listening = False
        self.mic_btn.setProperty("listening", "false")
        self.mic_btn.style().unpolish(self.mic_btn)
        self.mic_btn.style().polish(self.mic_btn)
        self.mic_btn.setText('🎤')
        
        if not self.is_continuous_mode:
            self.voice_viz.setText('🎤 Click microphone to speak or type a command below')
            self.statusBar().showMessage('Ready - Click mic or type a command')

    def show_voice_control(self):
        self.statusBar().showMessage('Voice Control Active')
        self.add_message("System", "Voice Control is active. You can use voice or text commands.")

    def show_notes(self):
        self.statusBar().showMessage('Notes Manager')
        self.add_message("System", "Notes feature - Try: 'create note buy groceries' or 'show my notes'")

    def show_calendar(self):
        self.statusBar().showMessage('Calendar View')
        self.add_message("System", "Calendar feature - Try: 'schedule meeting at 3pm' or 'show today's events'")

    def show_reminders(self):
        self.statusBar().showMessage('Reminders')
        self.add_message("System", "Reminders feature - Try: 'remind me to call John at 5pm'")

    def show_email(self):
        self.statusBar().showMessage('Email Manager')
        self.add_message("System", "Email feature - Try: 'send email to john@example.com'")

    def show_whatsapp(self):
        self.statusBar().showMessage('WhatsApp Integration')
        self.add_message("System", "WhatsApp feature - Try: 'send whatsapp to contact name'")

    def show_apps(self):
        self.statusBar().showMessage('App Controller')
        self.add_message("System", "App Control - Try: 'open chrome' or 'close notepad'")

    def show_custom_commands(self):
        self.statusBar().showMessage('Custom Commands')
        if self.assistant and self.assistant.custom_commands and self.assistant.profile_manager:
            user_id = getattr(self.assistant.profile_manager, 'current_user_id', None)
            if user_id:
                # Pass hardcoded_responses if it exists, otherwise pass None
                hardcoded_responses = getattr(self.assistant, 'hardcoded_responses', None)
                dialog = CustomCommandsGUI(user_id, self.assistant.custom_commands,
                                         hardcoded_responses, self)
                dialog.exec_()
                self.add_message("System", "Custom commands updated successfully")
            else:
                self.add_message("System", "Error: Could not determine user ID for custom commands")
        else:
            self.add_message("System", "Custom commands feature not initialized")

    def open_settings(self):
        self.statusBar().showMessage('Opening Settings')

        if not self.assistant or not self.assistant.profile_manager:
            QMessageBox.warning(self, "Error", "User profile not loaded")
            return

        user_id = getattr(self.assistant.profile_manager, "current_user_id", None)

        if not user_id:
            QMessageBox.warning(self, "Error", "User not logged in")
            return

        settings_dialog = SettingsWindow(user_id, self)
        settings_dialog.exec_()

    def _on_reminder(self, message):
        """Handle reminder notifications"""
        self.add_message("LYRA", message)
        if self.assistant and self.assistant.tts:
            self.assistant.tts.speak(message)
        
        # Show Windows notification
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast("LYRA Reminder", 
                             message, 
                             duration=10, 
                             threaded=True)
        except Exception as e:
            print(f"Notification error: {e}")

    def _add_message_thread_safe(self, sender, message):
        """Thread-safe method to add messages from background threads"""
        self.add_message(sender, message)

    def _update_state_thread_safe(self, state):
        """Thread-safe method to update assistant state from background threads"""
        self.update_assistant_state(state)

    def update_assistant_state(self, state):
        """Update the assistant state display (ready/listening/talking)"""
        state_messages = {
            "ready": "🎤 Ready - Speak naturally",
            "listening": "🔴 Listening...",
            "talking": "🔊 Speaking..."
        }
        
        state_colors = {
            "ready": "#0078d4",
            "listening": "#e81123",
            "talking": "#107c10"
        }
        
        if state in state_messages:
            self.voice_viz.setText(state_messages[state])
            self.voice_viz.setStyleSheet(f"""
                QLabel#voiceViz {{
                    background-color: #2d2d2d;
                    border-radius: 12px;
                    font-size: 19px;
                    color: {state_colors[state]};
                    padding: 12px;
                }}
            """)
            
            # Update status bar
            if state == "ready":
                self.statusBar().showMessage("Ready - Continuous listening active")
            elif state == "listening":
                self.statusBar().showMessage("Processing your speech...")
            elif state == "talking":
                self.statusBar().showMessage("Responding...")

    def set_continuous_mode(self, enabled):
        """Enable or disable continuous listening mode"""
        self.is_continuous_mode = enabled
        if enabled:
            self.statusBar().showMessage("Continuous listening: ACTIVE")
            self.voice_viz.setText("🎤 Continuous listening - Speak naturally!")
            # ✅ FIX: Keep mic button ENABLED for manual override
            self.mic_btn.setEnabled(True)
            self.mic_btn.setToolTip("Click for manual voice command (or just speak naturally)")
        else:
            self.statusBar().showMessage("Continuous listening: INACTIVE")
            self.voice_viz.setText("🎤 Click microphone to speak or type a command below")
            self.mic_btn.setEnabled(True)
            self.mic_btn.setToolTip("Click to record voice command")