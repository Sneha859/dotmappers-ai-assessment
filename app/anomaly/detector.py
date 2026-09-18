from __future__ import annotations

from typing import Any

import pandas as pd

from app.data.loader import load_dataframe


HIGH_PRIORITY_LEVELS = {"High", "Critical"}


def _records_to_json_safe(
    df: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Convert a DataFrame into JSON-safe Python dictionaries.
    """

    if df.empty:
        return []

    result = df.copy()

    for column in result.columns:
        if pd.api.types.is_datetime64_any_dtype(result[column]):
            result[column] = result[column].apply(
                lambda value: value.isoformat()
                if pd.notna(value)
                else None
            )

    result = result.astype(object).where(
        pd.notna(result),
        None,
    )

    return result.to_dict(orient="records")


def _prepare_dataset() -> tuple[pd.DataFrame, pd.Timestamp]:
    """
    Load the dataset and derive a resolution timestamp.

    The assessment dataset provides created_at and
    resolution_time_hrs but does not provide a resolved_at column.
    """

    df = load_dataframe().copy()

    if df.empty:
        raise ValueError("The support-ticket dataset is empty.")

    reference_time = df["created_at"].max()

    df["resolved_at"] = pd.NaT

    resolved_mask = (
        df["status"].eq("Resolved")
        & df["resolution_time_hrs"].notna()
    )

    df.loc[resolved_mask, "resolved_at"] = (
        df.loc[resolved_mask, "created_at"]
        + pd.to_timedelta(
            df.loc[resolved_mask, "resolution_time_hrs"],
            unit="h",
        )
    )

    return df, reference_time


def detect_resolution_anomalies(
    week_only: bool = False,
) -> dict[str, Any]:
    """
    Detect unusually long resolution times using the IQR rule.

    Threshold:
        upper_bound = Q3 + 1.5 * IQR

    When week_only=True, the global IQR threshold is retained and
    only anomalies resolved within the latest seven-day dataset
    window are returned.
    """

    df, reference_time = _prepare_dataset()

    resolved = df[
        df["status"].eq("Resolved")
        & df["resolution_time_hrs"].notna()
    ].copy()

    if resolved.empty:
        return {
            "rule": "IQR resolution-time anomaly detection",
            "reference_time": reference_time.isoformat(),
            "week_only": week_only,
            "q1_hours": None,
            "q3_hours": None,
            "iqr_hours": None,
            "upper_bound_hours": None,
            "anomaly_count": 0,
            "anomalies": [],
        }

    q1 = float(
        resolved["resolution_time_hrs"].quantile(0.25)
    )
    q3 = float(
        resolved["resolution_time_hrs"].quantile(0.75)
    )

    iqr = q3 - q1
    upper_bound = q3 + (1.5 * iqr)

    anomalies = resolved[
        resolved["resolution_time_hrs"] > upper_bound
    ].copy()

    if week_only:
        week_start = (
            reference_time - pd.Timedelta(days=7)
        )

        anomalies = anomalies[
            (anomalies["resolved_at"] >= week_start)
            & (anomalies["resolved_at"] <= reference_time)
        ].copy()

    selected_columns = [
        "ticket_id",
        "created_at",
        "category",
        "priority",
        "status",
        "response_time_hrs",
        "resolution_time_hrs",
        "resolved_at",
        "agent_id",
        "customer_rating",
        "issue_summary",
    ]

    anomalies = anomalies[
        selected_columns
    ].sort_values(
        "resolution_time_hrs",
        ascending=False,
    )

    return {
        "rule": "IQR resolution-time anomaly detection",
        "reference_time": reference_time.isoformat(),
        "week_only": week_only,
        "q1_hours": round(q1, 2),
        "q3_hours": round(q3, 2),
        "iqr_hours": round(iqr, 2),
        "upper_bound_hours": round(
            upper_bound,
            2,
        ),
        "anomaly_count": len(anomalies),
        "anomalies": _records_to_json_safe(
            anomalies
        ),
    }


def detect_stale_priority_tickets() -> dict[str, Any]:
    """
    Detect unresolved High/Critical tickets older than 24 hours.

    Age is calculated relative to the latest created_at timestamp
    in the supplied historical dataset.
    """

    df, reference_time = _prepare_dataset()

    age_threshold_hours = 24.0

    age_cutoff = (
        reference_time
        - pd.Timedelta(hours=age_threshold_hours)
    )

    stale = df[
        (~df["status"].eq("Resolved"))
        & df["priority"].isin(HIGH_PRIORITY_LEVELS)
        & (df["created_at"] < age_cutoff)
    ].copy()

    stale["age_hours"] = (
        reference_time - stale["created_at"]
    ).dt.total_seconds() / 3600.0

    selected_columns = [
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
        "age_hours",
    ]

    stale = stale[
        selected_columns
    ].sort_values(
        "age_hours",
        ascending=False,
    )

    return {
        "rule": (
            "Unresolved High/Critical tickets "
            "older than 24 hours"
        ),
        "reference_time": reference_time.isoformat(),
        "age_threshold_hours": age_threshold_hours,
        "anomaly_count": len(stale),
        "anomalies": _records_to_json_safe(
            stale
        ),
    }


def detect_anomalies() -> dict[str, Any]:
    """
    Run all required anomaly-detection rules.
    """

    resolution_result = detect_resolution_anomalies(
        week_only=False
    )

    weekly_resolution_result = detect_resolution_anomalies(
        week_only=True
    )

    stale_result = detect_stale_priority_tickets()

    # Count unique tickets across the two top-level anomaly rules.
    resolution_ticket_ids = {
        record["ticket_id"]
        for record in resolution_result["anomalies"]
        if record.get("ticket_id")
    }

    stale_ticket_ids = {
        record["ticket_id"]
        for record in stale_result["anomalies"]
        if record.get("ticket_id")
    }

    unique_anomaly_ticket_ids = (
        resolution_ticket_ids
        | stale_ticket_ids
    )

    return {
        "reference_time": resolution_result[
            "reference_time"
        ],
        "resolution_time_anomalies": resolution_result,
        "weekly_resolution_time_anomalies": (
            weekly_resolution_result
        ),
        "stale_priority_tickets": stale_result,
        "total_anomalies": len(
            unique_anomaly_ticket_ids
        ),
    }