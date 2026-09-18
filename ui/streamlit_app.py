from __future__ import annotations

from typing import Any

import pandas as pd
import requests
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

API_BASE_URL = "http://127.0.0.1:8000"


# ============================================================
# STREAMLIT PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="DotMappers AI Support Intelligence",
    page_icon="🎫",
    layout="wide",
)


# ============================================================
# API HELPERS
# ============================================================

def api_get(endpoint: str) -> dict[str, Any]:
    """
    Send a GET request to the FastAPI backend.
    """

    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            timeout=60,
        )

        response.raise_for_status()

        return response.json()

    except requests.HTTPError as exc:
        try:
            detail = response.json().get(
                "detail",
                response.text,
            )
        except Exception:
            detail = response.text

        raise RuntimeError(
            f"API request failed "
            f"({response.status_code}): {detail}"
        ) from exc

    except requests.RequestException as exc:
        raise RuntimeError(
            "Could not connect to the FastAPI backend. "
            "Make sure the FastAPI server is running."
        ) from exc


def api_post(
    endpoint: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Send a POST request to the FastAPI backend.
    """

    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=payload,
            timeout=180,
        )

        response.raise_for_status()

        return response.json()

    except requests.HTTPError as exc:
        try:
            detail = response.json().get(
                "detail",
                response.text,
            )
        except Exception:
            detail = response.text

        raise RuntimeError(
            f"API request failed "
            f"({response.status_code}): {detail}"
        ) from exc

    except requests.RequestException as exc:
        raise RuntimeError(
            "Could not connect to the FastAPI backend. "
            "Make sure the FastAPI server is running."
        ) from exc


# ============================================================
# QUERY DISPLAY
# ============================================================

def display_query_result(result: dict[str, Any]) -> None:
    """
    Display the response returned by POST /query.
    """

    st.subheader("Answer")

    answer = result.get(
        "answer",
        "No answer was returned.",
    )

    st.success(answer)

    st.subheader("Explanation")

    explanation = result.get(
        "explanation",
        "No explanation was returned.",
    )

    st.write(explanation)

    with st.expander("View Generated SQL"):
        st.code(
            result.get("sql", ""),
            language="sql",
        )

    results = result.get("results", [])

    st.subheader("Query Results")

    if results:
        results_df = pd.DataFrame(results)

        st.dataframe(
            results_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No matching records were found.")


# ============================================================
# ANOMALY DISPLAY
# ============================================================

def display_anomaly_results(
    anomaly_data: dict[str, Any],
) -> None:
    """
    Display the response returned by GET /anomalies.
    """

    resolution_data = anomaly_data.get(
        "resolution_time_anomalies",
        {},
    )

    weekly_data = anomaly_data.get(
        "weekly_resolution_time_anomalies",
        {},
    )

    stale_data = anomaly_data.get(
        "stale_priority_tickets",
        {},
    )

    # --------------------------------------------------------
    # Summary cards
    # --------------------------------------------------------

    st.subheader("Anomaly Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Resolution-Time Anomalies",
            resolution_data.get(
                "anomaly_count",
                0,
            ),
        )

    with col2:
        st.metric(
            "This Week",
            weekly_data.get(
                "anomaly_count",
                0,
            ),
        )

    with col3:
        st.metric(
            "Stale High/Critical",
            stale_data.get(
                "anomaly_count",
                0,
            ),
        )

    reference_time = anomaly_data.get(
        "reference_time",
        "Unknown",
    )

    st.caption(
        f"Dataset reference time: {reference_time}"
    )

    st.divider()

    # --------------------------------------------------------
    # Rule 1: IQR
    # --------------------------------------------------------

    st.subheader(
        "⏱️ Unusually Long Resolution Times"
    )

    st.write(
        "Resolved tickets are flagged as anomalies when their "
        "resolution time exceeds the IQR-based upper bound."
    )

    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

    with stat_col1:
        q1 = resolution_data.get("q1_hours")

        st.metric(
            "Q1",
            f"{q1:.2f} hrs"
            if q1 is not None
            else "N/A",
        )

    with stat_col2:
        q3 = resolution_data.get("q3_hours")

        st.metric(
            "Q3",
            f"{q3:.2f} hrs"
            if q3 is not None
            else "N/A",
        )

    with stat_col3:
        iqr = resolution_data.get("iqr_hours")

        st.metric(
            "IQR",
            f"{iqr:.2f} hrs"
            if iqr is not None
            else "N/A",
        )

    with stat_col4:
        upper_bound = resolution_data.get(
            "upper_bound_hours"
        )

        st.metric(
            "Upper Bound",
            f"{upper_bound:.2f} hrs"
            if upper_bound is not None
            else "N/A",
        )

    resolution_records = resolution_data.get(
        "anomalies",
        [],
    )

    if resolution_records:

        resolution_df = pd.DataFrame(
            resolution_records
        )

        columns_to_show = [
            "ticket_id",
            "created_at",
            "priority",
            "status",
            "resolution_time_hrs",
            "agent_id",
            "issue_summary",
        ]

        columns_to_show = [
            column
            for column in columns_to_show
            if column in resolution_df.columns
        ]

        st.dataframe(
            resolution_df[columns_to_show],
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.success(
            "No resolution-time anomalies detected."
        )

    st.divider()

    # --------------------------------------------------------
    # Rule 1 - This week
    # --------------------------------------------------------

    st.subheader(
        "📅 Resolution-Time Anomalies This Week"
    )

    weekly_records = weekly_data.get(
        "anomalies",
        [],
    )

    if weekly_records:

        weekly_df = pd.DataFrame(
            weekly_records
        )

        columns_to_show = [
            "ticket_id",
            "created_at",
            "resolved_at",
            "priority",
            "resolution_time_hrs",
            "agent_id",
            "issue_summary",
        ]

        columns_to_show = [
            column
            for column in columns_to_show
            if column in weekly_df.columns
        ]

        st.dataframe(
            weekly_df[columns_to_show],
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.success(
            "No resolution-time anomalies detected "
            "during the latest dataset week."
        )

    st.divider()

    # --------------------------------------------------------
    # Rule 2: stale high/critical tickets
    # --------------------------------------------------------

    st.subheader(
        "🚨 Unresolved High/Critical Tickets Older Than 24 Hours"
    )

    st.write(
        "Tickets are flagged when they are unresolved, have "
        "High or Critical priority, and are older than 24 hours "
        "relative to the dataset reference time."
    )

    age_threshold = stale_data.get(
        "age_threshold_hours",
        24,
    )

    st.metric(
        "Age Threshold",
        f"{age_threshold:.0f} hrs",
    )

    stale_records = stale_data.get(
        "anomalies",
        [],
    )

    if stale_records:

        stale_df = pd.DataFrame(
            stale_records
        )

        columns_to_show = [
            "ticket_id",
            "created_at",
            "category",
            "priority",
            "status",
            "agent_id",
            "age_hours",
            "issue_summary",
        ]

        columns_to_show = [
            column
            for column in columns_to_show
            if column in stale_df.columns
        ]

        st.dataframe(
            stale_df[columns_to_show],
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.success(
            "No stale High/Critical tickets detected."
        )


# ============================================================
# HEADER
# ============================================================

st.title(
    "🎫 DotMappers AI Support Ticket Intelligence"
)

st.write(
    "An AI-powered support-ticket analytics system that "
    "answers natural-language questions and detects "
    "data-driven anomalies."
)

st.caption(
    "FastAPI • Ollama / Qwen3 4B • DuckDB • Streamlit"
)


# ============================================================
# BACKEND HEALTH
# ============================================================

try:

    health = api_get("/health")

    health_col1, health_col2, health_col3 = st.columns(3)

    with health_col1:
        st.metric(
            "Dataset Rows",
            health.get(
                "dataset_rows",
                0,
            ),
        )

    with health_col2:
        st.metric(
            "LLM",
            health.get(
                "llm_model",
                "Unknown",
            ),
        )

    with health_col3:

        status = health.get(
            "status",
            "unknown",
        )

        if status.lower() == "healthy":
            st.success("API: HEALTHY")
        else:
            st.warning(
                f"API: {status.upper()}"
            )

except RuntimeError as exc:

    st.error(str(exc))

    st.stop()


st.divider()


# ============================================================
# NATURAL LANGUAGE QUERY
# ============================================================

st.header("💬 Ask About Your Tickets")

st.write(
    "Ask a question in normal language. "
    "The local LLM converts your question into a safe SQL query, "
    "and DuckDB calculates the answer from the dataset."
)


example_questions = [
    "How many tickets are currently open?",
    "Which agent resolved the most tickets this month?",
    "Show me all Critical tickets not resolved within 12 hours.",
    "What is the average customer rating for Technical category tickets?",
    "How many Critical tickets are unresolved?",
    "Which category has the most tickets?",
]


selected_question = st.selectbox(
    "Choose an example or write your own question",
    options=[
        "Write my own question"
    ] + example_questions,
)


if selected_question == "Write my own question":

    default_question = ""

else:

    default_question = selected_question


question = st.text_input(
    "Your question",
    value=default_question,
    max_chars=500,
    placeholder=(
        "Example: How many Critical tickets are unresolved?"
    ),
)


ask_button = st.button(
    "🔍 Ask AI",
    type="primary",
)


if ask_button:

    if not question.strip():

        st.warning(
            "Please enter a question."
        )

    else:

        with st.spinner(
            "Understanding your question and querying the dataset..."
        ):

            try:

                query_result = api_post(
                    "/query",
                    {
                        "question": question.strip()
                    },
                )

                display_query_result(
                    query_result
                )

            except RuntimeError as exc:

                st.error(str(exc))


st.divider()


# ============================================================
# ANOMALY DETECTION
# ============================================================

st.header("🚨 Anomaly Detection")

st.write(
    "Run deterministic anomaly-detection rules on the "
    "support-ticket dataset."
)


anomaly_button = st.button(
    "Run Anomaly Detection"
)


if anomaly_button:

    with st.spinner(
        "Analyzing support-ticket anomalies..."
    ):

        try:

            anomaly_result = api_get(
                "/anomalies"
            )

            display_anomaly_results(
                anomaly_result
            )

        except RuntimeError as exc:

            st.error(str(exc))


st.divider()


# ============================================================
# FOOTER
# ============================================================

st.caption(
    "Relative dates such as 'this week' and 'this month' "
    "use the latest timestamp available in the supplied dataset "
    "as the reference time."
)