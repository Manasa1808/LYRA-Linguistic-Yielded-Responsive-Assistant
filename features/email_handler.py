import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_SETTINGS
import json
import os
import re
from thefuzz import fuzz

class EmailHandler:
    def __init__(self, smtp_server=None, smtp_port=None, username=None, password=None):
        self.smtp_server = smtp_server or EMAIL_SETTINGS['smtp_server']
        self.smtp_port = smtp_port or EMAIL_SETTINGS['smtp_port']
        self.username = username or EMAIL_SETTINGS['username']
        self.password = password or EMAIL_SETTINGS['password']

        # Conversation state for multi-turn interactions
        self.state = None  # None, "waiting_for_subject", "waiting_for_message"
        self.pending_contact_name = None
        self.pending_contact_email = None
        self.pending_subject = None

        # Load contacts from data/contacts.json
        self.contacts = {}
        self.load_contacts()

    def load_contacts(self):
        """Load contacts from data/contacts.json"""
        contacts_file = os.path.join('data', 'contacts.json')

        if os.path.exists(contacts_file):
            try:
                with open(contacts_file, 'r', encoding='utf-8') as f:
                    contacts_data = json.load(f)

                # Store contacts with original names
                for name, info in contacts_data.items():
                    email = info.get('email', '')
                    if email:
                        self.contacts[name] = email

                print(f"✅ Loaded {len(self.contacts)} email contacts from {contacts_file}")
            except Exception as e:
                print(f"⚠️ Error loading contacts: {e}")
                self.contacts = {}
        else:
            print(f"⚠️ Contacts file not found: {contacts_file}")
            self.contacts = {}

    def normalize_text(self, text):
        """Normalize text: lowercase, trim spaces, remove punctuation"""
        text = text.lower().strip()
        # Remove punctuation except spaces
        text = re.sub(r'[^\w\s]', '', text)
        # Normalize multiple spaces to single space
        text = re.sub(r'\s+', ' ', text)
        return text

    def find_contact(self, contact_name):
        """Find contact with fuzzy matching (80% threshold)"""
        normalized_input = self.normalize_text(contact_name)

        best_match = None
        best_score = 0

        for original_name, email in self.contacts.items():
            normalized_contact = self.normalize_text(original_name)

            # Calculate fuzzy match score
            score = fuzz.ratio(normalized_input, normalized_contact)

            if score > best_score:
                best_score = score
                best_match = (original_name, email)

        # Accept match if confidence > 80%
        if best_score > 80:
            return best_match[0], best_match[1]

        # No match found
        return None, None

    def handle_input(self, user_input):
        """
        Handle user input in the context of current conversation state.
        This enables multi-turn interactions.

        Returns: (success, response_message)
        """
        # If we're waiting for subject
        if self.state == "waiting_for_subject" and self.pending_contact_name:
            self.pending_subject = user_input.strip()
            self.state = "waiting_for_message"
            response = "What message should I send?"
            print(f"🗣️ LYRA: {response}")
            return True, response

        # If we're waiting for message body
        if self.state == "waiting_for_message" and self.pending_contact_name and self.pending_subject:
            return self._send_email_to_contact(
                self.pending_contact_email,
                self.pending_subject,
                user_input.strip()
            )

        # Otherwise, this is a new request to send email
        return self.send_email(user_input)

    def send_email(self, contact_name, subject=None, body=None, cc=None, bcc=None):
        """
        Start email send flow. If subject or body not provided, ask for them.

        Args:
            contact_name: Name of contact (or full command like "send email to Harshitha")
            subject: Optional email subject
            body: Optional email body
            cc: Optional CC recipients
            bcc: Optional BCC recipients

        Returns: (success, response_message)
        """
        # Parse contact name from command if needed
        contact_name = self._extract_contact_name(contact_name)

        # Find contact with fuzzy matching
        original_name, email_address = self.find_contact(contact_name)

        if not original_name:
            return False, f"Contact '{contact_name}' not found in contacts.json"

        # If both subject and body provided, send directly
        if subject and subject.strip() and body and body.strip():
            return self._send_email_to_contact(email_address, subject, body, cc, bcc)

        # Missing subject or body - enter waiting state
        self.state = "waiting_for_subject"
        self.pending_contact_name = original_name
        self.pending_contact_email = email_address

        response = "What should be the subject?"
        print(f"🗣️ LYRA: {response}")

        return True, response

    def _extract_contact_name(self, text):
        """Extract contact name from command text"""
        # Remove common prefixes
        text = re.sub(r'^(send\s+)?(email\s+)?(to\s+)?', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^(compose\s+)?(email\s+)?(to\s+)?', '', text, flags=re.IGNORECASE)
        return text.strip()

    def _send_email_to_contact(self, to_email, subject, body, cc=None, bcc=None):
        """
        Actually send the email.

        Args:
            to_email: Email address
            subject: Email subject
            body: Email body
            cc: Optional CC recipients
            bcc: Optional BCC recipients

        Returns: (success, response_message)
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to_email
            msg['Subject'] = subject

            if cc:
                msg['Cc'] = cc
            if bcc:
                msg['Bcc'] = bcc

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)

            recipients = [to_email]
            if cc:
                recipients.extend(cc.split(','))
            if bcc:
                recipients.extend(bcc.split(','))

            server.send_message(msg)
            server.quit()

            # Reset state after successful send
            self._reset_state()

            success_msg = f"Email sent to {self.pending_contact_name or to_email}."
            print(f"✅ {success_msg}")

            return True, success_msg

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            print(f"❌ {error_msg}")
            self._reset_state()
            return False, error_msg

    def _reset_state(self):
        """Reset conversation state"""
        self.state = None
        self.pending_contact_name = None
        self.pending_contact_email = None
        self.pending_subject = None
