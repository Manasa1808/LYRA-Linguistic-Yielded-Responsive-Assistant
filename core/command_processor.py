# command_processor.py
import re
from thefuzz import fuzz, process
import json

class CommandProcessor:
    def __init__(self):
        self.intents = self.load_intents()
        
        # Try to load NLTK, but handle gracefully if not available
        try:
            from nltk.tokenize import word_tokenize
            from nltk.corpus import stopwords
            self.word_tokenize = word_tokenize
            self.stop_words = set(stopwords.words('english'))
            self.nltk_available = True
        except (ImportError, LookupError) as e:
            print(f"⚠️ NLTK not fully available: {e}")
            self.word_tokenize = lambda x: x.lower().split()
            self.stop_words = {'the', 'a', 'an', 'to', 'in', 'on', 'at', 'for'}
            self.nltk_available = False
        
        # ✅ NEW: Romanization mappings for Kannada commands
        self.kannada_romanization = {
            # Time queries
            "samaya": "ಸಮಯ",
            "samay": "ಸಮಯ",
            "time": "ಸಮಯ",
            "enu": "ಏನು",
            "yenu": "ಏನು",
            "eenu": "ಏನು",
            
            # App commands
            "tere": "ತೆರೆ",
            "there": "ತೆರೆ",
            "open": "ತೆರೆ",
            "muchu": "ಮುಚ್ಚು",
            "close": "ಮುಚ್ಚು",
            
            # Calculator
            "calculator": "ಕ್ಯಾಲ್ಕುಲೇಟರ್",
            "calc": "ಕ್ಯಾಲ್ಕುಲೇಟರ್",
            "kalkulater": "ಕ್ಯಾಲ್ಕುಲೇಟರ್",
            
            # Reminders
            "nenapisu": "ನೆನಪಿಸು",
            "remind": "ನೆನಪಿಸು",
            "reminder": "ರಿಮೈಂಡರ್",
        }
        
        # ✅ NEW: Hindi romanization mappings
        self.hindi_romanization = {
            "samay": "समय",
            "time": "समय",
            "kya": "क्या",
            "hai": "है",
            "kholo": "खोलो",
            "open": "खोलो",
            "band": "बंद",
            "close": "बंद",
            "calculator": "कैलकुलेटर",
            "yaad": "याद",
            "remind": "याद",
        }
        
    def normalize_romanized_text(self, text, language='en'):
        """
        ✅ NEW: Convert romanized Kannada/Hindi to native script
        Example: "samaya enu" → "ಸಮಯ ಏನು"
        """
        if language == 'kn':
            # Normalize Kannada romanization
            words = text.lower().split()
            normalized_words = []
            for word in words:
                # Check if word is romanized
                if word in self.kannada_romanization:
                    normalized_words.append(self.kannada_romanization[word])
                else:
                    normalized_words.append(word)
            return ' '.join(normalized_words)
        
        elif language == 'hi':
            # Normalize Hindi romanization
            words = text.lower().split()
            normalized_words = []
            for word in words:
                if word in self.hindi_romanization:
                    normalized_words.append(self.hindi_romanization[word])
                else:
                    normalized_words.append(word)
            return ' '.join(normalized_words)
        
        return text
    
    def load_intents(self):
        """Define command intents and patterns with multilingual support"""
        return {
            "open_app": {
                "patterns": [
                    r"open\s+(.+)",
                    r"launch\s+(.+)",
                    r"start\s+(.+)",
                    r"run\s+(.+)",
                    r"खोलो\s+(.+)",
                    r"शुरू करो\s+(.+)",
                    r"चलाओ\s+(.+)",
                    r"ತೆರೆ\s+(.+)",
                    r"ಪ್ರಾರಂಭಿಸು\s+(.+)",
                    # ✅ NEW: Romanized patterns
                    r"tere\s+(.+)",
                    r"there\s+(.+)",
                ],
                "keywords": ["open", "launch", "start", "run", "खोलो", "शुरू", "चलाओ", "ತೆರೆ", "ಪ್ರಾರಂಭಿಸು", "tere", "there"]
            },
            "close_app": {
                "patterns": [
                    r"close\s+(.+)",
                    r"quit\s+(.+)",
                    r"exit\s+(.+)",
                    r"stop\s+(.+)",
                    r"बंद करो\s+(.+)",
                    r"रोको\s+(.+)",
                    r"ಮುಚ್ಚು\s+(.+)",
                    r"ನಿಲ್ಲಿಸು\s+(.+)",
                    # ✅ NEW: Romanized patterns
                    r"muchu\s+(.+)",
                    r"band\s+(.+)",
                ],
                "keywords": ["close", "quit", "exit", "stop", "बंद", "रोको", "ಮುಚ್ಚು", "ನಿಲ್ಲಿಸು", "muchu", "band"]
            },
            "create_reminder": {
                "patterns": [
                    r"remind me to (.+) at (.+)",
                    r"set reminder for (.+)",
                    r"add reminder (.+)",
                    r"मुझे याद दिलाओ (.+)",
                    r"रिमाइंडर सेट करो (.+)",
                    r"ನನಗೆ ನೆನಪಿಸು (.+)",
                    r"ರಿಮೈಂಡರ್ ಸೆಟ್ ಮಾಡ (.+)",
                    # ✅ NEW: Romanized patterns
                    r"nenapisu (.+)",
                    r"yaad dilao (.+)",
                ],
                "keywords": ["remind", "reminder", "remember", "याद", "रिमाइंडर", "ನೆನಪಿಸು", "ರಿಮೈಂಡರ್", "nenapisu", "yaad"]
            },
            "create_event": {
                "patterns": [
                    r"schedule (.+) at (.+)",
                    r"add event (.+)",
                    r"create meeting (.+)",
                    r"मीटिंग बनाओ (.+)",
                    r"इवेंट जोड़ो (.+)",
                    r"ಸಭೆ ರಚಿಸು (.+)",
                    r"ಈವೆಂಟ್ ಸೇರಿಸು (.+)",
                ],
                "keywords": ["schedule", "event", "meeting", "appointment", "calendar"]
            },
            "create_note": {
                "patterns": [
                    r"take note (.+)",
                    r"create note (.+)",
                    r"write note (.+)",
                    r"note (.+)",
                    r"नोट बनाओ (.+)",
                    r"लिखो (.+)",
                    r"ನೋಟ್ ಮಾಡ (.+)",
                    r"ಬರೆ (.+)",
                ],
                "keywords": ["note", "write", "save"]
            },
            "search_note": {
                "patterns": [
                    r"find note (.+)",
                    r"search note (.+)",
                    r"show notes about (.+)",
                    r"नोट खोजो (.+)",
                    r"नोट दिखाओ (.+)",
                    r"ನೋಟ್ ಹುಡುಕು (.+)",
                    r"ನೋಟ್ ತೋರಿಸು (.+)",
                ],
                "keywords": ["find", "search", "show notes"]
            },
            "send_email": {
                "patterns": [
                    r"send email to (.+?) (?:subject|about|saying)?\s*(.+)?",
                    r"email (.+?) (?:about|saying)?\s*(.+)?",
                    r"ईमेल भेजो (.+)",
                    r"मेल करो (.+)",
                    r"ಇಮೇಲ್ ಕಳುಹಿಸು (.+)",
                ],
                "keywords": ["send email", "email", "compose"]
            },
            "send_whatsapp": {
                "patterns": [
                    # ✅ FIXED: Better patterns for WhatsApp
                    r"send\s+(.+?)\s+(?:whatsapp|via whatsapp|on whatsapp)\s+to\s+(.+)",
                    r"whatsapp\s+(.+?)\s+to\s+(.+)",
                    r"message\s+(.+?)\s+to\s+(.+?)\s+(?:on|via)?\s*whatsapp",
                    r"send\s+whatsapp\s+(?:message\s+)?to\s+(.+?)\s+saying\s+(.+)",
                    r"व्हाट्सअप (.+?) को (.+)",
                    r"मैसेज करो (.+)",
                    r"ವಾಟ್ಸಾಪ್ ಕಳುಹಿಸು (.+)",
                ],
                "keywords": ["whatsapp", "message"]
            },
            "read_pdf": {
                "patterns": [
                    r"read pdf (.+)",
                    r"open pdf (.+)",
                    r"read document (.+)",
                    r"पीडीएफ पढ़ो (.+)",
                    r"डॉक्युमेंट पढ़ो (.+)",
                    r"ಪಿಡಿಎಫ್ ಓದು (.+)",
                ],
                "keywords": ["read pdf", "read document", "pdf"]
            },
            "get_time": {
                "patterns": [
                    r"what time is it",
                    r"what's the time",
                    r"tell me the time",
                    r"current time",
                    r"समय क्या है",
                    r"टाइम बताओ",
                    r"अभी कितने बजे हैं",
                    r"ಸಮಯ ಏನು",
                    r"ಟೈಮ್ ಹೇಳು",
                    r"ಈಗ ಎಷ್ಟು ಗಂಟೆ",
                    # ✅ NEW: Romanized patterns
                    r"samaya\s+(?:enu|yenu|eenu)",
                    r"samay\s+(?:enu|yenu|kya)",
                    r"time\s+(?:enu|kya|hai)",
                ],
                "keywords": ["time", "clock", "समय", "टाइम", "ಸಮಯ", "samaya", "samay"]
            },
            "get_date": {
                "patterns": [
                    r"what's the date",
                    r"what day is it",
                    r"tell me the date",
                    r"today's date",
                    r"तारीख क्या है",
                    r"आज की तारीख",
                    r"कौन सा दिन है",
                    r"ದಿನಾಂಕ ಏನು",
                    r"ಇಂದಿನ ದಿನಾಂಕ",
                    r"ಯಾವ ದಿನ",
                ],
                "keywords": ["date", "day", "today", "तारीख", "दिन", "ದಿನಾಂಕ"]
            },
            "get_weather": {
                "patterns": [
                    r"what's the weather",
                    r"weather forecast",
                    r"how's the weather",
                    r"temperature today",
                    r"मौसम कैसा है",
                    r"आज का मौसम",
                    r"ತಾಪಮಾನ ಎಷ್ಟು",
                ],
                "keywords": ["weather", "temperature", "forecast"]
            },
            # Add these patterns to the load_intents() method in CommandProcessor class

            "tell_joke": {
                "patterns": [
                    r"tell me a joke",
                    r"tell a joke",
                    r"make me laugh",
                    r"say something funny",
                    r"joke",
                    r"i'm bored",
                    r"i am bored",
                    r"entertain me",
                    r"bore ho gaya",
                    r"bore ho raha",
                    r"मुझे बोर हो रहा है",
                    r"मजा नहीं आ रहा",
                    r"जोक सुनाओ",
                    r"मुझे हंसाओ",
                    r"कुछ मजेदार बताओ",
                    r"ನನಗೆ ಬೇಸರವಾಗಿದೆ",
                    r"ನನಗೆ ಬೋರ್ ಆಗಿದೆ",
                    r"ಜೋಕ್ ಹೇಳು",
                    r"ನನ್ನನ್ನು ನಗಿಸು",
                    r"ಏನಾದರೂ ಮಜೇದಾರ ಹೇಳು",
                ],
                "keywords": ["joke", "funny", "laugh", "bored", "entertain", "bore", "मजा", "हंसाओ", "ಮಜೇದಾರ", "ನಗಿಸು"]
            },
            "get_news": {
                "patterns": [
                    r"what's the news",
                    r"latest news",
                    r"news headlines",
                    r"tell me the news",
                    r"न्यूज़ क्या है",
                    r"समाचार सुनाओ",
                    r"ಸುದ್ದಿ ಏನು",
                ],
                "keywords": ["news", "headlines", "latest"]
            },
            "system_command": {
                "patterns": [
                    r"shutdown",
                    r"restart",
                    r"sleep",
                    r"बंद करो",
                    r"शटडाउन",
                    r"रीस्टार्ट",
                    r"ಷಟ್‌ಡೌನ್",
                    r"ಮರುಪ್ರಾರಂಭ",
                ],
                "keywords": ["shutdown", "restart", "sleep"]
            }
            
        }
    
    def preprocess_text(self, text):
        """Clean and normalize text"""
        text = text.lower().strip()
        tokens = self.word_tokenize(text)
        
        # Remove stop words but keep important ones for commands
        important_words = {'open', 'close', 'send', 'read', 'create', 'find'}
        tokens = [w for w in tokens if w not in self.stop_words or w in important_words]
        
        return text, tokens
    
    def detect_intent(self, text):
        """Detect command intent using pattern matching and fuzzy matching"""
        original_text, tokens = self.preprocess_text(text)
        
        best_match = {
            "intent": None,
            "confidence": 0,
            "entities": {}
        }
        
        # Pattern matching (highest priority)
        for intent_name, intent_data in self.intents.items():
            for pattern in intent_data["patterns"]:
                match = re.search(pattern, original_text, re.IGNORECASE)
                if match:
                    best_match["intent"] = intent_name
                    best_match["confidence"] = 0.95
                    best_match["entities"] = {f"entity_{i}": (g.strip() if g else "") for i, g in enumerate(match.groups())}
                    return best_match
        
        # Keyword fuzzy matching fallback
        for intent_name, intent_data in self.intents.items():
            for keyword in intent_data["keywords"]:
                ratio = fuzz.partial_ratio(keyword, original_text)
                if ratio > 80 and ratio > best_match["confidence"] * 100:
                    best_match["intent"] = intent_name
                    best_match["confidence"] = ratio / 100
        
        return best_match
    
    def extract_entities(self, text, intent):
        """Extract relevant entities based on intent - FIXED VERSION"""
        entities = {}
        
        if intent in ("open_app", "close_app"):
            # ✅ FIXED: Better app name extraction
            words = text.lower().split()
            action_words = ['open', 'close', 'launch', 'quit', 'start', 'stop', 'exit', 
                           'tere', 'there', 'muchu', 'band', 'खोलो', 'बंद', 'ತೆರೆ', 'ಮುಚ್ಚು']
            
            for i, word in enumerate(words):
                if word in action_words and i + 1 < len(words):
                    # Get the next word as app name
                    app_name = words[i + 1]
                    # Remove common suffixes
                    app_name = app_name.replace('.', '').replace(',', '')
                    entities["app_name"] = app_name
                    print(f"🔍 Extracted app_name: '{app_name}' from text: '{text}'")
                    break
        
        elif intent == "create_reminder":
            patterns = [
                r"remind me to (.+?)(?: at| on| in)?\s*(.+)?",
                r"मुझे याद दिलाओ (.+?)(?: को| में)?\s*(.+)?",
                r"ನನಗೆ ನೆನಪಿಸು (.+?)(?: ನಲ್ಲಿ)?\s*(.+)?",
                r"nenapisu (.+)",
                r"yaad dilao (.+)",
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    entities["task"] = match.group(1).strip()
                    entities["time"] = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else "later"
                    break

        elif intent == "send_email":
            match = re.search(r"to\s+(.+?)(?: saying| about| subject)?\s*(.+)?", text, re.IGNORECASE)
            if match:
                entities["recipient"] = match.group(1).strip()
                entities["content"] = match.group(2).strip() if match.group(2) else ""
        
        elif intent == "send_whatsapp":
            # ✅ FIXED: Better WhatsApp parsing
            # Pattern 1: "send <message> whatsapp to <contact>"
            match = re.search(r"send\s+(.+?)\s+(?:whatsapp|via whatsapp)\s+to\s+(.+)", text, re.IGNORECASE)
            if match:
                entities["message"] = match.group(1).strip()
                entities["contact"] = match.group(2).strip()
                print(f"🔍 WhatsApp - contact: '{entities['contact']}', message: '{entities['message']}'")
            else:
                # Pattern 2: "whatsapp <message> to <contact>"
                match = re.search(r"whatsapp\s+(.+?)\s+to\s+(.+)", text, re.IGNORECASE)
                if match:
                    entities["message"] = match.group(1).strip()
                    entities["contact"] = match.group(2).strip()
                    print(f"🔍 WhatsApp - contact: '{entities['contact']}', message: '{entities['message']}'")
                else:
                    # Pattern 3: "message <name> on whatsapp <message>"
                    match = re.search(r"message\s+(.+?)\s+on\s+whatsapp\s+(.+)", text, re.IGNORECASE)
                    if match:
                        entities["contact"] = match.group(1).strip()
                        entities["message"] = match.group(2).strip()
                        print(f"🔍 WhatsApp - contact: '{entities['contact']}', message: '{entities['message']}'")
        
        elif intent == "get_weather":
            match = re.search(r"weather (?:in|at|for)?\s*([A-Za-z\s]+)", text, re.IGNORECASE)
            if match:
                entities["city"] = match.group(1).strip()
        
        return entities
    
    def process_command(self, text):
        """Main command processing pipeline"""
        original_text = text.strip()
        detection = self.detect_intent(original_text)
        
        result = {
            "intent": detection.get("intent"),
            "confidence": detection.get("confidence", 0),
            "entities": detection.get("entities", {}),
            "original_text": original_text
        }
        
        if result["intent"] and result["confidence"] > 0.6:
            extracted = self.extract_entities(original_text, result["intent"])
            extracted.update(result["entities"])
            result["entities"] = extracted
            return result
        
        return {
            "intent": "unknown",
            "confidence": 0,
            "entities": {},
            "original_text": original_text
        }