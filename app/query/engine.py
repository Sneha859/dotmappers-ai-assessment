from __future__ import annotations

from functools import lru_cache
from typing import Any

import duckdb
import pandas as pd

from app.data.loader import create_connection
from app.llm.client import generate_sql
from app.query.validator import validate_sql


@lru_cache(maxsize=1)
def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Create and cache a single DuckDB connection for the application lifetime.

    The dataset is loaded once and reused for subsequent queries.
    """
    return create_connection()


def _format_value(value: Any) -> str:
    """
    Convert a result value into a clean user-facing string.
    """
    if pd.isna(value):
        return "N/A"

    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.2f}"

    return str(value)


def format_answer(result: pd.DataFrame) -> str:
    """
    Convert a DuckDB result DataFrame into a concise natural-language answer.

    Handles:
    - 0 rows
    - 1 row / 1 column
    - 1 row / multiple columns
    - multiple rows
    """
    if result.empty:
        return "No matching records were found."

    # ---------------------------------------------------------
    # Case 1: One value
    # Example:
    # open_ticket_count = 111
    # ---------------------------------------------------------
    if len(result) == 1 and len(result.columns) == 1:
        column = result.columns[0]
        value = _format_value(result.iloc[0][column])

        # More natural wording for common aggregate aliases.
        if column == "open_ticket_count":
            return f"There are {value} currently open tickets."

        if column == "ticket_count":
            return f"The ticket count is {value}."

        if column == "average_rating":
            return f"The average customer rating is {value}."

        if column == "avg_rating":
            return f"The average customer rating is {value}."

        if column == "resolved_count":
            return f"The resolved ticket count is {value}."

        return f"The result is {value}."

    # ---------------------------------------------------------
    # Case 2: One row with multiple columns
    # Example:
    # agent_id = AGT-01
    # resolved_count = 15
    #
    # Example:
    # category = General
    # ticket_count = 189
    # ---------------------------------------------------------
    if len(result) == 1 and len(result.columns) > 1:
        row = result.iloc[0]

        # Agent ranking query
        if "agent_id" in result.columns and "resolved_count" in result.columns:
            agent = _format_value(row["agent_id"])
            count = _format_value(row["resolved_count"])

            return (
                f"Agent {agent} resolved the most tickets this month, "
                f"with {count} resolved tickets."
            )

        # Category ranking query
        if "category" in result.columns and "ticket_count" in result.columns:
            category = _format_value(row["category"])
            count = _format_value(row["ticket_count"])

            return f"The category with the most tickets is {category}, with {count} tickets."

        # Generic fallback for other one-row multi-column results.
        parts = []

        for column in result.columns:
            value = _format_value(row[column])
            parts.append(f"{column}: {value}")

        return "The result is " + "; ".join(parts) + "."

    # ---------------------------------------------------------
    # Case 3: Multiple rows
    # ---------------------------------------------------------
    return f"The query returned {len(result)} result(s)."


def answer_question(question: str) -> dict[str, Any]:
    """
    Convert a natural-language question into safe SQL,
    execute it against DuckDB, and return the result.
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    generated = generate_sql(question)

    # Validate the SQL before execution.
    safe_sql = validate_sql(generated.sql)

    # Execute against the cached DuckDB connection.
    result_df = get_connection().execute(safe_sql).fetchdf()

    return {
        "question": question,
        "sql": safe_sql,
        "explanation": generated.explanation,
        "answer": format_answer(result_df),
        "results": result_df.to_dict(orient="records"),
    }