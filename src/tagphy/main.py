"""Local web UI entrypoint — fill in later."""

from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from tagphy.db.connection import SQLiteConnection


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SQLiteConnection()
    db.migrate()
    yield


app = FastAPI(title="TagPhy", lifespan=lifespan)


@app.get("/")
def home() -> dict:
    return {"app": "TagPhy", "status": "skeleton"}


def main() -> None:
    uvicorn.run("tagphy.main:app", host="127.0.0.1", port=8765)


if __name__ == "__main__":
    main()
