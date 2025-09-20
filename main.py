# Lütfen bu kodu kopyalayıp projenizin kök dizinindeki main.py dosyasının içine yapıştırın.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Her şey kök dizinde olduğu için, importlar basit ve doğrudur.
from api.v1.api import api_router
from core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS (Cross-Origin Resource Sharing)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# API router'ını uygulamaya dahil et
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"], include_in_schema=False)
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.get("/health", tags=["Root"], status_code=200)
def health_check():
    return {"status": "ok"}