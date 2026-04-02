import html
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import plotly.graph_objects as go
import psycopg
import requests
import streamlit as st

st.set_page_config(
    page_title="PulseGrid | Pipeline Control",
    page_icon=":zap:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CLEANING_BASE_URL = os.getenv("CLEANING_BASE_URL", "http://localhost:5000")
MODEL_BASE_URL = os.getenv("MODEL_BASE_URL", "http://localhost:4000")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://emotion_app:emotion_password_123@localhost:5432/emotion_db",
)

EMOTION_COLORS = {
    "joy": "#00F5FF",
    "anger": "#FF2D55",
    "fear": "#FF9F1C",
    "disgust": "#39FF14",
    "sadness": "#2E5BFF",
    "surprise": "#FFD60A",
    "neutral": "#8D99AE",
}


@dataclass
class BatchAssignResult:
    batch_id: str
    matched_count: int
    sample_rows: List[Dict[str, Any]]


class PipelineError(Exception):
    pass


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
            --text-main: #e8eeff;
            --text-muted: #96a7d3;
            --accent: #00f5ff;
            --accent-2: #39ff14;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 12% 14%, rgba(0, 245, 255, 0.16), transparent 28%),
                radial-gradient(circle at 88% 12%, rgba(57, 255, 20, 0.11), transparent 24%),
                radial-gradient(circle at 50% 78%, rgba(255, 45, 85, 0.1), transparent 30%),
                linear-gradient(160deg, var(--bg-0), var(--bg-1) 45%, var(--bg-2));
            color: var(--text-main);
            font-family: "Space Grotesk", "Segoe UI", sans-serif;
        }

        [data-testid="stHeader"] { background: transparent; }
        .block-container { max-width: 1320px; padding-top: 1rem; }

        .hero-shell {
            border: 1px solid rgba(0, 245, 255, 0.25);
            border-radius: 20px;
            background:
                linear-gradient(140deg, rgba(0, 245, 255, 0.08), rgba(0, 0, 0, 0.1) 40%, rgba(57, 255, 20, 0.06)),
                rgba(7, 12, 24, 0.88);
            box-shadow: 0 18px 40px rgba(1, 8, 20, 0.55), 0 0 34px rgba(0, 245, 255, 0.14);
            padding: 1.4rem 1.6rem;
            margin-bottom: 1rem;
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
            font-size: clamp(1.2rem, 2vw, 1.9rem);
            margin: 0;
            color: #f4f8ff;
        }

        .hero-sub {
            margin-top: 0.45rem;
            color: var(--text-muted);
            font-size: 0.95rem;
        }

        .status-grid {
            margin-top: 0.95rem;
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.8rem;
        }

        .status-chip {
            background: rgba(9, 17, 34, 0.88);
            border: 1px solid rgba(141, 153, 174, 0.2);
            border-radius: 13px;
            padding: 0.72rem 0.85rem;
        }

        .chip-label {
            color: var(--text-muted);
            font-size: 0.73rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 0.22rem;
        }

        .chip-value {
            font-family: "Orbitron", sans-serif;
            color: #f7fbff;
            font-size: 1rem;
            word-break: break-word;
        }

        .panel {
            border: 1px solid rgba(0, 245, 255, 0.2);
            border-radius: 16px;
            background: var(--panel);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.45);
            padding: 0.9rem 1rem 1rem;
            margin-bottom: 1rem;
        }

        .panel-title {
            margin: 0.08rem 0 0.55rem;
            color: #f4f8ff;
            font-family: "Orbitron", sans-serif;
            letter-spacing: 0.05em;
            font-size: 0.95rem;
        }

        .panel-subtitle {
            margin-top: -0.25rem;
            margin-bottom: 0.7rem;
            color: var(--text-muted);
            font-size: 0.84rem;
        }

        .table-shell {
            margin-top: 0.45rem;
            max-height: 540px;
            overflow: auto;
            border-radius: 12px;
            border: 1px solid rgba(141, 153, 174, 0.22);
        }

        table.post-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.86rem;
            background: rgba(8, 13, 24, 0.95);
        }

        .post-table thead th {
            position: sticky;
            top: 0;
            z-index: 2;
            text-align: left;
            padding: 0.7rem;
            background: rgba(11, 19, 34, 0.98);
            color: #9ab0dd;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            border-bottom: 1px solid rgba(141, 153, 174, 0.24);
        }

        .post-table td {
            padding: 0.66rem 0.72rem;
            border-bottom: 1px solid rgba(141, 153, 174, 0.12);
            vertical-align: top;
            color: #dbe7ff;
        }

        .emotion-pill {
            display: inline-block;
            padding: 0.27rem 0.6rem;
            border-radius: 999px;
            font-weight: 700;
            text-transform: capitalize;
            letter-spacing: 0.03em;
            font-size: 0.76rem;
            color: #08101b;
        }

        .conf-track {
            height: 8px;
            border-radius: 999px;
            background: rgba(131, 148, 184, 0.24);
            overflow: hidden;
            margin-bottom: 0.32rem;
            min-width: 130px;
        }

        .conf-fill {
            height: 100%;
            border-radius: 999px;
            box-shadow: 0 0 10px rgba(0, 245, 255, 0.45);
        }

        .mono {
            font-family: Consolas, monospace;
            color: #8cd4ff;
        }

        @media (max-width: 980px) {
            .status-grid { grid-template-columns: 1fr 1fr; }
        }

        @media (max-width: 620px) {
            .status-grid { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def normalize_database_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url


def db_fetch_all(query: str, params: tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
    conn_url = normalize_database_url(DATABASE_URL)
    with psycopg.connect(conn_url) as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(query, params)
            return list(cur.fetchall())


def db_execute(query: str, params: tuple[Any, ...] = ()) -> int:
    conn_url = normalize_database_url(DATABASE_URL)
    with psycopg.connect(conn_url) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            affected = cur.rowcount
        conn.commit()
        return affected


def generate_batch_id(keyword: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", keyword.lower().strip()).strip("-") or "batch"
    return f"frontend-{slug}-{int(time.time())}"


def search_and_assign_batch(keyword: str, limit: int = 50) -> BatchAssignResult:
    like_term = f"%{keyword}%"
    rows = db_fetch_all(
        """
        SELECT id, platform, keyword, raw_text, batch_id, created_at
        FROM raw_posts
        WHERE keyword ILIKE %s OR raw_text ILIKE %s
        ORDER BY created_at DESC, id DESC
        LIMIT %s
        """,
        (like_term, like_term, limit),
    )
    if not rows:
        raise PipelineError(f"No raw_posts found for keyword: {keyword}")

    new_batch_id = generate_batch_id(keyword)
    row_ids = [int(r["id"]) for r in rows]

    updated = db_execute(
        "UPDATE raw_posts SET batch_id = %s WHERE id = ANY(%s)",
        (new_batch_id, row_ids),
    )
    if updated <= 0:
        raise PipelineError("Batch assignment failed: no rows were updated.")

    return BatchAssignResult(
        batch_id=new_batch_id,
        matched_count=updated,
        sample_rows=rows[:8],
    )


def call_json(method: str, url: str, timeout: int = 15) -> Dict[str, Any]:
    try:
        response = requests.request(method=method, url=url, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            return payload
        return {"data": payload}
    except requests.RequestException as exc:
        raise PipelineError(f"Request failed for {url}: {exc}") from exc


def trigger_cleaning(batch_id: str) -> Dict[str, Any]:
    return call_json("POST", f"{CLEANING_BASE_URL}/api/clean/{batch_id}", timeout=90)


def fetch_cleaning_stats(batch_id: str) -> Dict[str, Any]:
    return call_json("GET", f"{CLEANING_BASE_URL}/api/clean/stats/{batch_id}")


def trigger_model(batch_id: str) -> Dict[str, Any]:
    return call_json("POST", f"{MODEL_BASE_URL}/api/analyze/{batch_id}", timeout=30)


def fetch_model_stats(batch_id: str) -> Dict[str, Any]:
    return call_json("GET", f"{MODEL_BASE_URL}/api/batch/{batch_id}")


def fetch_model_results(batch_id: str) -> Dict[str, Any]:
    return call_json("GET", f"{MODEL_BASE_URL}/results/{batch_id}")


def poll_model_completion(batch_id: str, max_checks: int = 20, sleep_secs: int = 2) -> Dict[str, Any]:
    latest: Dict[str, Any] = {}
    for _ in range(max_checks):
        latest = fetch_model_stats(batch_id)
        pending = int(latest.get("pending", 0))
        total_posts = int(latest.get("total_posts", 0))
        if total_posts > 0 and pending == 0:
            return latest
        time.sleep(sleep_secs)
    return latest


def fetch_pipeline_rows(batch_id: str) -> List[Dict[str, Any]]:
    return db_fetch_all(
        """
        SELECT
            rp.id AS raw_post_id,
            rp.raw_text,
            rp.keyword,
            cp.cleaned_text,
            cp.language,
            ep.emotion_label,
            ep.confidence,
            ep.analyzed_at
        FROM raw_posts rp
        LEFT JOIN cleaned_posts cp
            ON cp.raw_post_id = rp.id
           AND cp.batch_id = %s
        LEFT JOIN enriched_posts ep
            ON ep.cleaned_post_id = cp.id
           AND ep.batch_id = %s
        WHERE rp.batch_id = %s
        ORDER BY rp.id DESC
        """,
        (batch_id, batch_id, batch_id),
    )


def shorten(text: str, max_chars: int) -> str:
    value = (text or "").strip()
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3].rstrip() + "..."


def safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def render_hero(rows: List[Dict[str, Any]], batch_id: str) -> None:
    total = len(rows)
    analyzed = sum(1 for r in rows if r.get("emotion_label"))
    pending = total - analyzed

    st.markdown(
        f"""
        <section class="hero-shell">
            <div class="hero-topline">System Status // Frontend Orchestrator</div>
            <h1 class="hero-title">Keyword to Emotion Pipeline Control</h1>
            <p class="hero-sub">Search raw_posts, assign a shared batch ID, trigger cleaning then model analysis, and inspect enriched output in one flow.</p>
            <div class="status-grid">
                <div class="status-chip">
                    <div class="chip-label">Active Batch</div>
                    <div class="chip-value mono">{html.escape(batch_id or 'none')}</div>
                </div>
                <div class="status-chip">
                    <div class="chip-label">Total Posts In Batch</div>
                    <div class="chip-value">{total}</div>
                </div>
                <div class="status-chip">
                    <div class="chip-label">Analyzed</div>
                    <div class="chip-value">{analyzed}</div>
                </div>
                <div class="status-chip">
                    <div class="chip-label">Pending</div>
                    <div class="chip-value">{pending}</div>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def build_emotion_chart(rows: List[Dict[str, Any]]) -> go.Figure:
    counts = {emotion: 0 for emotion in EMOTION_COLORS}
    for row in rows:
        emotion = str(row.get("emotion_label") or "").lower()
        if emotion in counts:
            counts[emotion] += 1

    labels = [name.capitalize() for name in EMOTION_COLORS]
    values = [counts[name] for name in EMOTION_COLORS]
    colors = [EMOTION_COLORS[name] for name in EMOTION_COLORS]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.62,
                marker={"colors": colors, "line": {"color": "#0a1222", "width": 2}},
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>Posts: %{value}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 0, "r": 0, "t": 8, "b": 10},
        legend={"orientation": "h", "y": -0.15, "x": 0.5, "xanchor": "center", "font": {"size": 11}},
    )
    return fig


def render_explorer(rows: List[Dict[str, Any]]) -> None:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<h3 class="panel-title">Enriched Post Explorer</h3>', unsafe_allow_html=True)
    st.markdown(
        '<p class="panel-subtitle">Joined view from raw_posts + cleaned_posts + enriched_posts for the selected batch.</p>',
        unsafe_allow_html=True,
    )

    if not rows:
        st.info("No rows for this batch yet. Assign keyword batch first, then run cleaning/model.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = pd.DataFrame(rows)
    left, mid, right = st.columns([2.4, 1.3, 1.3])
    with left:
        q = st.text_input("Search in post text", placeholder="Try: climate, renewable, policy")
    with mid:
        emotion_filter = st.selectbox("Emotion filter", ["all"] + list(EMOTION_COLORS.keys()))
    with right:
        min_conf = st.slider("Min confidence", 0.0, 1.0, 0.0, 0.01)

    filtered = df.copy()
    if q:
        needle = q.lower().strip()
        filtered = filtered[
            filtered["raw_text"].fillna("").str.lower().str.contains(needle)
            | filtered["cleaned_text"].fillna("").str.lower().str.contains(needle)
        ]

    if emotion_filter != "all":
        filtered = filtered[filtered["emotion_label"].fillna("").str.lower() == emotion_filter]

    filtered["confidence"] = pd.to_numeric(filtered["confidence"], errors="coerce").fillna(0.0)
    filtered = filtered[filtered["confidence"] >= min_conf].sort_values(by="raw_post_id", ascending=False)

    st.caption(f"Showing {len(filtered)} of {len(df)} rows")

    html_rows: List[str] = []
    for _, row in filtered.iterrows():
        raw_text = html.escape(shorten(str(row.get("raw_text") or ""), 180))
        cleaned_text = html.escape(shorten(str(row.get("cleaned_text") or ""), 160))
        emotion = str(row.get("emotion_label") or "pending").lower()
        color = EMOTION_COLORS.get(emotion, "#7F8EA9")
        conf_pct = safe_float(row.get("confidence")) * 100
        keyword = html.escape(str(row.get("keyword") or ""))

        html_rows.append(
            f"""
            <tr>
                <td>{raw_text}</td>
                <td>{cleaned_text}</td>
                <td><span class=\"emotion-pill\" style=\"background:{color};\">{html.escape(emotion)}</span></td>
                <td>
                    <div class=\"conf-track\"><div class=\"conf-fill\" style=\"width:{conf_pct:.1f}%; background:linear-gradient(90deg,{color},#00f5ff);\"></div></div>
                    <div>{conf_pct:.1f}%</div>
                </td>
                <td>{keyword}</td>
            </tr>
            """
        )

    if html_rows:
        st.markdown(
            f"""
            <div class="table-shell">
              <table class="post-table">
                <thead>
                  <tr>
                    <th>Original Reddit Post</th>
                    <th>Cleaned Text</th>
                    <th>Emotion Tag</th>
                    <th>Confidence</th>
                    <th>Keyword</th>
                  </tr>
                </thead>
                <tbody>{''.join(html_rows)}</tbody>
              </table>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("No rows match current filters.")

    st.markdown("</div>", unsafe_allow_html=True)


def show_service_bar() -> None:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<h3 class="panel-title">Service Configuration</h3>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.7rem;">
          <div><strong>Cleaning API</strong><br><span class="mono">{html.escape(CLEANING_BASE_URL)}</span></div>
          <div><strong>Model API</strong><br><span class="mono">{html.escape(MODEL_BASE_URL)}</span></div>
          <div><strong>Database</strong><br><span class="mono">{html.escape(normalize_database_url(DATABASE_URL))}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def init_state() -> None:
    st.session_state.setdefault("active_batch_id", "")
    st.session_state.setdefault("last_keyword", "")
    st.session_state.setdefault("last_clean_stats", {})
    st.session_state.setdefault("last_model_stats", {})


def main() -> None:
    inject_custom_css()
    init_state()

    show_service_bar()

    control_col, action_col = st.columns([1.8, 1.2], gap="large")

    with control_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<h3 class="panel-title">Step 1: Keyword Search and Batch Assignment</h3>', unsafe_allow_html=True)
        keyword = st.text_input("Keyword", value=st.session_state["last_keyword"], placeholder="Enter keyword to find in raw_posts")
        limit = st.number_input("Max posts to include in batch", min_value=1, max_value=200, value=50, step=1)

        if st.button("Assign New Batch From Keyword", type="primary", use_container_width=True):
            try:
                if not keyword.strip():
                    raise PipelineError("Keyword cannot be empty.")
                with st.spinner("Searching raw_posts and assigning new batch_id..."):
                    result = search_and_assign_batch(keyword.strip(), int(limit))
                st.session_state["active_batch_id"] = result.batch_id
                st.session_state["last_keyword"] = keyword.strip()
                st.success(f"Batch assigned: {result.batch_id} ({result.matched_count} posts)")
                if result.sample_rows:
                    st.dataframe(pd.DataFrame(result.sample_rows), use_container_width=True, hide_index=True)
            except Exception as exc:
                st.error(str(exc))

        st.markdown("</div>", unsafe_allow_html=True)

    with action_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<h3 class="panel-title">Step 2/3: Trigger Services</h3>', unsafe_allow_html=True)

        active_batch_id = st.session_state.get("active_batch_id", "")
        st.markdown(f"Active batch: <span class='mono'>{html.escape(active_batch_id or 'none')}</span>", unsafe_allow_html=True)

        disable_actions = not active_batch_id

        if st.button("Trigger Cleaning", use_container_width=True, disabled=disable_actions):
            try:
                with st.spinner("Calling cleaning service..."):
                    payload = trigger_cleaning(active_batch_id)
                st.success(f"Cleaning done. Processed: {payload.get('total_processed', 0)}")
                st.session_state["last_clean_stats"] = fetch_cleaning_stats(active_batch_id)
            except Exception as exc:
                st.error(str(exc))

        if st.button("Trigger Model", use_container_width=True, disabled=disable_actions):
            try:
                with st.spinner("Queuing model analysis and polling completion..."):
                    trigger_model(active_batch_id)
                    st.session_state["last_model_stats"] = poll_model_completion(active_batch_id)
                st.success("Model analysis completed or reached polling timeout.")
            except Exception as exc:
                st.error(str(exc))

        if st.button("Run Full Pipeline", use_container_width=True, disabled=disable_actions):
            try:
                with st.spinner("Running cleaning then model..."):
                    trigger_cleaning(active_batch_id)
                    st.session_state["last_clean_stats"] = fetch_cleaning_stats(active_batch_id)
                    trigger_model(active_batch_id)
                    st.session_state["last_model_stats"] = poll_model_completion(active_batch_id)
                st.success("Full pipeline run finished.")
            except Exception as exc:
                st.error(str(exc))

        if st.button("Refresh Batch Status", use_container_width=True, disabled=disable_actions):
            try:
                st.session_state["last_clean_stats"] = fetch_cleaning_stats(active_batch_id)
            except Exception as exc:
                st.warning(f"Cleaning stats unavailable: {exc}")
            try:
                st.session_state["last_model_stats"] = fetch_model_stats(active_batch_id)
            except Exception as exc:
                st.warning(f"Model stats unavailable: {exc}")

        st.markdown("</div>", unsafe_allow_html=True)

    active_batch_id = st.session_state.get("active_batch_id", "")
    rows: List[Dict[str, Any]] = []
    if active_batch_id:
        try:
            rows = fetch_pipeline_rows(active_batch_id)
        except Exception as exc:
            st.error(f"Failed to load pipeline data from DB: {exc}")

    render_hero(rows, active_batch_id)

    metrics_col, chart_col = st.columns([1, 2], gap="large")
    with metrics_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<h3 class="panel-title">Batch Progress</h3>', unsafe_allow_html=True)

        clean_stats = st.session_state.get("last_clean_stats", {})
        model_stats = st.session_state.get("last_model_stats", {})

        st.write("Cleaning stats")
        st.json(clean_stats or {"info": "No cleaning stats yet"})

        st.write("Model stats")
        st.json(model_stats or {"info": "No model stats yet"})

        st.markdown("</div>", unsafe_allow_html=True)

    with chart_col:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<h3 class="panel-title">Emotion Distribution</h3>', unsafe_allow_html=True)
        st.markdown('<p class="panel-subtitle">Distribution in enriched_posts for active batch.</p>', unsafe_allow_html=True)
        st.plotly_chart(build_emotion_chart(rows), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    render_explorer(rows)

    if active_batch_id and st.button("Fetch Results API Payload", use_container_width=True):
        try:
            payload = fetch_model_results(active_batch_id)
            st.json(payload)
        except Exception as exc:
            st.error(f"Failed to fetch /results payload: {exc}")


if __name__ == "__main__":
    main()
