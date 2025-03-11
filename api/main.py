from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import get_settings
from api.routers import auth, data
from api.services.endpoint_requester import EndpointRequester

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = httpx.AsyncClient()

    try:
        app.state.endpoint_requester = EndpointRequester(client)

        yield
    finally:
        await client.aclose()


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(data.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)