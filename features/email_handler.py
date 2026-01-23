import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_SETTINGS
import json
import os
import difflib

class EmailHandler:
    def __init__(self, smtp_server=None, smtp_port=None, username=None, password=None):
        self.smtp_server = smtp_server or EMAIL_SETTINGS.get('smtp_server')
        self.smtp_port = smtp_port or EMAIL_SETTINGS.get('smtp_port')
        self.username = username or EMAIL_SETTINGS.get('username')
        self.password = password or EMAIL_SETTINGS.get('password')
        
        # Load email contacts
        self.contacts = {}
        self.contacts_normalized = {}
        self.load_contacts()
        
        # Check configuration on init
        self.check_configuration()
    
    def check_configuration(self):
        """Check if email is configured"""
        if not self.smtp_server or not self.username or not self.password:
            print("\n" + "="*60)
            print("⚠️ EMAIL NOT CONFIGURED")
            print("="*60)
            print("To use email features, please configure EMAIL_SETTINGS in config.py:")
            print("")
            print("EMAIL_SETTINGS = {")
            print("    'smtp_server': 'smtp.gmail.com',")
            print("    'smtp_port': 587,")
            print("    'username': 'your_email@gmail.com',")
            print("    'password': 'your_app_password'  # NOT your regular password!")
            print("}")
            print("")
            print("For Gmail:")
            print("  1. Enable 2-Factor Authentication")
            print("  2. Go to: https://myaccount.google.com/apppasswords")
            print("  3. Generate an App Password")
            print("  4. Use that password in config.py")
            print("="*60 + "\n")
        else:
            print(f"✅ Email configured: {self.username}")
    
    def load_contacts(self):
        """Load email contacts from data/contacts.json"""
        contacts_file = os.path.join('data', 'contacts.json')
        
        if os.path.exists(contacts_file):
            try:
                with open(contacts_file, 'r', encoding='utf-8') as f:
                    contacts_data = json.load(f)
                    
                # Store contacts with normalization
                for name, info in contacts_data.items():
                    email = info.get('email', '')
                    if email:
                        # Store original name and email
                        self.contacts[name] = email
                        
                        # Create normalized key: lowercase, no spaces, no dots
                        normalized_key = name.lower().replace(' ', '').replace('.', '')
                        self.contacts_normalized[normalized_key] = name
                
                print(f"✅ Loaded {len(self.contacts)} email contacts")
                for name, email in self.contacts.items():
                    print(f"   - {name}: {email}")
            except Exception as e:
                print(f"⚠️ Error loading email contacts: {e}")
                self.contacts = {}
                self.contacts_normalized = {}
        else:
            print(f"⚠️ Contacts file not found: {contacts_file}")
            print(f"   Please create {contacts_file} with contact information")
            self.contacts = {}
            self.contacts_normalized = {}
    
    def find_contact(self, contact_name):
        """Find contact email with fuzzy matching"""
        print(f"🔍 Finding email contact for: '{contact_name}'")
        
        # Normalize input
        normalized_input = contact_name.lower().replace(' ', '').replace('.', '')
        
        # Try exact normalized match first
        if normalized_input in self.contacts_normalized:
            original_name = self.contacts_normalized[normalized_input]
            email = self.contacts[original_name]
            print(f"✅ Found: {original_name} -> {email}")
            return original_name, email
        
        # Try fuzzy matching
        normalized_keys = list(self.contacts_normalized.keys())
        matches = difflib.get_close_matches(normalized_input, normalized_keys, n=1, cutoff=0.6)
        
        if matches:
            best_match_key = matches[0]
            original_name = self.contacts_normalized[best_match_key]
            email = self.contacts[original_name]
            print(f"✅ Fuzzy match: {original_name} -> {email}")
            return original_name, email
        
        # Check if input is already an email address
        if '@' in contact_name:
            print(f"✅ Using email directly: {contact_name}")
            return contact_name, contact_name
        
        # No match found
        print(f"❌ No email contact found for: '{contact_name}'")
        print(f"   Available contacts: {list(self.contacts.keys())}")
        return None, None
    
    def send_email(self, to_email, subject, body, cc=None, bcc=None):
        """Send an email with contact name resolution"""
        
        print("\n" + "="*60)
        print("📧 SENDING EMAIL")
        print("="*60)
        print(f"📮 To: {to_email}")
        print(f"📝 Subject: {subject}")
        print(f"💬 Body: {body[:50]}..." if len(body) > 50 else f"💬 Body: {body}")
        print("="*60)
        
        # Check if SMTP is configured
        if not self.smtp_server or not self.username or not self.password:
            error_msg = "Email not configured. Please update EMAIL_SETTINGS in config.py"
            print(f"❌ {error_msg}")
            print("\n💡 Configuration needed:")
            print("   Edit config.py and set:")
            print("   EMAIL_SETTINGS = {")
            print("       'smtp_server': 'smtp.gmail.com',")
            print("       'smtp_port': 587,")
            print("       'username': 'your_email@gmail.com',")
            print("       'password': 'your_app_password'")
            print("   }")
            print("="*60 + "\n")
            return False, error_msg
        
        # Try to resolve contact name to email
        recipient_name = to_email
        if '@' not in to_email:
            found_name, found_email = self.find_contact(to_email)
            if found_email:
                to_email = found_email
                print(f"📧 Resolved '{recipient_name}' to {to_email}")
            else:
                error_msg = f"Contact '{to_email}' not found and not a valid email address"
                print(f"❌ {error_msg}")
                print("="*60 + "\n")
                return False, error_msg
        
        try:
            print("📤 Creating email message...")
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = cc
            if bcc:
                msg['Bcc'] = bcc
            
            msg.attach(MIMEText(body, 'plain'))
            
            print(f"🔗 Connecting to {self.smtp_server}:{self.smtp_port}...")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            
            print("🔐 Authenticating...")
            server.login(self.username, self.password)
            
            recipients = [to_email]
            if cc:
                recipients.extend(cc.split(','))
            if bcc:
                recipients.extend(bcc.split(','))
            
            print("📨 Sending email...")
            server.send_message(msg)
            server.quit()
            
            success_msg = f"Email sent to {to_email}"
            print(f"✅ {success_msg}")
            print("="*60 + "\n")
            return True, success_msg
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = "Email authentication failed. Please check your email credentials in config.py"
            print(f"❌ {error_msg}")
            print("\n💡 For Gmail:")
            print("   1. Enable 2-Factor Authentication")
            print("   2. Generate App Password at: https://myaccount.google.com/apppasswords")
            print("   3. Use App Password (NOT regular password) in config.py")
            print(f"\n   Error details: {str(e)}")
            print("="*60 + "\n")
            return False, error_msg
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            print(f"❌ {error_msg}")
            print("="*60 + "\n")
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            print("="*60 + "\n")
            return False, error_msg
    
    def validate_config(self):
        """Check if email is properly configured"""
        if not self.smtp_server:
            return False, "SMTP server not configured"
        if not self.username:
            return False, "Email username not configured"
        if not self.password:
            return False, "Email password not configured"
        return True, "Email configured"

# ✅ Configuration Instructions:
# 
# Add to config.py:
# 
# EMAIL_SETTINGS = {
#     'smtp_server': 'smtp.gmail.com',
#     'smtp_port': 587,
#     'username': 'your_email@gmail.com',
#     'password': 'your_app_password'  # NOT your regular Gmail password!
# }
#
# For Gmail:
# 1. Enable 2-factor authentication in your Google Account
# 2. Go to: https://myaccount.google.com/apppasswords
# 3. Select "Mail" and your device
# 4. Generate password
# 5. Use that 16-character password in config.py (no spaces)
#
# For other email providers, check their SMTP settings:
# - Outlook: smtp.office365.com, port 587
# - Yahoo: smtp.mail.yahoo.com, port 587
# - Custom: Ask your email provider