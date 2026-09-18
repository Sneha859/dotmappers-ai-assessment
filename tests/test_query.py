from __future__ import annotations

import pandas as pd
import pytest

from app.models.schemas import GeneratedQuery
from app.query.engine import answer_question, format_answer
from app.query.validator import validate_sql


def test_validator_accepts_safe_select():
    sql = """
    SELECT COUNT(*) AS open_ticket_count
    FROM tickets
    WHERE status = 'Open';
    """

    validated = validate_sql(sql)

    assert "SELECT" in validated.upper()
    assert "tickets" in validated


def test_validator_rejects_non_select_sql():
    sql = """
    DELETE FROM tickets;
    """

    with pytest.raises(ValueError):
        validate_sql(sql)


def test_format_answer_single_value():
    result = pd.DataFrame(
        {
            "open_ticket_count": [111],
        }
    )

    answer = format_answer(result)

    assert answer == "There are 111 currently open tickets."


def test_format_answer_agent_result():
    result = pd.DataFrame(
        {
            "agent_id": ["AGT-01"],
            "resolved_count": [15],
        }
    )

    answer = format_answer(result)

    assert answer == (
        "Agent AGT-01 resolved the most tickets this month, "
        "with 15 resolved tickets."
    )


def test_format_answer_category_result():
    result = pd.DataFrame(
        {
            "category": ["General"],
            "ticket_count": [189],
        }
    )

    answer = format_answer(result)

    assert answer == (
        "The category with the most tickets is General, "
        "with 189 tickets."
    )


def test_format_answer_empty_result():
    result = pd.DataFrame()

    answer = format_answer(result)

    assert answer == "No matching records were found."


def test_answer_question_end_to_end_without_calling_llm(monkeypatch):
    generated = GeneratedQuery(
        intent="Count open tickets",
        sql="""
        SELECT COUNT(*) AS open_ticket_count
        FROM tickets
        WHERE status = 'Open';
        """,
        explanation="Counts tickets whose status is Open.",
    )

    monkeypatch.setattr(
        "app.query.engine.generate_sql",
        lambda question: generated,
    )

    response = answer_question("How many tickets are currently open?")

    assert response["question"] == "How many tickets are currently open?"
    assert response["answer"] == "There are 111 currently open tickets."
    assert response["results"][0]["open_ticket_count"] == 111
    assert "SELECT COUNT(*)" in response["sql"].upper()