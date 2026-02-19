# LandIt Export Service

Standalone Go microservice for resume PDF/DOCX export and HTML preview. Runs on port 8001. Called by FastAPI only; the React frontend does not call this service directly.

## Environment

- `PORT` — default 8001
- `ALLOWED_ORIGIN` — FastAPI URL for CORS (if needed)
- `MAX_CONCURRENT_EXPORTS` — default 50

## Endpoints

- `GET /health` — liveness check
- `POST /export/pdf` — JSON body (canonical resume payload), returns binary PDF
- `POST /export/docx` — same payload, returns binary DOCX
- `POST /export/preview` — same payload, returns JSON `{"html": "..."}` for iframe preview

## Build and run

```bash
go mod tidy
go build -o landit-export .
```

Then run the binary (Windows: `.\landit-export.exe` or `landit-export`; Linux/macOS: `./landit-export`).

Or: `go run .`

## Templates

- **Classic** — Single column, system fonts, ATS-safe. Forced when `metadata.ats_mode` is true.
- **Modern** — Two-column layout (stub: currently same as Classic).
- **Minimal** — More whitespace (stub: currently same as Classic).

Payload shape is defined in the FastAPI repo (`spacy-ner/export_payload.py`) and must match this service.
