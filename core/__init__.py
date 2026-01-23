def __init__(self):
    self.intents = self.load_intents()

    try:
        self.stop_words = set(stopwords.words('english'))
    except LookupError:
        import nltk
        nltk.download('stopwords')
        self.stop_words = set(stopwords.words('english'))
