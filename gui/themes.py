#themes.py
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

class ThemeManager:
    @staticmethod
    def get_dark_theme():
        """Modern dark theme stylesheet"""
        return """
            /* Main Window */
            QMainWindow {
                background-color: #1e1e1e;
            }
            
            /* Base Widget Styling */
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
                font-size: 14px;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 600;
                min-height: 35px;
            }
            
            QPushButton:hover {
                background-color: #106ebe;
            }
            
            QPushButton:pressed {
                background-color: #005a9e;
            }
            
            QPushButton:disabled {
                background-color: #3d3d3d;
                color: #808080;
            }
            
            QPushButton#dangerButton {
                background-color: #e81123;
            }
            
            QPushButton#dangerButton:hover {
                background-color: #c50f1f;
            }
            
            QPushButton#successButton {
                background-color: #107c10;
            }
            
            QPushButton#successButton:hover {
                background-color: #0e6b0e;
            }
            
            QPushButton#secondaryButton {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
            }
            
            QPushButton#secondaryButton:hover {
                background-color: #3d3d3d;
            }
            
            /* Input Fields */
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 10px;
                color: #ffffff;
                selection-background-color: #0078d4;
            }
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border: 2px solid #0078d4;
            }
            
            /* ComboBox */
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 8px;
                min-height: 35px;
            }
            
            QComboBox:hover {
                border: 1px solid #0078d4;
            }
            
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            
            QComboBox::down-arrow {
                image: url(assets/icons/down-arrow.png);
                width: 12px;
                height: 12px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                selection-background-color: #0078d4;
                outline: none;
            }
            
            /* List Widget */
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 5px;
                outline: none;
            }
            
            QListWidget::item {
                padding: 10px;
                border-radius: 4px;
                margin: 2px;
            }
            
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
            
            /* Table Widget */
            QTableWidget {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                gridline-color: #3d3d3d;
            }
            
            QTableWidget::item {
                padding: 8px;
            }
            
            QTableWidget::item:selected {
                background-color: #0078d4;
            }
            
            QHeaderView::section {
                background-color: #252525;
                color: white;
                padding: 10px;
                border: none;
                border-bottom: 1px solid #3d3d3d;
                font-weight: bold;
            }
            
            /* Scroll Bar */
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #5d5d5d;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #6d6d6d;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar:horizontal {
                background-color: #2d2d2d;
                height: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #5d5d5d;
                border-radius: 6px;
                min-width: 20px;
            }
            
            /* Tab Widget */
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                background-color: #2d2d2d;
            }
            
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 10px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background-color: #0078d4;
            }
            
            QTabBar::tab:hover {
                background-color: #3d3d3d;
            }
            
            /* Checkboxes and Radio Buttons */
            QCheckBox, QRadioButton {
                spacing: 8px;
            }
            
            QCheckBox::indicator, QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #3d3d3d;
                border-radius: 4px;
                background-color: #2d2d2d;
            }
            
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #0078d4;
            }
            
            QRadioButton::indicator {
                border-radius: 9px;
            }
            
            /* Progress Bar */
            QProgressBar {
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                background-color: #2d2d2d;
                text-align: center;
                height: 20px;
            }
            
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 5px;
            }
            
            /* Slider */
            QSlider::groove:horizontal {
                height: 6px;
                background: #3d3d3d;
                border-radius: 3px;
            }
            
            QSlider::handle:horizontal {
                background: #0078d4;
                width: 16px;
                height: 16px;
                border-radius: 8px;
                margin: -5px 0;
            }
            
            QSlider::handle:horizontal:hover {
                background: #106ebe;
            }
            
            /* Menu Bar */
            QMenuBar {
                background-color: #2d2d2d;
                color: white;
            }
            
            QMenuBar::item:selected {
                background-color: #0078d4;
            }
            
            QMenu {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
            }
            
            QMenu::item:selected {
                background-color: #0078d4;
            }
            
            /* Status Bar */
            QStatusBar {
                background-color: #252525;
                color: #ffffff;
                border-top: 1px solid #3d3d3d;
            }
            
            /* Tool Tip */
            QToolTip {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #0078d4;
                border-radius: 4px;
                padding: 5px;
            }
            
            /* Group Box */
            QGroupBox {
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            
            /* Spin Box */
            QSpinBox, QDoubleSpinBox {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 5px;
            }
            
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                background-color: #3d3d3d;
                border-radius: 3px;
            }
            
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                background-color: #3d3d3d;
                border-radius: 3px;
            }
        """
    
    @staticmethod
    def get_light_theme():
        """Modern light theme stylesheet"""
        return """
            /* Main Window */
            QMainWindow {
                background-color: #f5f5f5;
            }
            
            /* Base Widget Styling */
            QWidget {
                background-color: #f5f5f5;
                color: #000000;
                font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
                font-size: 14px;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 600;
                min-height: 35px;
            }
            
            QPushButton:hover {
                background-color: #106ebe;
            }
            
            QPushButton:pressed {
                background-color: #005a9e;
            }
            
            /* Input Fields */
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: white;
                border: 1px solid #d1d1d1;
                border-radius: 6px;
                padding: 10px;
                color: #000000;
                selection-background-color: #0078d4;
            }
            
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
                border: 2px solid #0078d4;
            }
            
            /* List Widget */
            QListWidget {
                background-color: white;
                border: 1px solid #d1d1d1;
                border-radius: 6px;
            }
            
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            
            QListWidget::item:hover {
                background-color: #e8e8e8;
            }
        """

    @staticmethod
    def apply_theme(app, theme_name="dark"):
        """Apply theme to application"""
        if theme_name == "dark":
            app.setStyleSheet(ThemeManager.get_dark_theme())
        else:
            app.setStyleSheet(ThemeManager.get_light_theme())