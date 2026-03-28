import html
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(
    page_title="PulseGrid | Emotion Ops",
    page_icon=":zap:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_BASE_URL = os.getenv("DASHBOARD_API_URL", "http://localhost:8000")

EMOTION_COLORS = {
    "joy": "#00F5FF",
    "anger": "#FF2D55",
    "fear": "#FF9F1C",
    "disgust": "#39FF14",
    "sadness": "#2E5BFF",
    "surprise": "#FFD60A",
    "neutral": "#8D99AE",
}


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

        :root {
            --bg-0: #070b14;
            --bg-1: #0f1729;
            --bg-2: #131f36;
            --panel: rgba(14, 21, 38, 0.82);
            --panel-border: rgba(0, 245, 255, 0.25);
            --text-main: #e8eeff;
            --text-muted: #96a7d3;
            --accent: #00f5ff;
            --accent-2: #39ff14;
            --danger: #ff2d55;
            --warning: #ffd60a;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 12% 14%, rgba(0, 245, 255, 0.18), transparent 28%),
                radial-gradient(circle at 88% 12%, rgba(57, 255, 20, 0.12), transparent 24%),
                radial-gradient(circle at 50% 78%, rgba(255, 45, 85, 0.12), transparent 30%),
                linear-gradient(160deg, var(--bg-0), var(--bg-1) 45%, var(--bg-2));
            color: var(--text-main);
            font-family: "Space Grotesk", "Segoe UI", sans-serif;
        }

        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stToolbar"] { right: 1rem; }

        .block-container {
            max-width: 1300px;
            padding-top: 1.2rem;
            padding-bottom: 2.25rem;
        }

        .hero-shell {
            border: 1px solid rgba(0, 245, 255, 0.25);
            border-radius: 20px;
            background:
                linear-gradient(140deg, rgba(0, 245, 255, 0.08), rgba(0, 0, 0, 0.1) 40%, rgba(57, 255, 20, 0.06)),
                rgba(7, 12, 24, 0.88);
            box-shadow:
                0 0 0 1px rgba(0, 245, 255, 0.06) inset,
                0 18px 40px rgba(1, 8, 20, 0.55),
                0 0 34px rgba(0, 245, 255, 0.14);
            padding: 1.4rem 1.6rem;
            overflow: hidden;
            position: relative;
            animation: pulseIn 0.7s ease-out;
        }

        .hero-shell::after {
            content: "";
            position: absolute;
            width: 260px;
            height: 260px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(57, 255, 20, 0.18), transparent 65%);
            right: -90px;
            top: -90px;
            pointer-events: none;
        }

        .hero-topline {
            color: var(--accent);
            font-family: "Orbitron", sans-serif;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            font-size: 0.74rem;
            margin-bottom: 0.35rem;
        }

        .hero-title {
            font-family: "Orbitron", sans-serif;
            font-size: clamp(1.3rem, 2.1vw, 2rem);
            letter-spacing: 0.03em;
            margin: 0;
            color: #f4f8ff;
        }

        .hero-sub {
            margin-top: 0.42rem;
            color: var(--text-muted);
            font-size: 0.96rem;
        }

        .status-grid {
            margin-top: 1rem;
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
        }

        .status-chip {
            background: rgba(9, 17, 34, 0.88);
            border: 1px solid rgba(141, 153, 174, 0.2);
            border-radius: 14px;
            padding: 0.75rem 0.9rem;
        }

        .chip-label {
            color: var(--text-muted);
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 0.25rem;
        }

        .chip-value {
            font-family: "Orbitron", sans-serif;
            color: #f7fbff;
            font-size: 1.1rem;
        }

        .chip-platform {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            font-weight: 700;
            color: #ff7b39;
            font-size: 1rem;
        }

        .chip-platform .dot {
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background: #ff7b39;
            box-shadow: 0 0 16px rgba(255, 123, 57, 0.8);
            display: inline-block;
        }

        .panel {
            border: 1px solid rgba(0, 245, 255, 0.2);
            border-radius: 18px;
            background: var(--panel);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.45);
            padding: 0.9rem 1rem 1rem;
            animation: riseIn 0.6s ease-out;
        }

        .panel-title {
            margin: 0.15rem 0 0.7rem;
            color: #f4f8ff;
            font-family: "Orbitron", sans-serif;
            letter-spacing: 0.05em;
            font-size: 1rem;
        }

        .panel-subtitle {
            margin-top: -0.4rem;
            margin-bottom: 0.7rem;
            color: var(--text-muted);
            font-size: 0.84rem;
        }

        .table-shell {
            margin-top: 0.4rem;
            max-height: 540px;
            overflow: auto;
            border-radius: 14px;
            border: 1px solid rgba(141, 153, 174, 0.22);
        }

        table.post-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
            background: rgba(8, 13, 24, 0.95);
        }

        .post-table thead th {
            position: sticky;
            top: 0;
            z-index: 2;
            text-align: left;
            padding: 0.75rem;
            background: rgba(11, 19, 34, 0.98);
            color: #9ab0dd;
            font-size: 0.73rem;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            border-bottom: 1px solid rgba(141, 153, 174, 0.24);
        }

        .post-table td {
            padding: 0.68rem 0.75rem;
            border-bottom: 1px solid rgba(141, 153, 174, 0.12);
            vertical-align: top;
            color: #dbe7ff;
        }

        .post-table tr:hover {
            background: rgba(22, 35, 58, 0.6);
        }

        .post-snippet {
            max-width: 360px;
            line-height: 1.36;
            color: #ecf2ff;
        }

        .cleaned-snippet {
            max-width: 370px;
            color: #adc2ea;
            line-height: 1.34;
        }

        .emotion-pill {
            display: inline-block;
            padding: 0.28rem 0.6rem;
            border-radius: 999px;
            font-weight: 700;
            text-transform: capitalize;
            letter-spacing: 0.03em;
            font-size: 0.78rem;
            color: #0a0f18;
        }

        .conf-wrap {
            min-width: 170px;
        }

        .conf-track {
            height: 8px;
            border-radius: 999px;
            background: rgba(131, 148, 184, 0.24);
            overflow: hidden;
            margin-bottom: 0.32rem;
        }

        .conf-fill {
            height: 100%;
            border-radius: 999px;
            box-shadow: 0 0 10px rgba(0, 245, 255, 0.45);
        }

        .conf-label {
            color: #a8bbe0;
            font-size: 0.79rem;
        }

        .small-note {
            color: #8ea2cf;
            font-size: 0.8rem;
            margin-top: 0.55rem;
        }

        @keyframes pulseIn {
            from { opacity: 0; transform: translateY(8px) scale(0.99); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        @keyframes riseIn {
            from { opacity: 0; transform: translateY(14px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @media (max-width: 980px) {
            .status-grid {
                grid-template-columns: 1fr;
            }

            .post-snippet,
            .cleaned-snippet {
                max-width: 260px;
            }

            .block-container {
                padding-top: 0.7rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mock_overview_data() -> Dict[str, Any]:
    now = datetime.now()
    return {
        "total_posts": 1842,
        "platform_split": {"reddit": 1842},
        "date_range": {
            "start": (now - timedelta(days=30)).strftime("%Y-%m-%d"),
            "end": now.strftime("%Y-%m-%d"),
        },
    }


def mock_emotions_data() -> Dict[str, Any]:
    return {
        "distribution": {
            "joy": 372,
            "anger": 214,
            "fear": 177,
            "disgust": 122,
            "sadness": 313,
            "surprise": 198,
            "neutral": 446,
        }
    }


def mock_posts_data() -> Dict[str, Any]:
    base_rows = [
        {
            "raw_text": "I finally got the internship offer after months of rejections and I cannot stop smiling.",
            "cleaned_text": "finally got internship offer months rejection cannot stop smiling",
            "emotion_label": "joy",
            "confidence": 0.94,
        },
        {
            "raw_text": "The policy change feels unfair and people are furious in the comments section.",
            "cleaned_text": "policy change feels unfair people furious comments section",
            "emotion_label": "anger",
            "confidence": 0.88,
        },
        {
            "raw_text": "The sudden layoffs have everyone worried about what happens next.",
            "cleaned_text": "sudden layoffs everyone worried happens next",
            "emotion_label": "fear",
            "confidence": 0.85,
        },
        {
            "raw_text": "The scam ad was all over the subreddit and it was honestly disgusting to see.",
            "cleaned_text": "scam ad subreddit honestly disgusting see",
            "emotion_label": "disgust",
            "confidence": 0.83,
        },
        {
            "raw_text": "I miss how the community used to be before all this drama started.",
            "cleaned_text": "miss community used drama started",
            "emotion_label": "sadness",
            "confidence": 0.81,
        },
        {
            "raw_text": "I opened the thread expecting bad news but the ending completely shocked me.",
            "cleaned_text": "opened thread expecting bad news ending completely shocked",
            "emotion_label": "surprise",
            "confidence": 0.79,
        },
        {
            "raw_text": "The update is out; looks stable so far and users are discussing minor improvements.",
            "cleaned_text": "update out looks stable far users discussing minor improvements",
            "emotion_label": "neutral",
            "confidence": 0.76,
        },
    ]

    rows: List[Dict[str, Any]] = []
    for i in range(1, 43):
        row = base_rows[i % len(base_rows)].copy()
        row["id"] = i
        row["platform"] = "reddit"
        row["created_at"] = (datetime.now() - timedelta(hours=i * 4)).isoformat(timespec="seconds")
        rows.append(row)

    return {"posts": rows}


def fetch_json(endpoint: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=2)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            return payload
    except (requests.RequestException, ValueError):
        pass
    return fallback


@st.cache_data(ttl=15)
def fetch_overview() -> Dict[str, Any]:
    return fetch_json("/overview", mock_overview_data())


@st.cache_data(ttl=15)
def fetch_emotions() -> Dict[str, Any]:
    return fetch_json("/emotions", mock_emotions_data())


@st.cache_data(ttl=15)
def fetch_posts() -> Dict[str, Any]:
    return fetch_json("/posts", mock_posts_data())


def render_overview_hero(overview: Dict[str, Any]) -> None:
    total_posts = int(overview.get("total_posts", 0))
    platform_split = overview.get("platform_split", {}) or {"reddit": 0}
    reddit_count = int(platform_split.get("reddit", 0))
    date_range = overview.get("date_range", {})
    start_date = date_range.get("start", "n/a")
    end_date = date_range.get("end", "n/a")

    st.markdown(
        f"""
        <section class="hero-shell">
            <div class="hero-topline">Dashboard</div>
            <h1 class="hero-title">Neural Emotion Pipeline Live</h1>
            <p class="hero-sub">Realtime view of Reddit ingestion, cleaning, and transformer-based emotion enrichment.</p>

            <div class="status-grid">
                <div class="status-chip">
                    <div class="chip-label">Total Posts Analyzed</div>
                    <div class="chip-value">{total_posts:,}</div>
                </div>
                <div class="status-chip">
                    <div class="chip-label">Primary Platform</div>
                    <div class="chip-platform"><span class="dot"></span>Reddit ({reddit_count:,})</div>
                </div>
                <div class="status-chip">
                    <div class="chip-label">Coverage Window</div>
                    <div class="chip-value">{start_date} to {end_date}</div>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def build_emotion_chart(distribution: Dict[str, int]) -> go.Figure:
    labels = []
    values = []
    colors = []

    for emotion in EMOTION_COLORS:
        labels.append(emotion.capitalize())
        values.append(int(distribution.get(emotion, 0)))
        colors.append(EMOTION_COLORS[emotion])

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.64,
                marker={"colors": colors, "line": {"color": "#0a1222", "width": 2}},
                textinfo="label+percent",
                textfont={"size": 12, "color": "#e7eeff"},
                hovertemplate="<b>%{label}</b><br>Posts: %{value}<br>Share: %{percent}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 0, "r": 0, "t": 4, "b": 4},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.14,
            "xanchor": "center",
            "x": 0.5,
            "font": {"color": "#b8caef", "size": 11},
        },
    )
    return fig


def shorten(text: str, max_chars: int = 170) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def render_post_explorer(posts: List[Dict[str, Any]]) -> None:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<h3 class="panel-title">Enriched Post Explorer</h3>', unsafe_allow_html=True)
    st.markdown(
        '<p class="panel-subtitle">Search, filter by emotion label, and inspect confidence signals from the classifier.</p>',
        unsafe_allow_html=True,
    )

    if not posts:
        st.warning("No posts available from API or mock payload.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = pd.DataFrame(posts)
    for col in ["raw_text", "cleaned_text", "emotion_label", "confidence"]:
        if col not in df.columns:
            df[col] = "" if col != "confidence" else 0.0

    left, middle, right = st.columns([2.6, 1.5, 1.4])
    with left:
        query = st.text_input("Search posts", placeholder="Try: internship, layoffs, policy, update")
    with middle:
        emotions = ["all"] + [emotion for emotion in EMOTION_COLORS.keys()]
        selected_emotion = st.selectbox("Emotion filter", emotions, index=0)
    with right:
        min_conf = st.slider("Min confidence", min_value=0.0, max_value=1.0, value=0.0, step=0.01)

    filtered = df.copy()
    if query:
        q = query.lower().strip()
        filtered = filtered[
            filtered["raw_text"].str.lower().str.contains(q, na=False)
            | filtered["cleaned_text"].str.lower().str.contains(q, na=False)
        ]

    if selected_emotion != "all":
        filtered = filtered[filtered["emotion_label"].str.lower() == selected_emotion]

    filtered["confidence"] = pd.to_numeric(filtered["confidence"], errors="coerce").fillna(0.0)
    filtered = filtered[filtered["confidence"] >= min_conf].sort_values(by="confidence", ascending=False)

    st.caption(f"Showing {len(filtered)} of {len(df)} posts")

    table_rows: List[str] = []
    for _, row in filtered.iterrows():
        raw_text = html.escape(shorten(str(row.get("raw_text", "")), 190))
        cleaned_text = html.escape(shorten(str(row.get("cleaned_text", "")), 170))
        emotion = str(row.get("emotion_label", "neutral")).lower().strip() or "neutral"
        color = EMOTION_COLORS.get(emotion, "#8D99AE")
        confidence_pct = max(0.0, min(100.0, float(row.get("confidence", 0.0)) * 100))

        table_rows.append(
            f"""
            <tr>
                <td><div class="post-snippet">{raw_text}</div></td>
                <td><div class="cleaned-snippet">{cleaned_text}</div></td>
                <td><span class="emotion-pill" style="background:{color};">{html.escape(emotion)}</span></td>
                <td>
                    <div class="conf-wrap">
                        <div class="conf-track">
                            <div class="conf-fill" style="width:{confidence_pct:.1f}%; background: linear-gradient(90deg, {color}, #00f5ff);"></div>
                        </div>
                        <div class="conf-label">{confidence_pct:.1f}%</div>
                    </div>
                </td>
            </tr>
            """
        )

    if not table_rows:
        st.info("No rows match the active filters.")
    else:
        st.markdown(
            f"""
            <div class="table-shell">
                <table class="post-table">
                    <thead>
                        <tr>
                            <th>Original Reddit Post</th>
                            <th>Cleaned Text</th>
                            <th>Emotion Tag</th>
                            <th>Confidence Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="small-note">API source: <strong>{}</strong>. If endpoints are unavailable, mock payloads are automatically used.</div>'.format(
            API_BASE_URL
        ),
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    inject_custom_css()

    overview_payload = fetch_overview()
    emotion_payload = fetch_emotions()
    posts_payload = fetch_posts()

    render_overview_hero(overview_payload)

    chart_col, legend_col = st.columns([2.0, 1.0], gap="large")
    with chart_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<h3 class="panel-title">Emotion Distribution Visualizer</h3>', unsafe_allow_html=True)
        st.markdown(
            '<p class="panel-subtitle">Transformer inference classes across enriched Reddit posts.</p>',
            unsafe_allow_html=True,
        )
        distribution = emotion_payload.get("distribution", {})
        fig = build_emotion_chart(distribution)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with legend_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<h3 class="panel-title">Class Map</h3>', unsafe_allow_html=True)
        st.markdown('<p class="panel-subtitle">Color coding used in chart and table badges.</p>', unsafe_allow_html=True)

        for emotion, color in EMOTION_COLORS.items():
            count = int(distribution.get(emotion, 0))
            st.markdown(
                f"""
                <div style="display:flex;align-items:center;justify-content:space-between;padding:0.45rem 0.1rem;border-bottom:1px solid rgba(141,153,174,0.14);">
                    <div style="display:flex;align-items:center;gap:0.55rem;">
                        <span style="display:inline-block;width:11px;height:11px;border-radius:50%;background:{color};box-shadow:0 0 10px {color};"></span>
                        <span style="color:#e9f0ff;text-transform:capitalize;">{emotion}</span>
                    </div>
                    <span style="color:#9ab0dd;font-weight:600;">{count}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    posts_list = posts_payload.get("posts", []) if isinstance(posts_payload, dict) else []
    render_post_explorer(posts_list)


if __name__ == "__main__":
    main()
