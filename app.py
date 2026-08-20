import streamlit as st

st.set_page_config(page_title="Sales Chat Assistant", page_icon="📊", layout="wide")

try:
    from src.data_processing import process_uploaded_file, generate_summary
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
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 1rem 1.2rem;
        border-radius: 12px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .app-subtitle {
        opacity: 0.7;
        font-size: 1.05rem;
        margin-top: -0.5rem;
    }
    .platform-badges span {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.25);
        color: var(--text-color);
        padding: 0.3rem 0.7rem;
        border-radius: 20px;
        margin-right: 0.4rem;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar — quick "how it works" guide and platform info
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ℹ️ How it works")
    st.markdown("""
    1. **Upload** your sales export (CSV or Excel)
    2. Get an **instant summary** — revenue, top products, trends
    3. **Ask anything** about your data, in plain English
    """)
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
st.title("📊 Sales Chat Assistant")
st.markdown('<p class="app-subtitle">Upload your sales data and get instant, AI-powered business insights.</p>', unsafe_allow_html=True)
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
            summary = generate_summary(df)
            st.session_state.df = df
            st.session_state.summary = summary
            st.session_state.uploaded_filename = uploaded_file.name
            st.session_state.messages = []
        except ValueError as e:
            st.error(str(e))

# --- Show summary + chat only after a file is successfully loaded ---
if st.session_state.df is not None:
    df = st.session_state.df
    summary = st.session_state.summary

    st.subheader("Quick Overview")
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

    st.divider()
    st.subheader("💬 Chat with your data")

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
    st.info("👆 Upload a sales export file above to get started — you'll get an instant summary and can chat with your data.")