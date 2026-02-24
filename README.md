# LandIt
AI Powered Resume Builder

## Running locally

1. **Backend (FastAPI):** `cd spacy-ner`, activate venv, `uvicorn api:app --reload --port 8000`. Set `GO_EXPORT_SERVICE_URL` to the Go export service URL (default `http://localhost:8001`) for PDF/DOCX/cover-letter export.
2. **Go export service (optional):** `cd go-export-service`, `go run .` (port 8001). If this service is not running, export endpoints return 503.
3. **Frontend:** `cd landit-ui`, `npm start`.

## Deploying to production

- **Frontend:** Set `REACT_APP_API_URL` to your deployed FastAPI URL (e.g. `https://your-api.railway.app`). Build and deploy (Vercel, Netlify, Railway, etc.).
- **Backend (FastAPI):** Set `CORS_ORIGINS` to your frontend URL(s), comma-separated (e.g. `https://your-app.vercel.app`). Localhost origins are always allowed.
- **Go export (optional):** Deploy the Go service and set `GO_EXPORT_SERVICE_URL` on FastAPI to its URL.
