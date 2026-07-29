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

Open http://127.0.0.1:8765

## Layout

```
src/tagphy/       # app code (pipeline functions, web, db)
```

Runtime folders like `Photo_Tagged/` belong on the USB drive when the app runs — not in this repo.
