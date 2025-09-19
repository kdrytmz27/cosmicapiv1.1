# Lütfen bu kodu kopyalayıp Cosmic API projenizdeki app/api/v1/endpoints/synastry.py dosyasının içine yapıştırın.

from typing import Dict, Any, List
from fastapi import APIRouter, Response, Depends, HTTPException

from fastapi_cache.decorator import cache
# --- DEĞİŞİKLİK: Pydantic modellerini doğrudan import ediyoruz ---
from app.models.pydantic_models import BirthData
from app.models.synastry_models import SynastryChartRequest # Eski SynastryData yerine bunu kullanacağız
# --- DEĞİŞİKLİK: Engine'den ve Drawer'dan doğru fonksiyonları import ediyoruz ---
from app.services.astrology_engine import calculate_natal_data, calculate_synastry_aspects
from app.services.chart_drawing_service import draw_bi_wheel_chart

router = APIRouter()

# --- BAĞIMLILIKLAR (DEPENDENCIES) ---

# Bu bağımlılık, bir kişinin doğum haritasını hesaplar ve önbelleğe alır.
# Natal endpoint'inden kopyalayıp buraya koymak, bu dosyanın kendi kendine yetmesini sağlar.
@cache(expire=3600) # Harita verisini 1 saat önbellekte tut
def get_natal_data_dependency(birth_data: BirthData) -> Dict[str, Any]:
    try:
        chart_data = calculate_natal_data(birth_data)
        if "error" in chart_data:
            raise HTTPException(status_code=400, detail=chart_data["error"])
        return chart_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Harita hesaplama sırasında sunucu hatası: {str(e)}")

# Bu bağımlılık, iki kişinin haritasını ayrı ayrı hesaplar.
def get_synastry_charts_dependency(request: SynastryChartRequest) -> Dict[str, Any]:
    p1_data = get_natal_data_dependency(birth_data=request.person1)
    p2_data = get_natal_data_dependency(birth_data=request.person2)
    return {"p1_data": p1_data, "p2_data": p2_data}

# Bu bağımlılık, hesaplanmış iki haritayı alıp aralarındaki sinastri açılarını hesaplar.
# Bu fonksiyonun sonucu da 10 dakika önbellekte tutulur.
@cache(expire=600)
def get_full_synastry_bundle_dependency(charts: Dict[str, Any] = Depends(get_synastry_charts_dependency)) -> Dict[str, Any]:
    p1_data = charts["p1_data"]
    p2_data = charts["p2_data"]
    
    # --- NİHAİ ZAFER KODU: DOĞRU FONKSİYONU DOĞRU PARAMETRELERLE ÇAĞIR ---
    # `astrology_engine.py`'deki `calculate_synastry_aspects` fonksiyonu,
    # iki ayrı gezegen listesi bekliyor. Biz de ona tam olarak bunu veriyoruz.
    synastry_aspects = calculate_synastry_aspects(p1_data['planets'], p2_data['planets'])
    
    return {**charts, "aspects": synastry_aspects}


# --- API ENDPOINTS ---
# Endpoint'lerin yapısında değişiklik yok, sadece kullandıkları modelleri ve bağımlılıkları güncelledik.

@router.post(
    "/house-overlays",
    summary="Ev Yerleşimleri (House Overlays)",
    description="Birinci kişinin gezegenlerinin, ikinci kişinin haritasındaki hangi evlere düştüğünü listeler."
)
def get_synastry_house_overlays(
    request: SynastryChartRequest,
    charts: Dict[str, Any] = Depends(get_synastry_charts_dependency)
):
    p1_planets = charts['p1_data']['planets']
    p2_houses = charts['p2_data']['house_cusps']
    
    overlays = []
    for planet in p1_planets:
        planet_lon = planet['longitude']
        found_house = 0
        for i in range(12):
            house_start = p2_houses[i]
            house_end = p2_houses[i+1] if i < 11 else p2_houses[0]
            if house_start > house_end:
                if planet_lon >= house_start or planet_lon < house_end:
                    found_house = i + 1; break
            else:
                if house_start <= planet_lon < house_end:
                    found_house = i + 1; break
        overlays.append({"person1_planet": planet['planet'], "in_person2_house": found_house})
        
    return {"person1": request.person1.dict(), "person2": request.person2.dict(), "overlays": overlays}

@router.post(
    "/aspects",
    summary="Sinastri Açıları",
    description="İki harita arasındaki gezegenlerin birbirleriyle yaptığı açıları listeler."
)
def get_synastry_aspects(
    request: SynastryChartRequest,
    synastry_bundle: Dict[str, Any] = Depends(get_full_synastry_bundle_dependency)
):
    # Artık doğrudan `synastry_bundle`'dan gelen açıları döndürebiliriz.
    return {
        "person1": request.person1.dict(),
        "person2": request.person2.dict(),
        "aspects": synastry_bundle["aspects"]
    }

@router.post(
    "/bi-wheel-chart",
    summary="Sinastri Haritası Görseli (Bi-Wheel)",
    description="İki doğum haritasını iç içe çizen profesyonel bir sinastri haritası (PNG) üretir."
)
def get_synastry_biwheel_chart_endpoint(
    request: SynastryChartRequest, # request'i de alalım ki chart_drawer'a gönderebilelim
    synastry_bundle: Dict[str, Any] = Depends(get_full_synastry_bundle_dependency)
):
    chart_image_bytes = draw_bi_wheel_chart(
        p1_data=synastry_bundle['p1_data'],
        p2_data=synastry_bundle['p2_data'],
        synastry_aspects=synastry_bundle['aspects'],
        person1_name=request.person1.name or "Person 1",
        person2_name=request.person2.name or "Person 2"
    )
    
    return Response(content=chart_image_bytes, media_type="image/png")