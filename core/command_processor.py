#command_processor.py
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
        
    def load_intents(self):
        """Define command intents and patterns with multilingual support"""
        return {
            "open_app": {
                "patterns": [
                    r"open\s+(\w+)",
                    r"launch\s+(\w+)",
                    r"start\s+(\w+)",
                    r"run\s+(\w+)",
                    r"खोलो\s+(\w+)",
                    r"शुरू करो\s+(\w+)",
                    r"चलाओ\s+(\w+)",
                    r"ತೆರೆ\s+(\w+)",
                    r"ಪ್ರಾರಂಭಿಸು\s+(\w+)",
                ],
                "keywords": ["open", "launch", "start", "run", "खोलो", "शुरू", "चलाओ", "ತೆರೆ", "ಪ್ರಾರಂಭಿಸು"]
            },
            "close_app": {
                "patterns": [
                    r"close\s+(\w+)",
                    r"quit\s+(\w+)",
                    r"exit\s+(\w+)",
                    r"stop\s+(\w+)",
                    r"बंद करो\s+(\w+)",
                    r"रोको\s+(\w+)",
                    r"ಮುಚ್ಚು\s+(\w+)",
                    r"ನಿಲ್ಲಿಸು\s+(\w+)",
                ],
                "keywords": ["close", "quit", "exit", "stop", "बंद", "रोको", "ಮುಚ್ಚು", "ನಿಲ್ಲಿಸು"]
            },
            "create_reminder": {
                "patterns": [
                    r"remind me to (.+) at (.+)",
                    r"set reminder for (.+)",
                    r"add reminder (.+)",
                    r"मुझे याद दिलाओ (.+)",
                    r"रिमाइंडर सेट करो (.+)",
                    r"ನನಗೆ ನೆನಪಿಸು (.+)",
                    r"ರಿಮೈಂಡರ್ ಸೆಟ್ ಮಾಡು (.+)",
                ],
                "keywords": ["remind", "reminder", "remember", "याद", "रिमाइंडर", "ನೆನಪಿಸು", "ರಿಮೈಂಡರ್"]
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
                "keywords": ["schedule", "event", "meeting", "appointment"]
            },
            "create_note": {
                "patterns": [
                    r"take note (.+)",
                    r"create note (.+)",
                    r"write note (.+)",
                    r"note (.+)",
                    r"नोट बनाओ (.+)",
                    r"लिखो (.+)",
                    r"ನೋಟ್ ಮಾಡು (.+)",
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
                    r"send email to (.+)",
                    r"email (.+)",
                    r"compose email (.+)",
                    r"ईमेल भेजो (.+)",
                    r"मेल करो (.+)",
                    r"ಇಮೇಲ್ ಕಳುಹಿಸು (.+)",
                ],
                "keywords": ["send email", "email", "compose"]
            },
            "send_whatsapp": {
                "patterns": [
                    r"send whatsapp to (.+)",
                    r"whatsapp (.+)",
                    r"message (.+) on whatsapp",
                    r"व्हाट्सएप भेजो (.+)",
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
                    r"डॉक्यूमेंट पढ़ो (.+)",
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
                ],
                "keywords": ["time", "clock", "समय", "टाइम", "ಸಮಯ"]
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
            "tell_joke": {
                "patterns": [
                    r"tell me a joke",
                    r"make me laugh",
                    r"say something funny",
                    r"जोक सुनाओ",
                    r"मुझे हंसाओ",
                    r"ಜೋಕ್ ಹೇಳು",
                ],
                "keywords": ["joke", "funny", "laugh"]
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
                    r"ಷಟ್ಡೌನ್",
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
                    # capture groups may be None, ensure strings
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
        """Extract relevant entities based on intent"""
        entities = {}
        
        if intent in ("open_app", "close_app"):
            # Extract app name (grab next word after action verb)
            words = text.lower().split()
            action_words = ['open', 'close', 'launch', 'quit', 'start', 'stop', 'exit']
            for i, word in enumerate(words):
                if word in action_words and i + 1 < len(words):
                    entities["app_name"] = words[i + 1]
                    break
        
        elif intent == "create_reminder":
            patterns = [
            r"remind me to (.+?)(?: at| on| in)?\s*(.+)?",
            r"मुझे याद दिलाओ (.+?)(?: को| में)?\s*(.+)?",
            r"ನನಗೆ ನೆನಪಿಸು (.+?)(?: ನಲ್ಲಿ)?\s*(.+)?"
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    entities["task"] = match.group(1).strip()       # FULL task
                    entities["time"] = match.group(2).strip() if match.group(2) else "later"
                    break


        elif intent == "send_email":
            match = re.search(r"to\s+(.+?)(?: saying| about| that)?\s*(.+)?", text, re.IGNORECASE)
            if match:
                entities["recipient"] = match.group(1).strip()
                entities["content"] = match.group(2).strip() if match.group(2) else ""
        
        elif intent == "get_weather":
            # Try to pull city name if present: "weather in <city>"
            match = re.search(r"weather (?:in|at|for)?\s*([A-Za-z\s]+)", text, re.IGNORECASE)
            if match:
                entities["city"] = match.group(1).strip()
        
        return entities
    
    def process_command(self, text):
        """Main command processing pipeline"""
        original_text = text.strip()
        detection = self.detect_intent(original_text)
        
        # Always include the original text in the returned result
        result = {
            "intent": detection.get("intent"),
            "confidence": detection.get("confidence", 0),
            "entities": detection.get("entities", {}),
            "original_text": original_text
        }
        
        # If intent confident enough, extract entities + return
        if result["intent"] and result["confidence"] > 0.6:
            extracted = self.extract_entities(original_text, result["intent"])
            # Merge entities (detection groups have higher priority)
            extracted.update(result["entities"])
            result["entities"] = extracted
            return result
        
        # otherwise unknown
        return {
            "intent": "unknown",
            "confidence": 0,
            "entities": {},
            "original_text": original_text
        }
