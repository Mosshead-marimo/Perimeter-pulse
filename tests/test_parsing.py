# Placeholder for tests/test_parsing.py
"""
Tests for firewall log parsing and normalization
"""

from parsing.firewall_parser import FirewallLogParser
from parsing.normalizer import LogNormalizer


def test_firewall_log_parsing_single_line():
    parser = FirewallLogParser()

    line = "2025-01-15 22:41:11 ALLOW TCP 192.168.1.10 45.33.12.98 60122 443 5400 - - - - - SEND"
    record = parser.parse_line(line)

    assert record is not None
    assert record["action"] == "ALLOW"
    assert record["protocol"] == "TCP"
    assert record["dst_ip"] == "45.33.12.98"
    assert record["bytes_sent"] == 5400


def test_normalizer_schema():
    records = [{
        "timestamp": "2025-01-15T22:41:11",
        "action": "ALLOW",
        "protocol": "TCP",
        "src_ip": "192.168.1.10",
        "dst_ip": "8.8.8.8",
        "src_port": 50000,
        "dst_port": 53,
        "bytes_sent": 60,
        "direction": "OUTBOUND"
    }]

    normalizer = LogNormalizer()
    df = normalizer.normalize(records)

    assert "timestamp" in df.columns
    assert df["bytes_sent"].iloc[0] == 60
