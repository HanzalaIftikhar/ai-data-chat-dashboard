import google.generativeai as genai
import logging

from src.config import GEMINI_API_KEY, GEMINI_MODEL_NAME

logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)


def build_context_prompt(df, summary):
    """
    Converts the dataset summary + a small sample of rows into a text
    block that gets injected into the system prompt, so Gemini
    "understands" the data without us sending the entire file.
    """
    sample_rows = df.head(8).to_string(index=False)

    top_products_text = "\n".join(
        f"- {item['product']}: ${item['revenue']:,}"
        for item in summary["top_products"]
    )

    insight = summary["insight"]
    if insight is None:
        insight_text = "No specific trend insight available."
    elif insight["type"] == "declining_product":
        insight_text = (
            f"'{insight['product']}' sales dropped {abs(insight['pct_change'])}% "
            f"between the first and second half of the available date range."
        )
    else:
        insight_text = (
            f"'{insight['product']}' is the lowest-selling product, "
            f"with total revenue of ${insight['revenue']:,}."
        )

    context = f"""
You are a business analyst assistant for an e-commerce seller (Shopify/Etsy/Amazon).
You are given their sales data and must answer questions with business context,
not just raw numbers. Always relate numbers to trends, comparisons, or possible
causes where relevant. Keep answers concise and conversational, like a knowledgeable
analyst would explain things to a busy store owner.

DATASET OVERVIEW:
Total Revenue: ${summary['total_revenue']:,}

Top 3 Products by Revenue:
{top_products_text}

Notable Insight:
{insight_text}

Sample of the raw data (first 8 rows, for reference):
{sample_rows}
"""
    return context.strip()


def ask_question(df, summary, user_question, chat_history=None):
    """
    Sends the user's question to Gemini, along with dataset context.
    chat_history (optional) lets the model see previous turns of the
    conversation for follow-up questions.
    """
    try:
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL_NAME,
            system_instruction=build_context_prompt(df, summary),
        )

        chat = model.start_chat(history=chat_history or [])
        response = chat.send_message(user_question)

        return response.text

    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        raise RuntimeError(
            "Couldn't get a response from the AI right now. Please try again in a moment."
        )