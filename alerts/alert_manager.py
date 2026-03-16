# Placeholder for alerts/alert_manager.py
"""
Central Alert Manager
Responsible for generating, formatting, and dispatching alerts
based on risk score and anomaly classification.
"""

from datetime import datetime
from alerts.email_alert import EmailAlert
from alerts.siem_export import SIEMExporter


class AlertManager:
    def __init__(self, config: dict):
        self.config = config
        self.email_enabled = config.get("email_alerts", False)
        self.siem_enabled = config.get("siem_export", False)

        self.email_client = EmailAlert(config) if self.email_enabled else None
        self.siem_client = SIEMExporter(config) if self.siem_enabled else None

    def generate_alert(self, alert_data: dict):
        """
        Core alert object generator
        """
        alert = {
            "alert_id": f"ALERT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.utcnow().isoformat(),
            "host": alert_data.get("host"),
            "severity": alert_data.get("severity"),
            "risk_score": alert_data.get("risk_score"),
            "alert_type": alert_data.get("alert_type"),
            "description": alert_data.get("description"),
            "indicators": alert_data.get("indicators"),
            "recommended_action": alert_data.get("recommended_action"),
        }

        self.dispatch(alert)
        return alert

    def dispatch(self, alert: dict):
        """
        Dispatch alert to configured channels
        """
        if self.email_enabled:
            self.email_client.send(alert)

        if self.siem_enabled:
            self.siem_client.export(alert)
