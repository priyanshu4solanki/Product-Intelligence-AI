from scrapers.review_collector import collect_reviews
from database.review_store import save_review
from nlp_pipeline.sentiment_model import analyze_sentiment
from scrapers.text_cleaner import clean_text
from utils.json_exporter import export_reviews_json
from sklearn.feature_extraction.text import TfidfVectorizer
from insights.insight_generator import generate_insights


def normalize_product_name(name):
    if not name:
        return name

    name = name.strip().lower()

    remove_words = ["ai", "app", "tool"]
    words = [w for w in name.split() if w not in remove_words]

    name = " ".join(words)

    return name.title()


def extract_keywords(texts, top_n=10):

    if not texts:
        return []

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(2, 3),  # improved topics
        max_features=1000
    )

    X = vectorizer.fit_transform(texts)

    scores = zip(
        vectorizer.get_feature_names_out(),
        X.sum(axis=0).tolist()[0]
    )

    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)

    return sorted_scores[:top_n]


def run_pipeline(product):

    product = normalize_product_name(product)

    reviews = collect_reviews(product)

    if not reviews:
        print("No reviews found from any source.")
        return

    stored = 0
    skipped = 0

    positive = 0
    negative = 0
    neutral = 0

    source_counts = {}

    processed_reviews = []

    for review in reviews:

        text = clean_text(review.get("review", ""))

        if not text or len(text) < 50:
            continue

        review["product"] = product
        review["review"] = text

        source = review.get("source", "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1

        label, score = analyze_sentiment(text)

        review["sentiment"] = label
        review["sentiment_score"] = score

        saved = save_review(review)

        if saved:
            stored += 1
        else:
            skipped += 1

        processed_reviews.append({
            "source": source,
            "review": text,
            "sentiment": label
        })

        if label == "positive":
            positive += 1
        elif label == "negative":
            negative += 1
        else:
            neutral += 1

    # -------- Topic Extraction --------

    all_texts = [r["review"] for r in processed_reviews]

    negative_texts = [
        r["review"] for r in processed_reviews
        if r["sentiment"] == "negative"
    ]

    topics = extract_keywords(all_texts, 8)
    complaints = extract_keywords(negative_texts, 8)

    # -------- FIXED SUMMARY --------

    total_reviews = positive + negative + neutral

    summary = {
        "total_reviews": total_reviews,
        "positive": positive,
        "negative": negative,
        "neutral": neutral
    }

    # -------- Export JSON --------

    export_reviews_json(
        product,
        processed_reviews,
        summary,
        source_counts,
        topics,
        complaints
    )

    filename = product.lower().replace(" ", "_")
    json_file = f"data/{filename}_analysis.json"

    print(f"\nJSON file generated: {json_file}")

    # -------- AI Insight Generation --------

    print("\nGenerating AI insights...\n")

    generate_insights(product)

    # -------- Output --------

    print("\n------ Pipeline Summary ------")

    print("\nProduct:", product)

    print("\nSource Breakdown:")
    for source, count in source_counts.items():
        print(f"{source}: {count} reviews collected")

    print("\nDatabase Status")
    print("New Reviews Stored:", stored)
    print("Duplicates Skipped:", skipped)

    print("\nSentiment Summary")
    print("Positive:", positive)
    print("Negative:", negative)
    print("Neutral:", neutral)

    print("\nTop Discussion Topics")
    for word, _ in topics:
        print("-", word)

    print("\nTop Complaint Topics")
    for word, _ in complaints:
        print("-", word)

    print("\nPipeline completed")


if __name__ == "__main__":

    product = input("Enter product name: ")
    run_pipeline(product)