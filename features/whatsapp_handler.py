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

class WhatsAppHandler:
    def __init__(self):
        self.driver = None
        self.is_logged_in = False
        self.contacts = {}
        self.contacts_original = {}  # Original names with proper casing
        self.contacts_normalized = {}  # Normalized names for matching
        
        # Load contacts from data/contacts.json
        self.load_contacts()
    
    def load_contacts(self):
        """Load contacts from data/contacts.json with normalization"""
        contacts_file = os.path.join('data', 'contacts.json')
        
        if os.path.exists(contacts_file):
            try:
                with open(contacts_file, 'r', encoding='utf-8') as f:
                    contacts_data = json.load(f)
                    
                # Store contacts with normalization
                for name, info in contacts_data.items():
                    phone = info.get('phone', '')
                    if phone:
                        # Store original name and phone
                        self.contacts[name] = phone
                        self.contacts_original[name] = phone
                        
                        # Create normalized key: lowercase, no spaces, no dots
                        normalized_key = name.lower().replace(' ', '').replace('.', '')
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
    
    def find_contact(self, contact_name):
        """Find contact with fuzzy matching"""
        # Normalize input
        normalized_input = contact_name.lower().replace(' ', '').replace('.', '')
        
        # Try exact normalized match first
        if normalized_input in self.contacts_normalized:
            original_name = self.contacts_normalized[normalized_input]
            return original_name, self.contacts_original[original_name]
        
        # Try fuzzy matching
        normalized_keys = list(self.contacts_normalized.keys())
        matches = difflib.get_close_matches(normalized_input, normalized_keys, n=1, cutoff=0.6)
        
        if matches:
            best_match_key = matches[0]
            original_name = self.contacts_normalized[best_match_key]
            return original_name, self.contacts_original[original_name]
        
        # No match found
        return None, None
    
    def initialize_driver(self):
        """Initialize Brave Browser WebDriver"""
        options = webdriver.ChromeOptions()
        
        # Set Brave browser binary location
        brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
        options.binary_location = brave_path
        
        # User data directory for persistent session
        options.add_argument('--user-data-dir=./whatsapp_session')
        
        # Additional options for stability
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        try:
            # Use Chrome driver (compatible with Brave)
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            self.driver.get('https://web.whatsapp.com')
            print("🔐 Scan QR code to login to WhatsApp Web in Brave browser")
            
            # Wait for login
            try:
                WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="chat-list"]'))
                )
                self.is_logged_in = True
                print("✅ WhatsApp Web logged in successfully")
            except:
                print("⏱️ Login timeout")
                
        except Exception as e:
            print(f"❌ Failed to initialize Brave browser: {e}")
            print("   Make sure Brave is installed at: C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe")
    
    def send_message(self, contact_name, message):
        """Send a WhatsApp message with fuzzy contact matching"""
        # Find contact with fuzzy matching
        original_name, phone_number = self.find_contact(contact_name)
        
        if not original_name:
            return False, f"Contact '{contact_name}' not found in contacts.json"

        if not self.driver or not self.is_logged_in:
            self.initialize_driver()
            if not self.is_logged_in:
                return False, "Please scan QR code in Brave to login WhatsApp"

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
            
            return True, f"Message sent to {original_name} ({phone_number})"
        except Exception as e:
            return False, f"Failed to send message: {str(e)}"
    
    def close(self):
        if self.driver:
            self.driver.quit()
