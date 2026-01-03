from database.db_manager import DatabaseManager
from datetime import datetime, timedelta
import subprocess

class CalendarManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def create_event(self, user_id, title, description='', start_datetime=None, end_datetime=None, location=''):
        if start_datetime is None:
            start_datetime = datetime.now()
        if end_datetime is None:
            end_datetime = start_datetime + timedelta(hours=1)
        # Insert in DB
        query = '''
            INSERT INTO calendar_events (user_id, title, description, start_datetime, end_datetime, location)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        self.db.execute_query(query, (user_id, title, description, start_datetime, end_datetime, location))
        # Add to macOS Calendar
        self._add_to_macos_calendar(title, description, start_datetime, end_datetime, location)
        return True, f"Event '{title}' created successfully"

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
        except Exception as e:
            print(f"Failed to add event to macOS Calendar: {e}")

    def get_user_events(self, user_id, start_date=None, end_date=None):
        query = '''
            SELECT event_id, title, description, start_datetime, end_datetime, location
            FROM calendar_events
            WHERE user_id = ?
            ORDER BY start_datetime ASC
        '''
        results = self.db.execute_query(query, (user_id,))
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
