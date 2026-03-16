# Placeholder for alerts/email_alert.py
"""
Email Alert Module
Sends alert notifications via SMTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailAlert:
    def __init__(self, config: dict):
        self.smtp_server = config.get("smtp_server")
        self.smtp_port = config.get("smtp_port", 587)
        self.username = config.get("smtp_username")
        self.password = config.get("smtp_password")
        self.sender = config.get("email_sender")
        self.recipient = config.get("email_recipient")

    def send(self, alert: dict):
        subject = f"[SECURITY ALERT] {alert['severity']} | {alert['alert_type']}"
        body = self._format_body(alert)

        msg = MIMEMultipart()
        msg["From"] = self.sender
        msg["To"] = self.recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
        except Exception as e:
            print(f"[Alert Error] Email dispatch failed: {e}")

    def _format_body(self, alert: dict) -> str:
        return f"""
SECURITY ALERT GENERATED

Alert ID       : {alert['alert_id']}
Timestamp      : {alert['timestamp']}
Host           : {alert['host']}
Severity       : {alert['severity']}
Risk Score     : {alert['risk_score']}
Type           : {alert['alert_type']}

Description:
{alert['description']}

Indicators:
{alert['indicators']}

Recommended Action:
{alert['recommended_action']}
"""
