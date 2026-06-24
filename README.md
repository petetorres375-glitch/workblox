# Workblox

A [Torres Tech Remote](https://petetorres375-glitch.github.io/torres-tech-remote/) product — AI-powered productivity tools in one place: Doc Analyzer, Workflow Builder, and OS Helpers (Linux, Windows, Mac).

## Stack

- **Frontend:** React + Vite (PWA)
- **Backend:** Flask + Anthropic API
- **Deployment:** Railway (backend), static host (frontend)

## Tools

| Tool | Description |
|---|---|
| Doc Analyzer | Upload a PDF/TXT/MD and get a structured AI summary |
| Workflow Builder | Describe a task, get a ready-to-run Python script |
| Linux Helper | Plain-English Linux problem → command + explanation |
| Windows Helper | Plain-English Windows problem → command + explanation |
| Mac Helper | Plain-English Mac problem → command + explanation |

## Development

```bash
# Backend
cd backend
source ~/venv/bin/activate
pip install -r requirements.txt
flask run --port 5000

# Frontend
cd frontend
npm install
npm run dev
```

## Environment Variables

Copy `.env.example` to `.env` and fill in `ANTHROPIC_API_KEY`.
