# Lütfen bu kodu kopyalayıp Cosmic API projenizin kök dizinindeki main.py dosyasının içine yapıştırın.

import os
import sys
from fastapi import FastAPI, Request, status, Security, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.security import APIKeyHeader
from redis import asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

# --- NİHAİ ZAFER KODU: RENDER İÇİN PYTHON YOLUNU AYARLAMA ---
# Bu kod, Render.com'un `gunicorn` komutunu çalıştırdığı `src` klasörünü
# Python'ın modül arama yoluna ekler. Bu, `from app...` gibi importların
# sunucu ortamında sorunsuz çalışmasını sağlar.
# Not: Bu kod, projenizi kendi bilgisayarınızda çalıştırırken de bir sorun yaratmaz.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

# Artık `app` bir modül olarak tanındığı için, bu importlar çalışacaktır.
from app.api.v1.api import api_router
from app.core.config import settings

# API Anahtarı güvenlik mekanizması
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    if settings.API_KEY and api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya eksik API Anahtarı."
        )

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    dependencies=[Depends(get_api_key)]
)

# CORS Middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.on_event("startup")
async def startup():
    """Uygulama başladığında Redis Cache'i başlatır."""
    try:
        redis = aioredis.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)
        await redis.ping()
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
        print(f"Redis bağlantısı {settings.REDIS_URL} adresine başarıyla kuruldu.")
    except Exception as e:
        print(f"HATA: Redis'e ({settings.REDIS_URL}) bağlanılamadı. Önbellekleme devre dışı. Detay: {e}")

# API router'ını uygulamaya dahil et
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )

@app.get("/", tags=["Root"])
def read_root():
    return {"message": f"CosmicAPI'ye hoş geldiniz! ({settings.PROJECT_NAME})"}

@app.get("/health", tags=["Root"], status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok"}