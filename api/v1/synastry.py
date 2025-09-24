from typing import Dict, Any
import traceback  # Hata dökümünü yakalamak için

from fastapi import APIRouter, Response, Depends, HTTPException
from fastapi_cache.decorator import cache

from models.pydantic_models import SynastryData
from services.astrology_engine import calculate_synastry_aspects
from services.chart_drawer import draw_synastry_biwheel_chart
from api.v1.natal import get_natal_data_dependency

router = APIRouter()

# --- BAĞIMLILIKLAR ---

# Bu fonksiyon, iki kişinin haritasını asenkron olarak çeker.
async def get_synastry_charts_dependency(data: SynastryData) -> Dict[str, Any]:
    p1_data = await get_natal_data_dependency(birth_data=data.person1)
    p2_data = await get_natal_data_dependency(birth_data=data.person2)
    return {"p1_data": p1_data, "p2_data": p2_data}

# Bu fonksiyon, iki harita arasındaki açıları hesaplar ve HATA YAKALAMA içerir.
@cache(expire=600)
async def get_full_synastry_bundle_dependency(charts: Dict[str, Any] = Depends(get_synastry_charts_dependency)) -> Dict[str, Any]:
    # --- YENİ: KAPSAMLI HATA YAKALAMA ---
    try:
        p1_data = charts["p1_data"]
        p2_data = charts["p2_data"]
        
        # Çökmenin yaşandığı varsayılan satır
        synastry_aspects = calculate_synastry_aspects(p1_data.get('planets', []), p2_data.get('planets', []))
        
        return {**charts, "aspects": synastry_aspects}
    except Exception as e:
        # Herhangi bir hata olursa, hatanın detaylarını yakala ve Vercel loglarına yazdır.
        error_details = traceback.format_exc()
        print(f"CRITICAL ERROR in get_full_synastry_bundle_dependency:\n{error_details}")
        
        # Kullanıcıya anlamlı bir hata mesajı döndür.
        raise HTTPException(
            status_code=500,
            detail=f"Sinastri açıları hesaplanırken beklenmedik bir sunucu hatası oluştu. Lütfen geliştiriciyle iletişime geçin. Hata: {type(e).__name__}"
        )
    # --- BİTTİ ---


# --- API ENDPOINT'LERİ (TÜMÜ async def OLARAK GÜNCELLENDİ) ---

@router.post(
    "/house-overlays",
    summary="Ev Yerleşimleri (House Overlays)",
    description="Birinci kişinin gezegenlerinin, ikinci kişinin haritasındaki hangi evlere düştüğünü listeler."
)
async def get_synastry_house_overlays(
    charts: Dict[str, Any] = Depends(get_synastry_charts_dependency)
):
    # .get() metodu ile daha güvenli veri çekme
    p1_planets = charts.get('p1_data', {}).get('planets', [])
    p2_houses = charts.get('p2_data', {}).get('house_cusps', [])

    if not p1_planets or not p2_houses:
        raise HTTPException(status_code=400, detail="Gezegen veya ev verileri eksik, hesaplama yapılamadı.")

    overlays = []
    for planet in p1_planets:
        planet_lon = planet['longitude']
        found_house = 0
        for i in range(12):
            house_start = p2_houses[i]
            house_end = p2_houses[i+1] if i < 11 else p2_houses[0]
            if house_start > house_end:
                if planet_lon >= house_start or planet_lon < house_end:
                    found_house = i + 1
                    break
            else:
                if house_start <= planet_lon < house_end:
                    found_house = i + 1
                    break
        overlays.append({"person1_planet": planet['planet'], "in_person2_house": found_house})
        
    return {"overlays": overlays}

@router.post(
    "/aspects",
    summary="Sinastri Açıları",
    description="İki harita arasındaki gezegenlerin birbirleriyle yaptığı açıları listeler."
)
async def get_synastry_aspects(
    synastry_bundle: Dict[str, Any] = Depends(get_full_synastry_bundle_dependency)
):
    return {
        "aspects": synastry_bundle.get("aspects", [])
    }

@router.post(
    "/bi-wheel-chart",
    summary="Sinastri Haritası Görseli (Bi-Wheel)",
    description="İki doğum haritasını iç içe çizen profesyonel bir sinastri haritası (PNG) üretir."
)
async def get_synastry_biwheel_chart_endpoint(
    synastry_bundle: Dict[str, Any] = Depends(get_full_synastry_bundle_dependency)
):
    chart_image_bytes = draw_synastry_biwheel_chart(
        p1_data=synastry_bundle['p1_data'],
        p2_data=synastry_bundle['p2_data'],
        synastry_aspects=synastry_bundle.get('aspects', [])
    )
    
    return Response(content=chart_image_bytes, media_type="image/png")