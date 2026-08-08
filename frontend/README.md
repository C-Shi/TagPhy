# TagPhy frontend

React + TypeScript + Vite + Tailwind. Desktop-oriented Library UI.

## Run (dev)

Terminal 1 — FastAPI:

```bash
# from repo root, with venv active
tagphy
```

Terminal 2 — UI:

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 — Vite proxies `/api/*` to FastAPI at `http://127.0.0.1:8765`.

## API expected by this UI

Implement these on FastAPI (DB queries are yours):

### `GET /api/tags`

```json
{
  "tags": [
    {
      "id": 1,
      "name": "Cat",
      "source": "vision",
      "description": "",
      "photo_count": 12,
      "child_count": 2,
      "parents": [{ "id": 10, "name": "Pet" }],
      "children": [{ "id": 2, "name": "Meowy" }]
    }
  ]
}
```

- `source === "metadata"` → shown under **Years** (newest year first).
- Other sources → **Tags** (A–Z).
- `photo_count`: direct `image_tags` only.
- `child_count`: one-hop children in `tag_edges`.

### `GET /api/tags/{id}`

Same object as one element of `tags` (404 if missing). Used by `/tags/:id/pictures`.

Types live in `src/api/types.ts`.
