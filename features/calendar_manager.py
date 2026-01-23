from database.db_manager import DatabaseManager
from datetime import datetime, timedelta
import subprocess
import platform
import os
import re

class CalendarManager:
    def __init__(self, db_manager):
        self.db = db_manager
        self.platform = platform.system()

    def open_calendar(self):
        """Open Windows Calendar app directly"""
        if self.platform == "Windows":
            try:
                # Method 1: Try Windows 10/11 Calendar app
                subprocess.Popen("start outlookcal:", shell=True)
                print("📅 Opening Windows Calendar app...")
                return True, "Opening Calendar"
            except:
                try:
                    # Method 2: Try Outlook Calendar
                    subprocess.Popen("start outlook:", shell=True)
                    print("📧 Opening Outlook Calendar...")
                    return True, "Opening Outlook Calendar"
                except:
                    try:
                        # Method 3: Try direct Calendar app
                        subprocess.Popen("explorer.exe shell:appsFolder\\Microsoft.WindowsCalendar_8wekyb3d8bbwe!microsoft.windowscalendar", shell=True)
                        print("📅 Opening Calendar via explorer...")
                        return True, "Opening Calendar"
                    except Exception as e:
                        print(f"⚠️ Could not open calendar: {e}")
                        return False, "Failed to open calendar app"
        else:
            return False, "Calendar opening only supported on Windows"

    def parse_datetime_from_text(self, text, language='en'):
        """Parse date/time from multilingual text - FIXED FOR UNICODE"""
        print(f"🔍 Parsing datetime from: '{text}' (language: {language})")
        
        now = datetime.now()
        
        # Remove common words that interfere with parsing
        clean_text = text.lower().strip()
        
        # Language-specific cleaning
        if language == 'hi':
            # Remove Hindi words
            remove_words = ['बनाओ', 'बनाना', 'बना', 'करो', 'कर', 'का', 'की', 'को', 'में', 'पर', 'से']
            for word in remove_words:
                clean_text = clean_text.replace(word, ' ')
        elif language == 'kn':
            # Remove Kannada words
            remove_words = ['ರಚಿಸು', 'ಮಾಡು', 'ಮಾಡಿ', 'ಗೆ', 'ನಲ್ಲಿ', 'ದಲ್ಲಿ']
            for word in remove_words:
                clean_text = clean_text.replace(word, ' ')
        
        clean_text = ' '.join(clean_text.split())  # Remove extra spaces
        
        # Try to extract time patterns (works for all languages with digits)
        # Pattern: 3pm, 3 pm, 15:00, 3:30pm, etc.
        time_patterns = [
            r'(\d{1,2})\s*(?:pm|पीएम|ಪಿಎಮ್)',  # 3pm, 3 pm
            r'(\d{1,2})\s*(?:am|एएम|ಎಎಮ್)',  # 3am, 3 am
            r'(\d{1,2}):(\d{2})\s*(?:pm|पीएम|ಪಿಎಮ್)?',  # 3:30pm
            r'(\d{1,2}):(\d{2})\s*(?:am|एएम|ಎಎಮ್)?',  # 3:30am
            r'(\d{1,2})\s+(?:बजे|ಗಂಟೆ|ಗಂಟೆಗೆ)',  # Hindi/Kannada hour markers
        ]
        
        parsed_time = None
        
        for pattern in time_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                try:
                    hour = int(match.group(1))
                    minute = int(match.group(2)) if len(match.groups()) > 1 and match.group(2) else 0
                    
                    # Handle PM/AM
                    if 'pm' in match.group(0).lower() or 'पीएम' in match.group(0) or 'ಪಿಎಮ್' in match.group(0):
                        if hour < 12:
                            hour += 12
                    elif 'am' in match.group(0).lower() or 'एएम' in match.group(0) or 'ಎಎಮ್' in match.group(0):
                        if hour == 12:
                            hour = 0
                    
                    # If hour is less than current hour and no AM/PM specified, assume next occurrence
                    if hour < now.hour and 'pm' not in match.group(0).lower() and 'am' not in match.group(0).lower():
                        if hour <= 12:  # Could be PM
                            hour += 12
                    
                    parsed_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    print(f"✅ Parsed time: {parsed_time.strftime('%I:%M %p')}")
                    break
                except Exception as e:
                    print(f"⚠️ Failed to parse time pattern: {e}")
                    continue
        
        # Check for relative time indicators
        if not parsed_time:
            # Tomorrow
            if any(word in clean_text for word in ['tomorrow', 'कल', 'ನಾಳೆ']):
                parsed_time = now + timedelta(days=1)
                parsed_time = parsed_time.replace(hour=9, minute=0, second=0, microsecond=0)
                print(f"✅ Parsed as tomorrow: {parsed_time.strftime('%Y-%m-%d %I:%M %p')}")
            # Today (default)
            else:
                # Default to 1 hour from now
                parsed_time = now + timedelta(hours=1)
                parsed_time = parsed_time.replace(second=0, microsecond=0)
                print(f"✅ Defaulting to 1 hour from now: {parsed_time.strftime('%I:%M %p')}")
        
        return parsed_time

    def create_event(self, user_id, title, description='', start_datetime=None, end_datetime=None, location='', language='en'):
        """Create event with proper datetime parsing"""
        
        # If start_datetime is a string, parse it
        if isinstance(start_datetime, str):
            start_datetime = self.parse_datetime_from_text(start_datetime, language)
        elif start_datetime is None:
            start_datetime = datetime.now() + timedelta(hours=1)
        
        if end_datetime is None:
            end_datetime = start_datetime + timedelta(hours=1)
        
        # Insert in DB first
        query = '''
            INSERT INTO calendar_events (user_id, title, description, start_datetime, end_datetime, location)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        try:
            self.db.execute_query(query, (user_id, title, description, start_datetime, end_datetime, location))
            print(f"✅ Event '{title}' saved to database at {start_datetime.strftime('%Y-%m-%d %I:%M %p')}")
        except Exception as e:
            print(f"⚠️ Failed to save to database: {e}")
        
        # Try to add to system calendar based on platform
        if self.platform == "Darwin":  # macOS
            self._add_to_macos_calendar(title, description, start_datetime, end_datetime, location)
        elif self.platform == "Windows":
            success = self._add_to_windows_calendar(title, description, start_datetime, end_datetime, location)
            if not success:
                # If failed, open calendar for manual entry
                print("📅 Opening Windows Calendar for manual entry...")
                self.open_calendar()
        
        return True, f"Event '{title}' created successfully for {start_datetime.strftime('%I:%M %p on %B %d')}"

    def _add_to_macos_calendar(self, title, description, start, end, location):
        """Use AppleScript to create macOS Calendar event"""
        start_str = start.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end.strftime("%Y-%m-%d %H:%M:%S")
        apple_script = f'''
        tell application "Calendar"
            tell calendar "Home"
                set newEvent to make new event with properties {{summary:"{title}", description:"{description}", location:"{location}", start date:date "{start_str}", end date:date "{end_str}"}}
            end tell
        end tell
        '''
        try:
            subprocess.run(["osascript", "-e", apple_script], check=True)
            print(f"✅ Event added to macOS Calendar")
        except Exception as e:
            print(f"⚠️ Failed to add event to macOS Calendar: {e}")

    def _add_to_windows_calendar(self, title, description, start, end, location):
        """Use PowerShell to create Windows Calendar event via Outlook"""
        # Format dates for Windows Calendar (Outlook format)
        start_str = start.strftime("%Y-%m-%dT%H:%M:%S")
        end_str = end.strftime("%Y-%m-%dT%H:%M:%S")
        
        # Escape single quotes in text fields
        title = title.replace("'", "''")
        description = description.replace("'", "''")
        location = location.replace("'", "''")
        
        # PowerShell script to create calendar event
        powershell_script = f'''
        try {{
            $outlook = New-Object -ComObject Outlook.Application
            $appointment = $outlook.CreateItem(1)
            $appointment.Subject = '{title}'
            $appointment.Body = '{description}'
            $appointment.Location = '{location}'
            $appointment.Start = '{start_str}'
            $appointment.End = '{end_str}'
            $appointment.ReminderSet = $true
            $appointment.ReminderMinutesBeforeStart = 15
            $appointment.Save()
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($outlook) | Out-Null
            Write-Output "SUCCESS"
        }} catch {{
            Write-Output "FAILED: $_"
        }}
        '''
        
        try:
            # Execute PowerShell command
            result = subprocess.run(
                ["powershell", "-Command", powershell_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "SUCCESS" in result.stdout:
                print(f"✅ Event '{title}' added to Windows Calendar (Outlook)")
                return True
            else:
                print(f"⚠️ Outlook method failed: {result.stdout}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⚠️ PowerShell command timed out")
            return False
        except Exception as e:
            print(f"⚠️ Error adding to Windows Calendar: {e}")
            return False

    def get_user_events(self, user_id, start_date=None, end_date=None):
        """Get user events from database"""
        query = '''
            SELECT event_id, title, description, start_datetime, end_datetime, location
            FROM calendar_events
            WHERE user_id = ?
        '''
        params = [user_id]
        
        if start_date and end_date:
            query += ' AND start_datetime BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        
        query += ' ORDER BY start_datetime ASC'
        
        results = self.db.execute_query(query, tuple(params))
        events = []
        for row in results:
            events.append({
                'event_id': row[0],
                'title': row[1],
                'description': row[2],
                'start_datetime': row[3],
                'end_datetime': row[4],
                'location': row[5]
            })
        return events
    
    def get_today_events(self, user_id):
        """Get today's events"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        return self.get_user_events(user_id, today_start, today_end)
    
    def get_upcoming_events(self, user_id, days=7):
        """Get upcoming events for next N days"""
        start = datetime.now()
        end = start + timedelta(days=days)
        return self.get_user_events(user_id, start, end)
    
    def delete_event(self, event_id):
        """Delete an event"""
        query = 'DELETE FROM calendar_events WHERE event_id = ?'
        self.db.execute_query(query, (event_id,))
        return True, f"Event deleted successfully"
    
    def update_event(self, event_id, **kwargs):
        """Update an event"""
        allowed_fields = ['title', 'description', 'start_datetime', 'end_datetime', 'location']
        updates = []
        values = []
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            return False, "No valid fields to update"
        
        values.append(event_id)
        query = f"UPDATE calendar_events SET {', '.join(updates)} WHERE event_id = ?"
        self.db.execute_query(query, tuple(values))
        
        return True, f"Event updated successfully"