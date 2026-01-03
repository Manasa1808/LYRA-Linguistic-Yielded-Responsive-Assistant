from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
import json
import os
import difflib
import re
import string

class WhatsAppHandler:
    def __init__(self, tts_engine=None, speech_recognizer=None, audio_handler=None):
        self.driver = None
        self.is_logged_in = False
        self.contacts = {}
        self.contacts_original = {}
        self.contacts_normalized = {}

        # For interactive message asking
        self.tts_engine = tts_engine
        self.speech_recognizer = speech_recognizer
        self.audio_handler = audio_handler

        self.load_contacts()

    def load_contacts(self):
        """Load contacts from data/contacts.json with normalization"""
        contacts_file = os.path.join('data', 'contacts.json')

        if os.path.exists(contacts_file):
            try:
                with open(contacts_file, 'r', encoding='utf-8') as f:
                    contacts_data = json.load(f)

                for name, info in contacts_data.items():
                    phone = info.get('phone', '')
                    if phone:
                        self.contacts[name] = phone
                        self.contacts_original[name] = phone

                        # Normalize: lowercase, strip spaces, remove punctuation
                        normalized_key = self._normalize_name(name)
                        self.contacts_normalized[normalized_key] = name

                print(f"✅ Loaded {len(self.contacts)} contacts from {contacts_file}")
            except Exception as e:
                print(f"⚠️ Error loading contacts: {e}")
                self.contacts = {}
                self.contacts_original = {}
                self.contacts_normalized = {}
        else:
            print(f"⚠️ Contacts file not found: {contacts_file}")
            self.contacts = {}
            self.contacts_original = {}
            self.contacts_normalized = {}

    def _normalize_name(self, name):
        """Normalize name: lowercase, trim spaces, remove punctuation"""
        # Lowercase
        name = name.lower()
        # Remove punctuation
        name = name.translate(str.maketrans('', '', string.punctuation))
        # Remove extra spaces and trim
        name = ' '.join(name.split())
        return name

    def find_contact(self, contact_name):
        """Find contact with fuzzy matching (80% confidence threshold)"""
        # Normalize input
        normalized_input = self._normalize_name(contact_name)

        # Try exact normalized match first
        if normalized_input in self.contacts_normalized:
            original_name = self.contacts_normalized[normalized_input]
            return original_name, self.contacts_original[original_name]

        # Try fuzzy matching with 80% threshold (0.8 cutoff)
        normalized_keys = list(self.contacts_normalized.keys())
        matches = difflib.get_close_matches(normalized_input, normalized_keys, n=1, cutoff=0.8)

        if matches:
            best_match_key = matches[0]
            original_name = self.contacts_normalized[best_match_key]
            return original_name, self.contacts_original[original_name]

        # No match found
        return None, None

    def initialize_driver(self):
        """Initialize Brave Browser WebDriver using real user profile"""
        options = webdriver.ChromeOptions()

        # Set Brave browser binary location
        brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
        options.binary_location = brave_path

        # Use REAL Brave user profile (NO QR scanning needed)
        user_data_dir = r"C:\Users\manas\AppData\Local\BraveSoftware\Brave-Browser\User Data"
        options.add_argument(f'--user-data-dir={user_data_dir}')
        options.add_argument('--profile-directory=Default')

        # Additional options for stability
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

            self.driver.get('https://web.whatsapp.com')
            print("🔄 Opening WhatsApp Web with your existing Brave session...")

            # Wait for WhatsApp to load (should already be logged in)
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="chat-list"]'))
                )
                self.is_logged_in = True
                print("✅ WhatsApp Web loaded successfully (already logged in)")
            except:
                print("⏱️ WhatsApp Web login timeout")

        except Exception as e:
            print(f"❌ Failed to initialize Brave browser: {e}")
            print("   Make sure Brave is installed and the profile path is correct")

    def ask_for_message(self, contact_name):
        """Ask user for the message to send"""
        if not self.tts_engine or not self.speech_recognizer or not self.audio_handler:
            # Fallback: return default message if no TTS/ASR available
            return "Hello from LYRA!"

        try:
            # Ask user what message to send
            question = f"What message should I send to {contact_name}?"
            print(f"🗣️ LYRA: {question}")
            self.tts_engine.speak(question)

            # Wait for TTS to finish
            time.sleep(1)

            # Listen for user's response
            print("👂 Listening for your message...")
            audio_data = self.audio_handler.record_audio(duration=5)

            if audio_data is not None:
                message_text = self.speech_recognizer.transcribe(audio_data)

                if message_text and message_text.strip():
                    print(f"📝 Message to send: {message_text}")
                    return message_text.strip()
                else:
                    print("⚠️ No message detected, using default")
                    return "Hello from LYRA!"
            else:
                print("⚠️ Could not record audio, using default message")
                return "Hello from LYRA!"

        except Exception as e:
            print(f"⚠️ Error asking for message: {e}")
            return "Hello from LYRA!"

    def send_message(self, contact_name, message=None):
        """Send a WhatsApp message with fuzzy contact matching and interactive message asking"""
        # Find contact with fuzzy matching
        original_name, phone_number = self.find_contact(contact_name)

        if not original_name:
            return False, f"Contact '{contact_name}' not found in contacts.json"

        # If no message provided, ask the user
        if not message or message == "Hello from LYRA!":
            message = self.ask_for_message(original_name)

        if not self.driver or not self.is_logged_in:
            self.initialize_driver()
            if not self.is_logged_in:
                return False, "Could not connect to WhatsApp Web"

        try:
            # Search for contact
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="chat-list-search"]'))
            )
            search_box.click()
            search_box.clear()
            search_box.send_keys(original_name)

            # Wait for search results to appear
            contact_xpath = f'//span[@title="{original_name}"]'
            contact = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, contact_xpath))
            )

            # Click on contact
            contact.click()
            time.sleep(1)

            # Type and send message
            message_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="conversation-compose-box-input"]'))
            )
            message_box.send_keys(message)
            message_box.send_keys(Keys.ENTER)

            # Confirm success
            success_msg = f"Message sent to {original_name}."
            print(f"✅ {success_msg}")

            # Speak confirmation if TTS available
            if self.tts_engine:
                self.tts_engine.speak(success_msg)

            return True, success_msg
        except Exception as e:
            error_msg = f"Failed to send message: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg

    def close(self):
        if self.driver:
            self.driver.quit()
