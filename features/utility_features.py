from datetime import datetime
import random
import requests
import json

class UtilityFeatures:
    def __init__(self):
        self.jokes_cache = []
        self.weather_api_key = None  # Set your API key
        
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
        # Using OpenWeatherMap API (you need to sign up for free API key)
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
            return f"Unable to fetch weather data. Please check your internet connection or set up weather API key."
        elif language == "hi":
            return f"मौसम की जानकारी प्राप्त नहीं की जा सकी। कृपया इंटरनेट कनेक्शन जांचें।"
        elif language == "kn":
            return f"ಹವಾಮಾನ ಮಾಹಿತಿ ಪಡೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ। ದಯವಿಟ್ಟು ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕ ಪರಿಶೀಲಿಸಿ।"
    
    def tell_joke(self, language="en"):
        """Tell a random joke"""
        jokes = {
            "en": [
                "Why don't scientists trust atoms? Because they make up everything!",
                "Why did the scarecrow win an award? He was outstanding in his field!",
                "Why don't eggs tell jokes? They'd crack each other up!",
                "What do you call a bear with no teeth? A gummy bear!",
                "Why did the bicycle fall over? Because it was two-tired!",
                "What do you call a fake noodle? An impasta!",
                "Why couldn't the bicycle stand up by itself? It was two tired!",
                "What did the ocean say to the beach? Nothing, it just waved!",
            ],
            "hi": [
                "टीचर: बताओ, अगर तुम्हारे पास 10 आम हैं और तुम 5 खा लेते हो, तो क्या बचेगा? छात्र: पेट दर्द!",
                "पत्नी: आप मुझसे इतना प्यार क्यों करते हैं? पति: क्योंकि तुम्हारे अलावा कोई मुझे बर्दाश्त ही नहीं करता!",
                "डॉक्टर: आपको हंसना चाहिए, यह सेहत के लिए अच्छा है। मरीज: लेकिन डॉक्टर साहब, आपकी फीस देखकर रोना आता है!",
                "बेटा: पापा, मैं बड़ा होकर पायलट बनूंगा! पापा: बेटा, दोनों एक साथ नहीं हो सकते!",
            ],
            "kn": [
                "ಶಿಕ್ಷಕರು: ನಿಮ್ಮ ಬಳಿ 10 ಮಾವಿನ ಹಣ್ಣುಗಳಿದ್ದರೆ ಮತ್ತು ನೀವು 5 ತಿಂದರೆ, ಏನು ಉಳಿಯುತ್ತದೆ? ವಿದ್ಯಾರ್ಥಿ: ಹೊಟ್ಟೆ ನೋವು!",
                "ಪತಿ: ನಾನು ನಿನ್ನನ್ನು ತುಂಬಾ ಪ್ರೀತಿಸುತ್ತೇನೆ. ಪತ್ನಿ: ಯಾಕೆ? ಪತಿ: ನಿನ್ನ ಹೊರತು ಬೇರೆ ಯಾರೂ ನನ್ನನ್ನು ಸಹಿಸುವುದಿಲ್ಲ!",
                "ಡಾಕ್ಟರ್: ನೀವು ನಗಬೇಕು, ಅದು ಆರೋಗ್ಯಕ್ಕೆ ಒಳ್ಳೆಯದು. ರೋಗಿ: ಆದರೆ ಡಾಕ್ಟರ್, ನಿಮ್ಮ ಫೀಸ್ ನೋಡಿದರೆ ಅಳುವುದು ಬರುತ್ತದೆ!",
            ]
        }
        
        joke_list = jokes.get(language, jokes["en"])
        return random.choice(joke_list)
    
    def get_news(self, language="en", country="in"):

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
                    return "यहाँ शीर्ष समाचार हैं: " + " ".join(headlines)
                elif language == "kn":
                    return "ಇಲ್ಲಿ ಪ್ರಮುಖ ಸುದ್ದಿಗಳಿವೆ: " + " ".join(headlines)
            else:
                return self._get_mock_news(language)
        except:
            return self._get_mock_news(language)

    def _get_mock_news(self, language):
        if language == "en":
            return "Unable to fetch news. Please check your internet connection or set up news API key."
        elif language == "hi":
            return "समाचार प्राप्त नहीं किया जा सका। कृपया इंटरनेट कनेक्शन जांचें।"
        elif language == "kn":
            return "ಸುದ್ದಿ ಪಡೆಯಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ। ದಯವಿಟ್ಟು ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕ ಪರಿಶೀಲಿಸಿ।"

    def set_weather_api_key(self, api_key):
        """Set weather API key"""
        self.weather_api_key = api_key