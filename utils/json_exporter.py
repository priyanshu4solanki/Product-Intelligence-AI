import json
import os
import random


def sample_reviews(reviews, sentiment, n=5):
    """
    Select representative reviews by sentiment
    to reduce token usage for LLM insight generation
    """

    filtered = [r["review"] for r in reviews if r["sentiment"] == sentiment]

    if len(filtered) <= n:
        return filtered

    return random.sample(filtered, n)


def export_reviews_json(product, reviews, summary, sources, topics, complaints):

    os.makedirs("data", exist_ok=True)

    # ---- Sample representative reviews ----

    positive_samples = sample_reviews(reviews, "positive", 6)
    negative_samples = sample_reviews(reviews, "negative", 6)
    neutral_samples = sample_reviews(reviews, "neutral", 4)

    # ---- Clean topics ----

    clean_topics = [t[0] for t in topics]
    clean_complaints = [c[0] for c in complaints]

    # ---- JSON Structure ----

    data = {
        "product": product,

        "summary": summary,

        "sources": sources,

        "top_topics": clean_topics,

        "top_complaints": clean_complaints,

        "representative_reviews": {
            "positive": positive_samples,
            "negative": negative_samples,
            "neutral": neutral_samples
        }
    }

    # ---- File name safe formatting ----

    filename = f"data/{product.lower().replace(' ', '_')}_analysis.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"\nJSON exported → {filename}")

    return filename