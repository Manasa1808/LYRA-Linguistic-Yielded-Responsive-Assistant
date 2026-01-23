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
import platform
import re

class WhatsAppHandler:
    def __init__(self):
        self.driver = None
        self.is_logged_in = False
        self.contacts = {}
        self.contacts_original = {}  # Original names with proper casing
        self.contacts_normalized = {}  # Normalized names for matching
        self.platform = platform.system()
        self.initialization_attempted = False
        self.login_wait_time = 90  # Seconds to wait for QR scan
        
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
                        
                        # Create normalized key: lowercase, no spaces, no dots, no dashes
                        normalized_key = name.lower().replace(' ', '').replace('.', '').replace('-', '').replace('_', '')
                        self.contacts_normalized[normalized_key] = name
                
                print(f"✅ Loaded {len(self.contacts)} WhatsApp contacts:")
                for name in self.contacts.keys():
                    print(f"   - {name}")
            except Exception as e:
                print(f"⚠️ Error loading contacts: {e}")
                self.contacts = {}
                self.contacts_original = {}
                self.contacts_normalized = {}
        else:
            print(f"❌ Contacts file not found: {contacts_file}")
            print(f"   Please create {contacts_file} with contact information")
            print(f"   Example format:")
            print(f'   {{"Mohitha": {{"phone": "+919876543210", "email": "mohitha@example.com"}}}}')
            self.contacts = {}
            self.contacts_original = {}
            self.contacts_normalized = {}
    
    def find_contact(self, contact_name):
        """Find contact with enhanced fuzzy matching for voice input"""
        print(f"🔍 Finding contact for: '{contact_name}'")
        
        # Remove common voice recognition artifacts
        contact_name = contact_name.strip().lower()
        
        # Remove voice command words in multiple languages
        remove_words = [
            'send', 'message', 'to', 'whatsapp', 'on', 'via',
            'भेजो', 'भेज', 'मैसेज', 'को', 'पर',
            'ಕಳುಹಿಸು', 'ಸಂದೇಶ', 'ಗೆ'
        ]
        for word in remove_words:
            contact_name = contact_name.replace(word, '').strip()
        
        # Normalize input
        normalized_input = contact_name.replace(' ', '').replace('.', '').replace('-', '').replace('_', '')
        
        print(f"🔍 Normalized input: '{normalized_input}'")
        
        # Try exact normalized match first
        if normalized_input in self.contacts_normalized:
            original_name = self.contacts_normalized[normalized_input]
            print(f"✅ Exact match found: '{original_name}'")
            return original_name, self.contacts_original[original_name]
        
        # Try fuzzy matching with lower threshold for voice input
        normalized_keys = list(self.contacts_normalized.keys())
        matches = difflib.get_close_matches(normalized_input, normalized_keys, n=1, cutoff=0.5)
        
        if matches:
            best_match_key = matches[0]
            original_name = self.contacts_normalized[best_match_key]
            print(f"✅ Fuzzy match found: '{original_name}' (from key: '{best_match_key}')")
            return original_name, self.contacts_original[original_name]
        
        # Try partial matching (if input is contained in any contact name)
        for norm_key, orig_name in self.contacts_normalized.items():
            if normalized_input in norm_key or norm_key in normalized_input:
                print(f"✅ Partial match found: '{orig_name}'")
                return orig_name, self.contacts_original[orig_name]
        
        # No match found
        print(f"❌ No match found for: '{contact_name}'")
        print(f"   Available contacts: {list(self.contacts.keys())}")
        return None, None
    
    def get_browser_path(self):
        """Get browser path based on platform and available browsers"""
        if self.platform == "Windows":
            # Try multiple browsers in order of preference
            browsers = [
                (r"C:\Program Files\Google\Chrome\Application\chrome.exe", "Chrome"),
                (r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe", "Chrome"),
                (r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe", "Brave"),
                (r"C:\Program Files\Microsoft\Edge\Application\msedge.exe", "Edge"),
            ]
            
            for browser_path, browser_name in browsers:
                if os.path.exists(browser_path):
                    print(f"✅ Found {browser_name} at {browser_path}")
                    return browser_path, browser_name
            
            # Default to Chrome if none found
            print("⚠️ No browser found at standard locations, will try default Chrome")
            return None, "Chrome"
        
        elif self.platform == "Darwin":  # macOS
            return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "Chrome"
        
        else:  # Linux
            return None, "Chrome"
    
    def initialize_driver(self):
        """Initialize WebDriver - FIXED to prevent auto-close"""
        
        if self.driver:
            print("⚠️ Browser already initialized, checking status...")
            try:
                # Check if browser is still alive
                self.driver.current_url
                print("✅ Browser still active")
                return
            except:
                print("⚠️ Browser was closed, reinitializing...")
                self.driver = None
                self.is_logged_in = False
                self.initialization_attempted = False
        
        if self.initialization_attempted and not self.driver:
            print("⚠️ Previous initialization failed, trying again...")
            self.initialization_attempted = False
        
        self.initialization_attempted = True
        
        print("\n" + "="*60)
        print("🌐 INITIALIZING WHATSAPP WEB BROWSER")
        print("="*60)
        
        try:
            options = webdriver.ChromeOptions()
            
            # Get browser path
            browser_path, browser_name = self.get_browser_path()
            
            if browser_path and os.path.exists(browser_path):
                options.binary_location = browser_path
                print(f"📍 Using browser: {browser_path}")
            else:
                print(f"📍 Using default {browser_name}")
            
            # User data directory for persistent session
            session_dir = os.path.abspath(os.path.join(os.getcwd(), 'whatsapp_session'))
            os.makedirs(session_dir, exist_ok=True)
            
            print(f"💾 Session directory: {session_dir}")
            
            # ✅ CRITICAL FIX: Keep browser open with detach option
            options.add_experimental_option("detach", True)  # Prevents browser from closing
            
            # Add options for stability
            options.add_argument(f'--user-data-dir={session_dir}')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1200,900')
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # ✅ Disable auto-closing features
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-infobars')
            
            print("🔧 Configuring WebDriver...")
            
            # Use webdriver-manager to get ChromeDriver
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                print("✅ ChromeDriver installed")
            except Exception as e:
                print(f"⚠️ webdriver_manager failed: {e}")
                print("   Trying system ChromeDriver...")
                service = None
            
            # Create driver
            print(f"🚀 Launching {browser_name}...")
            
            if service:
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                self.driver = webdriver.Chrome(options=options)
            
            # ✅ IMPORTANT: Set implicit wait to prevent premature exits
            self.driver.implicitly_wait(10)
            
            print(f"✅ Browser launched successfully!")
            
            # Navigate to WhatsApp Web
            print("📱 Opening WhatsApp Web...")
            self.driver.get('https://web.whatsapp.com')
            print("✅ Navigated to WhatsApp Web")
            
            # Wait a bit for page to load
            time.sleep(3)
            
            print("\n" + "="*60)
            print("📱 WHATSAPP WEB - CHECKING LOGIN STATUS")
            print("="*60)
            
            # Check if already logged in (from previous session)
            try:
                # Look for chat list (means already logged in)
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="chat-list"]'))
                )
                self.is_logged_in = True
                print("✅ Already logged in from previous session!")
                print("="*60 + "\n")
                return
            except:
                print("📱 Not logged in yet, QR code scan required")
            
            print("="*60)
            print("📱 WHATSAPP WEB - QR CODE SCAN REQUIRED")
            print("="*60)
            print("👉 Please scan the QR code with your phone")
            print("   1. Open WhatsApp on your phone")
            print("   2. Go to Settings > Linked Devices")
            print("   3. Tap 'Link a Device'")
            print("   4. Scan the QR code on the screen")
            print(f"   ⏱️  You have {self.login_wait_time} seconds")
            print("="*60 + "\n")
            
            # Wait for login with timeout
            try:
                print(f"⏳ Waiting for QR code scan (max {self.login_wait_time} seconds)...")
                WebDriverWait(self.driver, self.login_wait_time).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="chat-list"]'))
                )
                self.is_logged_in = True
                print("\n✅ WhatsApp Web logged in successfully!")
                print("✅ Browser will stay open for future messages")
                print("="*60 + "\n")
                time.sleep(2)  # Wait for full load
            except:
                print(f"\n⏱️ Login timeout - QR code was not scanned within {self.login_wait_time} seconds")
                print("   Browser will stay open - you can still scan the QR code")
                print("   Or try sending the message again")
                print("="*60 + "\n")
                self.is_logged_in = False
                # ✅ DON'T CLOSE THE BROWSER - Let user scan QR code later
                
        except Exception as e:
            print(f"\n❌ Failed to initialize browser: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            print(f"\n💡 Troubleshooting:")
            print(f"   1. Make sure Chrome, Brave, or Edge is installed")
            print(f"   2. Install webdriver-manager: pip install webdriver-manager")
            print(f"   3. Check if antivirus is blocking browser automation")
            print("="*60 + "\n")
            # ✅ Don't set driver to None if it was created
            if not self.driver:
                self.is_logged_in = False
    
    def send_message(self, contact_name, message):
        """Send a WhatsApp message - FIXED to work after QR scan"""
        print("\n" + "="*60)
        print(f"📤 SENDING WHATSAPP MESSAGE")
        print("="*60)
        print(f"📱 Contact: {contact_name}")
        print(f"💬 Message: {message}")
        print("="*60)
        
        # Find contact with fuzzy matching
        original_name, phone_number = self.find_contact(contact_name)
        
        if not original_name:
            error_msg = f"Contact '{contact_name}' not found in contacts.json"
            print(f"❌ {error_msg}")
            print(f"   Please add contact to data/contacts.json")
            print("="*60 + "\n")
            return False, error_msg

        print(f"✅ Contact found: {original_name} ({phone_number})")
        
        # Initialize driver if not already done
        if not self.driver:
            print("🌐 Browser not initialized, launching now...")
            self.initialize_driver()
            
            # Wait for login if needed
            if not self.is_logged_in:
                print("⏳ Waiting for WhatsApp login...")
                try:
                    WebDriverWait(self.driver, self.login_wait_time).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="chat-list"]'))
                    )
                    self.is_logged_in = True
                    print("✅ Login successful!")
                except:
                    error_msg = "Please scan QR code to login to WhatsApp Web"
                    print(f"⚠️ {error_msg}")
                    print("="*60 + "\n")
                    return False, error_msg

        # Check if logged in
        if not self.is_logged_in:
            # Check again in case user logged in manually
            try:
                self.driver.find_element(By.CSS_SELECTOR, '[data-testid="chat-list"]')
                self.is_logged_in = True
                print("✅ Login detected!")
            except:
                error_msg = "Please scan QR code to login to WhatsApp Web"
                print(f"⚠️ {error_msg}")
                print("="*60 + "\n")
                return False, error_msg

        try:
            print("🔍 Searching for contact...")
            
            # Search for contact
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="chat-list-search"]'))
            )
            search_box.click()
            time.sleep(0.5)
            search_box.clear()
            search_box.send_keys(original_name)
            time.sleep(1.5)  # Wait for search results
            
            print(f"✅ Searched for: {original_name}")
            
            # Try multiple strategies to find the contact
            contact_found = False
            
            # Strategy 1: Try by title attribute
            try:
                contact_xpath = f'//span[@title="{original_name}"]'
                contact = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, contact_xpath))
                )
                contact.click()
                contact_found = True
                print("✅ Found contact by title")
            except:
                print("⚠️ Strategy 1 failed (title search)")
            
            # Strategy 2: Try by phone number
            if not contact_found and phone_number:
                try:
                    search_box.clear()
                    search_box.send_keys(phone_number)
                    time.sleep(1.5)
                    
                    # Click first result
                    first_result = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="cell-frame-container"]'))
                    )
                    first_result.click()
                    contact_found = True
                    print("✅ Found contact by phone number")
                except:
                    print("⚠️ Strategy 2 failed (phone search)")
            
            # Strategy 3: Click first search result
            if not contact_found:
                try:
                    first_result = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="cell-frame-container"]'))
                    )
                    first_result.click()
                    contact_found = True
                    print("✅ Clicked first search result")
                except:
                    print("⚠️ Strategy 3 failed (first result)")
            
            if not contact_found:
                error_msg = f"Could not find chat with {original_name}"
                print(f"❌ {error_msg}")
                print("="*60 + "\n")
                return False, error_msg
            
            time.sleep(1)
            
            # Type and send message
            print("📝 Typing message...")
            message_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="conversation-compose-box-input"]'))
            )
            message_box.click()
            message_box.send_keys(message)
            time.sleep(0.5)
            message_box.send_keys(Keys.ENTER)
            
            print(f"✅ Message sent to {original_name} ({phone_number})")
            print("✅ Browser will remain open for future messages")
            print("="*60 + "\n")
            return True, f"Message sent to {original_name}"
            
        except Exception as e:
            error_msg = f"Failed to send message: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            print("="*60 + "\n")
            return False, error_msg
    
    def close(self):
        """Close the browser - only call this explicitly"""
        if self.driver:
            try:
                self.driver.quit()
                print("🔒 WhatsApp Web session closed")
            except:
                pass
            finally:
                self.driver = None
                self.is_logged_in = False
                self.initialization_attempted = False