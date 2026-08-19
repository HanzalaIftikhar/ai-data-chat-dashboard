import streamlit as st

st.set_page_config(page_title="E-commerce Sales Chat Assistant", page_icon="📊", layout="wide")

try:
    from src.data_processing import process_uploaded_file, generate_summary
    from src.ai_engine import ask_question
    from src.logger_config import setup_logging

    setup_logging()
except ValueError as e:
    st.error(f"⚠️ Setup issue: {e}")
    st.info("Please check your `.env` file and make sure GROQ_API_KEY is set correctly.")
    st.stop()

st.title("📊 E-commerce Sales Chat Assistant")
st.caption("Upload your Shopify, Etsy, Amazon, or sales export and chat with your data.")

# --- Session state setup: memory that survives Streamlit's reruns ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df" not in st.session_state:
    st.session_state.df = None
if "summary" not in st.session_state:
    st.session_state.summary = None

# --- File upload ---
uploaded_file = st.file_uploader("Upload your sales file", type=["csv", "xlsx", "xls"])

if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = None

is_new_file = uploaded_file is not None and uploaded_file.name != st.session_state.uploaded_filename

if is_new_file:
    with st.spinner("Reading and analyzing your data..."):
        try:
            df, detected_columns = process_uploaded_file(uploaded_file)
            summary = generate_summary(df)
            st.session_state.df = df
            st.session_state.summary = summary
            st.session_state.uploaded_filename = uploaded_file.name
            st.session_state.messages = []  # reset chat for the new file
        except ValueError as e:
            st.error(str(e))


# --- Show summary + chat only after a file is successfully loaded ---
if st.session_state.df is not None:
    df = st.session_state.df
    summary = st.session_state.summary

    st.subheader("Quick Overview")
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Revenue", f"${summary['total_revenue']:,.2f}")

    top_product_names = ", ".join(item["product"] for item in summary["top_products"][:1])
    col2.metric("Top Product", top_product_names or "N/A")

    insight = summary["insight"]
    if insight and insight["type"] == "declining_product":
        col3.metric("⚠️ Declining", insight["product"], f"{insight['pct_change']}%")
    elif insight:
        col3.metric("Lowest Seller", insight["product"])

    with st.expander("See top 3 products"):
        for item in summary["top_products"]:
            st.write(f"**{item['product']}** — ${item['revenue']:,.2f}")

    with st.expander("Preview your data"):
        st.dataframe(df.head(20))

    st.divider()
    st.subheader("💬 Chat with your data")

    # Display past messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input box
    user_input = st.chat_input("Ask a question about your sales data...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Convert our chat history into the format Groq expects
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
    st.info("👆 Upload a sales export file to get started.")