from transformers import pipeline

print("Loading sentiment model...")

sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest"
)

print("Model loaded successfully")


def analyze_sentiment(text):

    text = text[:512]  # transformer token limit safety

    result = sentiment_pipeline(text)[0]

    label_map = {
        "LABEL_0": "negative",
        "LABEL_1": "neutral",
        "LABEL_2": "positive",
        "negative": "negative",
        "neutral": "neutral",
        "positive": "positive"
    }

    label = label_map.get(result["label"], "neutral")
    score = float(result["score"])

    return label, score