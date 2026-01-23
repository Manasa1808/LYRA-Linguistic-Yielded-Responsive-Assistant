#profile_manager.py
from PyQt5.QtWidgets import (
    QDialog, QWidget, QLabel, QPushButton, QLineEdit, QVBoxLayout, 
    QHBoxLayout, QTableWidget, QTableWidgetItem, QMessageBox, 
    QComboBox, QTextEdit, QDialogButtonBox
)
from PyQt5.QtCore import Qt

from database.db_manager import DatabaseManager
import json
from datetime import datetime

class ProfileManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.current_user_id = None
        self.current_username = None
    
    def login(self, username):
        """Login user and load profile"""
        query = 'SELECT user_id, username, preferences, last_login FROM users WHERE username = ?'
        result = self.db.execute_query(query, (username,))
        
        if result:
            self.current_user_id = result[0][0]
            self.current_username = result[0][1]
            preferences_json = result[0][2]
            
            # Update last login
            update_query = 'UPDATE users SET last_login = ? WHERE user_id = ?'
            self.db.execute_query(update_query, (datetime.now(), self.current_user_id))
            
            return True, json.loads(preferences_json) if preferences_json else {}
        
        return False, None
    
    def logout(self):
        """Logout current user"""
        self.current_user_id = None
        self.current_username = None
    
    def get_user_preferences(self):
        """Get current user preferences"""
        if not self.current_user_id:
            return {}
        
        query = 'SELECT preferences FROM users WHERE user_id = ?'
        result = self.db.execute_query(query, (self.current_user_id,))
        
        if result and result[0][0]:
            return json.loads(result[0][0])
        return {}
    
    def update_preferences(self, preferences):
        """Update user preferences"""
        if not self.current_user_id:
            return False
        
        query = 'UPDATE users SET preferences = ? WHERE user_id = ?'
        self.db.execute_query(query, (json.dumps(preferences), self.current_user_id))
        return True
    
    def get_user_stats(self):
        """Get user statistics"""
        if not self.current_user_id:
            return {}
        
        stats = {}
        
        # Count notes
        notes_query = 'SELECT COUNT(*) FROM notes WHERE user_id = ?'
        notes_result = self.db.execute_query(notes_query, (self.current_user_id,))
        stats['notes_count'] = notes_result[0][0] if notes_result else 0
        
        # Count reminders
        reminders_query = 'SELECT COUNT(*) FROM reminders WHERE user_id = ?'
        reminders_result = self.db.execute_query(reminders_query, (self.current_user_id,))
        stats['reminders_count'] = reminders_result[0][0] if reminders_result else 0
        
        # Count events
        events_query = 'SELECT COUNT(*) FROM calendar_events WHERE user_id = ?'
        events_result = self.db.execute_query(events_query, (self.current_user_id,))
        stats['events_count'] = events_result[0][0] if events_result else 0
        
        # Count commands
        commands_query = 'SELECT COUNT(*) FROM command_history WHERE user_id = ?'
        commands_result = self.db.execute_query(commands_query, (self.current_user_id,))
        stats['commands_count'] = commands_result[0][0] if commands_result else 0
        
        return stats
    
    def delete_user_data(self):
        """Delete all user data (except account)"""
        if not self.current_user_id:
            return False
        
        tables = ['notes', 'reminders', 'calendar_events', 'custom_commands', 'command_history']
        
        for table in tables:
            query = f'DELETE FROM {table} WHERE user_id = ?'
            self.db.execute_query(query, (self.current_user_id,))
        
        return True

from database.db_manager import DatabaseManager
import json
import subprocess
import os

class CustomCommandsManager:
    def __init__(self, db_manager):
        self.db = db_manager
        self.commands_cache = {}
    
    def create_custom_command(self, user_id, trigger_phrase, action_type, action_params):
        """Create a new custom command"""
        query = '''
            INSERT INTO custom_commands (user_id, trigger_phrase, action_type, action_params)
            VALUES (?, ?, ?, ?)
        '''
        
        action_params_json = json.dumps(action_params)
        self.db.execute_query(query, (user_id, trigger_phrase.lower(), action_type, action_params_json))
        
        # Update cache
        self.load_user_commands(user_id)
        
        return True, f"Custom command '{trigger_phrase}' created successfully"
    
    def get_user_commands(self, user_id):
        """Get all custom commands for a user"""
        query = '''
            SELECT command_id, trigger_phrase, action_type, action_params, is_active
            FROM custom_commands
            WHERE user_id = ?
            ORDER BY trigger_phrase
        '''
        
        results = self.db.execute_query(query, (user_id,))
        commands = []
        
        for row in results:
            commands.append({
                'command_id': row[0],
                'trigger_phrase': row[1],
                'action_type': row[2],
                'action_params': json.loads(row[3]) if row[3] else {},
                'is_active': bool(row[4])
            })
        
        return commands
    
    def load_user_commands(self, user_id):
        """Load user commands into cache"""
        commands = self.get_user_commands(user_id)
        self.commands_cache[user_id] = {cmd['trigger_phrase']: cmd for cmd in commands if cmd['is_active']}
    
    def match_custom_command(self, user_id, text):
        """Check if text matches any custom command"""
        if user_id not in self.commands_cache:
            self.load_user_commands(user_id)
        
        text_lower = text.lower()
        
        for trigger, command in self.commands_cache[user_id].items():
            if trigger in text_lower:
                return command
        
        return None
    
    def execute_custom_command(self, command):
        """Execute a custom command"""
        action_type = command['action_type']
        action_params = command['action_params']
        
        try:
            if action_type == 'run_script':
                # Execute a script
                script_path = action_params.get('script_path')
                if script_path and os.path.exists(script_path):
                    subprocess.run([script_path], shell=True)
                    return True, f"Executed script: {script_path}"
                return False, "Script not found"
            
            elif action_type == 'open_url':
                # Open URL in browser
                url = action_params.get('url')
                import webbrowser
                webbrowser.open(url)
                return True, f"Opened URL: {url}"
            
            elif action_type == 'type_text':
                # Type text using pyautogui
                import pyautogui
                text = action_params.get('text', '')
                pyautogui.write(text)
                return True, "Text typed"
            
            elif action_type == 'press_keys':
                # Press keyboard shortcut
                import pyautogui
                keys = action_params.get('keys', [])
                pyautogui.hotkey(*keys)
                return True, f"Pressed keys: {'+'.join(keys)}"
            
            elif action_type == 'run_command':
                # Run system command
                command = action_params.get('command')
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                return True, f"Command output: {result.stdout}"
            
            elif action_type == 'speak_text':
                # Speak custom text (will be handled by TTS)
                text = action_params.get('text', '')
                return True, text
            
            else:
                return False, f"Unknown action type: {action_type}"
        
        except Exception as e:
            return False, f"Error executing command: {str(e)}"
    
    def update_custom_command(self, command_id, **kwargs):
        """Update a custom command"""
        updates = []
        params = []
        
        for key, value in kwargs.items():
            if key == 'action_params':
                value = json.dumps(value)
            updates.append(f"{key} = ?")
            params.append(value)
        
        params.append(command_id)
        
        query = f"UPDATE custom_commands SET {', '.join(updates)} WHERE command_id = ?"
        self.db.execute_query(query, tuple(params))
        
        return True, "Command updated successfully"
    
    def delete_custom_command(self, command_id):
        """Delete a custom command"""
        query = 'DELETE FROM custom_commands WHERE command_id = ?'
        self.db.execute_query(query, (command_id,))
        return True, "Command deleted successfully"
    
    def toggle_command(self, command_id, is_active):
        """Enable or disable a command"""
        query = 'UPDATE custom_commands SET is_active = ? WHERE command_id = ?'
        self.db.execute_query(query, (1 if is_active else 0, command_id))
        return True, f"Command {'enabled' if is_active else 'disabled'}"


class CustomCommandsGUI(QDialog):
    """GUI for managing custom commands"""
    def __init__(self, user_id, commands_manager, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.commands_manager = commands_manager
        self.init_ui()
        self.load_commands()
    
    def init_ui(self):
        self.setWindowTitle('Custom Commands')
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel('⚡ Custom Commands')
        title.setStyleSheet('font-size: 24px; font-weight: bold; color: #0078d4;')
        layout.addWidget(title)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        add_btn = QPushButton('➕ Add Command')
        add_btn.clicked.connect(self.add_command)
        toolbar_layout.addWidget(add_btn)
        
        edit_btn = QPushButton('✏️ Edit')
        edit_btn.clicked.connect(self.edit_command)
        toolbar_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton('🗑️ Delete')
        delete_btn.setObjectName('dangerButton')
        delete_btn.clicked.connect(self.delete_command)
        toolbar_layout.addWidget(delete_btn)
        
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Commands table
        self.commands_table = QTableWidget()
        self.commands_table.setColumnCount(4)
        self.commands_table.setHorizontalHeaderLabels(['Trigger Phrase', 'Action Type', 'Status', 'ID'])
        self.commands_table.setColumnHidden(3, True)
        self.commands_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.commands_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.commands_table)
        
        # Close button
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def load_commands(self):
        """Load commands into table"""
        commands = self.commands_manager.get_user_commands(self.user_id)
        self.commands_table.setRowCount(len(commands))
        
        for row, cmd in enumerate(commands):
            self.commands_table.setItem(row, 0, QTableWidgetItem(cmd['trigger_phrase']))
            self.commands_table.setItem(row, 1, QTableWidgetItem(cmd['action_type']))
            self.commands_table.setItem(row, 2, QTableWidgetItem('Active' if cmd['is_active'] else 'Inactive'))
            self.commands_table.setItem(row, 3, QTableWidgetItem(str(cmd['command_id'])))
    
    def add_command(self):
        """Show dialog to add new command"""
        dialog = AddCommandDialog(self.user_id, self.commands_manager, self)
        if dialog.exec_():
            self.load_commands()
    
    def edit_command(self):
        """Edit selected command"""
        current_row = self.commands_table.currentRow()
        if current_row >= 0:
            command_id = int(self.commands_table.item(current_row, 3).text())
            # Show edit dialog
            QMessageBox.information(self, 'Edit', 'Edit functionality will be implemented')
    
    def delete_command(self):
        """Delete selected command"""
        current_row = self.commands_table.currentRow()
        if current_row >= 0:
            command_id = int(self.commands_table.item(current_row, 3).text())
            
            reply = QMessageBox.question(
                self,
                'Delete Command',
                'Are you sure you want to delete this command?',
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.commands_manager.delete_custom_command(command_id)
                self.load_commands()


from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class AddCommandDialog(QDialog):
    """Dialog for adding new custom command"""
    def __init__(self, user_id, commands_manager, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.commands_manager = commands_manager
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle('Add Custom Command')
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        
        # Trigger phrase
        phrase_label = QLabel('Trigger Phrase:')
        layout.addWidget(phrase_label)
        
        self.phrase_input = QLineEdit()
        self.phrase_input.setPlaceholderText('e.g., "turn on the lights"')
        layout.addWidget(self.phrase_input)
        
        # Action type
        type_label = QLabel('Action Type:')
        layout.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            'run_script',
            'open_url',
            'type_text',
            'press_keys',
            'run_command',
            'speak_text'
        ])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        layout.addWidget(self.type_combo)
        
        # Action parameters (dynamic based on type)
        self.params_widget = QWidget()
        self.params_layout = QVBoxLayout()
        self.params_widget.setLayout(self.params_layout)
        layout.addWidget(self.params_widget)
        
        self.on_type_changed(self.type_combo.currentText())
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_command)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def on_type_changed(self, action_type):
        """Update parameters based on action type"""
        # Clear existing params
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if action_type == 'run_script':
            label = QLabel('Script Path:')
            self.params_layout.addWidget(label)
            
            self.param_input = QLineEdit()
            self.param_input.setPlaceholderText('/path/to/script.sh')
            self.params_layout.addWidget(self.param_input)
        
        elif action_type == 'open_url':
            label = QLabel('URL:')
            self.params_layout.addWidget(label)
            
            self.param_input = QLineEdit()
            self.param_input.setPlaceholderText('https://example.com')
            self.params_layout.addWidget(self.param_input)
        
        elif action_type == 'type_text':
            label = QLabel('Text to Type:')
            self.params_layout.addWidget(label)
            
            self.param_input = QTextEdit()
            self.param_input.setPlaceholderText('Enter text to be typed')
            self.param_input.setMaximumHeight(100)
            self.params_layout.addWidget(self.param_input)
        
        elif action_type == 'press_keys':
            label = QLabel('Keys (comma-separated):')
            self.params_layout.addWidget(label)
            
            self.param_input = QLineEdit()
            self.param_input.setPlaceholderText('ctrl, c (for Ctrl+C)')
            self.params_layout.addWidget(self.param_input)
        
        elif action_type == 'run_command':
            label = QLabel('System Command:')
            self.params_layout.addWidget(label)
            
            self.param_input = QLineEdit()
            self.param_input.setPlaceholderText('echo "Hello World"')
            self.params_layout.addWidget(self.param_input)
        
        elif action_type == 'speak_text':
            label = QLabel('Text to Speak:')