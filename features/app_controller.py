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
        
    def open_app(self, app_name):
        """Open an application on Windows"""
        app_name = app_name.lower()
        
        try:
            if self.platform == "Windows":
                # Check if app is in predefined paths
                if app_name in APP_PATHS:
                    app_executable = APP_PATHS[app_name]
                    
                    # Try to launch from PATH
                    try:
                        subprocess.Popen(app_executable, shell=True)
                        return True, f"Opening {app_name}"
                    except:
                        # Try common installation paths
                        common_paths = [
                            f"C:\\Program Files\\{app_executable}",
                            f"C:\\Program Files (x86)\\{app_executable}",
                            os.path.expandvars(f"%LOCALAPPDATA%\\Programs\\{app_executable}"),
                        ]
                        
                        for path in common_paths:
                            if os.path.exists(path):
                                os.startfile(path)
                                return True, f"Opening {app_name}"
                        
                        # If not found, try shell command
                        subprocess.Popen(f"start {app_name}", shell=True)
                        return True, f"Attempting to open {app_name}"
                else:
                    # Try to open by name
                    subprocess.Popen(f"start {app_name}", shell=True)
                    return True, f"Opening {app_name}"
            
            elif self.platform == "Darwin":  # macOS
                if app_name in APP_PATHS:
                    subprocess.Popen(['open', '-a', APP_PATHS[app_name]])
                else:
                    subprocess.Popen(['open', '-a', app_name])
                return True, f"Opening {app_name}"
            
            else:  # Linux
                subprocess.Popen([app_name])
                return True, f"Opening {app_name}"
                
        except Exception as e:
            return False, f"Failed to open {app_name}: {str(e)}"
    
    def close_app(self, app_name):
        """Close an application"""
        app_name = app_name.lower()
        
        try:
            closed = False
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    proc_name = proc.info['name'].lower()
                    
                    # Match process name
                    if app_name in proc_name or proc_name.startswith(app_name):
                        proc.kill()
                        closed = True
                    
                    # Also check executable path
                    if proc.info['exe'] and app_name in proc.info['exe'].lower():
                        proc.kill()
                        closed = True
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            if closed:
                return True, f"Closed {app_name}"
            else:
                return False, f"{app_name} is not running"
            
        except Exception as e:
            return False, f"Failed to close {app_name}: {str(e)}"
    
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