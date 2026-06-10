import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import asyncio
import io
import json

import pandas as pd
import streamlit as st

from core.database import init_db, SessionLocal
from services.pipeline import process_leads_from_df, process_leads_from_list
from models.lead import Lead
from utils.exporter import export_leads_to_csv, export_leads_to_json

st.set_page_config(
    page_title="Lead Intelligence System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
[data-testid="stSidebar"] { background: #0d0d14 !important; border-right: 1px solid #1e1e2e; }
[data-testid="stSidebar"] * { color: #c9d1d9 !important; }
.stApp { background: #090912; color: #e6edf3; }
div[data-testid="metric-container"] { background: #0d1117; border: 1px solid #21262d; border-radius: 12px; padding: 16px; }
.score-high { color: #3fb950; font-weight: 700; }
.score-medium { color: #d29922; font-weight: 700; }
.score-low { color: #f85149; font-weight: 700; }
.badge-high { background: #0f2a1a; color: #3fb950; padding: 2px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid #238636; }
.badge-medium { background: #2a1f0a; color: #d29922; padding: 2px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid #9e6a03; }
.badge-low { background: #2a0a0a; color: #f85149; padding: 2px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid #6e2020; }
.stButton > button { background: linear-gradient(135deg, #238636, #2ea043) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; }
.section-header { font-size: 11px; font-weight: 600; letter-spacing: 2px; color: #8b949e; text-transform: uppercase; margin: 16px 0 8px 0; }
</style>
""", unsafe_allow_html=True)

init_db()


def get_db_session():
    return SessionLocal()


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def get_stats():
    db = get_db_session()
    try:
        from sqlalchemy import func
        total = db.query(func.count(Lead.id)).scalar() or 0
        high = db.query(func.count(Lead.id)).filter(Lead.lead_quality_label == "High").scalar() or 0
        medium = db.query(func.count(Lead.id)).filter(Lead.lead_quality_label == "Medium").scalar() or 0
        low = db.query(func.count(Lead.id)).filter(Lead.lead_quality_label == "Low").scalar() or 0
        avg = db.query(func.avg(Lead.lead_score)).scalar() or 0
        return {"total": total, "high": high, "medium": medium, "low": low, "avg_score": round(avg, 1)}
    finally:
        db.close()


def get_all_leads(quality_filter=None, limit=200):
    db = get_db_session()
    try:
        q = db.query(Lead)
        if quality_filter and quality_filter != "All":
            q = q.filter(Lead.lead_quality_label == quality_filter)
        return q.order_by(Lead.lead_score.desc()).limit(limit).all()
    finally:
        db.close()


def leads_to_df(leads):
    rows = []
    for l in leads:
        rows.append({
            "ID": l.id,
            "Name": l.name,
            "Email": l.email or "—",
            "Company": l.company or "—",
            "Website": l.website or "—",
            "Industry": l.industry or "—",
            "Business Type": l.business_type or "—",
            "AI Confidence": f"{l.ai_confidence:.0%}",
            "Score": l.lead_score,
            "Quality": l.lead_quality_label,
            "Email Valid": "✓" if l.email_valid else "✗",
            "Batch": l.batch_id or "—",
        })
    return pd.DataFrame(rows)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ Lead Intelligence")
    st.markdown("**Enrichment & Scoring System**")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["📊 Dashboard", "📤 Upload Leads", "✏️ Manual Entry", "📋 Lead Browser", "📥 Export"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    stats = get_stats()
    st.markdown('<div class="section-header">Live Stats</div>', unsafe_allow_html=True)
    st.markdown(f"**Total Leads:** {stats['total']}")
    st.markdown(f"<span class='score-high'>● High: {stats['high']}</span>", unsafe_allow_html=True)
    st.markdown(f"<span class='score-medium'>● Medium: {stats['medium']}</span>", unsafe_allow_html=True)
    st.markdown(f"<span class='score-low'>● Low: {stats['low']}</span>", unsafe_allow_html=True)
    st.markdown(f"**Avg Score:** {stats['avg_score']}")
    st.markdown("---")
    if st.button("🗑️ Clear All Leads"):
        db = get_db_session()
        db.query(Lead).delete()
        db.commit()
        db.close()
        st.success("Cleared.")
        st.rerun()


# ── Dashboard ──────────────────────────────────────────────────────────────────
if page == "📊 Dashboard":
    st.title("📊 Lead Intelligence Dashboard")
    st.markdown("*AI-powered lead enrichment and qualification at scale*")
    st.markdown("---")
    stats = get_stats()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Leads", stats["total"])
    c2.metric("🟢 High Quality", stats["high"])
    c3.metric("🟡 Medium Quality", stats["medium"])
    c4.metric("🔴 Low Quality", stats["low"])
    c5.metric("Avg Score", f"{stats['avg_score']}/100")
    st.markdown("---")
    if stats["total"] > 0:
        leads = get_all_leads()
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("Quality Distribution")
            quality_data = pd.DataFrame({"Quality": ["High", "Medium", "Low"], "Count": [stats["high"], stats["medium"], stats["low"]]})
            st.bar_chart(quality_data.set_index("Quality"), color=["#3fb950"])
        with col_right:
            st.subheader("Industry Breakdown")
            industries = [l.industry for l in leads if l.industry]
            if industries:
                ind_df = pd.Series(industries).value_counts().reset_index()
                ind_df.columns = ["Industry", "Count"]
                st.bar_chart(ind_df.set_index("Industry"), color=["#58a6ff"])
        st.markdown("---")
        st.subheader("🏆 Top Leads by Score")
        for lead in sorted(leads, key=lambda x: x.lead_score, reverse=True)[:5]:
            badge_class = f"badge-{lead.lead_quality_label.lower()}"
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            col1.markdown(f"**{lead.name}** — {lead.company or '—'}")
            col2.markdown(f"_{lead.industry or '—'}_")
            col3.markdown(f"<span class='{badge_class}'>{lead.lead_quality_label}</span>", unsafe_allow_html=True)
            col4.markdown(f"**{lead.lead_score}**")
    else:
        st.info("No leads yet. Upload a CSV or add leads manually to get started.")


# ── Upload ─────────────────────────────────────────────────────────────────────
elif page == "📤 Upload Leads":
    st.title("📤 Upload Leads")
    st.markdown("Upload a CSV file to batch-enrich and score your leads.")
    st.markdown("---")
    with st.expander("📄 Expected CSV Format"):
        st.code("name,email,company,website\nAlice Chen,alice@techflow.io,TechFlow Solutions,techflow.io", language="csv")
    uploaded_file = st.file_uploader("Drop your CSV here", type=["csv"])
    if uploaded_file:
        df_preview = pd.read_csv(uploaded_file)
        uploaded_file.seek(0)
        st.markdown(f"**{len(df_preview)} rows detected** — preview:")
        st.dataframe(df_preview.head(5), use_container_width=True)
        if st.button("⚡ Process & Enrich Leads", use_container_width=True):
            with st.spinner("Cleaning, enriching, and scoring leads..."):
                try:
                    csv_bytes = uploaded_file.read()
                    df = pd.read_csv(io.StringIO(csv_bytes.decode("utf-8")))
                    db = get_db_session()
                    leads, pipeline_stats = run_async(process_leads_from_df(df, db))
                    db.close()
                    st.success(f"✅ Processed **{pipeline_stats.successfully_processed}** leads!")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Received", pipeline_stats.total_received)
                    c2.metric("Processed", pipeline_stats.successfully_processed)
                    c3.metric("Duplicates Removed", pipeline_stats.duplicates_removed)
                    c4.metric("Batch ID", pipeline_stats.batch_id)
                    st.markdown("### Results")
                    st.dataframe(leads_to_df(leads), use_container_width=True)
                except Exception as e:
                    st.error(f"Error: {e}")
                    raise


# ── Manual Entry ───────────────────────────────────────────────────────────────
elif page == "✏️ Manual Entry":
    st.title("✏️ Manual Lead Entry")
    st.markdown("---")
    if "manual_leads" not in st.session_state:
        st.session_state.manual_leads = [{"name": "", "email": "", "company": "", "website": ""}]

    def add_lead_row():
        st.session_state.manual_leads.append({"name": "", "email": "", "company": "", "website": ""})

    for i, lead in enumerate(st.session_state.manual_leads):
        cols = st.columns([3, 3, 3, 3, 1])
        st.session_state.manual_leads[i]["name"] = cols[0].text_input("Name", value=lead["name"], key=f"name_{i}", placeholder="Full Name")
        st.session_state.manual_leads[i]["email"] = cols[1].text_input("Email", value=lead["email"], key=f"email_{i}", placeholder="email@company.com")
        st.session_state.manual_leads[i]["company"] = cols[2].text_input("Company", value=lead["company"], key=f"company_{i}", placeholder="Acme Corp")
        st.session_state.manual_leads[i]["website"] = cols[3].text_input("Website", value=lead["website"], key=f"website_{i}", placeholder="acme.com")
        if cols[4].button("✕", key=f"del_{i}") and len(st.session_state.manual_leads) > 1:
            st.session_state.manual_leads.pop(i)
            st.rerun()

    st.button("➕ Add Row", on_click=add_lead_row)
    st.markdown("---")
    if st.button("⚡ Enrich & Score", use_container_width=True):
        valid_leads = [l for l in st.session_state.manual_leads if l.get("name", "").strip()]
        if not valid_leads:
            st.warning("Please enter at least one lead with a name.")
        else:
            with st.spinner("Processing..."):
                try:
                    db = get_db_session()
                    leads, stats = run_async(process_leads_from_list(valid_leads, db))
                    db.close()
                    st.success(f"✅ Enriched {stats.successfully_processed} lead(s)!")
                    st.dataframe(leads_to_df(leads), use_container_width=True)
                    st.session_state.manual_leads = [{"name": "", "email": "", "company": "", "website": ""}]
                except Exception as e:
                    st.error(f"Error: {e}")
                    raise


# ── Lead Browser ───────────────────────────────────────────────────────────────
elif page == "📋 Lead Browser":
    st.title("📋 Lead Browser")
    st.markdown("---")
    quality_filter = st.selectbox("Filter by Quality", ["All", "High", "Medium", "Low"])
    leads = get_all_leads(quality_filter)
    if not leads:
        st.info("No leads found. Upload some leads first!")
    else:
        st.markdown(f"**{len(leads)} leads** matching filter")
        st.dataframe(leads_to_df(leads), use_container_width=True, height=400)
        st.markdown("---")
        st.subheader("🔍 Lead Detail View")
        lead_ids = [l.id for l in leads]
        selected_id = st.selectbox("Select Lead ID", lead_ids, format_func=lambda x: f"#{x} — {next((l.name for l in leads if l.id == x), '')}")
        selected = next((l for l in leads if l.id == selected_id), None)
        if selected:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Contact Info**")
                st.markdown(f"- **Name:** {selected.name}")
                st.markdown(f"- **Email:** {selected.email or '—'} {'✓' if selected.email_valid else '✗'}")
                st.markdown(f"- **Company:** {selected.company or '—'}")
                st.markdown(f"- **Website:** {selected.website or '—'}")
            with c2:
                st.markdown("**Enrichment**")
                st.markdown(f"- **Industry:** {selected.industry or '—'}")
                st.markdown(f"- **Business Type:** {selected.business_type or '—'}")
                st.markdown(f"- **AI Confidence:** {selected.ai_confidence:.0%}")
                badge = f"badge-{selected.lead_quality_label.lower()}"
                st.markdown(f"- **Score:** {selected.lead_score}/100 — <span class='{badge}'>{selected.lead_quality_label}</span>", unsafe_allow_html=True)
            st.markdown("**Company Description**")
            st.info(selected.company_description or "No description available.")


# ── Export ─────────────────────────────────────────────────────────────────────
elif page == "📥 Export":
    st.title("📥 Export Leads")
    st.markdown("---")
    quality_filter = st.selectbox("Filter by Quality", ["All", "High", "Medium", "Low"])
    leads = get_all_leads(quality_filter)
    st.markdown(f"**{len(leads)} leads** ready for export")
    if leads:
        col_csv, col_json = st.columns(2)
        with col_csv:
            st.markdown("### 📊 CSV Export")
            filepath = export_leads_to_csv(leads)
            with open(filepath, "rb") as f:
                st.download_button("⬇️ Download CSV", data=f, file_name="enriched_leads.csv", mime="text/csv", use_container_width=True)
        with col_json:
            st.markdown("### 🔧 JSON Export")
            json_data = export_leads_to_json(leads)
            json_str = json.dumps(json_data, indent=2, default=str)
            st.download_button("⬇️ Download JSON", data=json_str, file_name="enriched_leads.json", mime="application/json", use_container_width=True)
        st.markdown("---")
        st.subheader("Preview")
        st.dataframe(leads_to_df(leads), use_container_width=True)
    else:
        st.info("No leads to export yet.")