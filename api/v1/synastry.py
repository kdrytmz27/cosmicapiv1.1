from typing import Dict, Any

from fastapi import APIRouter, Response, Depends, HTTPException

# --- DEĞİŞİKLİK: Caching ve ana natal bağımlılığını import ediyoruz ---
from fastapi_cache.decorator import cache
from models.pydantic_models import SynastryData, BirthData
from services.astrology_engine import calculate_synastry_aspects
from services.chart_drawer import draw_synastry_biwheel_chart
from api.v1.natal import get_natal_data_dependency

router = APIRouter()

# --- DEPENDENCIES (BAĞIMLILIKLAR) ---

# YENİ ve GÜNCELLENMİŞ: Bu fonksiyon, iki kişinin natal haritasını,
# zaten önbelleğe alınmış olan `get_natal_data_dependency`'yi kullanarak hesaplar.
def get_synastry_charts_dependency(data: SynastryData) -> Dict[str, Any]:
    """
    İki kişilik doğum verilerini, ana önbellekli bağımlılığı kullanarak hesaplar.
    Bu, eğer haritalardan biri daha önce hesaplandıysa, sonucun doğrudan
    önbellekten gelmesini sağlar.
    """
    # Not: Burada doğrudan `raise HTTPException` kullanmıyoruz, çünkü
    # `get_natal_data_dependency` zaten hata durumunda bunu bizim için yapıyor.
    p1_data = get_natal_data_dependency(birth_data=data.person1)
    p2_data = get_natal_data_dependency(birth_data=data.person2)

    return {"p1_data": p1_data, "p2_data": p2_data}

# YENİ ve GÜNCELLENMİŞ: Bu bağımlılık artık kendisi de önbelleğe alınıyor.
# Aynı iki kişi için sinastri analizi tekrar istendiğinde, tüm sonuç anında dönecektir.
@cache(expire=600)
def get_full_synastry_bundle_dependency(charts: Dict[str, Any] = Depends(get_synastry_charts_dependency)) -> Dict[str, Any]:
    """
    Hazır hesaplanmış haritaları alıp üzerine sinastri açılarını ekler.
    Bu fonksiyonun sonucu da 10 dakika boyunca önbellekte tutulur.
    """
    p1_data = charts["p1_data"]
    p2_data = charts["p2_data"]
    
    synastry_aspects = calculate_synastry_aspects(p1_data['planets'], p2_data['planets'])
    
    return {**charts, "aspects": synastry_aspects}


# --- API ENDPOINTS ---
# Endpoint'lerde hiçbir değişiklik yapmamıza gerek yok, çünkü tüm mantık
# güncellenmiş bağımlılıklar tarafından yönetiliyor.

@router.post(
    "/house-overlays",
    summary="Ev Yerleşimleri (House Overlays)",
    description="Birinci kişinin gezegenlerinin, ikinci kişinin haritasındaki hangi evlere düştüğünü listeler."
)
def get_synastry_house_overlays(
    data: SynastryData,
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
                    found_house = i + 1
                    break
            else:
                if house_start <= planet_lon < house_end:
                    found_house = i + 1
                    break
        overlays.append({"person1_planet": planet['planet'], "in_person2_house": found_house})
        
    return {"person1": data.person1.dict(), "person2": data.person2.dict(), "overlays": overlays}

@router.post(
    "/aspects",
    summary="Sinastri Açıları",
    description="İki harita arasındaki gezegenlerin birbirleriyle yaptığı açıları listeler."
)
def get_synastry_aspects(
    data: SynastryData,
    synastry_bundle: Dict[str, Any] = Depends(get_full_synastry_bundle_dependency)
):
    return {
        "person1": data.person1.dict(),
        "person2": data.person2.dict(),
        "aspects": synastry_bundle["aspects"]
    }

@router.post(
    "/bi-wheel-chart",
    summary="Sinastri Haritası Görseli (Bi-Wheel)",
    description="İki doğum haritasını iç içe çizen profesyonel bir sinastri haritası (PNG) üretir."
)
def get_synastry_biwheel_chart_endpoint(
    synastry_bundle: Dict[str, Any] = Depends(get_full_synastry_bundle_dependency)
):
    chart_image_bytes = draw_synastry_biwheel_chart(
        p1_data=synastry_bundle['p1_data'],
        p2_data=synastry_bundle['p2_data'],
        synastry_aspects=synastry_bundle['aspects']
    )
    
    return Response(content=chart_image_bytes, media_type="image/png")