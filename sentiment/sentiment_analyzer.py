from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class SentimentAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    def analyze(self, text):
        score = self.analyzer.polarity_scores(text)
        if score['compound'] > 0.05:
            return 1  # bullish
        elif score['compound'] < -0.05:
            return -1  # bearish
        else:
            return 0  # neutral

    def analyze_latest_news(self, asset):
        # Placeholder: Replace with real news fetching
        news_headline = f"Latest news about {asset}"
        return self.analyze(news_headline)