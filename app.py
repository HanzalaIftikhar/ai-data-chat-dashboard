import streamlit as st

st.set_page_config(page_title="Sales Chat Assistant", page_icon="📊", layout="wide")

try:
    from src.data_processing import process_uploaded_file, generate_summary, filter_valid_products
    from src.ai_engine import ask_question
    from src.logger_config import setup_logging

    setup_logging()
except ValueError as e:
    st.error(f"⚠️ Setup issue: {e}")
    st.info("Please check your `.env` file and make sure GROQ_API_KEY is set correctly.")
    st.stop()

# ---------------------------------------------------------------------------
# Custom styling — makes the app look like a polished product, not a
# default Streamlit template.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        max-width: 1100px;
    }

    /* Hero banner — the one bold color statement in the design */
    .hero-band {
        background: linear-gradient(135deg, #1F6F54 0%, #16543F 100%);
        border-radius: 16px;
        padding: 2rem 2.2rem;
        display: flex;
        align-items: center;
        gap: 1.2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 14px rgba(31,111,84,0.25);
    }
    .hero-icon { font-size: 2.6rem; line-height: 1; }
    .hero-title {
        font-family: 'Fraunces', serif;
        font-size: 2.1rem;
        font-weight: 700;
        color: #FAFAF7;
        margin-bottom: 0.2rem;
    }
    .hero-subtitle {
        color: rgba(250,250,247,0.85);
        font-size: 1.02rem;
    }

    /* Metric cards — each gets its own accent color on top */
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(31, 111, 84, 0.15);
        padding: 1.1rem 1.3rem;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetricValue"] {
        font-family: 'IBM Plex Mono', monospace;
        font-variant-numeric: tabular-nums;
    }
    [data-testid="stHorizontalBlock"] > div:nth-of-type(1) [data-testid="stMetric"] {
        border-top: 3px solid #1F6F54;
    }
    [data-testid="stHorizontalBlock"] > div:nth-of-type(2) [data-testid="stMetric"] {
        border-top: 3px solid #C89B3C;
    }
    [data-testid="stHorizontalBlock"] > div:nth-of-type(3) [data-testid="stMetric"] {
        border-top: 3px solid #B54834;
    }

    /* Sidebar — colored accent border instead of a hardcoded tint,
       so it works correctly in both light and dark mode */
    [data-testid="stSidebar"] {
        border-right: 2px solid rgba(31,111,84,0.25);
    }

    /* Sidebar numbered steps */
    .step-item {
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
        margin-bottom: 0.7rem;
    }
    .step-number {
        background-color: #1F6F54;
        color: #FAFAF7;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-family: 'IBM Plex Mono', monospace;
        flex-shrink: 0;
        margin-top: 0.15rem;
    }

    /* Signature element: dashed "receipt tear-line" divider */
    .receipt-divider {
        border: none;
        border-top: 2px dashed rgba(31, 111, 84, 0.3);
        margin: 1.8rem 0;
    }

    /* Platform badges — each platform gets its own accent color */
    .platform-badges span {
        padding: 0.3rem 0.75rem;
        border-radius: 20px;
        margin-right: 0.4rem;
        font-size: 0.85rem;
        font-family: 'IBM Plex Mono', monospace;
        border: 1px solid;
    }
    .platform-badges span:nth-child(1) {
        background-color: rgba(31,111,84,0.12);
        border-color: rgba(31,111,84,0.35);
    }
    .platform-badges span:nth-child(2) {
        background-color: rgba(200,155,60,0.14);
        border-color: rgba(200,155,60,0.4);
    }
    .platform-badges span:nth-child(3) {
        background-color: rgba(181,72,52,0.12);
        border-color: rgba(181,72,52,0.35);
    }

    /* Chat bubbles — user vs assistant get distinct tints */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background-color: rgba(31,111,84,0.06);
        border-radius: 12px;
        padding: 0.5rem 0.7rem;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        background-color: rgba(200,155,60,0.08);
        border-radius: 12px;
        padding: 0.5rem 0.7rem;
    }

    /* File uploader dropzone — ties into the ledger/receipt motif */
    [data-testid="stFileUploaderDropzone"] {
        background-color: rgba(31,111,84,0.04);
        border: 2px dashed rgba(31,111,84,0.35) !important;
        border-radius: 12px;
    }

    /* Expander headers get a touch of color */
    [data-testid="stExpander"] summary {
        background-color: rgba(31,111,84,0.05);
        border-radius: 8px;
    }
    

    /* Chat bubbles get a colored left-edge accent too */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        border-left: 3px solid #1F6F54;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        border-left: 3px solid #C89B3C;
    }

    /* One deliberate motion moment: the hero band eases in on load */
    .hero-band {
        animation: heroFadeIn 0.5s ease-out;
    }
    @keyframes heroFadeIn {
        from { opacity: 0; transform: translateY(-8px); }
        to { opacity: 1; transform: translateY(0); }
    }

        /* Section headings — match hero's Fraunces font with a colored accent bar */
    .section-heading {
        font-family: 'Fraunces', serif;
        font-size: 1.4rem;
        font-weight: 600;
        color: var(--text-color);
        border-left: 4px solid #1F6F54;
        padding-left: 0.6rem;
        margin: 0.4rem 0 0.9rem 0;
    }

    /* Empty state — replaces Streamlit's default blue info box */
    .empty-state {
        background-color: rgba(31,111,84,0.06);
        border: 1px dashed rgba(31,111,84,0.3);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        color: var(--text-color);
        font-size: 0.98rem;
    }

    /* Sidebar dividers — match the receipt dashed-line motif */
    [data-testid="stSidebar"] hr {
        border-top: 1px dashed rgba(31,111,84,0.3);
    }

        /* Receipt-style footer — closes out the ledger metaphor */
    .receipt-footer {
        margin-top: 3rem;
        text-align: center;
    }
    .receipt-footer p {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.8rem;
        color: var(--text-color);
        opacity: 0.5;
        letter-spacing: 0.03em;
    }

    /* Custom scrollbar — matches the brand color instead of default gray */
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background-color: rgba(31,111,84,0.35);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background-color: rgba(31,111,84,0.55);
    }

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar — quick "how it works" guide and platform info
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ℹ️ How it works")
    st.markdown("""
    <div class="step-item"><div class="step-number">1</div><div>Upload your sales export (CSV or Excel)</div></div>
    <div class="step-item"><div class="step-number">2</div><div>Get an instant summary — revenue, top products, trends</div></div>
    <div class="step-item"><div class="step-number">3</div><div>Ask anything about your data, in plain English</div></div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### Works with")
    st.markdown(
        '<div class="platform-badges">'
        '<span>🛍️ Shopify</span><span>🧵 Etsy</span><span>📦 Amazon</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.caption("AI Data Chat Dashboard — built by Hanzala")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero-band">
    <div class="hero-icon">📊</div>
    <div>
        <div class="hero-title">Sales Chat Assistant</div>
        <div class="hero-subtitle">Upload your sales data and get instant, AI-powered business insights.</div>
    </div>
</div>
""", unsafe_allow_html=True)
st.write("")

# --- Session state setup: memory that survives Streamlit's reruns ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df" not in st.session_state:
    st.session_state.df = None
if "summary" not in st.session_state:
    st.session_state.summary = None
if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = None

# --- File upload ---
uploaded_file = st.file_uploader("Upload your sales file (CSV or Excel)", type=["csv", "xlsx", "xls"])

is_new_file = uploaded_file is not None and uploaded_file.name != st.session_state.uploaded_filename

if is_new_file:
    with st.spinner("Reading and analyzing your data..."):
        try:
            df, detected_columns = process_uploaded_file(uploaded_file)
            clean_df = filter_valid_products(df)
            summary = generate_summary(df)
            st.session_state.df = clean_df
            st.session_state.summary = summary
            st.session_state.uploaded_filename = uploaded_file.name
            st.session_state.messages = []
            st.toast(f"Data loaded — {uploaded_file.name}", icon="✅")
        except ValueError as e:
            st.error(str(e))

# --- Show summary + chat only after a file is successfully loaded ---
if st.session_state.df is not None:
    df = st.session_state.df
    summary = st.session_state.summary

    st.markdown('<div class="section-heading">Quick Overview</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Total Revenue", f"${summary['total_revenue']:,.2f}")

    top_product_names = ", ".join(item["product"] for item in summary["top_products"][:1])
    col2.metric("🏆 Top Product", top_product_names or "N/A")

    insight = summary["insight"]
    if insight and insight["type"] == "declining_product":
        col3.metric("⚠️ Declining", insight["product"][:20] + "...", f"{insight['pct_change']}%")
    elif insight:
        col3.metric("📉 Lowest Seller", insight["product"][:20] + "...")

    col_a, col_b = st.columns(2)
    with col_a:
        with st.expander("📦 See top 3 products"):
            for item in summary["top_products"]:
                st.write(f"**{item['product']}** — ${item['revenue']:,.2f}")
    with col_b:
        with st.expander("🔍 Preview your data"):
            st.dataframe(df.head(20))

    st.markdown('<hr class="receipt-divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-heading" style="border-left-color:#C89B3C;">💬 Chat with your data</div>', unsafe_allow_html=True)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask a question about your sales data...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        groq_history = []
        for msg in st.session_state.messages[:-1]:
            groq_history.append({"role": msg["role"], "content": msg["content"]})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    answer = ask_question(df, summary, user_input, chat_history=groq_history)
                except RuntimeError as e:
                    answer = str(e)
                st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})

else:
    st.markdown("""
    <div class="empty-state">
        👆 Upload a sales export file above to get started — you'll get an instant summary and can chat with your data.
    </div>
    """, unsafe_allow_html=True)