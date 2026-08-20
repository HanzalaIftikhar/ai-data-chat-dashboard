import io
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column mapping: our standard internal name -> list of known column names
# used by different platforms. All matching is done in lowercase, so
# "Product Name" (Superstore) and "product-name" (Amazon) both match.
# ---------------------------------------------------------------------------
COLUMN_MAPPING = {
    "product_name": ["product name", "lineitem name", "item name", "product-name", "description"],
    "quantity": ["quantity", "lineitem quantity", "quantity-purchased", "qty"],
    "unit_price": ["lineitem price", "price", "item-price", "unit price", "unitprice"],
    "revenue": ["sales", "total", "item total", "order total", "amount"],
    "order_date": ["order date", "created at", "purchase-date", "invoicedate"],
    "status": ["status", "fulfillment status", "order-status", "financial status", "order status"],
}


def load_file(uploaded_file):
    """
    Reads an uploaded CSV or Excel file into a pandas DataFrame.
    Raises a clear ValueError for common problems, instead of letting
    pandas throw a confusing raw error.
    """
    filename = uploaded_file.name

    if filename.endswith(".csv"):
        uploaded_file.seek(0)
        raw_bytes = uploaded_file.read()

        # Try UTF-8 first (most common). Fall back to Latin-1, which can
        # decode any byte sequence and handles older Excel-exported CSVs.
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = raw_bytes.decode("latin-1")

        try:
            df = pd.read_csv(io.StringIO(text))
        except pd.errors.EmptyDataError:
            raise ValueError("This file appears to be empty.")
        except Exception as e:
            logger.error(f"Failed to parse CSV {filename}: {e}")
            raise ValueError("Could not read the file. It may be corrupted or in an unexpected format.")

    elif filename.endswith((".xlsx", ".xls")):
        try:
            df = pd.read_excel(uploaded_file)
        except Exception as e:
            logger.error(f"Failed to read file {filename}: {e}")
            raise ValueError("Could not read the file. It may be corrupted or in an unexpected format.")

    else:
        raise ValueError("Unsupported file type. Please upload a .csv or .xlsx file.")

    if df.empty:
        raise ValueError("The uploaded file has no data rows.")

    return df


def detect_columns(df):
    """
    Compares the DataFrame's actual column names against COLUMN_MAPPING
    to figure out which standard field each column represents.

    Returns something like:
    {"product_name": "Lineitem name", "revenue": "Sales", ...}

    Only fields that were actually found in this file are included.
    """
    detected = {}
    lower_columns = {col.lower().strip(): col for col in df.columns}

    for standard_name, known_variations in COLUMN_MAPPING.items():
        for variation in known_variations:
            if variation in lower_columns:
                detected[standard_name] = lower_columns[variation]
                break  # stop checking once we find a match for this field

    return detected


def normalize_dataframe(df, detected_columns):
    """
    Renames platform-specific columns to our standard internal names.
    Example: "Lineitem name" -> "product_name"
    """
    rename_map = {original: standard for standard, original in detected_columns.items()}
    return df.rename(columns=rename_map)


def process_uploaded_file(uploaded_file):
    """
    Main entry point: reads the file, detects columns, validates that
    the essentials are present, and returns a normalized DataFrame.
    """
    df = load_file(uploaded_file)
    detected_columns = detect_columns(df)

    if "product_name" not in detected_columns:
        raise ValueError(
            "Could not find a product name column. Please check that your "
            "file has a column like 'Product Name', 'Item Name', or similar."
        )

    if "revenue" not in detected_columns and "unit_price" not in detected_columns:
        raise ValueError(
            "Could not find a price or revenue column. Please check that your "
            "file has a column like 'Sales', 'Price', or 'Total'."
        )

    normalized_df = normalize_dataframe(df, detected_columns)

    logger.info(f"Detected columns: {detected_columns}")

    return normalized_df, detected_columns

def calculate_total_revenue(df):
    """
    Returns the total revenue across all rows.
    Uses the 'revenue' column if present; otherwise calculates it
    from quantity * unit_price (needed for platforms like Shopify
    where raw exports only have per-unit price).
    """
    if "revenue" in df.columns:
        return round(df["revenue"].sum(), 2)
    elif "quantity" in df.columns and "unit_price" in df.columns:
        return round((df["quantity"] * df["unit_price"]).sum(), 2)
    else:
        return None


def get_top_products(df, top_n=3):
    """
    Returns the top N products by total revenue, as a list of dicts:
    [{"product": "Chair", "revenue": 1234.56}, ...]
    """
    if "product_name" not in df.columns:
        return []

    working_df = df.copy()

    if "revenue" not in working_df.columns:
        if "quantity" in working_df.columns and "unit_price" in working_df.columns:
            working_df["revenue"] = working_df["quantity"] * working_df["unit_price"]
        else:
            return []

    grouped = (
        working_df.groupby("product_name")["revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(top_n)
    )

    return [{"product": name, "revenue": round(value, 2)} for name, value in grouped.items()]


def detect_notable_insight(df):
    """
    Tries to find a "declining product" insight by comparing the first
    half of the date range against the second half. If order_date isn't
    available, falls back to reporting the lowest-selling product instead.
    """
    has_date = "order_date" in df.columns
    has_revenue_data = "revenue" in df.columns or (
        "quantity" in df.columns and "unit_price" in df.columns
    )

    if not has_revenue_data or "product_name" not in df.columns:
        return None

    working_df = df.copy()
    if "revenue" not in working_df.columns:
        working_df["revenue"] = working_df["quantity"] * working_df["unit_price"]

    # --- Case 1: we have dates, so we can detect a declining trend ---
    if has_date:
        working_df["order_date"] = pd.to_datetime(working_df["order_date"], errors="coerce")
        working_df = working_df.dropna(subset=["order_date"])

        if len(working_df) >= 4:  # need enough rows to split meaningfully
            midpoint = working_df["order_date"].median()
            first_half = working_df[working_df["order_date"] <= midpoint]
            second_half = working_df[working_df["order_date"] > midpoint]

            first_totals = first_half.groupby("product_name")["revenue"].sum()
            second_totals = second_half.groupby("product_name")["revenue"].sum()

            comparison = first_totals.to_frame("first_half").join(
                second_totals.to_frame("second_half"), how="inner"
            )

            if not comparison.empty:
                comparison["pct_change"] = (
                    (comparison["second_half"] - comparison["first_half"])
                    / comparison["first_half"]
                ) * 100
                declining = comparison.sort_values("pct_change").iloc[0]

                if declining["pct_change"] < 0:
                    return {
                        "type": "declining_product",
                        "product": comparison.sort_values("pct_change").index[0],
                        "pct_change": round(declining["pct_change"], 1),
                    }

    # --- Case 2: fallback when no usable dates ---
    totals = working_df.groupby("product_name")["revenue"].sum().sort_values()
    if not totals.empty:
        return {
            "type": "lowest_selling_product",
            "product": totals.index[0],
            "revenue": round(totals.iloc[0], 2),
        }

    return None


def generate_summary(df):
    """
    Main entry point for Part 2: combines revenue, top products, and
    a notable insight into a single summary dictionary that app.py
    can display right after file upload.
    """
    return {
        "total_revenue": calculate_total_revenue(df),
        "top_products": get_top_products(df),
        "insight": detect_notable_insight(df),
    }

