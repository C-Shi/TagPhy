"""Local web UI entrypoint — fill in later."""

from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from tagphy.db.connection import SQLiteConnection
from tagphy.web.api import router as api_router
from tagphy.web.ws import router as ws_router, start_scan_log_broadcaster, stop_scan_log_broadcaster


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SQLiteConnection()
    db.migrate()
    start_scan_log_broadcaster()
    yield
    await stop_scan_log_broadcaster()


app = FastAPI(title="TagPhy", lifespan=lifespan)
app.include_router(api_router)
app.include_router(ws_router)


@app.get("/")
def home() -> dict:
    return {"app": "TagPhy", "status": "skeleton"}


def main() -> None:
    uvicorn.run("tagphy.main:app", host="127.0.0.1", port=8765, reload=True)


if __name__ == "__main__":
    main()
