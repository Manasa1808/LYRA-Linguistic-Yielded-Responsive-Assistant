# gui/settings_window.py
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from database.db_manager import DatabaseManager
import json
import os

class SettingsWindow(QDialog):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.db = DatabaseManager()
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        self.setWindowTitle('Settings')
        self.setMinimumSize(750, 650)  # Windows adjusted size
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)
        
        # Title
        title = QLabel('⚙️ Settings')
        title.setStyleSheet('font-size: 26px; font-weight: bold; color: #0078d4;')
        main_layout.addWidget(title)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # General settings
        general_tab = self.create_general_tab()
        tab_widget.addTab(general_tab, 'General')
        
        # Voice settings
        voice_tab = self.create_voice_tab()
        tab_widget.addTab(voice_tab, 'Voice')
        
        # Email settings
        email_tab = self.create_email_tab()
        tab_widget.addTab(email_tab, 'Email')
        
        # Privacy settings
        privacy_tab = self.create_privacy_tab()
        tab_widget.addTab(privacy_tab, 'Privacy')
        
        # Security settings (Face Recognition)
        security_tab = self.create_security_tab()
        tab_widget.addTab(security_tab, 'Security')
        
        # Contacts settings
        contacts_tab = self.create_contacts_tab()
        tab_widget.addTab(contacts_tab, 'Contacts')
        
        main_layout.addWidget(tab_widget)
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
        self.setLayout(main_layout)
    
    def create_general_tab(self):
        """Create general settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(18)
        
        # Theme selection
        theme_group = QGroupBox('Appearance')
        theme_layout = QVBoxLayout()
        
        theme_label = QLabel('Theme:')
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['Dark', 'Light'])
        theme_layout.addWidget(self.theme_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Language selection
        language_group = QGroupBox('Language')
        language_layout = QVBoxLayout()
        
        language_label = QLabel('Default Language:')
        language_layout.addWidget(language_label)
        
        self.language_combo = QComboBox()
        languages = [
            'English', 'Spanish', 'French', 'German', 'Italian',
            'Portuguese', 'Russian', 'Chinese', 'Japanese', 'Korean',
            'Arabic', 'Hindi', 'Kannada', 'Auto-detect'
        ]
        self.language_combo.addItems(languages)
        language_layout.addWidget(self.language_combo)
        
        language_group.setLayout(language_layout)
        layout.addWidget(language_group)
        
        # Startup options
        startup_group = QGroupBox('Startup')
        startup_layout = QVBoxLayout()
        
        self.autostart_checkbox = QCheckBox('Launch LYRA at system startup')
        startup_layout.addWidget(self.autostart_checkbox)
        
        self.minimize_checkbox = QCheckBox('Minimize to system tray')
        startup_layout.addWidget(self.minimize_checkbox)
        
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_voice_tab(self):
        """Create voice settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(18)
        
        # Voice engine settings
        engine_group = QGroupBox('Text-to-Speech Engine')
        engine_layout = QVBoxLayout()
        
        # TTS voice selection
        voice_label = QLabel('Text-to-Speech Voice:')
        engine_layout.addWidget(voice_label)
    
        self.voice_combo = QComboBox()
        # Will be populated with available voices
        engine_layout.addWidget(self.voice_combo)
    
        # Voice rate
        rate_label = QLabel('Speech Rate:')
        engine_layout.addWidget(rate_label)
    
        rate_layout = QHBoxLayout()
        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setMinimum(50)
        self.rate_slider.setMaximum(300)
        self.rate_slider.setValue(150)
        self.rate_slider.setTickPosition(QSlider.TicksBelow)
        self.rate_slider.setTickInterval(25)
        rate_layout.addWidget(self.rate_slider)
    
        self.rate_value_label = QLabel('150')
        self.rate_slider.valueChanged.connect(lambda v: self.rate_value_label.setText(str(v)))
        rate_layout.addWidget(self.rate_value_label)
    
        engine_layout.addLayout(rate_layout)
    
        # Volume
        volume_label = QLabel('Volume:')
        engine_layout.addWidget(volume_label)
    
        volume_layout = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(90)
        volume_layout.addWidget(self.volume_slider)
    
        self.volume_value_label = QLabel('90%')
        self.volume_slider.valueChanged.connect(lambda v: self.volume_value_label.setText(f'{v}%'))
        volume_layout.addWidget(self.volume_value_label)
    
        engine_layout.addLayout(volume_layout)
    
        # Test button
        test_btn = QPushButton('🔊 Test Voice')
        test_btn.clicked.connect(self.test_voice)
        engine_layout.addWidget(test_btn)
    
        engine_group.setLayout(engine_layout)
        layout.addWidget(engine_group)
    
        # Recognition settings
        recognition_group = QGroupBox('Speech Recognition')
        recognition_layout = QVBoxLayout()
    
        # Whisper model
        model_label = QLabel('Whisper Model:')
        recognition_layout.addWidget(model_label)
    
        self.model_combo = QComboBox()
        self.model_combo.addItems(['tiny', 'base', 'small', 'medium', 'large'])
        self.model_combo.setCurrentText('base')
        recognition_layout.addWidget(self.model_combo)
    
        model_info = QLabel('Note: Larger models are more accurate but slower')
        model_info.setStyleSheet('color: #808080; font-size: 12px;')
        recognition_layout.addWidget(model_info)
    
        # Voice isolation
        self.voice_isolation_checkbox = QCheckBox('Enable voice isolation (noise reduction)')
        self.voice_isolation_checkbox.setChecked(True)
        recognition_layout.addWidget(self.voice_isolation_checkbox)
    
        recognition_group.setLayout(recognition_layout)
        layout.addWidget(recognition_group)
    
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_email_tab(self):
        """Create email settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(18)
        
        email_group = QGroupBox('Email Configuration')
        email_layout = QVBoxLayout()
        
        # Email address
        email_label = QLabel('Email Address:')
        email_layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText('your.email@example.com')
        email_layout.addWidget(self.email_input)
        
        # SMTP server
        smtp_label = QLabel('SMTP Server:')
        email_layout.addWidget(smtp_label)
        
        self.smtp_input = QLineEdit()
        self.smtp_input.setPlaceholderText('smtp.gmail.com')
        email_layout.addWidget(self.smtp_input)
        
        # SMTP port
        port_label = QLabel('SMTP Port:')
        email_layout.addWidget(port_label)
        
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText('587')
        email_layout.addWidget(self.port_input)
        
        # Password
        password_label = QLabel('Email Password:')
        email_layout.addWidget(password_label)
        
        self.email_password_input = QLineEdit()
        self.email_password_input.setEchoMode(QLineEdit.Password)
        self.email_password_input.setPlaceholderText('Your email password or app password')
        email_layout.addWidget(self.email_password_input)
        
        # Info label
        info_label = QLabel('⚠️ For Gmail, use an App Password instead of your regular password')
        info_label.setWordWrap(True)
        info_label.setStyleSheet('color: #ffc107; font-size: 13px;')
        email_layout.addWidget(info_label)
        
        # Test email button
        test_email_btn = QPushButton('📧 Test Email Configuration')
        test_email_btn.clicked.connect(self.test_email)
        email_layout.addWidget(test_email_btn)
        
        email_group.setLayout(email_layout)
        layout.addWidget(email_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_privacy_tab(self):
        """Create privacy settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(18)
        
        # Data collection
        data_group = QGroupBox('Data & Privacy')
        data_layout = QVBoxLayout()
        
        self.save_history_checkbox = QCheckBox('Save command history')
        self.save_history_checkbox.setChecked(True)
        data_layout.addWidget(self.save_history_checkbox)
        
        self.save_recordings_checkbox = QCheckBox('Save voice recordings for improvement')
        data_layout.addWidget(self.save_recordings_checkbox)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # Data management
        manage_group = QGroupBox('Data Management')
        manage_layout = QVBoxLayout()
        
        clear_history_btn = QPushButton('🗑️ Clear Command History')
        clear_history_btn.setObjectName('dangerButton')
        clear_history_btn.clicked.connect(self.clear_history)
        manage_layout.addWidget(clear_history_btn)
        
        export_data_btn = QPushButton('📦 Export My Data')
        export_data_btn.clicked.connect(self.export_data)
        manage_layout.addWidget(export_data_btn)
        
        manage_group.setLayout(manage_layout)
        layout.addWidget(manage_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_security_tab(self):
        """Create security settings tab (Face Recognition)"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(18)
        
        # Face recognition
        face_group = QGroupBox('Facial Recognition')
        face_layout = QVBoxLayout()
        
        self.face_login_checkbox = QCheckBox('Enable facial recognition login')
        self.face_login_checkbox.setChecked(True)
        face_layout.addWidget(self.face_login_checkbox)
        
        # Re-register face button
        reregister_btn = QPushButton('🔄 Re-register Face')
        reregister_btn.clicked.connect(self.reregister_face)
        face_layout.addWidget(reregister_btn)
        
        info_label = QLabel('Facial recognition allows you to log in without typing your password.')
        info_label.setWordWrap(True)
        info_label.setStyleSheet('color: #808080; font-size: 12px;')
        face_layout.addWidget(info_label)
        
        face_group.setLayout(face_layout)
        layout.addWidget(face_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def load_settings(self):
        """Load user settings from database"""
        query = 'SELECT preferences, email FROM users WHERE user_id = ?'
        result = self.db.execute_query(query, (self.user_id,))
        
        if result:
            preferences_json = result[0][0]
            email = result[0][1]
            
            if preferences_json:
                preferences = json.loads(preferences_json)
                
                # Apply preferences
                theme = preferences.get('theme', 'dark')
                self.theme_combo.setCurrentText(theme.capitalize())
                
                language = preferences.get('language', 'en')
                # Set language combo
                
                voice_index = preferences.get('voice_index', 0)
                # Set voice combo
            
            if email:
                self.email_input.setText(email)

    def save_settings(self):
        """Save settings to database"""
        preferences = {
            'theme': self.theme_combo.currentText().lower(),
            'language': self.language_combo.currentText(),
            'voice_index': self.voice_combo.currentIndex(),
            'speech_rate': self.rate_slider.value(),
            'volume': self.volume_slider.value() / 100,
            'whisper_model': self.model_combo.currentText(),
            'voice_isolation': self.voice_isolation_checkbox.isChecked(),
            'save_history': self.save_history_checkbox.isChecked(),
            'face_login': self.face_login_checkbox.isChecked()
        }
        
        email_config = {
            'email': self.email_input.text(),
            'smtp_server': self.smtp_input.text(),
            'smtp_port': self.port_input.text(),
            'password': self.email_password_input.text()
        }
        
        # Update database
        update_query = '''
            UPDATE users 
            SET preferences = ?, email = ?
            WHERE user_id = ?
        '''
        self.db.execute_query(update_query, (json.dumps(preferences), email_config['email'], self.user_id))
        
        QMessageBox.information(self, 'Success', 'Settings saved successfully!')
        self.accept()

    def test_voice(self):
        """Test TTS voice"""
        from core.tts_engine import TTSEngine
        tts = TTSEngine()
        tts.set_rate(self.rate_slider.value())
        tts.set_volume(self.volume_slider.value() / 100)
        tts.speak('Hello! This is a test of the text to speech engine.')

    def test_email(self):
        """Test email configuration"""
        QMessageBox.information(self, 'Test Email', 'Email test functionality will be implemented')

    def reregister_face(self):
        """Re-register user's face"""
        reply = QMessageBox.question(
            self,
            'Re-register Face',
            'This will replace your current facial recognition data. Continue?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            from auth.face_recognition import FaceRecognition
            face_rec = FaceRecognition()
            
            # Get username
            query = 'SELECT username FROM users WHERE user_id = ?'
            result = self.db.execute_query(query, (self.user_id,))
            if result:
                username = result[0][0]
                success, message = face_rec.register_user(username)
                
                if success:
                    QMessageBox.information(self, 'Success', message)
                else:
                    QMessageBox.warning(self, 'Error', message)

    def clear_history(self):
        """Clear command history"""
        reply = QMessageBox.question(
            self,
            'Clear History',
            'This will permanently delete all your command history. Continue?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            query = 'DELETE FROM command_history WHERE user_id = ?'
            self.db.execute_query(query, (self.user_id,))
            QMessageBox.information(self, 'Success', 'Command history cleared')

    def export_data(self):
        """Export user data"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Export Data',
            'lyra_data.json',
            'JSON Files (*.json)'
        )
        
        if file_path:
            # Export user data
            user_data = {
                'notes': [],
                'reminders': [],
                'events': [],
                'custom_commands': []
            }
            
            # Query and export each data type
            # Implementation details...
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, indent=2)
            
            QMessageBox.information(self, 'Success', f'Data exported to {file_path}')
    def create_contacts_tab(self):
        """Create WhatsApp & Email contacts management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(18)
        
        # Title and description
        contacts_group = QGroupBox('WhatsApp & Email Contacts')
        contacts_layout = QVBoxLayout()
        
        info_label = QLabel('Manage contacts for WhatsApp and Email features')
        info_label.setStyleSheet('color: #808080; font-size: 12px;')
        contacts_layout.addWidget(info_label)
        
        # Contacts list
        self.contacts_list = QListWidget()
        self.contacts_list.setMinimumHeight(250)
        contacts_layout.addWidget(self.contacts_list)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton('➕ Add Contact')
        add_btn.clicked.connect(self.add_contact)
        buttons_layout.addWidget(add_btn)
        
        edit_btn = QPushButton('✏️ Edit Contact')
        edit_btn.clicked.connect(self.edit_contact)
        buttons_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton('🗑️ Delete Contact')
        delete_btn.clicked.connect(self.delete_contact)
        buttons_layout.addWidget(delete_btn)
        
        contacts_layout.addLayout(buttons_layout)
        
        contacts_group.setLayout(contacts_layout)
        layout.addWidget(contacts_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        
        # Load contacts
        self.load_contacts()
        
        return widget
    
    def get_contacts_file_path(self):
        """Get the path to contacts.json"""
        return os.path.join('data', 'contacts.json')
    
    def load_contacts(self):
        """Load contacts from data/contacts.json"""
        contacts_file = self.get_contacts_file_path()
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        # Load or create contacts file
        if os.path.exists(contacts_file):
            try:
                with open(contacts_file, 'r', encoding='utf-8') as f:
                    self.contacts_data = json.load(f)
            except Exception as e:
                print(f"Error loading contacts: {e}")
                self.contacts_data = {}
        else:
            self.contacts_data = {}
            self.save_contacts()
        
        # Populate list
        self.contacts_list.clear()
        for name, info in self.contacts_data.items():
            phone = info.get('phone', '')
            email = info.get('email', '')
            display_text = f"{name} - Phone: {phone}, Email: {email}"
            self.contacts_list.addItem(display_text)
    
    def save_contacts(self):
        """Save contacts to data/contacts.json"""
        contacts_file = self.get_contacts_file_path()
        
        try:
            with open(contacts_file, 'w', encoding='utf-8') as f:
                json.dump(self.contacts_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to save contacts: {str(e)}')
    
    def add_contact(self):
        """Add a new contact"""
        dialog = QDialog(self)
        dialog.setWindowTitle('Add Contact')
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Name
        name_label = QLabel('Name:')
        layout.addWidget(name_label)
        name_input = QLineEdit()
        name_input.setPlaceholderText('Enter contact name')
        layout.addWidget(name_input)
        
        # Phone
        phone_label = QLabel('Phone:')
        layout.addWidget(phone_label)
        phone_input = QLineEdit()
        phone_input.setPlaceholderText('+91xxxxxxxxxx')
        layout.addWidget(phone_input)
        
        # Email
        email_label = QLabel('Email:')
        layout.addWidget(email_label)
        email_input = QLineEdit()
        email_input.setPlaceholderText('contact@example.com')
        layout.addWidget(email_input)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            name = name_input.text().strip()
            phone = phone_input.text().strip()
            email = email_input.text().strip()
            
            if not name:
                QMessageBox.warning(self, 'Error', 'Name is required')
                return
            
            if name in self.contacts_data:
                QMessageBox.warning(self, 'Error', 'Contact already exists')
                return
            
            self.contacts_data[name] = {
                'phone': phone,
                'email': email
            }
            
            self.save_contacts()
            self.load_contacts()
            QMessageBox.information(self, 'Success', f'Contact "{name}" added successfully')
    
    def edit_contact(self):
        """Edit selected contact"""
        current_item = self.contacts_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, 'Error', 'Please select a contact to edit')
            return
        
        # Extract name from display text
        display_text = current_item.text()
        name = display_text.split(' - ')[0]
        
        if name not in self.contacts_data:
            QMessageBox.warning(self, 'Error', 'Contact not found')
            return
        
        contact_info = self.contacts_data[name]
        
        dialog = QDialog(self)
        dialog.setWindowTitle('Edit Contact')
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Name (read-only)
        name_label = QLabel('Name:')
        layout.addWidget(name_label)
        name_display = QLineEdit()
        name_display.setText(name)
        name_display.setReadOnly(True)
        layout.addWidget(name_display)
        
        # Phone
        phone_label = QLabel('Phone:')
        layout.addWidget(phone_label)
        phone_input = QLineEdit()
        phone_input.setText(contact_info.get('phone', ''))
        phone_input.setPlaceholderText('+91xxxxxxxxxx')
        layout.addWidget(phone_input)
        
        # Email
        email_label = QLabel('Email:')
        layout.addWidget(email_label)
        email_input = QLineEdit()
        email_input.setText(contact_info.get('email', ''))
        email_input.setPlaceholderText('contact@example.com')
        layout.addWidget(email_input)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            phone = phone_input.text().strip()
            email = email_input.text().strip()
            
            self.contacts_data[name] = {
                'phone': phone,
                'email': email
            }
            
            self.save_contacts()
            self.load_contacts()
            QMessageBox.information(self, 'Success', f'Contact "{name}" updated successfully')
    
    def delete_contact(self):
        """Delete selected contact"""
        current_item = self.contacts_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, 'Error', 'Please select a contact to delete')
            return
        
        # Extract name from display text
        display_text = current_item.text()
        name = display_text.split(' - ')[0]
        
        if name not in self.contacts_data:
            QMessageBox.warning(self, 'Error', 'Contact not found')
            return
        
        reply = QMessageBox.question(
            self,
            'Confirm Delete',
            f'Are you sure you want to delete contact "{name}"?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.contacts_data[name]
            self.save_contacts()
            self.load_contacts()
            QMessageBox.information(self, 'Success', f'Contact "{name}" deleted successfully')
