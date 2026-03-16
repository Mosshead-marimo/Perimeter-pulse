"""
Generic Log Parser
Supports JSON logs, key=value logs, syslog lines, Apache/Nginx access logs,
and falls back to raw-line records when format is unknown.
"""

from datetime import datetime
import json
import re


APACHE_RE = re.compile(
    r'(?P<src_ip>\S+)\s+\S+\s+\S+\s+\[(?P<timestamp>[^\]]+)\]\s+"(?P<request>[^"]*)"\s+'
    r"(?P<status>\d{3})\s+(?P<bytes_sent>\S+)"
)
SYSLOG_RE = re.compile(
    r"^(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d\d:\d\d:\d\d)\s+"
    r"(?P<host>\S+)\s+(?P<program>[\w\-.\/]+)(?:\[(?P<pid>\d+)\])?:\s*(?P<message>.*)$"
)
KV_RE = re.compile(r"([A-Za-z0-9_.@-]+)=('([^']*)'|\"([^\"]*)\"|(\S+))")


class GenericLogParser:
    def parse_line(self, line: str) -> dict | None:
        if not line:
            return None

        raw = line.strip()
        if not raw or raw.startswith("#"):
            return None

        json_record = self._try_json(raw)
        if json_record:
            return self._normalize_record(json_record, "json", raw)

        apache_record = self._try_apache(raw)
        if apache_record:
            return self._normalize_record(apache_record, "apache", raw)

        syslog_record = self._try_syslog(raw)
        if syslog_record:
            return self._normalize_record(syslog_record, "syslog", raw)

        kv_record = self._try_key_value(raw)
        if kv_record:
            return self._normalize_record(kv_record, "key_value", raw)

        firewall_record = self._try_firewall(raw)
        if firewall_record:
            return self._normalize_record(firewall_record, "firewall_legacy", raw)

        return self._normalize_record({"message": raw}, "raw", raw)

    def parse_file(self, file_path: str) -> list:
        records = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f, start=1):
                record = self.parse_line(line)
                if record:
                    record["line_number"] = idx
                    records.append(record)
        return records

    def _try_json(self, raw: str) -> dict | None:
        if not (raw.startswith("{") and raw.endswith("}")):
            return None
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                return obj
        except Exception:
            return None
        return None

    def _try_apache(self, raw: str) -> dict | None:
        match = APACHE_RE.match(raw)
        if not match:
            return None
        data = match.groupdict()
        request = data.get("request", "")
        parts = request.split()
        if len(parts) >= 1:
            data["method"] = parts[0]
        if len(parts) >= 2:
            data["path"] = parts[1]
        return data

    def _try_syslog(self, raw: str) -> dict | None:
        match = SYSLOG_RE.match(raw)
        if not match:
            return None
        return match.groupdict()

    def _try_key_value(self, raw: str) -> dict | None:
        matches = KV_RE.findall(raw)
        if not matches:
            return None

        parsed = {}
        for full in matches:
            key = full[0]
            value = full[2] or full[3] or full[4]
            parsed[key] = value
        return parsed if parsed else None

    def _try_firewall(self, raw: str) -> dict | None:
        parts = raw.split()
        if len(parts) < 8:
            return None
        try:
            direction_raw = parts[-1].upper()
            direction = "OUTBOUND" if direction_raw == "SEND" else "INBOUND"
            return {
                "timestamp": self._parse_timestamp(f"{parts[0]} {parts[1]}"),
                "action": parts[2],
                "protocol": parts[3],
                "src_ip": parts[4],
                "dst_ip": parts[5],
                "src_port": self._safe_int(parts[6]),
                "dst_port": self._safe_int(parts[7]),
                "bytes_sent": self._safe_int(parts[8]) if len(parts) > 8 else 0,
                "direction": direction,
            }
        except Exception:
            return None

    def _normalize_record(self, data: dict, log_type: str, raw: str) -> dict:
        normalized = {
            "log_type": log_type,
            "raw_message": raw,
            "timestamp": self._extract_timestamp(data),
            "level": self._extract_first(
                data,
                ["level", "severity", "log_level", "priority"],
                default="UNKNOWN",
            ).upper(),
            "message": self._extract_first(
                data,
                ["message", "msg", "log", "event", "description"],
                default=raw,
            ),
            "direction": self._normalize_direction(
                self._extract_first(data, ["direction", "dir", "flow"], default="UNKNOWN")
            ),
            "src_ip": self._extract_first(
                data,
                ["src_ip", "source_ip", "client_ip", "src", "source"],
                default="",
            ),
            "dst_ip": self._extract_first(
                data,
                ["dst_ip", "dest_ip", "destination_ip", "dst", "destination", "server_ip"],
                default="",
            ),
            "src_port": self._safe_int(
                self._extract_first(data, ["src_port", "source_port", "sport"], default=0)
            ),
            "dst_port": self._safe_int(
                self._extract_first(
                    data, ["dst_port", "dest_port", "destination_port", "dport", "port"], default=0
                )
            ),
            "bytes_sent": self._safe_int(
                self._extract_first(data, ["bytes_sent", "bytes", "size", "sent_bytes"], default=0)
            ),
            "process_name": self._extract_first(
                data, ["process_name", "process", "proc", "program", "app"], default=""
            ),
            "host": self._extract_first(data, ["host", "hostname", "device", "node"], default=""),
            "action": self._extract_first(data, ["action", "event_type", "operation"], default=""),
            "status": self._extract_first(data, ["status", "status_code", "code"], default=""),
        }
        return normalized

    def _extract_timestamp(self, data: dict) -> str:
        for key in ["timestamp", "@timestamp", "time", "datetime", "ts", "date"]:
            if key in data and data[key]:
                parsed = self._parse_timestamp(str(data[key]))
                if parsed:
                    return parsed
        return ""

    @staticmethod
    def _extract_first(data: dict, keys: list[str], default=""):
        for key in keys:
            if key in data and data[key] is not None:
                return str(data[key]).strip()
        return default

    @staticmethod
    def _normalize_direction(value: str) -> str:
        token = (value or "").strip().upper()
        if token in {"OUT", "OUTBOUND", "SEND", "EGRESS"}:
            return "OUTBOUND"
        if token in {"IN", "INBOUND", "RECEIVE", "INGRESS"}:
            return "INBOUND"
        return "UNKNOWN"

    @staticmethod
    def _parse_timestamp(value: str) -> str:
        value = value.strip()
        if not value:
            return ""

        # Fast path for ISO timestamps
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.isoformat()
        except Exception:
            pass

        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%d/%b/%Y:%H:%M:%S %z",
            "%b %d %H:%M:%S",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(value, fmt)
                if fmt == "%b %d %H:%M:%S":
                    dt = dt.replace(year=datetime.utcnow().year)
                return dt.isoformat()
            except Exception:
                continue

        return ""

    @staticmethod
    def _safe_int(value) -> int:
        try:
            if value in ("-", "", None):
                return 0
            return int(float(value))
        except Exception:
            return 0


# Backward-compatible alias
FirewallLogParser = GenericLogParser
