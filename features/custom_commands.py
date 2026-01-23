# features/custom_commands.py
from database.db_manager import DatabaseManager
import json
import subprocess
import os
import webbrowser

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class CustomCommandsManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.commands_cache = {}

    # --------------------
    # Persistence helpers
    # --------------------
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
        """Check if text matches any custom command (simple substring match)"""
        if user_id not in self.commands_cache:
            self.load_user_commands(user_id)

        text_lower = text.lower()
        user_map = self.commands_cache.get(user_id, {})

        # exact trigger or substring
        for trigger, command in user_map.items():
            if trigger.strip() and (trigger == text_lower or trigger in text_lower):
                return command
        return None

    # --------------------
    # Execution
    # --------------------
    def execute_custom_command(self, command):
        """Execute a custom command"""
        action_type = command['action_type']
        action_params = command['action_params'] or {}

        try:
            if action_type == 'run_script':
                script_path = action_params.get('script_path')
                if script_path and os.path.exists(script_path):
                    subprocess.run([script_path], shell=True)
                    return True, f"Executed script: {script_path}"
                return False, "Script not found"

            elif action_type == 'open_url':
                url = action_params.get('url')
                if url:
                    webbrowser.open(url)
                    return True, f"Opened URL: {url}"
                return False, "No URL provided"

            elif action_type == 'type_text':
                try:
                    import pyautogui
                except Exception as e:
                    return False, f"pyautogui not available: {e}"
                text = action_params.get('text', '')
                pyautogui.write(text)
                return True, "Text typed"

            elif action_type == 'press_keys':
                try:
                    import pyautogui
                except Exception as e:
                    return False, f"pyautogui not available: {e}"
                keys = action_params.get('keys', [])
                if not isinstance(keys, list):
                    return False, "Keys must be a list"
                pyautogui.hotkey(*keys)
                return True, f"Pressed keys: {'+'.join(keys)}"

            elif action_type == 'run_command':
                cmd = action_params.get('command')
                if not cmd:
                    return False, "No command provided"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                return True, result.stdout.strip() if result.stdout else "Command executed"

            elif action_type == 'speak_text':
                text = action_params.get('text', '')
                return True, text

            else:
                return False, f"Unknown action type: {action_type}"

        except Exception as e:
            return False, f"Error executing command: {str(e)}"

    # --------------------
    # CRUD helpers
    # --------------------
    def update_custom_command(self, command_id, **kwargs):
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
        query = 'DELETE FROM custom_commands WHERE command_id = ?'
        self.db.execute_query(query, (command_id,))
        return True, "Command deleted successfully"

    def toggle_command(self, command_id, is_active):
        query = 'UPDATE custom_commands SET is_active = ? WHERE command_id = ?'
        self.db.execute_query(query, (1 if is_active else 0, command_id))
        return True, f"Command {'enabled' if is_active else 'disabled'}"


# ---------------------------
# GUI classes (PyQt)
# ---------------------------
class CustomCommandsGUI(QDialog):
    """GUI for managing custom commands - now integrated with hardcoded responses"""
    def __init__(self, user_id, commands_manager, hardcoded_responses=None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.commands_manager = commands_manager
        self.hardcoded_responses = hardcoded_responses  # New: reference to hardcoded responses
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

        add_btn = QPushButton('➕ Add Database Command')
        add_btn.clicked.connect(self.add_command)
        add_btn.setToolTip('Add command stored in database (persistent)')
        toolbar_layout.addWidget(add_btn)

        add_hardcoded_btn = QPushButton('🔥 Add Hardcoded Command')
        add_hardcoded_btn.setStyleSheet('background-color: #ff6b35; color: white; font-weight: bold;')
        add_hardcoded_btn.clicked.connect(self.add_hardcoded_command)
        add_hardcoded_btn.setToolTip('Add command hardcoded in memory (like sentiment analysis)')
        toolbar_layout.addWidget(add_hardcoded_btn)

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

    def add_hardcoded_command(self):
        """Show dialog to add new hardcoded command (integrated with hardcoded responses)"""
        if not self.hardcoded_responses:
            QMessageBox.warning(self, 'Error', 'Hardcoded responses system not available')
            return

        dialog = AddHardcodedCommandDialog(self.hardcoded_responses, self)
        if dialog.exec_():
            self.load_commands()


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

        # Default widgets (we will set param_input for each case)
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
            self.params_layout.addWidget(label)

            self.param_input = QTextEdit()
            self.param_input.setPlaceholderText('Enter text to be spoken')
            self.param_input.setMaximumHeight(100)
            self.params_layout.addWidget(self.param_input)

    def save_command(self):
        """Save the custom command"""
        trigger_phrase = self.phrase_input.text().strip()
        action_type = self.type_combo.currentText()

        if not trigger_phrase:
            QMessageBox.warning(self, 'Error', 'Please enter a trigger phrase')
            return

        # Build action params based on type
        action_params = {}

        if action_type == 'run_script':
            action_params['script_path'] = self.param_input.text().strip()
        elif action_type == 'open_url':
            action_params['url'] = self.param_input.text().strip()
        elif action_type in ['type_text', 'speak_text']:
            action_params['text'] = self.param_input.toPlainText().strip()
        elif action_type == 'press_keys':
            keys_text = self.param_input.text().strip()
            # split by comma and sanitize
            action_params['keys'] = [k.strip() for k in keys_text.split(',') if k.strip()]
        elif action_type == 'run_command':
            action_params['command'] = self.param_input.text().strip()

        # Save to database
        success, message = self.commands_manager.create_custom_command(
            self.user_id,
            trigger_phrase,
            action_type,
            action_params
        )

        if success:
            QMessageBox.information(self, 'Success', message)
            self.accept()
        else:
            QMessageBox.warning(self, 'Error', message)


class AddHardcodedCommandDialog(QDialog):
    """Dialog for adding new hardcoded command (integrated with hardcoded responses)"""
    def __init__(self, hardcoded_responses, parent=None):
        super().__init__(parent)
        self.hardcoded_responses = hardcoded_responses
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Add Hardcoded Command')
        self.setMinimumSize(500, 300)

        layout = QVBoxLayout()

        # Title
        title = QLabel('🔥 Add Hardcoded Command')
        title.setStyleSheet('font-size: 18px; font-weight: bold; color: #ff6b35;')
        layout.addWidget(title)

        # Language selector
        lang_label = QLabel('Language:')
        layout.addWidget(lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.addItem('English (en)', 'en')
        self.lang_combo.addItem('Hindi (hi) - हिन्दी', 'hi')
        self.lang_combo.addItem('Kannada (kn) - ಕನ್ನಡ', 'kn')
        layout.addWidget(self.lang_combo)

        # Command text
        cmd_label = QLabel('Command Text:')
        layout.addWidget(cmd_label)

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText('e.g., "hello", "namaste", "namaskara"')
        layout.addWidget(self.cmd_input)

        # Response text
        resp_label = QLabel('Response Text:')
        layout.addWidget(resp_label)

        self.resp_input = QTextEdit()
        self.resp_input.setPlaceholderText('e.g., "Hello! How can I help you?", "नमस्ते! मैं आपकी कैसे मदद कर सकता हूं?", "ನಮಸ್ಕಾರ! ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?"')
        self.resp_input.setMaximumHeight(80)
        layout.addWidget(self.resp_input)

        # Info label
        info_label = QLabel('ℹ️ This command will be hardcoded in memory like sentiment analysis.\nIt will work immediately without database lookup.')
        info_label.setStyleSheet('color: #666; font-size: 12px;')
        layout.addWidget(info_label)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_hardcoded_command)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def save_hardcoded_command(self):
        """Save the hardcoded command"""
        command_text = self.cmd_input.text().strip()
        response_text = self.resp_input.toPlainText().strip()
        language = self.lang_combo.currentData()

        if not command_text:
            QMessageBox.warning(self, 'Error', 'Please enter a command text')
            return

        if not response_text:
            QMessageBox.warning(self, 'Error', 'Please enter a response text')
            return

        # Add to hardcoded responses system
        success = self.hardcoded_responses.add_custom_command(command_text, response_text, language)

        if success:
            QMessageBox.information(self, 'Success',
                f'Hardcoded command added successfully!\n\nCommand: "{command_text}"\nResponse: "{response_text}"\nLanguage: {language.upper()}')
            self.accept()
        else:
            QMessageBox.warning(self, 'Error', 'Failed to add hardcoded command')
