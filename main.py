from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles
from config import env

from routes import api

app = FastAPI(
    title="Learn API",
    docs_url="/docs",
    debug=env.DEBUG
)

app.mount("/files", app=StaticFiles(directory="/tmp"),  name="tmp")
app.include_router(api)

@app.get("/")
async def root() -> ORJSONResponse:
    return ORJSONResponse(
        {
            "version": env.LEARN_VERSION,
            "debug": env.DEBUG
        }
    )

