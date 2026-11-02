import os

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


_vader = SentimentIntensityAnalyzer()
_roberta = None


def _roberta_sentiment(text):
    global _roberta

    if _roberta is None:
        try:
            from transformers import pipeline
        except ImportError as exc:
            raise RuntimeError(
                "RoBERTa sentiment requires the optional transformers and torch packages."
            ) from exc

        print("Loading optional RoBERTa sentiment model...")
        _roberta = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest"
        )
        print("RoBERTa model loaded successfully")

    result = _roberta(text[:512])[0]
    label_map = {
        "LABEL_0": "negative",
        "LABEL_1": "neutral",
        "LABEL_2": "positive",
        "negative": "negative",
        "neutral": "neutral",
        "positive": "positive"
    }
    return label_map.get(result["label"], "neutral"), float(result["score"])


def analyze_sentiment(text):
    if os.getenv("SENTIMENT_BACKEND", "vader").lower() == "roberta":
        return _roberta_sentiment(text)

    compound = _vader.polarity_scores(text[:400])["compound"]
    if compound >= 0.05:
        return "positive", abs(float(compound))
    if compound <= -0.05:
        return "negative", abs(float(compound))
    return "neutral", abs(float(compound))