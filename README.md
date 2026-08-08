# TagPhy

Learning project: portable USB photo cataloger. Scan pipeline is plain Python functions (Gemini for vision); ADK is reserved for a later Catalog Assistant. Local web UI comes after the core loop.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
tagphy
```

API: http://127.0.0.1:8765

### Frontend (Library UI)

```bash
cd frontend
npm install
npm run dev
```

UI: http://127.0.0.1:5173 — proxies `/api` to FastAPI. See `frontend/README.md` for the JSON contract you implement on the backend.

## Layout

```
src/tagphy/       # app code (pipeline functions, web, db)
frontend/         # React + Vite + Tailwind (Library UI)
```

Runtime folders like `Photo_Tagged/` belong on the USB drive when the app runs — not in this repo.
