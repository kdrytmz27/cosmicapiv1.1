import os
from fastapi import FastAPI, Request, status, Security, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.security import APIKeyHeader

from redis import asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from api.v1 import natal, synastry, transit

# --- Güvenlik Mekanizması ---
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "COSMIC_API_SECRET_KEY_12345")
api_key_header = APIKeyHeader(name="X-API-Key")

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya eksik API Anahtarı."
        )

# --- FastAPI Uygulaması ---
app = FastAPI(
    title="CosmicAPI - Gelişmiş Astroloji Motoru",
    description="Yol haritamıza uygun olarak yeniden yapılandırılmış profesyonel astroloji API'si.",
    version="3.0.0",
    contact={
        "name": "Proje Geliştiricisi",
        "url": "https://github.com/cosmicapi",
        "email": "iletisim@cosmicapi.com",
    },
)

# --- UYGULAMA BAŞLANGICINDA CACHING'İ BAŞLATMA ---
@app.on_event("startup")
async def startup():
    redis_url = os.getenv("REDIS_URL")
    print(f"Bilgi: REDIS_URL ortam değişkeni okunuyor. Değer: {redis_url}")

    if redis_url:
        try:
            # --- DEĞİŞİKLİK BURADA ---
            # decode_responses=True parametresi kaldırıldı.
            redis = await aioredis.from_url(redis_url, encoding="utf8")
            # --- DEĞİŞİKLİK BİTTİ ---
            
            await redis.ping()
            
            FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
            print("BAŞARI: Redis bağlantısı kuruldu ve FastAPI-Cache başlatıldı.")
        except Exception as e:
            print(f"HATA: Redis'e ({redis_url}) bağlanılamadı. Önbellekleme devre dışı kalacak. Detay: {e}")
    else:
        print("UYARI: REDIS_URL ortam değişkeni bulunamadı. Önbellekleme devre dışı.")

# --- Hata Yakalayıcılar ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # ... (içerik aynı, değişiklik yok)
    try:
        raw_errors = exc.errors()
        error_details = []
        for error in raw_errors:
            field = " -> ".join(map(str, error.get('loc', ['body'])))
            message = error.get('msg', 'Bilinmeyen bir doğrulama hatası.')
            error_details.append(f"Alan: '{field}', Hata: {message}")
        friendly_message = " | ".join(error_details)
    except Exception:
        friendly_message = "Girdi verisi işlenirken bir sorun oluştu. Lütfen JSON yapınızı kontrol edin."
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"status": "error", "message": "Girdiğiniz veriler geçersiz veya hatalı biçimlendirilmiş.", "detail": friendly_message})

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"status": "error", "message": exc.detail})

# --- API Rotaları ---
app.include_router(natal.router, prefix="/v1/natal", tags=["1. Natal Harita"], dependencies=[Depends(get_api_key)])
app.include_router(synastry.router, prefix="/v1/synastry", tags=["2. Sinastri (İlişki) Haritası"], dependencies=[Depends(get_api_key)])
app.include_router(transit.router, prefix="/v1/transit", tags=["3. Transit (Anlık) Harita"], dependencies=[Depends(get_api_key)])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "CosmicAPI'ye hoş geldiniz! API dokümantasyonu için /docs adresine gidin."}

@app.get("/health", tags=["Root"], status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok"}