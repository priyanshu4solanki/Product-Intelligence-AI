from sklearn.feature_extraction.text import TfidfVectorizer


def _filter_phrases(sorted_scores, top_n):
    results = []

    for phrase, score in sorted_scores:

        words = phrase.split()

        # Require 2–4 word phrases
        if len(words) < 2 or len(words) > 4:
            continue

        # Skip phrases containing digits
        if any(c.isdigit() for c in phrase):
            continue

        # Skip repeated-word phrases
        if len(set(words)) == 1:
            continue

        results.append((phrase, score))

        if len(results) >= top_n:
            break

    return results


def extract_keywords(reviews, top_n=10):

    texts = [r["review"] for r in reviews if r.get("review")]

    if not texts:
        return []

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(2, 4),
        max_features=3000,
        min_df=3
    )

    X = vectorizer.fit_transform(texts)

    scores = zip(
        vectorizer.get_feature_names_out(),
        X.sum(axis=0).tolist()[0]
    )

    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)

    return _filter_phrases(sorted_scores, top_n)


def extract_negative_topics(reviews, top_n=10):

    negatives = [
        r["review"]
        for r in reviews
        if r.get("sentiment") == "negative"
    ]

    if not negatives:
        return []

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(2, 4),
        max_features=3000,
        min_df=2
    )

    X = vectorizer.fit_transform(negatives)

    scores = zip(
        vectorizer.get_feature_names_out(),
        X.sum(axis=0).tolist()[0]
    )

    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)

    return _filter_phrases(sorted_scores, top_n)