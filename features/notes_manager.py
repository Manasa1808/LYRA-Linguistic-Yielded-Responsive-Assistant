# notes_manager.py - Windows Compatible with Multilingual Support
from database.db_manager import DatabaseManager
from datetime import datetime
import json
import platform

class NotesManager:
    def __init__(self, db_manager):
        self.db = db_manager
        self.platform = platform.system()

    def create_note(self, user_id, title, content, tags=None, language='en'):
        """Create a new note with multilingual support"""
        
        print(f"\n{'='*60}")
        print(f"📝 CREATING NOTE")
        print(f"{'='*60}")
        print(f"👤 User ID: {user_id}")
        print(f"📌 Title: {title}")
        print(f"📄 Content: {content[:50]}..." if len(content) > 50 else f"📄 Content: {content}")
        print(f"🏷️  Tags: {tags}")
        print(f"{'='*60}")
        
        try:
            tags_str = json.dumps(tags) if tags else None
            
            query = '''
                INSERT INTO notes (user_id, title, content, tags, updated_at)
                VALUES (?, ?, ?, ?, ?)
            '''
            self.db.execute_query(query, (user_id, title, content, tags_str, datetime.now()))
            
            success_messages = {
                'en': f"Note created successfully: {title}",
                'hi': f"नोट सफलतापूर्वक बनाया गया: {title}",
                'kn': f"ನೋಟ್ ಯಶಸ್ವಿಯಾಗಿ ರಚಿಸಲಾಗಿದೆ: {title}"
            }
            success_msg = success_messages.get(language, success_messages['en'])
            print(f"✅ {success_msg}")
            print(f"{'='*60}\n")
            
            return True, success_msg
        except Exception as e:
            error_messages = {
                'en': f"Failed to create note: {str(e)}",
                'hi': f"नोट बनाने में विफल: {str(e)}",
                'kn': f"ನೋಟ್ ರಚಿಸಲು ವಿಫಲವಾಗಿದೆ: {str(e)}"
            }
            error_msg = error_messages.get(language, error_messages['en'])
            print(f"❌ {error_msg}")
            print(f"{'='*60}\n")
            return False, error_msg

    def search_notes(self, user_id, search_term, language='en'):
        """Search notes by title, content, or tags"""
        
        print(f"\n{'='*60}")
        print(f"🔍 SEARCHING NOTES")
        print(f"{'='*60}")
        print(f"👤 User ID: {user_id}")
        print(f"🔎 Search term: {search_term}")
        print(f"{'='*60}")
        
        try:
            query = '''
                SELECT note_id, title, content, tags, updated_at FROM notes
                WHERE user_id = ? AND (
                    title LIKE ? OR
                    content LIKE ? OR
                    tags LIKE ?
                )
                ORDER BY updated_at DESC
            '''
            search_pattern = f"%{search_term}%"
            results = self.db.execute_query(query, (user_id, search_pattern, search_pattern, search_pattern))
            
            if results:
                print(f"✅ Found {len(results)} notes")
                print(f"{'='*60}\n")
                
                notes_list = []
                for row in results:
                    notes_list.append({
                        'note_id': row[0],
                        'title': row[1],
                        'content': row[2],
                        'tags': row[3],
                        'updated_at': row[4]
                    })
                
                result_messages = {
                    'en': f"Found {len(results)} notes matching '{search_term}'",
                    'hi': f"'{search_term}' से मेल खाते {len(results)} नोट मिले",
                    'kn': f"'{search_term}' ಗೆ ಹೊಂದಿಕೆಯಾಗುವ {len(results)} ನೋಟ್‌ಗಳು ಕಂಡುಬಂದಿವೆ"
                }
                return True, result_messages.get(language, result_messages['en']), notes_list
            else:
                print(f"⚠️ No notes found")
                print(f"{'='*60}\n")
                
                no_result_messages = {
                    'en': f"No notes found matching '{search_term}'",
                    'hi': f"'{search_term}' से मेल खाने वाले कोई नोट नहीं मिले",
                    'kn': f"'{search_term}' ಗೆ ಹೊಂದಿಕೆಯಾಗುವ ನೋಟ್‌ಗಳು ಕಂಡುಬಂದಿಲ್ಲ"
                }
                return False, no_result_messages.get(language, no_result_messages['en']), []
        except Exception as e:
            error_messages = {
                'en': f"Failed to search notes: {str(e)}",
                'hi': f"नोट खोजने में विफल: {str(e)}",
                'kn': f"ನೋಟ್‌ಗಳನ್ನು ಹುಡುಕಲು ವಿಫಲವಾಗಿದೆ: {str(e)}"
            }
            error_msg = error_messages.get(language, error_messages['en'])
            print(f"❌ {error_msg}")
            print(f"{'='*60}\n")
            return False, error_msg, []

    def get_all_notes(self, user_id, language='en'):
        """Get all notes for a user"""
        
        print(f"📋 Fetching all notes for user {user_id}...")
        
        try:
            query = 'SELECT note_id, title, content, tags, updated_at FROM notes WHERE user_id = ? ORDER BY updated_at DESC'
            results = self.db.execute_query(query, (user_id,))
            
            if results:
                print(f"✅ Found {len(results)} notes")
                
                notes_list = []
                for row in results:
                    notes_list.append({
                        'note_id': row[0],
                        'title': row[1],
                        'content': row[2],
                        'tags': row[3],
                        'updated_at': row[4]
                    })
                
                result_messages = {
                    'en': f"You have {len(results)} notes",
                    'hi': f"आपके पास {len(results)} नोट हैं",
                    'kn': f"ನಿಮ್ಮ ಬಳಿ {len(results)} ನೋಟ್‌ಗಳಿವೆ"
                }
                return True, result_messages.get(language, result_messages['en']), notes_list
            else:
                no_notes_messages = {
                    'en': "You don't have any notes yet",
                    'hi': "आपके पास अभी तक कोई नोट नहीं है",
                    'kn': "ನಿಮ್ಮ ಬಳಿ ಇನ್ನೂ ಯಾವುದೇ ನೋಟ್‌ಗಳಿಲ್ಲ"
                }
                return False, no_notes_messages.get(language, no_notes_messages['en']), []
        except Exception as e:
            error_messages = {
                'en': f"Failed to fetch notes: {str(e)}",
                'hi': f"नोट प्राप्त करने में विफल: {str(e)}",
                'kn': f"ನೋಟ್‌ಗಳನ್ನು ಪಡೆಯಲು ವಿಫಲವಾಗಿದೆ: {str(e)}"
            }
            return False, error_messages.get(language, error_messages['en']), []

    def update_note(self, note_id, title=None, content=None, tags=None, language='en'):
        """Update an existing note"""
        
        print(f"\n{'='*60}")
        print(f"✏️ UPDATING NOTE")
        print(f"{'='*60}")
        print(f"📝 Note ID: {note_id}")
        print(f"{'='*60}")
        
        try:
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
            
            if not updates:
                no_update_messages = {
                    'en': "No changes to update",
                    'hi': "अपडेट करने के लिए कोई परिवर्तन नहीं",
                    'kn': "ನವೀಕರಿಸಲು ಯಾವುದೇ ಬದಲಾವಣೆಗಳಿಲ್ಲ"
                }
                return False, no_update_messages.get(language, no_update_messages['en'])
            
            updates.append("updated_at = ?")
            params.append(datetime.now())
            params.append(note_id)
            
            query = f"UPDATE notes SET {', '.join(updates)} WHERE note_id = ?"
            self.db.execute_query(query, tuple(params))
            
            success_messages = {
                'en': "Note updated successfully",
                'hi': "नोट सफलतापूर्वक अपडेट किया गया",
                'kn': "ನೋಟ್ ಯಶಸ್ವಿಯಾಗಿ ನವೀಕರಿಸಲಾಗಿದೆ"
            }
            success_msg = success_messages.get(language, success_messages['en'])
            print(f"✅ {success_msg}")
            print(f"{'='*60}\n")
            
            return True, success_msg
        except Exception as e:
            error_messages = {
                'en': f"Failed to update note: {str(e)}",
                'hi': f"नोट अपडेट करने में विफल: {str(e)}",
                'kn': f"ನೋಟ್ ನವೀಕರಿಸಲು ವಿಫಲವಾಗಿದೆ: {str(e)}"
            }
            error_msg = error_messages.get(language, error_messages['en'])
            print(f"❌ {error_msg}")
            print(f"{'='*60}\n")
            return False, error_msg

    def delete_note(self, note_id, language='en'):
        """Delete a note"""
        
        print(f"\n{'='*60}")
        print(f"🗑️ DELETING NOTE")
        print(f"{'='*60}")
        print(f"📝 Note ID: {note_id}")
        print(f"{'='*60}")
        
        try:
            query = 'DELETE FROM notes WHERE note_id = ?'
            self.db.execute_query(query, (note_id,))
            
            success_messages = {
                'en': "Note deleted successfully",
                'hi': "नोट सफलतापूर्वक हटाया गया",
                'kn': "ನೋಟ್ ಯಶಸ್ವಿಯಾಗಿ ಅಳಿಸಲಾಗಿದೆ"
            }
            success_msg = success_messages.get(language, success_messages['en'])
            print(f"✅ {success_msg}")
            print(f"{'='*60}\n")
            
            return True, success_msg
        except Exception as e:
            error_messages = {
                'en': f"Failed to delete note: {str(e)}",
                'hi': f"नोट हटाने में विफल: {str(e)}",
                'kn': f"ನೋಟ್ ಅಳಿಸಲು ವಿಫಲವಾಗಿದೆ: {str(e)}"
            }
            error_msg = error_messages.get(language, error_messages['en'])
            print(f"❌ {error_msg}")
            print(f"{'='*60}\n")
            return False, error_msg