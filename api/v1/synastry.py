# Lütfen bu kodu kopyalayıp Cosmic API projenizdeki app/api/v1/endpoints/synastry.py dosyasının içine yapıştırın.

from typing import Dict, Any, List
from fastapi import APIRouter, Response, Depends, HTTPException

from fastapi_cache.decorator import cache
# --- NİHAİ DÜZELTME: GÖRECELİ IMPORT KULLANIMI ---
# "app." ile başlayan importları, bulunduğumuz konuma göre (iki klasör yukarı)
# göreceli yollarla değiştiriyoruz. Bu, Render ortamında doğru çalışmasını sağlar.
from ....models.pydantic_models import BirthData
from ....models.synastry_models import SynastryChartRequest
from ....services.astrology_engine import calculate_natal_data, calculate_synastry_aspects
from ....services.chart_drawing_service import draw_bi_wheel_chart

router = APIRouter()

# --- BAĞIMLILIKLAR (DEPENDENCIES) ---

@cache(expire=3600)
def get_natal_data_dependency(birth_data: BirthData) -> Dict[str, Any]:
    try:
        chart_data = calculate_natal_data(birth_data)
        if "error" in chart_data:
            raise HTTPException(status_code=400, detail=chart_data["error"])
        return chart_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Harita hesaplama sırasında sunucu hatası: {str(e)}")

def get_synastry_charts_dependency(request: SynastryChartRequest) -> Dict[str, Any]:
    p1_data = get_natal_data_dependency(birth_data=request.person1)
    p2_data = get_natal_data_dependency(birth_data=request.person2)
    return {"p1_data": p1_data, "p2_data": p2_data}

@cache(expire=600)
def get_full_synastry_bundle_dependency(charts: Dict[str, Any] = Depends(get_synastry_charts_dependency)) -> Dict[str, Any]:
    p1_data = charts["p1_data"]
    p2_data = charts["p2_data"]
    synastry_aspects = calculate_synastry_aspects(p1_data['planets'], p2_data['planets'])
    return {**charts, "aspects": synastry_aspects}

# --- API ENDPOINTS (Değişiklik yok) ---

@router.post("/house-overlays", summary="Ev Yerleşimleri (House Overlays)")
def get_synastry_house_overlays(
    request: SynastryChartRequest,
    charts: Dict[str, Any] = Depends(get_synastry_charts_dependency)
):
    p1_planets = charts['p1_data']['planets']; p2_houses = charts['p2_data']['house_cusps']; overlays = []
    for planet in p1_planets:
        planet_lon = planet['longitude']; found_house = 0
        for i in range(12):
            house_start = p2_houses[i]; house_end = p2_houses[i+1] if i < 11 else p2_houses[0]
            if house_start > house_end:
                if planet_lon >= house_start or planet_lon < house_end:
                    found_house = i + 1; break
            else:
                if house_start <= planet_lon < house_end:
                    found_house = i + 1; break
        overlays.append({"person1_planet": planet['planet'], "in_person2_house": found_house})
    return {"person1": request.person1.dict(), "person2": request.person2.dict(), "overlays": overlays}

@router.post("/aspects", summary="Sinastri Açıları")
def get_synastry_aspects(
    request: SynastryChartRequest,
    synastry_bundle: Dict[str, Any] = Depends(get_full_synastry_bundle_dependency)
):
    return {"person1": request.person1.dict(), "person2": request.person2.dict(), "aspects": synastry_bundle["aspects"]}

@router.post("/bi-wheel-chart", summary="Sinastri Haritası Görseli (Bi-Wheel)")
def get_synastry_biwheel_chart_endpoint(
    request: SynastryChartRequest,
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