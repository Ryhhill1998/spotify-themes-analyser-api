from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import get_settings
from api.routers import auth, data

settings = get_settings()

app = FastAPI()

app.include_router(auth.router)
app.include_router(data.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
