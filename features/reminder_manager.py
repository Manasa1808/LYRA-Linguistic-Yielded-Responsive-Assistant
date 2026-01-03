from datetime import datetime, timedelta
import re

class ReminderManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def create_reminder(self, user_id, title, description='', due_datetime=None, priority='Normal'):
        """Insert a reminder into the database"""
        query = '''
            INSERT INTO reminders (user_id, title, description, due_datetime, priority, notified)
            VALUES (?, ?, ?, ?, ?, 0)
        '''
        dt_str = due_datetime.strftime("%Y-%m-%d %H:%M:%S") if due_datetime else None
        self.db.execute_query(query, (user_id, title, description, dt_str, priority))

    def get_due_reminders(self, user_id, now):
        query = '''
            SELECT reminder_id, title, description, due_datetime
            FROM reminders
            WHERE user_id = ?
              AND is_completed = 0
              AND notified = 0
              AND due_datetime <= ?
            ORDER BY due_datetime ASC
        '''
        rows = self.db.execute_query(query, (user_id, now.strftime("%Y-%m-%d %H:%M:%S")))
        return [
            {
                "reminder_id": r[0],
                "title": r[1],
                "description": r[2],
                "due_datetime": datetime.strptime(r[3], "%Y-%m-%d %H:%M:%S") if r[3] else None,
            }
            for r in rows
        ]

    def mark_notified(self, reminder_id):
        self.db.execute_query(
            "UPDATE reminders SET notified = 1 WHERE reminder_id = ?",
            (reminder_id,)
        )

    def parse_reminder_time(self, time_str):
        """Parse natural language times"""
        now = datetime.now()
        time_str = (time_str or "").lower().strip()

        # "in X minutes/hours"
        match = re.search(r"in (\d+) (minute|minutes|hour|hours)", time_str)
        if match:
            val = int(match.group(1))
            return now + (timedelta(minutes=val) if "minute" in match.group(2) else timedelta(hours=val))

        # "at HH:MM am/pm"
        match = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)?", time_str)
        if match:
            h, m, ap = match.groups()
            h, m = int(h), int(m)
            if ap == "pm" and h != 12:
                h += 12
            if ap == "am" and h == 12:
                h = 0
            dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
            return dt if dt > now else dt + timedelta(days=1)

        # fallback 5 min
        return now + timedelta(minutes=5)

    def extract_task_and_time(self, text):
        text = text.lower().strip()
        match = re.search(r"remind me to (.+?) at (\d{1,2}(:\d{2})?\s*(am|pm)?)", text, re.IGNORECASE)
        if match:
            task = match.group(1).strip()      # FULL task
            time_str = match.group(2).strip()  # Time part
            due_time = self.parse_reminder_time(time_str)
            return task, due_time

        # "remind me in X minutes/hours to TASK"
        match = re.search(r"remind me in (\d+) (minute|minutes|hour|hours) to (.+)", text, re.IGNORECASE)
        if match:
            val = int(match.group(1))
            unit = match.group(2)
            task = match.group(3).strip()
            due_time = datetime.now() + (timedelta(minutes=val) if "minute" in unit else timedelta(hours=val))
            return task, due_time

        # fallback: anything after "remind me to"
        match = re.search(r"remind me to (.+)", text, re.IGNORECASE)
        if match:
            task = match.group(1).strip()
            due_time = datetime.now() + timedelta(minutes=5)
            return task, due_time

            # default fallback
        return "Reminder", datetime.now() + timedelta(minutes=5)
