import os # YENİ: Ortam değişkenlerini okumak için
from fastapi import FastAPI, Request, status, Security, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.security import APIKeyHeader

from redis import asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from api.v1 import natal, synastry, transit
from core.config import API_KEY

# ... (Güvenlik Mekanizması aynı kalıyor) ...
api_key_header = APIKeyHeader(name="X-API-Key")
async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya eksik API Anahtarı."
        )

app = FastAPI(
    title="CosmicAPI - Gelişmiş Astroloji Motoru",
    description="Yol haritamıza uygun olarak yeniden yapılandırılmış profesyonel astroloji API'si.",
    version="3.0.0", # Versiyonu güncelledik (Yayına Hazır)
    contact={
        "name": "Proje Geliştiricisi",
        "url": "https://github.com/cosmicapi",
        "email": "iletisim@cosmicapi.com",
    },
    dependencies=[Depends(get_api_key)]
)

# --- DEĞİŞTİRİLDİ: UYGULAMA BAŞLANGICINDA CACHING'İ BAŞLATMA ---
@app.on_event("startup")
async def startup():
    """
    Uygulama başladığında çalışır. Ortama göre doğru Redis adresine bağlanır.
    """
    # Render, canlıdaki Redis adresini REDIS_URL ortam değişkeniyle sağlar.
    # Eğer bu değişken varsa (yani kod Render'da çalışıyorsa) onu kullan.
    # Eğer yoksa (yani kod kendi bilgisayarımızda çalışıyorsa) "redis://localhost" kullan.
    redis_url = os.getenv("REDIS_URL", "redis://localhost")
    
    try:
        redis = aioredis.from_url(redis_url, encoding="utf8", decode_responses=True)
        # Redis sunucusuna gerçekten ulaşıp ulaşamadığımızı kontrol et
        await redis.ping()
        
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
        print(f"Redis bağlantısı {redis_url} adresine başarıyla kuruldu ve FastAPI-Cache başlatıldı.")
    except Exception as e:
        # Redis'e bağlanamazsa, bunu terminalde açıkça belirt.
        print(f"HATA: Redis'e ({redis_url}) bağlanılamadı. Önbellekleme devre dışı kalacak. Detay: {e}")

# ... (Hata Yakalayıcılar ve API Rotaları aynı kalıyor) ...
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
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

app.include_router(natal.router, prefix="/v1/natal", tags=["1. Natal Harita"])
app.include_router(synastry.router, prefix="/v1/synastry", tags=["2. Sinastri (İlişki) Haritası"])
app.include_router(transit.router, prefix="/v1/transit", tags=["3. Transit (Anlık) Harita"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "CosmicAPI'ye hoş geldiniz! API dokümantasyonu için /docs adresine gidin."}

@app.get("/health", tags=["Root"], status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok"}