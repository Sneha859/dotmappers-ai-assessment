import re

import sqlglot
from sqlglot import exp


class SQLValidationError(ValueError):
    """Raised when LLM-generated SQL violates application safety rules."""


ALLOWED_TABLES = {"tickets"}


def _normalize_sql(sql: str) -> str:
    """
    Normalize common formatting artifacts returned by an LLM.

    The model may return:
    - literal escaped newlines (\\n)
    - literal escaped tabs (\\t)
    - markdown SQL fences
    - unnecessary leading/trailing whitespace

    This function changes formatting only. It does not change SQL logic.
    """

    if not isinstance(sql, str):
        raise SQLValidationError("Generated SQL must be a string.")

    normalized = sql.strip()

    # Remove common markdown code fences if the model accidentally adds them.
    normalized = re.sub(
        r"^```(?:sql)?\s*",
        "",
        normalized,
        flags=re.IGNORECASE,
    )

    normalized = re.sub(
        r"\s*```$",
        "",
        normalized,
    )

    # Convert literal escape sequences into actual whitespace.
    normalized = normalized.replace("\\r\\n", "\n")
    normalized = normalized.replace("\\n", "\n")
    normalized = normalized.replace("\\t", "\t")
    normalized = normalized.replace("\\r", "\r")

    return normalized.strip()


def validate_sql(sql: str) -> str:
    """
    Validate LLM-generated SQL before execution.

    Security rules:
    - SQL must not be empty.
    - Exactly one statement is allowed.
    - Only read-only SELECT queries are allowed.
    - WITH/CTE queries are allowed.
    - Only the physical table 'tickets' may be referenced.
    - CTEs defined inside the same statement are allowed.
    """

    normalized_sql = _normalize_sql(sql)

    if not normalized_sql:
        raise SQLValidationError("Generated SQL is empty.")

    # ---------------------------------------------------------
    # Parse the normalized SQL using SQLGlot.
    # ---------------------------------------------------------
    try:
        statements = sqlglot.parse(
            normalized_sql,
            read="duckdb",
        )
    except Exception as exc:
        raise SQLValidationError(
            f"Generated SQL could not be parsed: {exc}"
        ) from exc

    # ---------------------------------------------------------
    # Only one SQL statement is permitted.
    # ---------------------------------------------------------
    if len(statements) != 1:
        raise SQLValidationError(
            "Only one SQL statement is allowed."
        )

    statement = statements[0]

    # ---------------------------------------------------------
    # Only SELECT-style read queries are permitted.
    #
    # SELECT and UNION queries are supported.
    # WITH ... SELECT is represented by SQLGlot as a SELECT
    # containing a WITH expression.
    # ---------------------------------------------------------
    if not isinstance(statement, (exp.Select, exp.Union)):
        raise SQLValidationError(
            "Only read-only SELECT queries are allowed."
        )

    # ---------------------------------------------------------
    # Collect CTE names defined inside this query.
    #
    # Example:
    #
    # WITH resolved_tickets AS (...)
    # SELECT ...
    # FROM resolved_tickets
    #
    # resolved_tickets is an internal CTE, not an external table.
    # ---------------------------------------------------------
    cte_names = {
        cte.alias_or_name.lower()
        for cte in statement.find_all(exp.CTE)
        if cte.alias_or_name
    }

    # ---------------------------------------------------------
    # Collect every referenced table.
    # ---------------------------------------------------------
    referenced_tables = {
        table.name.lower()
        for table in statement.find_all(exp.Table)
        if table.name
    }

    # Physical references may only be:
    # - tickets
    # - CTEs defined inside this query
    allowed_references = ALLOWED_TABLES | cte_names

    invalid_tables = referenced_tables - allowed_references

    if invalid_tables:
        raise SQLValidationError(
            "Unauthorized tables referenced: "
            f"{sorted(invalid_tables)}"
        )

    return normalized_sql