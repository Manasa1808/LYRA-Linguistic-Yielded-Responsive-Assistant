# gui/login_window.py - Windows Version with Responsive Sizing
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from auth.face_recognition import FaceRecognition
from database.db_manager import DatabaseManager
import hashlib

class LoginWindow(QDialog):
    def __init__(self, face_recognition, parent=None):
        super().__init__(parent)
        self.face_recognition = face_recognition
        self.db = DatabaseManager()
        self.authenticated_user = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('LYRA - Login')
        
        # Get screen size for responsive design
        screen = QApplication.desktop().screenGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # Set window size based on screen resolution (responsive)
        window_width = min(650, int(screen_width * 0.35))
        window_height = min(750, int(screen_height * 0.75))
        
        self.setMinimumSize(550, 650)
        self.resize(window_width, window_height)
        
        # Allow window resizing
        self.setModal(True)
        
        # Apply responsive styling with scalable fonts
        self.apply_responsive_style()
        
        # Main layout with proper margins
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(15)
        
        # Logo and title - responsive font size
        title_label = QLabel('🎤 LYRA')
        title_label.setObjectName('titleLabel')
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle = QLabel('Multilingual Voice Assistant')
        subtitle.setObjectName('subtitleLabel')
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(15)
        
        # Tab widget for different login methods
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName('mainTabWidget')
        
        # Password login tab
        password_tab = self.create_password_login_tab()
        self.tab_widget.addTab(password_tab, "Password Login")
        
        # Face recognition tab
        face_tab = self.create_face_login_tab()
        self.tab_widget.addTab(face_tab, "Face Login")
        
        # Register tab
        register_tab = self.create_register_tab()
        self.tab_widget.addTab(register_tab, "Register")
        
        layout.addWidget(self.tab_widget)
        
        # Status label - responsive font
        self.status_label = QLabel('')
        self.status_label.setObjectName('statusLabel')
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Install event filter for resize events
        self.installEventFilter(self)
    
    def apply_responsive_style(self):
        """Apply responsive stylesheet that scales with window size"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            
            QLabel {
                color: white;
            }
            
            QLabel#titleLabel {
                font-size: 42px;
                font-weight: bold;
                color: #0078d4;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 10px;
            }
            
            QLabel#subtitleLabel {
                font-size: 16px;
                color: #b0b0b0;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 5px;
            }
            
            QLabel#statusLabel {
                font-size: 14px;
                color: #e81123;
                padding: 8px;
                min-height: 25px;
            }
            
            QLineEdit {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                padding: 14px;
                color: white;
                font-size: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
                min-height: 20px;
            }
            
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
            
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 16px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                font-family: 'Segoe UI', Arial, sans-serif;
                min-height: 20px;
            }
            
            QPushButton:hover {
                background-color: #106ebe;
            }
            
            QPushButton:pressed {
                background-color: #005a9e;
            }
            
            QCheckBox {
                color: white;
                font-size: 14px;
                spacing: 8px;
                padding: 5px;
            }
            
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #3d3d3d;
                border-radius: 4px;
                background-color: #2d2d2d;
            }
            
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #0078d4;
            }
            
            QTabWidget#mainTabWidget::pane {
                border: 2px solid #3d3d3d;
                background-color: #2d2d2d;
                border-radius: 8px;
                padding: 5px;
            }
            
            QTabWidget#mainTabWidget QTabBar::tab {
                background-color: #2d2d2d;
                color: white;
                padding: 14px 24px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 15px;
                font-weight: 500;
                margin-right: 2px;
                min-width: 120px;
            }
            
            QTabWidget#mainTabWidget QTabBar::tab:selected {
                background-color: #0078d4;
                color: white;
            }
            
            QTabWidget#mainTabWidget QTabBar::tab:hover {
                background-color: #3d3d3d;
            }
        """)
    
    def eventFilter(self, obj, event):
        """Handle window resize events for responsive layout"""
        if event.type() == QEvent.Resize and obj == self:
            # You can add dynamic font size adjustments here if needed
            pass
        return super().eventFilter(obj, event)
    
    def create_password_login_tab(self):
        """Create password login interface with responsive layout"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Scroll area for smaller screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)
        
        # Username
        username_label = QLabel('Username:')
        username_label.setStyleSheet('font-size: 15px; font-weight: 500; color: #e0e0e0;')
        scroll_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('Enter your username')
        scroll_layout.addWidget(self.username_input)
        
        # Password
        password_label = QLabel('Password:')
        password_label.setStyleSheet('font-size: 15px; font-weight: 500; color: #e0e0e0;')
        scroll_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText('Enter your password')
        self.password_input.returnPressed.connect(self.password_login)
        scroll_layout.addWidget(self.password_input)
        
        # Remember me checkbox
        self.remember_checkbox = QCheckBox('Remember me')
        scroll_layout.addWidget(self.remember_checkbox)
        
        scroll_layout.addSpacing(10)
        
        # Login button
        login_btn = QPushButton('🔐 Login')
        login_btn.clicked.connect(self.password_login)
        scroll_layout.addWidget(login_btn)
        
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        widget.setLayout(main_layout)
        
        return widget
    
    def create_face_login_tab(self):
        """Create face recognition login interface with responsive layout"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Instructions
        instructions = QLabel('Click the button below to authenticate with your face')
        instructions.setWordWrap(True)
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setStyleSheet('color: #b0b0b0; font-size: 15px; padding: 10px;')
        layout.addWidget(instructions)
        
        # Camera icon/placeholder
        camera_label = QLabel('📷')
        camera_label.setStyleSheet('font-size: 90px; padding: 20px;')
        camera_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(camera_label)
        
        # Face login button
        face_login_btn = QPushButton('🔐 Authenticate with Face')
        face_login_btn.clicked.connect(self.face_login)
        face_login_btn.setMinimumHeight(60)
        face_login_btn.setStyleSheet("""
            QPushButton {
                font-size: 17px;
                padding: 18px;
            }
        """)
        layout.addWidget(face_login_btn)
        
        # Status
        self.face_status = QLabel('')
        self.face_status.setAlignment(Qt.AlignCenter)
        self.face_status.setStyleSheet('color: #b0b0b0; font-size: 14px; padding: 10px;')
        self.face_status.setWordWrap(True)
        layout.addWidget(self.face_status)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_register_tab(self):
        """Create user registration interface with responsive layout"""
        widget = QWidget()
        
        # Scroll area for all content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(12)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Username
        username_label = QLabel('Username:')
        username_label.setStyleSheet('font-size: 15px; font-weight: 500; color: #e0e0e0;')
        layout.addWidget(username_label)
        
        self.reg_username_input = QLineEdit()
        self.reg_username_input.setPlaceholderText('Choose a username (min 3 characters)')
        layout.addWidget(self.reg_username_input)
        
        # Email
        email_label = QLabel('Email (optional):')
        email_label.setStyleSheet('font-size: 15px; font-weight: 500; color: #e0e0e0;')
        layout.addWidget(email_label)
        
        self.reg_email_input = QLineEdit()
        self.reg_email_input.setPlaceholderText('your.email@example.com')
        layout.addWidget(self.reg_email_input)
        
        # Password
        password_label = QLabel('Password:')
        password_label.setStyleSheet('font-size: 15px; font-weight: 500; color: #e0e0e0;')
        layout.addWidget(password_label)
        
        self.reg_password_input = QLineEdit()
        self.reg_password_input.setEchoMode(QLineEdit.Password)
        self.reg_password_input.setPlaceholderText('Choose a password (min 6 characters)')
        layout.addWidget(self.reg_password_input)
        
        # Confirm password
        confirm_label = QLabel('Confirm Password:')
        confirm_label.setStyleSheet('font-size: 15px; font-weight: 500; color: #e0e0e0;')
        layout.addWidget(confirm_label)
        
        self.reg_confirm_input = QLineEdit()
        self.reg_confirm_input.setEchoMode(QLineEdit.Password)
        self.reg_confirm_input.setPlaceholderText('Confirm your password')
        layout.addWidget(self.reg_confirm_input)
        
        layout.addSpacing(8)
        
        # Register with face checkbox
        self.register_face_checkbox = QCheckBox('Register with facial recognition')
        self.register_face_checkbox.setChecked(True)
        layout.addWidget(self.register_face_checkbox)
        
        layout.addSpacing(10)
        
        # Register button
        register_btn = QPushButton('✨ Create Account')
        register_btn.clicked.connect(self.register_user)
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: #107c10;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #0e6b0e;
            }
        """)
        layout.addWidget(register_btn)
        
        layout.addStretch()
        
        scroll.setWidget(scroll_content)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        widget.setLayout(main_layout)
        
        return widget
    
    def password_login(self):
        """Handle password-based login"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            self.status_label.setText('❌ Please enter username and password')
            self.status_label.setStyleSheet('color: #e81123; font-size: 14px;')
            return
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Check credentials in database
        query = 'SELECT user_id, username FROM users WHERE username = ? AND password_hash = ?'
        result = self.db.execute_query(query, (username, password_hash))
        
        if result:
            self.authenticated_user = result[0][1]
            self.status_label.setStyleSheet('color: #107c10; font-size: 14px;')
            self.status_label.setText(f'✅ Welcome, {self.authenticated_user}!')
            
            # Update last login
            update_query = 'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = ?'
            self.db.execute_query(update_query, (username,))
            
            QTimer.singleShot(1000, self.accept)
        else:
            self.status_label.setStyleSheet('color: #e81123; font-size: 14px;')
            self.status_label.setText('❌ Invalid username or password')
    
    def face_login(self):
        """Handle face recognition login"""
        # Check if face recognition is available
        if self.face_recognition is None:
            self.face_status.setStyleSheet('color: #e81123; font-size: 14px;')
            self.face_status.setText('❌ Face recognition is not available. Please use password login or register first.')
            return
        
        # Check if there are any registered users
        if not hasattr(self.face_recognition, 'known_encodings') or not self.face_recognition.known_encodings:
            self.face_status.setStyleSheet('color: #e81123; font-size: 14px;')
            self.face_status.setText('❌ No registered users found. Please register first using the Register tab.')
            return
        
        registered_users = list(self.face_recognition.known_encodings.keys())
        self.face_status.setText(f'📷 Initializing camera... (Registered: {", ".join(registered_users)})')
        self.face_status.setStyleSheet('color: #0078d4; font-size: 14px;')
        QApplication.processEvents()
        
        # Authenticate with face - try with different thresholds for better matching
        success, username = self.face_recognition.authenticate_user(timeout=20, distance_threshold=0.6)
        
        if success:
            # Verify user exists in database
            check_query = 'SELECT user_id, username FROM users WHERE username = ?'
            user_data = self.db.execute_query(check_query, (username,))
            
            if not user_data:
                self.face_status.setStyleSheet('color: #e81123; font-size: 14px;')
                self.face_status.setText(f'❌ User "{username}" not found in database. Please register first.')
                return
            
            self.authenticated_user = username
            self.face_status.setStyleSheet('color: #107c10; font-size: 14px;')
            self.face_status.setText(f'✅ Welcome, {username}!')
            
            # Update last login
            update_query = 'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = ?'
            self.db.execute_query(update_query, (username,))
            
            QTimer.singleShot(1000, self.accept)
        else:
            self.face_status.setStyleSheet('color: #e81123; font-size: 14px;')
            error_msg = f'❌ Face authentication failed. '
            if registered_users:
                error_msg += f'Make sure you are one of: {", ".join(registered_users)}'
            else:
                error_msg += 'Please register first.'
            self.face_status.setText(error_msg)
    
    def register_user(self):
        """Handle user registration"""
        username = self.reg_username_input.text().strip()
        email = self.reg_email_input.text().strip()
        password = self.reg_password_input.text()
        confirm_password = self.reg_confirm_input.text()
        
        # Validation
        if not username:
            self.status_label.setText('❌ Username is required')
            self.status_label.setStyleSheet('color: #e81123; font-size: 14px;')
            return
        
        if len(username) < 3:
            self.status_label.setText('❌ Username must be at least 3 characters')
            self.status_label.setStyleSheet('color: #e81123; font-size: 14px;')
            return
        
        if not password:
            self.status_label.setText('❌ Password is required')
            self.status_label.setStyleSheet('color: #e81123; font-size: 14px;')
            return
        
        if len(password) < 6:
            self.status_label.setText('❌ Password must be at least 6 characters')
            self.status_label.setStyleSheet('color: #e81123; font-size: 14px;')
            return
        
        if password != confirm_password:
            self.status_label.setText('❌ Passwords do not match')
            self.status_label.setStyleSheet('color: #e81123; font-size: 14px;')
            return
        
        # Check if username exists
        check_query = 'SELECT user_id FROM users WHERE username = ?'
        existing = self.db.execute_query(check_query, (username,))
        
        if existing:
            self.status_label.setText('❌ Username already exists')
            self.status_label.setStyleSheet('color: #e81123; font-size: 14px;')
            return
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Register with face if checked
        face_encoding_path = None
        if self.register_face_checkbox.isChecked():
            # Check if face recognition is available
            if self.face_recognition is None:
                self.status_label.setStyleSheet('color: #e81123; font-size: 14px;')
                self.status_label.setText('❌ Face recognition is not available. Registration will continue without face recognition.')
                self.register_face_checkbox.setChecked(False)
            else:
                self.status_label.setStyleSheet('color: #0078d4; font-size: 14px;')
                self.status_label.setText('📷 Registering face... Look at the camera and wait for samples to be collected')
                QApplication.processEvents()
                
                success, message = self.face_recognition.register_user(username)
                if not success:
                    self.status_label.setStyleSheet('color: #e81123; font-size: 14px;')
                    self.status_label.setText(f'❌ Face registration failed: {message}')
                    return
                
                # Reload encodings to include the newly registered user
                self.face_recognition.load_encodings()
                face_encoding_path = f'data/face_encodings/{username}.pkl'
        
        # Insert user into database
        insert_query = '''
            INSERT INTO users (username, email, password_hash, face_encoding_path, preferences)
            VALUES (?, ?, ?, ?, ?)
        '''
        default_preferences = '{"theme": "dark", "language": "en", "voice_index": 0}'
        self.db.execute_query(insert_query, (username, email, password_hash, face_encoding_path, default_preferences))
        
        self.status_label.setStyleSheet('color: #107c10; font-size: 15px;')
        self.status_label.setText('✅ Registration successful! You can now login')
        
        # Switch to login tab
        QTimer.singleShot(2000, lambda: self.tab_widget.setCurrentIndex(0))
    
    def get_authenticated_user(self):
        """Return authenticated username"""
        return self.authenticated_user
    
    def resizeEvent(self, event):
        """Handle window resize to maintain responsive layout"""
        super().resizeEvent(event)
        # Window will auto-adjust due to responsive stylesheet