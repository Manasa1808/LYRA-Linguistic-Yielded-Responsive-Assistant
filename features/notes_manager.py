#notes_manager.py
from database.db_manager import DatabaseManager
from datetime import datetime
import json

class NotesManager:
    def __init__(self, db_manager):  # FIXED CONSTRUCTOR
        self.db = db_manager

    def create_note(self, user_id, title, content, tags=None):
        """Create a new note"""
        tags_str = json.dumps(tags) if tags else None
        
        query = '''
            INSERT INTO notes (user_id, title, content, tags, updated_at)
            VALUES (?, ?, ?, ?, ?)
        '''
        self.db.execute_query(query, (user_id, title, content, tags_str, datetime.now()))
        return True, "Note created successfully"

    def search_notes(self, user_id, search_term):
        """Search notes by title, content, or tags"""
        query = '''
            SELECT * FROM notes
            WHERE user_id = ? AND (
                title LIKE ? OR
                content LIKE ? OR
                tags LIKE ?
            )
            ORDER BY updated_at DESC
        '''
        search_pattern = f"%{search_term}%"
        results = self.db.execute_query(query, (user_id, search_pattern, search_pattern, search_pattern))
        return results

    def get_all_notes(self, user_id):
        """Get all notes for a user"""
        query = 'SELECT * FROM notes WHERE user_id = ? ORDER BY updated_at DESC'
        return self.db.execute_query(query, (user_id,))

    def update_note(self, note_id, title=None, content=None, tags=None):
        """Update an existing note"""
        updates = []
        params = []
        
        if title:
            updates.append("title = ?")
            params.append(title)
        if content:
            updates.append("content = ?")
            params.append(content)
        if tags:
            updates.append("tags = ?")
            params.append(json.dumps(tags))
        
        updates.append("updated_at = ?")
        params.append(datetime.now())
        params.append(note_id)
        
        query = f"UPDATE notes SET {', '.join(updates)} WHERE note_id = ?"
        self.db.execute_query(query, tuple(params))
        return True, "Note updated successfully"

    def delete_note(self, note_id):
        """Delete a note"""
        query = 'DELETE FROM notes WHERE note_id = ?'
        self.db.execute_query(query, (note_id,))
        return True, "Note deleted successfully"
