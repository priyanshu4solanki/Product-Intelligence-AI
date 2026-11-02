import sys
import os
import json
import tempfile
import subprocess
from html import escape
from pathlib import Path

import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas

st.set_page_config(
    page_title="Product Intelligence AI",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────────────────────
# BRIEFING BINDER DESIGN SYSTEM
# ─────────────────────────────────────────────────────────────

INK = "#1C2B3A"
INK_SOFT = "#5B6472"
POSITIVE = "#2F7D5D"
NEGATIVE = "#8C3A4A"
OCHRE = "#C08A2E"
LINE = "#DDE1DA"
PAGE_BG = "#FFFFFF"
BACKDROP = "#E7E9E3"


def _usable_findings(items, product, fallback_reviews, label):
    product_words = {word.lower() for word in product.split() if len(word) > 2}
    usable = []
    for item in items if isinstance(items, list) else []:
        text = str(item).strip()
        words = text.split()
        if not text or len(words) < 4 or product.lower() in text.lower():
            continue
        if product_words and all(word in text.lower().split() for word in product_words):
            continue
        usable.append(text)
    if usable:
        return usable[:4]

    review_text = str(fallback_reviews[0]).strip() if fallback_reviews else ""
    if review_text and label == "weakness":
        return [f"Users report this problem: {review_text}"]
    if review_text:
        return ["Users repeatedly praise a core part of the experience."]
    return [f"No clear {label} pattern was found in the available feedback."]


def _render_finding_list(items, color, marker):
    row_class = "friction-row" if color == NEGATIVE else "finding-row"
    for item in items:
        st.markdown(
            f'<div class="{row_class}"><span class="mark" style="color:{color}">{marker}</span>'
            f'<span>{escape(str(item))}</span></div>',
            unsafe_allow_html=True,
        )


st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,500;0,600;1,500&family=Work+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

*, *::before, *::after {{
    box-sizing: border-box;
}}

html {{
    scroll-behavior: smooth;
}}

html, body, [class*="css"] {{
    font-family: 'Work Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    color: {INK} !important;
    text-align: left !important;
}}

.stApp {{
    background-color: {BACKDROP} !important;
}}

section.main > div.block-container {{
    max-width: 920px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}}

::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {BACKDROP}; }}
::-webkit-scrollbar-thumb {{ background: #C7CBC1; border-radius: 3px; }}

/* Binder index tabs as functional anchor links */
.tab-row {{
    display: flex;
    gap: 0.3rem;
    padding-left: 1.5rem;
}}
.tab {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.03em;
    padding: 0.5rem 1rem 0.4rem;
    border-radius: 6px 6px 0 0;
    border: 1px solid {LINE};
    border-bottom: none;
    color: {INK_SOFT} !important;
    background: #F2F3EF;
    display: inline-block;
    text-decoration: none !important;
    transition: all 0.15s ease-in-out;
}}
.tab:hover {{
    background: #EAECE6;
    color: {INK} !important;
}}
.tab.active {{
    background: {PAGE_BG};
    color: {INK} !important;
    font-weight: 600;
}}

/* The "page" surface */
.page-open {{
    background: {PAGE_BG};
    border: 1px solid {LINE};
    border-top: none;
    border-radius: 0 6px 0 0;
    padding: 2rem 2.2rem 0.2rem;
    margin-top: -1px;
}}
.page-close {{
    background: {PAGE_BG};
    border: 1px solid {LINE};
    border-top: none;
    border-radius: 0 0 6px 6px;
    padding: 0.2rem 2.2rem 1.8rem;
    margin-top: -1px;
}}
.page-mid {{
    background: {PAGE_BG};
    border-left: 1px solid {LINE};
    border-right: 1px solid {LINE};
    padding: 0 2.2rem;
}}
.query-row {{
    align-items: end;
}}

.meta-line {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: {INK_SOFT};
    letter-spacing: 0.03em;
    margin-bottom: 0.6rem;
}}
.doc-title {{
    font-family: 'Fraunces', serif;
    font-weight: 600;
    font-size: 2.1rem;
    margin: 0 0 0.3rem;
    color: {INK};
}}
.doc-subtitle {{
    color: {INK_SOFT};
    font-size: 0.95rem;
    margin-bottom: 0.4rem;
}}

/* Executive Summary Gist Box */
.summary-gist-box {{
    background: #FAFBF9;
    border: 1px solid {LINE};
    border-left: 3px solid {INK};
    border-radius: 4px;
    padding: 0.9rem 1.2rem;
    margin-top: 1.2rem;
    margin-bottom: 0.8rem;
}}
.gist-header {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    color: {INK_SOFT};
    text-transform: uppercase;
    margin-bottom: 0.35rem;
}}
.gist-body {{
    font-size: 0.9rem;
    line-height: 1.55;
    color: {INK};
}}

.section-label {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: {INK_SOFT};
    letter-spacing: 0.04em;
    margin: 1.8rem 0 0.8rem;
    scroll-margin-top: 20px;
}}

/* Sentiment summary */
.summary-total {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    color: {INK_SOFT};
    margin-bottom: 0.6rem;
}}
.stackbar {{
    display: flex;
    height: 14px;
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 0.5rem;
}}
.legend {{
    display: flex;
    gap: 1.6rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: {INK_SOFT};
}}
.legend b {{ color: {INK}; }}

/* Voice quotes */
blockquote.brief {{
    margin: 0;
    padding-left: 1rem;
    border-left: 3px solid {POSITIVE};
    font-family: 'Fraunces', serif;
    font-style: italic;
    font-size: 1.0rem;
    line-height: 1.5;
    color: {INK};
}}
blockquote.brief.negative {{ border-left-color: {NEGATIVE}; }}
.cite {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: {INK_SOFT};
    margin-top: 0.6rem;
    padding-left: 1rem;
}}

/* Findings */
.findings-list {{ list-style: none; margin: 0; padding: 0; }}
.findings-list li {{
    display: flex;
    gap: 0.6rem;
    padding: 0.55rem 0;
    border-bottom: 1px solid {LINE};
    font-size: 0.9rem;
}}
.findings-list li:last-child {{ border-bottom: none; }}
.finding-row,
.friction-row {{
    display: flex;
    gap: 0.6rem;
    padding: 0.65rem 0;
    margin-bottom: 0.45rem;
    padding: 0.75rem 0.85rem;
    border: 1px solid {LINE};
    border-left: 3px solid {POSITIVE};
    border-radius: 4px;
    background: #FFFFFF;
    color: {INK} !important;
    font-size: 0.9rem;
    line-height: 1.5;
}}
.finding-row {{
    border-left-color: {POSITIVE} !important;
}}
.finding-row .mark {{
    color: {POSITIVE} !important;
}}
.friction-row {{
    border-left-color: {NEGATIVE} !important;
    color: {INK} !important;
}}
.friction-row .mark,
.friction-row span {{
    color: {NEGATIVE} !important;
}}
.friction-row span:last-child {{
    color: {INK} !important;
}}
.mark {{ font-weight: 600; flex-shrink: 0; }}

/* Actions */
.actions {{ list-style: none; margin: 0; padding: 0; }}
.actions li {{
    display: flex;
    gap: 0.9rem;
    align-items: flex-start;
    padding: 0.6rem 0;
    margin-bottom: 0.55rem;
    padding: 0.8rem 0.9rem;
    border: 1px solid {LINE};
    border-radius: 4px;
    background: #FFFFFF;
    color: {INK} !important;
    font-size: 0.9rem;
    line-height: 1.55;
}}
.actions li > span:last-child {{
    color: {INK} !important;
}}
.pipeline-output {{
    background: #F7F8F5 !important;
    color: {INK} !important;
    border: 1px solid {LINE} !important;
}}
.stCode,
.stCode pre,
.stCode code {{
    background: #F7F8F5 !important;
    color: {INK} !important;
}}
.anum {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    background: {INK};
    color: #fff;
    border-radius: 50%;
    width: 22px; height: 22px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.stamp-text {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: {INK_SOFT};
    letter-spacing: 0.03em;
}}

/* Native input & button restyling */
.stTextInput input {{
    background: #FFFFFF !important;
    border: 1px solid {LINE} !important;
    border-bottom: 1.5px solid {INK} !important;
    border-radius: 4px !important;
    color: {INK} !important;
    -webkit-text-fill-color: {INK} !important;
    caret-color: {INK} !important;
    font-size: 1rem !important;
    padding: 0.65rem 0.75rem !important;
    height: 2.8rem !important;
}}
.stTextInput input::placeholder {{
    color: {INK_SOFT} !important;
    -webkit-text-fill-color: {INK_SOFT} !important;
    opacity: 1 !important;
}}
.input-label {{
    color: {INK} !important;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 0.35rem;
}}
.stTextInput label,
.stTextInput label p {{
    color: {INK} !important;
    font-weight: 600 !important;
    opacity: 1 !important;
}}
.stTextInput input:focus {{
    border-color: {INK} !important;
    box-shadow: 0 0 0 2px rgba(28, 43, 58, 0.12) !important;
}}
.stButton button {{
    background: {INK} !important;
    color: #ffffff !important;
    font-family: 'Work Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    border: none !important;
    border-radius: 4px !important;
    height: 2.7rem !important;
}}
.stButton button:hover {{
    background: #2A3E52 !important;
}}
.stDownloadButton button {{
    background: {INK} !important;
    border: none !important;
    color: #ffffff !important;
    font-family: 'Work Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    border-radius: 4px !important;
    height: 2.9rem !important;
}}
.stDownloadButton button:hover {{
    background: #2A3E52 !important;
}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# BINDER TABS (CLICKABLE ANCHOR LINKS) + PAGE HEADER
# ─────────────────────────────────────────────────────────────

st.markdown("""
<div class="tab-row">
    <a href="#tab-overview" class="tab active">Overview</a>
    <a href="#tab-voice" class="tab">Voice</a>
    <a href="#tab-findings" class="tab">Findings</a>
    <a href="#tab-actions" class="tab">Actions</a>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="page-open">', unsafe_allow_html=True)
st.markdown('<div class="meta-line">Prepared for leadership review</div>', unsafe_allow_html=True)
st.markdown('<div class="doc-title">Product Intelligence Briefing</div>', unsafe_allow_html=True)
st.markdown('<div class="doc-subtitle">Cross-channel sentiment diagnostics, failure-mode extraction, and turnaround strategy</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="page-mid query-row">', unsafe_allow_html=True)
query_col, trigger_col = st.columns([5, 1])
with query_col:
    st.markdown(
        '<div class="input-label">Product name</div>',
        unsafe_allow_html=True,
    )
    target_product = st.text_input(
        "Product name",
        placeholder="Enter target product (e.g., iPhone 15, Notion, Linear)",
        label_visibility="collapsed"
    )
with trigger_col:
    st.markdown('<div style="height: 1.65rem;"></div>', unsafe_allow_html=True)
    run_audit = st.button("Run audit", width="stretch")
st.markdown('</div>', unsafe_allow_html=True)

if run_audit and target_product:
    with st.spinner(f"Ingesting public telemetry and running NLP classification for '{target_product}'..."):
        repo_base = Path(__file__).resolve().parent.parent
        pipeline_result = subprocess.run(
            [sys.executable, str(repo_base / "main.py")],
            input=target_product,
            text=True,
            cwd=repo_base,
            capture_output=True
        )
    if pipeline_result.returncode != 0:
        st.error("The audit could not be completed. Review the pipeline output below.")
        if pipeline_result.stdout:
            st.code(pipeline_result.stdout, language="text")
        if pipeline_result.stderr:
            st.code(pipeline_result.stderr, language="text")
    elif "No reviews found from any source." in pipeline_result.stdout:
        st.warning("No usable public reviews were found for that product. Try a more specific or widely discussed product name.")
        st.code(pipeline_result.stdout, language="text")
    else:
        st.success("Audit complete.")
        if pipeline_result.stdout:
            with st.expander("Pipeline details"):
                st.code(pipeline_result.stdout, language="text")

# ─────────────────────────────────────────────────────────────
# LOAD PROCESSED DATA
# ─────────────────────────────────────────────────────────────

slug = target_product.lower().replace(" ", "_") if target_product else ""
analysis_path = f"data/{slug}_analysis.json"
report_path = f"reports/{slug}_product_report.txt"

if Path(analysis_path).exists():
    with open(analysis_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    metrics = data.get("summary", {})
    citations = data.get("representative_reviews", {})
    dossier = data.get("ai_dossier", {})

    total_n = metrics.get("total_reviews", 0)
    pos_n = metrics.get("positive", 0)
    neg_n = metrics.get("negative", 0)
    neu_n = metrics.get("neutral", 0)

    pos_pct = round(100 * pos_n / total_n) if total_n else 0
    neu_pct = round(100 * neu_n / total_n) if total_n else 0
    neg_pct = max(0, 100 - pos_pct - neu_pct) if total_n else 0

    pos_samples = citations.get("positive", [])
    top_pos = pos_samples[0] if pos_samples else "No positive feedback recorded."

    neg_samples = citations.get("negative", [])
    top_neg = neg_samples[0] if neg_samples else "No negative complaints recorded."

    positives = dossier.get("major_positive_points", [])
    if not positives:
        positives = [t[0] if isinstance(t, (list, tuple)) else t for t in data.get("top_topics", [])[:4]]

    negatives = dossier.get("major_negative_points", [])
    if not negatives:
        negatives = [c[0] if isinstance(c, (list, tuple)) else c for c in data.get("top_complaints", [])[:4]]

    positives = _usable_findings(positives, target_product, pos_samples, "strength")
    negatives = _usable_findings(negatives, target_product, neg_samples, "weakness")
    recommendations = dossier.get("actionable_recommendations", [])

    # Extract or synthesize executive summary / gist
    product_summary_text = dossier.get("product_summary")
    if not product_summary_text:
        product_summary_text = (
            f"Based on an audit of {total_n:,} unstructured customer discussions, sentiment skews "
            f"{'favorably' if pos_n >= neg_n else 'cautiously'} with {pos_pct}% positive and {neg_pct}% negative volume. "
            "Primary praise centers on core feature execution and design, while critical friction clusters around "
            "reliability and operational expectations."
        )

    st.markdown('<div class="page-mid">', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────
    # EXECUTIVE SUMMARY / GIST
    # ─────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="summary-gist-box">
        <div class="gist-header">Plain-language summary</div>
        <div class="gist-body">{escape(str(product_summary_text))}</div>
    </div>
    """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────
    # 1. OVERVIEW SECTION (ANCHOR: tab-overview)
    # ─────────────────────────────────────────────────────
    st.markdown('<div id="tab-overview" class="section-label">SENTIMENT SUMMARY & OVERVIEW</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="summary-total">{total_n:,} reviews analyzed</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="stackbar">
        <div style="width:{pos_pct}%; background:{POSITIVE};"></div>
        <div style="width:{neu_pct}%; background:{OCHRE};"></div>
        <div style="width:{neg_pct}%; background:{NEGATIVE};"></div>
    </div>
    <div class="legend">
        <span><b>{pos_pct}%</b> positive ({pos_n:,})</span>
        <span><b>{neu_pct}%</b> neutral ({neu_n:,})</span>
        <span><b>{neg_pct}%</b> negative ({neg_n:,})</span>
    </div>
    """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────
    # 2. VOICE OF CUSTOMER SECTION (ANCHOR: tab-voice)
    # ─────────────────────────────────────────────────────
    st.markdown('<div id="tab-voice" style="padding-top: 0.6rem;"></div>', unsafe_allow_html=True)
    voice_left, voice_right = st.columns(2)
    with voice_left:
        st.markdown('<div class="section-label">WHAT USERS LIKE</div>', unsafe_allow_html=True)
        st.markdown(f'<blockquote class="brief">{escape(str(top_pos))}</blockquote>', unsafe_allow_html=True)
        st.markdown('<div class="cite">Representative user comment</div>', unsafe_allow_html=True)
    with voice_right:
        st.markdown('<div class="section-label">WHAT USERS DISLIKE</div>', unsafe_allow_html=True)
        st.markdown(f'<blockquote class="brief negative">{escape(str(top_neg))}</blockquote>', unsafe_allow_html=True)
        st.markdown('<div class="cite">Representative user comment</div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────
    # 3. FINDINGS SECTION (ANCHOR: tab-findings)
    # ─────────────────────────────────────────────────────
    st.markdown('<div id="tab-findings" style="padding-top: 0.6rem;"></div>', unsafe_allow_html=True)
    find_left, find_right = st.columns(2)
    with find_left:
        st.markdown('<div class="section-label">STRENGTHS</div>', unsafe_allow_html=True)
        _render_finding_list(positives, POSITIVE, "+")
    with find_right:
        st.markdown('<div class="section-label">FRICTION POINTS</div>', unsafe_allow_html=True)
        _render_finding_list(negatives, NEGATIVE, "−")

    # ─────────────────────────────────────────────────────
    # 4. RECOMMENDED ACTIONS SECTION (ANCHOR: tab-actions)
    # ─────────────────────────────────────────────────────
    st.markdown('<div id="tab-actions" class="section-label">RECOMMENDED ACTIONS</div>', unsafe_allow_html=True)
    if recommendations:
        rows = "".join(
            f'<li><span class="anum">{i}</span>{escape(str(rec))}</li>'
            for i, rec in enumerate(recommendations, start=1)
        )
        st.markdown(f'<ul class="actions">{rows}</ul>', unsafe_allow_html=True)
    else:
        if Path(report_path).exists():
            with open(report_path, "r", encoding="utf-8") as rf:
                st.code(rf.read(), language="markdown")
        else:
            st.info("Generating turnaround strategy... Re-run audit to view.")

    st.markdown('</div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────
    # MULTI-PAGE REPORTLAB PDF ENGINE
    # ─────────────────────────────────────────────────────
    def generate_pdf(product_name, summary_body, p_quote, n_quote, pos_list, neg_list, act_list):
        ink = Color(28 / 255, 43 / 255, 58 / 255)
        positive = Color(47 / 255, 125 / 255, 93 / 255)
        negative = Color(140 / 255, 58 / 255, 74 / 255)
        black = Color(0, 0, 0)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf = canvas.Canvas(temp_file.name, pagesize=letter)
        y = 750

        def paginate_if_needed(cur_y, space=28):
            if cur_y < space:
                pdf.showPage()
                return 750
            return cur_y

        # Header Block
        pdf.setFillColor(ink)
        pdf.setFont("Helvetica-Bold", 15)
        pdf.drawString(40, y, f"Product Intelligence Briefing: {product_name.title()}")
        y -= 20

        # Executive Summary in PDF
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(40, y, "EXECUTIVE BRIEF")
        y -= 13
        pdf.setFillColor(black)
        pdf.setFont("Helvetica", 8.5)
        
        words = summary_body.split(" ")
        line = ""
        for w in words:
            if len(line + " " + w) < 95:
                line += (" " if line else "") + w
            else:
                pdf.drawString(48, y, line)
                y -= 11
                line = w
        if line:
            pdf.drawString(48, y, line)
            y -= 16

        # Section 1: Customer Voices
        y = paginate_if_needed(y, 60)
        pdf.setFillColor(ink)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(40, y, "1. LEADING CUSTOMER VOICES")
        y -= 15
        pdf.setFillColor(black)
        pdf.setFont("Helvetica-Oblique", 8.5)
        pdf.drawString(48, y, f"(+) Positive: {p_quote[:95]}...")
        y -= 13
        pdf.drawString(48, y, f"(-) Negative: {n_quote[:95]}...")
        y -= 20

        # Section 2: Strengths
        y = paginate_if_needed(y, 75)
        pdf.setFillColor(ink)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(40, y, "2. STRENGTHS")
        y -= 15
        pdf.setFont("Helvetica", 8.5)
        for p in pos_list:
            y = paginate_if_needed(y, 20)
            pdf.setFillColor(positive)
            pdf.drawString(48, y, "+")
            pdf.setFillColor(black)
            pdf.drawString(58, y, p[:100])
            y -= 13
        y -= 12

        # Section 3: Friction Points
        y = paginate_if_needed(y, 75)
        pdf.setFillColor(ink)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(40, y, "3. FRICTION POINTS")
        y -= 15
        pdf.setFont("Helvetica", 8.5)
        for n in neg_list:
            y = paginate_if_needed(y, 20)
            pdf.setFillColor(negative)
            pdf.drawString(48, y, "-")
            pdf.setFillColor(black)
            pdf.drawString(58, y, n[:100])
            y -= 13
        y -= 12

        # Section 4: Recommended Actions
        y = paginate_if_needed(y, 85)
        pdf.setFillColor(ink)
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(40, y, "4. RECOMMENDED ACTIONS")
        y -= 15
        pdf.setFillColor(black)
        pdf.setFont("Helvetica", 8.5)
        for idx, act in enumerate(act_list, start=1):
            y = paginate_if_needed(y, 35)
            words = f"{idx}. {act}".split(" ")
            line1, line2 = "", ""
            for w in words:
                if len(line1 + " " + w) < 95:
                    line1 += (" " if line1 else "") + w
                else:
                    line2 += (" " if line2 else "") + w

            pdf.drawString(48, y, line1)
            y -= 12
            if line2:
                y = paginate_if_needed(y, 18)
                pdf.drawString(58, y, line2)
                y -= 12
            y -= 4

        pdf.save()
        return temp_file.name

    pdf_target = generate_pdf(target_product, product_summary_text, top_pos, top_neg, positives, negatives, recommendations)

    st.markdown('<div class="page-mid">', unsafe_allow_html=True)
    footer_left, footer_right = st.columns([2, 1])
    with footer_left:
        st.markdown('<div class="stamp-text" style="padding-top:0.9rem;">Confidential — internal use only</div>', unsafe_allow_html=True)
    with footer_right:
        with open(pdf_target, "rb") as pf:
            st.download_button(
                label="Download briefing — PDF",
                data=pf,
                file_name=f"{slug}_product_intelligence_briefing.pdf",
                mime="application/pdf",
                width="stretch"
            )
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-close"></div>', unsafe_allow_html=True)

else:
    st.markdown('<div class="page-mid">', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="text-align:center; padding: 4rem 1rem; border: 1px dashed {LINE}; border-radius:6px; margin: 1.5rem 0;">
        <div style="font-size: 0.95rem; color: {INK};">No briefing loaded.</div>
        <div style="font-size: 0.85rem; color: {INK_SOFT}; margin-top: 0.25rem;">Enter a product above and click <b>Run audit</b> to prepare a briefing.</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-close"></div>', unsafe_allow_html=True)
