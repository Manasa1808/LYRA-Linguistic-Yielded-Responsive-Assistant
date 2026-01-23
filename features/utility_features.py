from datetime import datetime
import random
import requests
import json
import platform
import subprocess
import webbrowser
import os

class UtilityFeatures:
    def __init__(self):
        self.jokes_cache = []
        self.weather_api_key = None
        self.platform = platform.system()
        
        # Check if pyautogui is available for keyboard controls
        self.keyboard_available = False
        try:
            import pyautogui
            self.keyboard_available = True
            print("✅ Keyboard control (pyautogui) available")
        except ImportError:
            print("⚠️ pyautogui not installed. Install with: pip install pyautogui")
        
        # Extended joke collection for all languages
        self.jokes_database = {
            'en': [
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "Why don't scientists trust atoms? Because they make up everything!",
                "What's the object-oriented way to become wealthy? Inheritance!",
                "Why do Java developers wear glasses? Because they don't C#!",
                "Why did the scarecrow win an award? He was outstanding in his field!",
                "Why don't eggs tell jokes? They'd crack each other up!",
                "What do you call a bear with no teeth? A gummy bear!",
                "Why did the bicycle fall over? Because it was two-tired!",
                "What do you call a fake noodle? An impasta!",
                "Why couldn't the bicycle stand up by itself? It was two tired!",
                "What did the ocean say to the beach? Nothing, it just waved!",
                "Why don't skeletons fight each other? They don't have the guts!",
                "What do you call a dinosaur that crashes his car? Tyrannosaurus Wrecks!",
                "Why did the math book look so sad? Because it had too many problems!",
                "I'm reading a book about anti-gravity. It's impossible to put down!",
                "Did you hear about the claustrophobic astronaut? He just needed a little space!",
                "What do you call cheese that isn't yours? Nacho cheese!",
                "Why can't you hear a pterodactyl go to the bathroom? Because the 'P' is silent!",
            ],
            'hi': [
                "प्रोग्रामर डार्क मोड क्यों पसंद करते हैं? क्योंकि लाइट बग्स को आकर्षित करती है!",
                "कंप्यूटर को ठंडक क्यों नहीं लगती? क्योंकि उसके पास Windows हैं!",
                "टीचर: बताओ, अगर तुम्हारे पास 10 आम हैं और तुम 5 खा लेते हो, तो क्या बचेगा? छात्र: पेट दर्द!",
                "पत्नी: आप मुझसे इतना प्यार क्यों करते हैं? पति: क्योंकि तुम्हारे अलावा कोई मुझे बर्दाश्त ही नहीं करता!",
                "डॉक्टर: आपको हंसना चाहिए, यह सेहत के लिए अच्छा है। मरीज: लेकिन डॉक्टर साहब, आपकी फीस देखकर रोना आता है!",
                "बेटा: पापा, मैं बड़ा होकर पायलट बनूंगा! पापा: बेटा, दोनों एक साथ नहीं हो सकते!",
                "पत्नी: ये कपड़े मुझ पर कैसे लग रहे हैं? पति: बहुत महंगे!",
                "बॉस: तुम हमेशा लेट क्यों आते हो? कर्मचारी: सर, आप जल्दी आने का कोई इनाम तो देते नहीं!",
            ],
            'kn': [
                "ಪ್ರೋಗ್ರಾಮರ್‌ಗಳು ಡಾರ್ಕ್ ಮೋಡ್ ಏಕೆ ಇಷ್ಟಪಡುತ್ತಾರೆ? ಬೆಳಕು ಬಗ್‌ಗಳನ್ನು ಆಕರ್ಷಿಸುತ್ತದೆ!",
                "ಶಿಕ್ಷಕರು: ನಿಮ್ಮ ಬಳಿ 10 ಮಾವಿನ ಹಣ್ಣುಗಳಿದ್ದರೆ ಮತ್ತು ನೀವು 5 ತಿಂದರೆ, ಏನು ಉಳಿಯುತ್ತದೆ? ವಿದ್ಯಾರ್ಥಿ: ಹೊಟ್ಟೆ ನೋವು!",
                "ಪತಿ: ನಾನು ನಿನ್ನನ್ನು ತುಂಬಾ ಪ್ರೀತಿಸುತ್ತೇನೆ. ಪತ್ನಿ: ಯಾಕೆ? ಪತಿ: ನಿನ್ನ ಹೊರತು ಬೇರೆ ಯಾರೂ ನನ್ನನ್ನು ಸಹಿಸುವುದಿಲ್ಲ!",
                "ಡಾಕ್ಟರ್: ನೀವು ನಗಬೇಕು, ಅದು ಆರೋಗ್ಯಕ್ಕೆ ಒಳ್ಳೆಯದು. ರೋಗಿ: ಆದರೆ ಡಾಕ್ಟರ್, ನಿಮ್ಮ ಫೀಸ್ ನೋಡಿದರೆ ಅಳುವುದು ಬರುತ್ತದೆ!",
                "ಮಗ: ಅಪ್ಪಾ, ನನಗೆ ಹೊಸ ಸೈಕಲ್ ಬೇಕು. ಅಪ್ಪ: ಮೊದಲು ಓದಿನಲ್ಲಿ ಫರ್ಸ್ಟ್ ಬಾ. ಮಗ: ಅಪ್ಪಾ, ಸೈಕಲ್ ಸಿಗುತ್ತದೆ, ಆದರೆ ಫರ್ಸ್ಟ್ ಹೇಗೆ ಬರಲಿ!",
            ]
        }
    
    # ============================================================================
    # SYSTEM CONTROL COMMANDS
    # ============================================================================
    
    def shutdown_system(self, language='en'):
        """Shutdown the computer"""
        print(f"\n{'='*60}")
        print(f"🔴 SHUTTING DOWN SYSTEM")
        print(f"{'='*60}")
        
        if self.platform == "Windows":
            try:
                subprocess.run(["shutdown", "/s", "/t", "5"], check=True)
                success_messages = {
                    'en': "System will shutdown in 5 seconds",
                    'hi': "सिस्टम 5 सेकंड में बंद हो जाएगा",
                    'kn': "ಸಿಸ್ಟಮ್ 5 ಸೆಕೆಂಡ್‌ಗಳಲ್ಲಿ ಮುಚ್ಚುತ್ತದೆ"
                }
                print(f"✅ {success_messages.get(language, success_messages['en'])}")
                print(f"{'='*60}\n")
                return True, success_messages.get(language, success_messages['en'])
            except Exception as e:
                error_messages = {
                    'en': f"Failed to shutdown: {str(e)}",
                    'hi': f"शटडाउन विफल: {str(e)}",
                    'kn': f"ಷಟ್‌ಡೌನ್ ವಿಫಲವಾಯಿತು: {str(e)}"
                }
                print(f"❌ {error_messages.get(language, error_messages['en'])}")
                print(f"{'='*60}\n")
                return False, error_messages.get(language, error_messages['en'])
        else:
            error_messages = {
                'en': "Shutdown only supported on Windows",
                'hi': "शटडाउन केवल Windows पर समर्थित है",
                'kn': "ಷಟ್‌ಡೌನ್ Windows ನಲ್ಲಿ ಮಾತ್ರ ಬೆಂಬಲಿತವಾಗಿದೆ"
            }
            print(f"❌ {error_messages.get(language, error_messages['en'])}")
            print(f"{'='*60}\n")
            return False, error_messages.get(language, error_messages['en'])
    
    def restart_system(self, language='en'):
        """Restart the computer"""
        print(f"\n{'='*60}")
        print(f"🔄 RESTARTING SYSTEM")
        print(f"{'='*60}")
        
        if self.platform == "Windows":
            try:
                subprocess.run(["shutdown", "/r", "/t", "5"], check=True)
                success_messages = {
                    'en': "System will restart in 5 seconds",
                    'hi': "सिस्टम 5 सेकंड में रीस्टार्ट होगा",
                    'kn': "ಸಿಸ್ಟಮ್ 5 ಸೆಕೆಂಡ್‌ಗಳಲ್ಲಿ ಮರುಪ್ರಾರಂಭವಾಗುತ್ತದೆ"
                }
                print(f"✅ {success_messages.get(language, success_messages['en'])}")
                print(f"{'='*60}\n")
                return True, success_messages.get(language, success_messages['en'])
            except Exception as e:
                error_messages = {
                    'en': f"Failed to restart: {str(e)}",
                    'hi': f"रीस्टार्ट विफल: {str(e)}",
                    'kn': f"ಮರುಪ್ರಾರಂಭ ವಿಫಲವಾಯಿತು: {str(e)}"
                }
                print(f"❌ {error_messages.get(language, error_messages['en'])}")
                print(f"{'='*60}\n")
                return False, error_messages.get(language, error_messages['en'])
        else:
            error_messages = {
                'en': "Restart only supported on Windows",
                'hi': "रीस्टार्ट केवल Windows पर समर्थित है",
                'kn': "ಮರುಪ್ರಾರಂಭ Windows ನಲ್ಲಿ ಮಾತ್ರ ಬೆಂಬಲಿತವಾಗಿದೆ"
            }
            print(f"❌ {error_messages.get(language, error_messages['en'])}")
            print(f"{'='*60}\n")
            return False, error_messages.get(language, error_messages['en'])
    
    def sleep_system(self, language='en'):
        """Put system to sleep"""
        print(f"\n{'='*60}")
        print(f"😴 PUTTING SYSTEM TO SLEEP")
        print(f"{'='*60}")
        
        if self.platform == "Windows":
            try:
                subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=True)
                success_messages = {
                    'en': "System going to sleep",
                    'hi': "सिस्टम स्लीप मोड में जा रहा है",
                    'kn': "ಸಿಸ್ಟಮ್ ಸ್ಲೀಪ್ ಮೋಡ್‌ಗೆ ಹೋಗುತ್ತಿದೆ"
                }
                print(f"✅ {success_messages.get(language, success_messages['en'])}")
                print(f"{'='*60}\n")
                return True, success_messages.get(language, success_messages['en'])
            except Exception as e:
                error_messages = {
                    'en': f"Failed to sleep: {str(e)}",
                    'hi': f"स्लीप विफल: {str(e)}",
                    'kn': f"ಸ್ಲೀಪ್ ವಿಫಲವಾಯಿತು: {str(e)}"
                }
                print(f"❌ {error_messages.get(language, error_messages['en'])}")
                print(f"{'='*60}\n")
                return False, error_messages.get(language, error_messages['en'])
        else:
            error_messages = {
                'en': "Sleep only supported on Windows",
                'hi': "स्लीप केवल Windows पर समर्थित है",
                'kn': "ಸ್ಲೀಪ್ Windows ನಲ್ಲಿ ಮಾತ್ರ ಬೆಂಬಲಿತವಾಗಿದೆ"
            }
            print(f"❌ {error_messages.get(language, error_messages['en'])}")
            print(f"{'='*60}\n")
            return False, error_messages.get(language, error_messages['en'])
    
    def lock_system(self, language='en'):
        """Lock the computer"""
        print(f"\n{'='*60}")
        print(f"🔒 LOCKING SYSTEM")
        print(f"{'='*60}")
        
        if self.platform == "Windows":
            try:
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
                success_messages = {
                    'en': "System locked",
                    'hi': "सिस्टम लॉक हो गया",
                    'kn': "ಸಿಸ್ಟಮ್ ಲಾಕ್ ಆಗಿದೆ"
                }
                print(f"✅ {success_messages.get(language, success_messages['en'])}")
                print(f"{'='*60}\n")
                return True, success_messages.get(language, success_messages['en'])
            except Exception as e:
                error_messages = {
                    'en': f"Failed to lock: {str(e)}",
                    'hi': f"लॉक विफल: {str(e)}",
                    'kn': f"ಲಾಕ್ ವಿಫಲವಾಯಿತು: {str(e)}"
                }
                print(f"❌ {error_messages.get(language, error_messages['en'])}")
                print(f"{'='*60}\n")
                return False, error_messages.get(language, error_messages['en'])
        else:
            error_messages = {
                'en': "Lock only supported on Windows",
                'hi': "लॉक केवल Windows पर समर्थित है",
                'kn': "ಲಾಕ್ Windows ನಲ್ಲಿ ಮಾತ್ರ ಬೆಂಬಲಿತವಾಗಿದೆ"
            }
            print(f"❌ {error_messages.get(language, error_messages['en'])}")
            print(f"{'='*60}\n")
            return False, error_messages.get(language, error_messages['en'])
    
    def open_website(self, url, language='en'):
        """Open a specific website"""
        print(f"\n{'='*60}")
        print(f"🌐 OPENING WEBSITE")
        print(f"{'='*60}")
        print(f"🔗 URL: {url}")
        print(f"{'='*60}")
        
        try:
            # Add https:// if not present
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            webbrowser.open(url)
            
            success_messages = {
                'en': f"Opening: {url}",
                'hi': f"खोल रहे हैं: {url}",
                'kn': f"ತೆರೆಯುತ್ತಿದೆ: {url}"
            }
            print(f"✅ {success_messages.get(language, success_messages['en'])}")
            print(f"{'='*60}\n")
            return True, success_messages.get(language, success_messages['en'])
        except Exception as e:
            error_messages = {
                'en': f"Failed to open website: {str(e)}",
                'hi': f"वेबसाइट खोलने में विफल: {str(e)}",
                'kn': f"ವೆಬ್‌ಸೈಟ್ ತೆರೆಯಲು ವಿಫಲವಾಗಿದೆ: {str(e)}"
            }
            print(f"❌ {error_messages.get(language, error_messages['en'])}")
            print(f"{'='*60}\n")
            return False, error_messages.get(language, error_messages['en'])
    
    # ============================================================================
    # KEYBOARD CONTROL COMMANDS
    # ============================================================================
    
    def copy_text(self, language='en'):
        """Simulate Ctrl+C"""
        if not self.keyboard_available:
            error_messages = {
                'en': "Keyboard control not available. Install: pip install pyautogui",
                'hi': "कीबोर्ड नियंत्रण उपलब्ध नहीं है। इंस्टॉल करें: pip install pyautogui",
                'kn': "ಕೀಬೋರ್ಡ್ ನಿಯಂತ್ರಣ ಲಭ್ಯವಿಲ್ಲ. ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಿ: pip install pyautogui"
            }
            return False, error_messages.get(language, error_messages['en'])
        
        try:
            import pyautogui
            pyautogui.hotkey('ctrl', 'c')
            success_messages = {
                'en': "Text copied to clipboard",
                'hi': "टेक्स्ट कॉपी हो गया",
                'kn': "ಪಠ್ಯ ಕಾಪಿ ಆಗಿದೆ"
            }
            return True, success_messages.get(language, success_messages['en'])
        except Exception as e:
            error_messages = {
                'en': f"Failed to copy: {str(e)}",
                'hi': f"कॉपी विफल: {str(e)}",
                'kn': f"ಕಾಪಿ ವಿಫಲವಾಯಿತು: {str(e)}"
            }
            return False, error_messages.get(language, error_messages['en'])
    
    def paste_text(self, language='en'):
        """Simulate Ctrl+V"""
        if not self.keyboard_available:
            error_messages = {
                'en': "Keyboard control not available. Install: pip install pyautogui",
                'hi': "कीबोर्ड नियंत्रण उपलब्ध नहीं है। इंस्टॉल करें: pip install pyautogui",
                'kn': "ಕೀಬೋರ್ಡ್ ನಿಯಂತ್ರಣ ಲಭ್ಯವಿಲ್ಲ. ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಿ: pip install pyautogui"
            }
            return False, error_messages.get(language, error_messages['en'])
        
        try:
            import pyautogui
            pyautogui.hotkey('ctrl', 'v')
            success_messages = {
                'en': "Text pasted from clipboard",
                'hi': "टेक्स्ट पेस्ट हो गया",
                'kn': "ಪಠ್ಯ ಪೇಸ್ಟ್ ಆಗಿದೆ"
            }
            return True, success_messages.get(language, success_messages['en'])
        except Exception as e:
            error_messages = {
                'en': f"Failed to paste: {str(e)}",
                'hi': f"पेस्ट विफल: {str(e)}",
                'kn': f"ಪೇಸ್ಟ್ ವಿಫಲವಾಯಿತು: {str(e)}"
            }
            return False, error_messages.get(language, error_messages['en'])
    
    def select_all(self, language='en'):
        """Simulate Ctrl+A"""
        if not self.keyboard_available:
            error_messages = {
                'en': "Keyboard control not available",
                'hi': "कीबोर्ड नियंत्रण उपलब्ध नहीं है",
                'kn': "ಕೀಬೋರ್ಡ್ ನಿಯಂತ್ರಣ ಲಭ್ಯವಿಲ್ಲ"
            }
            return False, error_messages.get(language, error_messages['en'])
        
        try:
            import pyautogui
            pyautogui.hotkey('ctrl', 'a')
            success_messages = {
                'en': "All content selected",
                'hi': "सभी टेक्स्ट चुना गया",
                'kn': "ಎಲ್ಲಾ ಪಠ್ಯ ಆಯ್ಕೆಯಾಗಿದೆ"
            }
            return True, success_messages.get(language, success_messages['en'])
        except Exception as e:
            return False, f"Failed: {str(e)}"
    
    def undo_action(self, language='en'):
        """Simulate Ctrl+Z"""
        if not self.keyboard_available:
            return False, "Keyboard control not available"
        
        try:
            import pyautogui
            pyautogui.hotkey('ctrl', 'z')
            success_messages = {
                'en': "Action undone",
                'hi': "क्रिया पूर्ववत हुई",
                'kn': "ಕ್ರಿಯೆ ರದ್ದುಗೊಳಿಸಲಾಗಿದೆ"
            }
            return True, success_messages.get(language, success_messages['en'])
        except Exception as e:
            return False, f"Failed: {str(e)}"
    
    def redo_action(self, language='en'):
        """Simulate Ctrl+Y"""
        if not self.keyboard_available:
            return False, "Keyboard control not available"
        
        try:
            import pyautogui
            pyautogui.hotkey('ctrl', 'y')
            success_messages = {
                'en': "Action redone",
                'hi': "क्रिया फिर से की गई",
                'kn': "ಕ್ರಿಯೆ ಪುನಃ ಮಾಡಲಾಗಿದೆ"
            }
            return True, success_messages.get(language, success_messages['en'])
        except Exception as e:
            return False, f"Failed: {str(e)}"
    
    def take_screenshot(self, filename="screenshot.png", language='en'):
        """Take a screenshot"""
        if not self.keyboard_available:
            error_messages = {
                'en': "Screenshot feature not available. Install: pip install pyautogui",
                'hi': "स्क्रीनशॉट सुविधा उपलब्ध नहीं है",
                'kn': "ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ವೈಶಿಷ್ಟ್ಯ ಲಭ್ಯವಿಲ್ಲ"
            }
            return False, error_messages.get(language, error_messages['en'])
        
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            success_messages = {
                'en': f"Screenshot saved as {filename}",
                'hi': f"स्क्रीनशॉट {filename} के रूप में सहेजा गया",
                'kn': f"ಸ್ಕ್ರೀನ್‌ಶಾಟ್ {filename} ಆಗಿ ಉಳಿಸಲಾಗಿದೆ"
            }
            return True, success_messages.get(language, success_messages['en'])
        except Exception as e:
            error_messages = {
                'en': f"Failed to take screenshot: {str(e)}",
                'hi': f"स्क्रीनशॉट लेने में विफल: {str(e)}",
                'kn': f"ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ತೆಗೆಯಲು ವಿಫಲವಾಗಿದೆ: {str(e)}"
            }
            return False, error_messages.get(language, error_messages['en'])
    
    def increase_volume(self, language='en'):
        """Increase system volume"""
        if not self.keyboard_available:
            return False, "Keyboard control not available"
        
        try:
            import pyautogui
            pyautogui.press('volumeup')
            pyautogui.press('volumeup')
            success_messages = {
                'en': "Volume increased",
                'hi': "वॉल्यूम बढ़ाया गया",
                'kn': "ವಾಲ್ಯೂಮ್ ಹೆಚ್ಚಿಸಲಾಗಿದೆ"
            }
            return True, success_messages.get(language, success_messages['en'])
        except Exception as e:
            return False, f"Failed: {str(e)}"
    
    def decrease_volume(self, language='en'):
        """Decrease system volume"""
        if not self.keyboard_available:
            return False, "Keyboard control not available"
        
        try:
            import pyautogui
            pyautogui.press('volumedown')
            pyautogui.press('volumedown')
            success_messages = {
                'en': "Volume decreased",
                'hi': "वॉल्यूम कम किया गया",
                'kn': "ವಾಲ್ಯೂಮ್ ಕಡಿಮೆ ಮಾಡಲಾಗಿದೆ"
            }
            return True, success_messages.get(language, success_messages['en'])
        except Exception as e:
            return False, f"Failed: {str(e)}"
    
    def mute_volume(self, language='en'):
        """Mute system volume"""
        if not self.keyboard_available:
            return False, "Keyboard control not available"
        
        try:
            import pyautogui
            pyautogui.press('volumemute')
            success_messages = {
                'en': "Volume muted",
                'hi': "वॉल्यूम म्यूट किया गया",
                'kn': "ವಾಲ್ಯೂಮ್ ಮ್ಯೂಟ್ ಮಾಡಲಾಗಿದೆ"
            }
            return True, success_messages.get(language, success_messages['en'])
        except Exception as e:
            return False, f"Failed: {str(e)}"
    
    # ============================================================================
    # WEB SEARCH COMMANDS
    # ============================================================================
    
    def search_web(self, query, language='en'):
        """Search on Google"""
        print(f"\n{'='*60}")
        print(f"🔍 WEB SEARCH")
        print(f"{'='*60}")
        print(f"🔎 Query: {query}")
        print(f"{'='*60}")
        
        try:
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.google.com/search?q={encoded_query}"
            
            webbrowser.open(url)
            
            success_messages = {
                'en': f"Searching for: {query}",
                'hi': f"खोज रहे हैं: {query}",
                'kn': f"ಹುಡುಕುತ್ತಿದೆ: {query}"
            }
            print(f"✅ {success_messages.get(language, success_messages['en'])}")
            print(f"{'='*60}\n")
            return True, success_messages.get(language, success_messages['en'])
        except Exception as e:
            error_messages = {
                'en': f"Failed to search: {str(e)}",
                'hi': f"खोज विफल: {str(e)}",
                'kn': f"ಹುಡುಕಾಟ ವಿಫಲವಾಗಿದೆ: {str(e)}"
            }
            print(f"❌ {error_messages.get(language, error_messages['en'])}")
            print(f"{'='*60}\n")
            return False, error_messages.get(language, error_messages['en'])
    
    def search_youtube(self, query, language='en'):
        """Search on YouTube"""
        print(f"\n{'='*60}")
        print(f"📺 YOUTUBE SEARCH")
        print(f"{'='*60}")
        print(f"🔎 Query: {query}")
        print(f"{'='*60}")
        
        try:
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.youtube.com/results?search_query={encoded_query}"
            
            webbrowser.open(url)
            
            success_messages = {
                'en': f"Searching YouTube for: {query}",
                'hi': f"YouTube पर खोज रहे हैं: {query}",
                'kn': f"YouTube ನಲ್ಲಿ ಹುಡುಕುತ್ತಿದೆ: {query}"
            }
            print(f"✅ {success_messages.get(language, success_messages['en'])}")
            print(f"{'='*60}\n")
            return True, success_messages.get(language, success_messages['en'])
        except Exception as e:
            error_messages = {
                'en': f"Failed to search YouTube: {str(e)}",
                'hi': f"YouTube खोज विफल: {str(e)}",
                'kn': f"YouTube ಹುಡುಕಾಟ ವಿಫಲವಾಗಿದೆ: {str(e)}"
            }
            print(f"❌ {error_messages.get(language, error_messages['en'])}")
            print(f"{'='*60}\n")
            return False, error_messages.get(language, error_messages['en'])
    
    # ============================================================================
    # EXISTING METHODS (Time, Date, Weather, Jokes, News)
    # ============================================================================
    
    def get_current_time(self, language="en"):
        """Get current time in specified language"""
        now = datetime.now()
        
        if language == "en":
            return now.strftime("The current time is %I:%M %p")
        elif language == "hi":
            time_str = now.strftime("%I:%M %p")
            return f"अभी समय है {time_str}"
        elif language == "kn":
            time_str = now.strftime("%I:%M %p")
            return f"ಈಗ ಸಮಯ {time_str}"
        else:
            return now.strftime("The current time is %I:%M %p")
    
    def get_current_date(self, language="en"):
        """Get current date in specified language"""
        now = datetime.now()
    
        if language == "en":
            return now.strftime("Today is %A, %B %d, %Y")
        elif language == "hi":
            weekdays_hi = ['सोमवार', 'मंगलवार', 'बुधवार', 'गुरुवार', 'शुक्रवार', 'शनिवार', 'रविवार']
            months_hi = ['जनवरी', 'फरवरी', 'मार्च', 'अप्रैल', 'मई', 'जून', 
                     'जुलाई', 'अगस्त', 'सितंबर', 'अक्टूबर', 'नवंबर', 'दिसंबर']
            weekday = weekdays_hi[now.weekday()]
            month = months_hi[now.month - 1]
            return f"आज {weekday}, {now.day} {month} {now.year} है"
        elif language == "kn":
            weekdays_kn = ['ಸೋಮವಾರ', 'ಮಂಗಳವಾರ', 'ಬುಧವಾರ', 'ಗುರುವಾರ', 'ಶುಕ್ರವಾರ', 'ಶನಿವಾರ', 'ಭಾನುವಾರ']
            months_kn = ['ಜನವರಿ', 'ಫೆಬ್ರವರಿ', 'ಮಾರ್ಚ್', 'ಏಪ್ರಿಲ್', 'ಮೇ', 'ಜೂನ್',
                     'ಜುಲೈ', 'ಆಗಸ್ಟ್', 'ಸೆಪ್ಟೆಂಬರ್', 'ಅಕ್ಟೋಬರ್', 'ನವೆಂಬರ್', 'ಡಿಸೆಂಬರ್']
            weekday = weekdays_kn[now.weekday()]
            month = months_kn[now.month - 1]
            return f"ಇಂದು {weekday}, {now.day} {month} {now.year}"
        else:
            return now.strftime("Today is %A, %B %d, %Y")
    
    def get_weather(self, city="Bengaluru", language="en"):
        """Get weather information"""
        if not self.weather_api_key:
            return self._get_mock_weather(city, language)
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.weather_api_key}&units=metric"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if response.status_code == 200:
                temp = data['main']['temp']
                description = data['weather'][0]['description']
                humidity = data['main']['humidity']
                
                if language == "en":
                    return f"The weather in {city} is {description}. Temperature is {temp}°C with {humidity}% humidity."
                elif language == "hi":
                    return f"{city} में मौसम {description} है। तापमान {temp}°C है और आर्द्रता {humidity}% है।"
                elif language == "kn":
                    return f"{city} ನಲ್ಲಿ ಹವಾಮಾನ {description} ಇದೆ। ತಾಪಮಾನ {temp}°C ಮತ್ತು ಆರ್ದ್ರತೆ {humidity}% ಇದೆ।"
            else:
                return self._get_mock_weather(city, language)
        except:
            return self._get_mock_weather(city, language)
    
    def _get_mock_weather(self, city, language):
        """Return mock weather data when API is not available"""
        if language == "en":
            return f"Unable to fetch weather data. Please check your internet connection."
        elif language == "hi":
            return f"मौसम की जानकारी प्राप्त नहीं की जा सकी। कृपया इंटरनेट कनेक्शन जांचें।"
        elif language == "kn":
            return f"ಹವಾಮಾನ ಮಾಹಿತಿ ಪಡೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕ ಪರಿಶೀಲಿಸಿ।"
    
    def tell_joke(self, language="en"):
        """Tell a random joke"""
        print(f"\n{'='*60}")
        print(f"😄 TELLING A JOKE")
        print(f"{'='*60}")
        print(f"🌍 Language: {language}")
        print(f"{'='*60}")
        
        joke_list = self.jokes_database.get(language, self.jokes_database["en"])
        joke = random.choice(joke_list)
        
        print(f"🎭 Joke: {joke}")
        print(f"{'='*60}\n")
        
        return joke
    
    def entertain_me(self, language="en"):
        """Respond to entertainment requests with jokes and fun responses"""
        options = ['joke', 'fact', 'quote']
        choice = random.choice(options)
        
        if choice == 'joke':
            return self.tell_joke(language)
        
        elif choice == 'fact':
            fun_facts = {
                'en': [
                    "Did you know? Honey never spoils. Archaeologists have found 3000-year-old honey in Egyptian tombs that's still edible!",
                    "Fun fact: A group of flamingos is called a 'flamboyance'!",
                    "Did you know? Bananas are berries, but strawberries aren't!",
                    "Interesting: An octopus has three hearts and blue blood!",
                    "Did you know? The shortest war in history lasted only 38 minutes!",
                ],
                'hi': [
                    "क्या आप जानते हैं? शहद कभी खराब नहीं होता। 3000 साल पुराना शहद अभी भी खाने योग्य है!",
                    "रोचक तथ्य: एक ऑक्टोपस के तीन दिल होते हैं!",
                    "क्या आप जानते हैं? केले बेरी हैं, लेकिन स्ट्रॉबेरी नहीं!",
                ],
                'kn': [
                    "ನಿಮಗೆ ಗೊತ್ತೇ? ಜೇನು ಎಂದಿಗೂ ಹಾಳಾಗುವುದಿಲ್ಲ. 3000 ವರ್ಷಗಳಷ್ಟು ಹಳೆಯ ಜೇನು ಸಿಕ್ಕಿದೆ!",
                    "ಮಜೆದಾರ ಸತ್ಯ: ಆಕ್ಟೋಪಸ್‌ಗೆ ಮೂರು ಹೃದಯಗಳಿವೆ!",
                ]
            }
            facts = fun_facts.get(language, fun_facts['en'])
            return random.choice(facts)
        
        else:
            quotes = {
                'en': [
                    "\"The only way to do great work is to love what you do.\" - Steve Jobs",
                    "\"Be yourself; everyone else is already taken.\" - Oscar Wilde",
                ],
                'hi': [
                    "\"महान कार्य करने का एकमात्र तरीका है कि आप जो करते हैं उससे प्यार करें।\" - स्टीव जॉब्स",
                ],
                'kn': [
                    "\"ಮಹಾನ್ ಕೆಲಸ ಮಾಡುವ ಏಕೈಕ ಮಾರ್ಗವೆಂದರೆ ನೀವು ಮಾಡುವುದನ್ನು ಪ್ರೀತಿಸುವುದು.\" - ಸ್ಟೀವ್ ಜಾಬ್ಸ್",
                ]
            }
            quote_list = quotes.get(language, quotes['en'])
            return random.choice(quote_list)
    
    def get_news(self, language="en", country="in"):
        """Get latest news headlines"""
        NEWS_API_KEY = "61363611018b493db9676479c15ab541" 
        
        if not NEWS_API_KEY:
            return self._get_mock_news(language)

        try:
            url = f"https://newsapi.org/v2/top-headlines?country={country}&apiKey={NEWS_API_KEY}"
            response = requests.get(url, timeout=5)
            data = response.json()

            if response.status_code == 200 and data.get('articles'):
                headlines = []
                for i, article in enumerate(data['articles'][:5], 1):
                    headlines.append(f"{i}. {article.get('title','')}")
            
                if language == "en":
                    return "Here are the top news headlines: " + " ".join(headlines)
                elif language == "hi":
                    return "यहां शीर्ष समाचार हैं: " + " ".join(headlines)
                elif language == "kn":
                    return "ಇಲ್ಲಿ ಪ್ರಮುಖ ಸುದ್ದಿಗಳಿವೆ: " + " ".join(headlines)
            else:
                return self._get_mock_news(language)
        except:
            return self._get_mock_news(language)

    def _get_mock_news(self, language):
        """Return mock news when API is unavailable"""
        if language == "en":
            return "Unable to fetch news. Please check your internet connection."
        elif language == "hi":
            return "समाचार प्राप्त नहीं किया जा सका। कृपया इंटरनेट कनेक्शन जांचें।"
        elif language == "kn":
            return "ಸುದ್ದಿ ಪಡೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕ ಪರಿಶೀಲಿಸಿ।"

    def set_weather_api_key(self, api_key):
        """Set weather API key"""
        self.weather_api_key = api_key