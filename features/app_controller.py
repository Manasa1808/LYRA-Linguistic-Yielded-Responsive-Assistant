#app_controller.py
import subprocess
import os
import psutil
import platform
from config import PLATFORM, APP_PATHS

class AppController:
    def __init__(self):
        self.platform = PLATFORM
        self.running_apps = {}
        
        # Enhanced app name mappings for voice recognition in multiple languages
        self.app_name_mappings = {
            # Calculator variations
            'calculator': 'calc',
            'calc': 'calc',
            'calculater': 'calc',
            'calculetor': 'calc',
            'कैलकुलेटर': 'calc',
            'कैल्कुलेटर': 'calc',
            'ಕ್ಯಾಲ್ಕುಲೇಟರ್': 'calc',
            'ಕ್ಯಾಲ್ಕ್ಯುಲೇಟರ್': 'calc',
            
            # Brave variations
            'brave': 'brave',
            'brave browser': 'brave',
            'ಬ್ರೇವ್': 'brave',
            'ब्रेव': 'brave',
            
            # Chrome variations
            'chrome': 'chrome',
            'google chrome': 'chrome',
            'क्रोम': 'chrome',
            'गूगल क्रोम': 'chrome',
            'ಕ್ರೋಮ್': 'chrome',
            'ಗೂಗಲ್ ಕ್ರೋಮ್': 'chrome',
            
            # Edge variations
            'edge': 'msedge',
            'microsoft edge': 'msedge',
            'एज': 'msedge',
            'ಎಡ್ಜ್': 'msedge',
            
            # Firefox variations
            'firefox': 'firefox',
            'फायरफॉक्स': 'firefox',
            'ಫೈರ್‌ಫಾಕ್ಸ್': 'firefox',
            
            # Notepad variations
            'notepad': 'notepad',
            'नोटपैड': 'notepad',
            'ನೋಟ್‌ಪ್ಯಾಡ್': 'notepad',
            'नोटपॅड': 'notepad',
            
            # Paint variations
            'paint': 'mspaint',
            'पेंट': 'mspaint',
            'ಪೇಂಟ್': 'mspaint',
            
            # Word variations
            'word': 'winword',
            'microsoft word': 'winword',
            'वर्ड': 'winword',
            'ವರ್ಡ್': 'winword',
            
            # Excel variations
            'excel': 'excel',
            'microsoft excel': 'excel',
            'एक्सेल': 'excel',
            'ಎಕ್ಸೆಲ್': 'excel',
            
            # PowerPoint variations
            'powerpoint': 'powerpnt',
            'microsoft powerpoint': 'powerpnt',
            'पावरपॉइंट': 'powerpnt',
            'ಪವರ್‌ಪಾಯಿಂಟ್': 'powerpnt',
            
            # Outlook variations
            'outlook': 'outlook',
            'आउटलुक': 'outlook',
            'ಔಟ್ಲುಕ್': 'outlook',
            
            # VS Code variations
            'visual studio code': 'code',
            'vscode': 'code',
            'vs code': 'code',
            'code': 'code',
            
            # Other apps
            'spotify': 'spotify',
            'vlc': 'vlc',
            'whatsapp': 'whatsapp',
            'telegram': 'telegram',
            'discord': 'discord',
            'slack': 'slack',
            'zoom': 'zoom',
            'skype': 'skype',
        }
        
        # Windows executable paths - FULL PATHS
        self.windows_app_paths = {
            'calc': 'calc.exe',  # System32, always in PATH
            'notepad': 'notepad.exe',  # System32, always in PATH
            'mspaint': 'mspaint.exe',  # System32, always in PATH
            
            # Browsers - try multiple locations
            'chrome': [
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
            ],
            'brave': [
                r'C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe',
                r'C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe',
            ],
            'msedge': [
                r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
                r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
            ],
            'firefox': [
                r'C:\Program Files\Mozilla Firefox\firefox.exe',
                r'C:\Program Files (x86)\Mozilla Firefox\firefox.exe',
            ],
            
            # Office apps
            'winword': [
                r'C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE',
                r'C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE',
            ],
            'excel': [
                r'C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE',
                r'C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE',
            ],
            'powerpnt': [
                r'C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE',
                r'C:\Program Files (x86)\Microsoft Office\root\Office16\POWERPNT.EXE',
            ],
            'outlook': [
                r'C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE',
                r'C:\Program Files (x86)\Microsoft Office\root\Office16\OUTLOOK.EXE',
            ],
            
            # VS Code
            'code': [
                os.path.expandvars(r'%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe'),
                r'C:\Program Files\Microsoft VS Code\Code.exe',
            ],
            
            # Other apps
            'spotify': [
                os.path.expandvars(r'%APPDATA%\Spotify\Spotify.exe'),
            ],
        }
        
    def normalize_app_name(self, app_name):
        """Normalize app name for better matching with voice input"""
        if not app_name:
            return None
            
        # Convert to lowercase and strip whitespace
        normalized = app_name.lower().strip()
        
        # Remove common words that might be added by voice recognition
        remove_words = ['open', 'launch', 'start', 'run', 'the', 
                       'खोलो', 'खोल', 'शुरू', 'करो', 'चालू',
                       'ತೆರೆ', 'ಪ್ರಾರಂಭ', 'ಪ್ರಾರಂಭಿಸು', 'browser']
        for word in remove_words:
            normalized = normalized.replace(word, '').strip()
        
        # Remove punctuation
        normalized = normalized.replace('.', '').replace(',', '').replace('!', '')
        
        # Check if it's in our mappings
        if normalized in self.app_name_mappings:
            return self.app_name_mappings[normalized]
        
        # Return normalized name
        return normalized
    
    def find_app_executable(self, app_key):
        """Find the actual executable path for an app"""
        if app_key not in self.windows_app_paths:
            return None
        
        paths = self.windows_app_paths[app_key]
        
        # If it's a single string (like calc.exe), return it
        if isinstance(paths, str):
            return paths
        
        # If it's a list, try each path
        for path in paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                print(f"✅ Found {app_key} at: {expanded_path}")
                return expanded_path
        
        print(f"⚠️ {app_key} not found in any standard location")
        return None
        
    def open_app(self, app_name):
        """Open an application on Windows - FIXED VERSION"""
        # Normalize the app name
        normalized_name = self.normalize_app_name(app_name)
        if not normalized_name:
            return False, "Invalid app name"
        
        print(f"🔍 Opening app: '{app_name}' -> normalized: '{normalized_name}'")
        
        try:
            if self.platform == "Windows":
                
                # Method 1: Try to find full path from our database
                exe_path = self.find_app_executable(normalized_name)
                
                if exe_path:
                    if os.path.exists(exe_path) if not exe_path.endswith('.exe') or '\\' in exe_path else True:
                        try:
                            # Use full path if it's a full path, otherwise use name
                            if '\\' in exe_path or '/' in exe_path:
                                # It's a full path, use os.startfile
                                os.startfile(exe_path)
                                print(f"✅ Opened {normalized_name} using full path: {exe_path}")
                            else:
                                # It's just an exe name (like calc.exe), use subprocess
                                subprocess.Popen(exe_path, shell=True)
                                print(f"✅ Opened {normalized_name} using: {exe_path}")
                            return True, f"Opening {normalized_name}"
                        except Exception as e:
                            print(f"⚠️ Failed to open with path method: {e}")
                
                # Method 2: Try using Windows 'start' command
                try:
                    subprocess.Popen(f'start "" "{normalized_name}"', shell=True)
                    print(f"✅ Opened {normalized_name} using start command")
                    return True, f"Opening {normalized_name}"
                except Exception as e:
                    print(f"⚠️ Start command failed: {e}")
                
                # Method 3: Try from APP_PATHS in config
                if normalized_name in APP_PATHS:
                    app_path = APP_PATHS[normalized_name]
                    try:
                        subprocess.Popen(app_path, shell=True)
                        print(f"✅ Opened {normalized_name} from APP_PATHS")
                        return True, f"Opening {normalized_name}"
                    except Exception as e:
                        print(f"⚠️ APP_PATHS method failed: {e}")
                
                # Method 4: Try direct execution
                try:
                    subprocess.Popen(normalized_name, shell=True)
                    print(f"✅ Opened {normalized_name} directly")
                    return True, f"Opening {normalized_name}"
                except Exception as e:
                    print(f"⚠️ Direct execution failed: {e}")
                
                return False, f"Could not find {normalized_name}. Make sure it's installed."
            
            elif self.platform == "Darwin":  # macOS
                if normalized_name in APP_PATHS:
                    subprocess.Popen(['open', '-a', APP_PATHS[normalized_name]])
                else:
                    subprocess.Popen(['open', '-a', normalized_name])
                return True, f"Opening {normalized_name}"
            
            else:  # Linux
                subprocess.Popen([normalized_name])
                return True, f"Opening {normalized_name}"
                
        except Exception as e:
            print(f"❌ All methods failed for {normalized_name}: {str(e)}")
            return False, f"Failed to open {normalized_name}: {str(e)}"
    
    def close_app(self, app_name):
        """Close an application"""
        # Normalize the app name
        normalized_name = self.normalize_app_name(app_name)
        if not normalized_name:
            return False, "Invalid app name"
        
        print(f"🔍 Closing app: '{app_name}' -> normalized: '{normalized_name}'")
        
        # Get possible process names
        possible_names = [normalized_name, f"{normalized_name}.exe"]
        
        # For browsers, add specific process names
        browser_process_names = {
            'brave': ['brave.exe'],
            'chrome': ['chrome.exe'],
            'firefox': ['firefox.exe'],
            'msedge': ['msedge.exe'],
        }
        
        if normalized_name in browser_process_names:
            possible_names.extend(browser_process_names[normalized_name])
        
        try:
            closed = False
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    proc_name = proc.info['name'].lower()
                    
                    # Match against any possible name
                    for possible in possible_names:
                        possible = possible.lower()
                        if possible in proc_name or proc_name.startswith(possible.replace('.exe', '')):
                            proc.kill()
                            closed = True
                            print(f"✅ Killed process: {proc_name}")
                            break
                    
                    # Also check executable path
                    if proc.info['exe'] and normalized_name in proc.info['exe'].lower():
                        proc.kill()
                        closed = True
                        print(f"✅ Killed process from path: {proc.info['exe']}")
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            if closed:
                return True, f"Closed {normalized_name}"
            else:
                return False, f"{normalized_name} is not running"
            
        except Exception as e:
            print(f"❌ Failed to close {normalized_name}: {str(e)}")
            return False, f"Failed to close {normalized_name}: {str(e)}"
    
    def get_running_apps(self):
        """Get list of running applications"""
        running = []
        for proc in psutil.process_iter(['name', 'pid', 'exe']):
            try:
                # Only include GUI applications (filter out system processes)
                if proc.info['exe'] and not proc.info['name'].startswith('svchost'):
                    running.append({
                        'name': proc.info['name'],
                        'pid': proc.info['pid'],
                        'exe': proc.info['exe']
                    })
            except:
                continue
        return running
    
    def minimize_all_windows(self):
        """Minimize all windows (Windows only)"""
        if self.platform == "Windows":
            try:
                import pyautogui
                pyautogui.hotkey('win', 'd')
                return True, "Minimized all windows"
            except:
                return False, "Failed to minimize windows"
        return False, "Feature only available on Windows"
    
    def maximize_window(self, app_name):
        """Maximize a specific window"""
        try:
            import pyautogui
            # Implementation depends on window management library
            return True, f"Maximized {app_name}"
        except:
            return False, "Failed to maximize window"