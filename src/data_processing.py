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
    "product_name": ["product name", "lineitem name", "item name", "product-name"],
    "quantity": ["quantity", "lineitem quantity", "quantity-purchased", "qty"],
    "unit_price": ["lineitem price", "price", "item-price", "unit price"],
    "revenue": ["sales", "total", "item total", "order total"],
    "order_date": ["order date", "created at", "purchase-date"],
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