# Placeholder for tests/test_features.py
"""
Tests for feature engineering module
"""

from feature_engineering import generate_feature_vector


def test_feature_vector_generation():
    parsed_logs = [
        {
            "timestamp": "2025-01-15T22:41:11",
            "direction": "OUTBOUND",
            "bytes_sent": 5000,
            "dst_ip": "45.33.12.98",
            "dst_port": 443
        },
        {
            "timestamp": "2025-01-15T22:41:21",
            "direction": "OUTBOUND",
            "bytes_sent": 5200,
            "dst_ip": "45.33.12.98",
            "dst_port": 443
        }
    ]

    features = generate_feature_vector(parsed_logs)

    assert features["connection_count"] == 2
    assert features["total_bytes_sent"] == 10200
    assert features["unique_destination_ips"] == 1
