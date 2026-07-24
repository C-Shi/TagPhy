# TagPhy

Learning project: portable USB photo cataloger with Google ADK agents and a local web UI.

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
agents/           # ADK agents (fill these in)
src/tagphy/       # app code (fill these in)
```

Runtime folders like `Photo_Tagged/` belong on the USB drive when the app runs — not in this repo.
