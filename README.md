# Firewalloganalyzer

## Run backend + frontend with Docker

From the project root:

```bash
docker compose up --build
```

Then open:

- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:5000/health`

To stop:

```bash
docker compose down
```
