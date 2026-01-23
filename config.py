import platform
import os

# Platform detection
PLATFORM = platform.system()

# Whisper settings - Support multiple languages
WHISPER_MODEL = 'base'  # Options: tiny, base, small, medium, large
WHISPER_LANGUAGE = None  # Set to None to auto-detect language, or specify 'en', 'hi', 'kn'

# TTS settings
TTS_RATE = 150  # Speech rate (words per minute)
TTS_VOLUME = 0.9  # Volume (0.0 to 1.0)

# Windows Application paths
APP_PATHS = {
    'chrome': 'chrome.exe',
    'firefox': 'firefox.exe',
    'edge': 'msedge.exe',
    'notepad': 'notepad.exe',
    'calculator': 'calc.exe',
    'cmd': 'cmd.exe',
    'terminal': 'cmd.exe',
    'powershell': 'powershell.exe',
    'explorer': 'explorer.exe',
    'word': 'WINWORD.EXE',
    'excel': 'EXCEL.EXE',
    'outlook': 'OUTLOOK.EXE',
    'mail': 'OUTLOOK.EXE',
    'paint': 'mspaint.exe',
    'spotify': 'Spotify.exe',
    'vscode': 'Code.exe',
    'teams': 'Teams.exe',
    'music': 'wmplayer.exe',
}

DEFAULT_LANGUAGE = "en"  # en, hi, kn
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "हिन्दी (Hindi)",
    "kn": "ಕನ್ನಡ (Kannada)"
}

# Database settings
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'voiceos.db')

# Ensure data directory exists
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# API Keys (set these with actual keys)
WEATHER_API_KEY = None  # Get from https://openweathermap.org/api

# Audio settings
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024
RECORDING_DURATION = 5  # seconds

# Voice isolation settings
ENABLE_VOICE_ISOLATION = True
NOISE_REDUCTION_STRENGTH = 0.5

EMAIL_SETTINGS = {
    "smtp_server": "smtp.gmail.com",  # For Gmail
    "smtp_port": 587,
    "username": "your.email@gmail.com",
    "password": "your_app_password"
}

WHATSAPP_SETTINGS = {
    'Kavya': '+919738331139',
    'Deeksha': '+917204361194'
}