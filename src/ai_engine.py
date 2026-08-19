import json
import pandas as pd
from groq import Groq
import logging

from src.config import GROQ_API_KEY, GROQ_MODEL_NAME

logger = logging.getLogger(__name__)

client = Groq(api_key=GROQ_API_KEY)

# ---------------------------------------------------------------------------
# Tool definition: this tells the AI "you have a calculator available,
# here's how to use it." The AI never runs this itself — it just requests
# it, and our own code executes it safely.
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_dataframe",
            "description": (
                "Run a single pandas expression against the sales data (variable name `df`) "
                "to get exact numbers, rankings, filters, sums, or counts. Use this any time "
                "you need a precise answer instead of guessing. Available columns include: "
                "product_name, quantity, unit_price, revenue, order_date, status, plus other "
                "original columns from the file. "
                "Examples: "
                "\"df.groupby('product_name')['revenue'].sum().sort_values().head(3)\" "
                "\"df['revenue'].sum()\" "
                "\"df[df['status'] == 'Cancelled'].shape[0]\""
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A single pandas expression using `df`. No assignments, imports, or loops — just one calculation.",
                    }
                },
                "required": ["expression"],
            },
        },
    }
]


def run_dataframe_query(df, expression):
    """
    Safely evaluates a pandas expression against the DataFrame.
    Blocks anything that looks like it's trying to do something
    beyond a simple read-only calculation (imports, file access, etc).
    """
    forbidden = ["import", "__", "open(", "exec(", "eval(", "os.", "sys.", "subprocess"]
    lowered = expression.lower()
    if any(bad in lowered for bad in forbidden):
        return "Error: This expression is not allowed for security reasons."

    try:
        safe_globals = {"__builtins__": {}}
        safe_locals = {"df": df, "pd": pd}
        result = eval(expression, safe_globals, safe_locals)

        result_str = str(result)
        if len(result_str) > 2000:
            result_str = result_str[:2000] + "... (truncated)"
        return result_str
    except Exception as e:
        return f"Error running that calculation: {e}"


def build_context_prompt(df, summary):
    """
    Gives the AI a quick overview of the dataset, plus instructions
    on when to use the query_dataframe tool for anything precise.
    """
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
Answer with business context, not just raw numbers — relate numbers to trends,
comparisons, or possible causes. Keep answers concise and conversational.

For ANY question that needs a specific number, ranking, filter, or calculation
that isn't already given below, use the query_dataframe tool to get the exact
answer from the real data. Do not guess or make up numbers.

QUICK OVERVIEW (already known, no need to query for these):
Total Revenue: ${summary['total_revenue']:,}

Top 3 Products by Revenue:
{top_products_text}

Notable Insight:
{insight_text}
"""
    return context.strip()


def ask_question(df, summary, user_question, chat_history=None):
    """
    Sends the user's question to the AI. If the AI needs exact data,
    it requests the query_dataframe tool, we run it, and send the
    result back so the AI can explain it in plain business language.
    """
    try:
        messages = [{"role": "system", "content": build_context_prompt(df, summary)}]

        if chat_history:
            messages.extend(chat_history)

        messages.append({"role": "user", "content": user_question})

        response = client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        response_message = response.choices[0].message

        # --- Case 1: AI wants to run a calculation first ---
        if response_message.tool_calls:
            messages.append({
                "role": "assistant",
                "content": response_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in response_message.tool_calls
                ],
            })

            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "query_dataframe":
                    args = json.loads(tool_call.function.arguments)
                    expression = args.get("expression", "")
                    logger.info(f"Running pandas query: {expression}")

                    result = run_dataframe_query(df, expression)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })

            # Ask again, now that the AI has the real result
            second_response = client.chat.completions.create(
                model=GROQ_MODEL_NAME,
                messages=messages,
            )
            return second_response.choices[0].message.content

        # --- Case 2: AI already knew the answer, no calculation needed ---
        return response_message.content

    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        raise RuntimeError(
            "Couldn't get a response from the AI right now. Please try again in a moment."
        )