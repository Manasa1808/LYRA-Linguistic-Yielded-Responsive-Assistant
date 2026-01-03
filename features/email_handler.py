import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_SETTINGS

class EmailHandler:
    def __init__(self, smtp_server=None, smtp_port=None, username=None, password=None):
        self.smtp_server = smtp_server or EMAIL_SETTINGS['smtp_server']
        self.smtp_port = smtp_port or EMAIL_SETTINGS['smtp_port']
        self.username = username or EMAIL_SETTINGS['username']
        self.password = password or EMAIL_SETTINGS['password']
    
    def send_email(self, to_email, subject, body, cc=None, bcc=None):
        """Send an email"""
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
            
            return True, f"Email sent to {to_email}"
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"

# ✅ Enter your email credentials here or in config.py
# EMAIL_SETTINGS = {
#     'smtp_server': 'smtp.gmail.com',
#     'smtp_port': 587,
#     'username': 'your_email@gmail.com',
#     'password': 'your_email_app_password'
# }
