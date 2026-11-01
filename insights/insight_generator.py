import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-20b"


def generate_insights(product):
    filename = product.lower().replace(" ", "_")
    json_path = f"data/{filename}_analysis.json"

    if not os.path.exists(json_path):
        print("JSON file not found:", json_path)
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    summary = data.get("summary", {})
    sources = data.get("sources", {})
    topics = data.get("top_topics", [])
    complaints = data.get("top_complaints", [])
    reviews = data.get("representative_reviews", {})

    formatted_reviews = ""
    for sentiment, review_list in reviews.items():
        formatted_reviews += f"\n{sentiment.upper()} SAMPLES:\n"
        for r in review_list[:8]:
            formatted_reviews += f"- {r}\n"

    prompt =prompt = f"""
You are an executive product strategist and principal systems engineer conducting a commercial and technical audit of the product: "{product}".

The team building "{product}" has hired you to tell them exactly what is working, what is broken, and what concrete actions they must take to dominate their market.

AGGREGATED REVIEW SIGNALS:
- Total Reviews Analyzed: {summary.get('total_reviews', 0)}
- Sentiment Polarity Split: {summary.get('positive', 0)} Positive | {summary.get('negative', 0)} Negative | {summary.get('neutral', 0)} Neutral

DISCOVERED TOPICS & FEATURE CLUSTERS:
{topics}

DISCOVERED DEFECTS & FRICTION SIGNALS:
{complaints}

RAW USER FEEDBACK CORPUS:
{formatted_reviews}

CRITICAL DIRECTIVES:
1. FOCUS EXCLUSIVELY ON THE PRODUCT:
   - Provide recommendations ONLY for improving "{product}".
   - NEVER mention scrapers, APIs, data collection, sentiment pipelines, social monitoring tools, or external platforms (e.g., YouTube, Reddit, HackerNews, Trustpilot). Act as if the user feedback was delivered directly to the product team.
2. SUBSTANTIVE SPECIFICS OVER GENERIC LABELS:
   - NEVER repeat just the product name or category words (e.g., do NOT write "iPhone 15", "phone", "software").
   - Name explicit features, thermal states, workflow bottlenecks, pricing tiers, ergonomics, or failure modes directly mentioned by users.
3. HOLISTIC & OPEN-ENDED RECOMMENDATIONS:
   - Provide 5 to 7 concrete, high-impact recommendations for the makers of "{product}".
   - Cover diverse operational levers: engineering/firmware patches, positioning/narrative pivots, pricing/packaging models, user onboarding/misconceptions, and high-defensibility roadmap moats.
   - Each recommendation must name the specific problem it solves and the tactical fix.

Respond strictly in valid JSON using this exact schema:
{{
  "product_summary": "A sharp, 2-3 sentence commercial audit detailing what '{product}' is, its current market standing, and the core tension between user praise and user frustration.",
  "major_positive_points": [
    "Specific genuine capability, technical moat, or high-praise user delight point",
    "Second distinct capability or ergonomic advantage",
    "Third distinct capability or workflow strength",
    "Fourth distinct capability or delight point"
  ],
  "major_negative_points": [
    "Specific technical defect, thermal issue, bug, or hardware/software friction point",
    "Second distinct complaint or reliability failure",
    "Third distinct complaint or pricing/usability grievance",
    "Fourth distinct complaint or unmet expectation"
  ],
  "actionable_recommendations": [
    "Detailed action covering problem context, concrete fix, and expected business/retention impact.",
    "Detailed action...",
    "Detailed action...",
    "Detailed action...",
    "Detailed action..."
  ]
}}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a product intelligence analyst. Output strictly valid JSON without markdown fences."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        raw_content = response.choices[0].message.content
        insights_data = json.loads(raw_content)

        data["ai_dossier"] = insights_data
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        os.makedirs("reports", exist_ok=True)
        report_path = f"reports/{filename}_product_report.txt"

        pos_lines = "\n".join([f"- {p}" for p in insights_data.get("major_positive_points", [])])
        neg_lines = "\n".join([f"- {n}" for n in insights_data.get("major_negative_points", [])])
        rec_lines = "\n".join([f"{idx + 1}. {a}" for idx, a in enumerate(insights_data.get("actionable_recommendations", []))])

        readable_report = f"""PRODUCT INTELLIGENCE AUDIT: {product.upper()}

1. PRODUCT SUMMARY
{insights_data.get('product_summary', '')}

2. MAJOR POSITIVE ATTRIBUTES
{pos_lines}

3. MAJOR LAGGING & DEFECT POINTS
{neg_lines}

4. EXPLORATORY STRATEGIC RECOMMENDATIONS & INSIGHTS
{rec_lines}
"""

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(readable_report)

        print("\n------ Product Insight Report Generated ------\n")
        print(f"Report successfully saved to: {report_path}")

    except Exception as e:
        print("Error generating insights:", e)