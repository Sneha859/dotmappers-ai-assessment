from __future__ import annotations

from app.anomaly.detector import detect_anomalies


def test_anomaly_detection_counts():
    result = detect_anomalies()

    assert result["resolution_time_anomalies"]["anomaly_count"] == 21
    assert result["weekly_resolution_time_anomalies"]["anomaly_count"] == 3
    assert result["stale_priority_tickets"]["anomaly_count"] == 80
    assert result["total_anomalies"] == 101


def test_iqr_resolution_anomaly_threshold():
    result = detect_anomalies()

    resolution = result["resolution_time_anomalies"]

    assert round(resolution["q1_hours"], 2) == 6.15
    assert round(resolution["q3_hours"], 2) == 22.95
    assert round(resolution["iqr_hours"], 2) == 16.80
    assert round(resolution["upper_bound_hours"], 2) == 48.15


def test_weekly_anomaly_result_uses_week_filter():
    result = detect_anomalies()

    weekly = result["weekly_resolution_time_anomalies"]

    assert weekly["week_only"] is True
    assert weekly["anomaly_count"] == 3


def test_stale_high_critical_ticket_detection():
    result = detect_anomalies()

    stale = result["stale_priority_tickets"]

    assert stale["age_threshold_hours"] == 24
    assert stale["anomaly_count"] == 80