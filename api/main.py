import sys
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.dependencies import get_settings
from api.routers.auth import auth
from api.routers.data import data
from api.services.endpoint_requester import EndpointRequester

settings = get_settings()


def initialise_logger():
    logger.remove()
    logger.add(sys.stdout, format="{time} {level} {message}", level="INFO")
    logger.add(sys.stderr, format="{time} {level} {message}", level="ERROR")


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = httpx.AsyncClient()

    try:
        initialise_logger()
        app.state.endpoint_requester = EndpointRequester(client)

        yield
    finally:
        await client.aclose()


app = FastAPI(lifespan=lifespan)


# healthcheck route
@app.get("/")
def health_check():
    return {"status": "running"}


app.include_router(auth.router)
app.include_router(data.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)