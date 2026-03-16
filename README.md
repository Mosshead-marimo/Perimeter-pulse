# Perimeter Pulse

Perimeter Pulse is a log analysis platform with a Flask backend and React frontend.  
It lets security teams upload log files, run an analysis pipeline, and review risk/anomaly results in a dashboard.

## Why this project is used

This project is used to:
- centralize log analysis in one interface
- detect suspicious behavior patterns (anomaly + leakage indicators)
- generate risk-scored results for faster triage and investigation
- keep report snapshots/history for review over time

## Installation (Docker)

Prerequisites:
- Docker Desktop (or Docker Engine + Docker Compose) installed and running

From the project root:

```bash
docker compose up --build
```

## Run and Access

After containers start:
- Frontend: `http://localhost`
- Backend health check: `http://localhost:5000/health`

Use the frontend to sign up/login and upload logs for analysis.

To stop:

```bash
docker compose down
```
