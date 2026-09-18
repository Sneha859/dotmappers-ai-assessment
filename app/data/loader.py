from pathlib import Path

import duckdb
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data" / "support_tickets.csv"

EXPECTED_COLUMNS = [
    "ticket_id",
    "created_at",
    "category",
    "priority",
    "status",
    "response_time_hrs",
    "resolution_time_hrs",
    "agent_id",
    "customer_rating",
    "issue_summary",
]


def load_dataframe() -> pd.DataFrame:
    """Load and validate the support ticket dataset."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    missing_columns = [
        column for column in EXPECTED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    df["created_at"] = pd.to_datetime(
        df["created_at"],
        errors="coerce"
    )

    if df["created_at"].isna().any():
        raise ValueError("Invalid created_at values found.")

    if df["ticket_id"].duplicated().any():
        raise ValueError("Duplicate ticket_id values found.")

    return df


def create_connection() -> duckdb.DuckDBPyConnection:
    """Create an in-memory DuckDB database from the CSV."""
    df = load_dataframe()

    connection = duckdb.connect(":memory:")

    connection.register("tickets_dataframe", df)

    connection.execute("""
        CREATE TABLE tickets AS
        SELECT *
        FROM tickets_dataframe
    """)

    return connection
