# Lütfen bu kodu kopyalayıp Cosmic API projenizdeki api/v1/synastry.py dosyasının içine yapıştırın.

from typing import Dict, Any, List
from fastapi import APIRouter, Response, Depends, HTTPException

# ÖNEMLİ: Orijinal kodunuzdaki gibi, diğer modülleri doğru yoldan import ediyoruz.
from models.pydantic_models import BirthData
from models.synastry_models import SynastryChartRequest # SynastryData yerine doğru modeli kullanıyoruz
from services.astrology_engine import calculate_natal_data, calculate_synastry_aspects
from services.chart_drawing_service import draw_bi_wheel_chart

router = APIRouter()

# --- BAĞIMLILIKLAR (DEPENDENCIES) ---
# Bu yapı, iki haritayı ayrı ayrı hesaplar ve bu, hatayı çözmek için en sağlam yöntemdir.

def get_natal_data_for_synastry(birth_data: BirthData) -> Dict[str, Any]:
    """Bir kişinin doğum haritası verilerini hesaplar."""
    try:
        chart_data = calculate_natal_data(birth_data)
        if "error" in chart_data:
            raise HTTPException(status_code=400, detail=chart_data["error"])
        return chart_data
    except Exception as e:
        # Geliştirme sırasında hatanın detayını görmek önemlidir.
        print(f"HATA - get_natal_data_for_synastry: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Harita hesaplama sırasında sunucu hatası: {str(e)}")

def get_synastry_charts_dependency(request: SynastryChartRequest) -> Dict[str, Any]:
    """İki kişinin doğum haritası verilerini bir araya getirir."""
    p1_data = get_natal_data_for_synastry(birth_data=request.person1)
    p2_data = get_natal_data_for_synastry(birth_data=request.person2)
    return {"p1_data": p1_data, "p2_data": p2_data}

# --- API ENDPOINTS ---

@router.post(
    "/house-overlays",
    summary="Ev Yerleşimleri (House Overlays)",
    description="Birinci kişinin gezegenlerinin, ikinci kişinin haritasındaki hangi evlere düştüğünü listeler."
)
def get_synastry_house_overlays(
    request: SynastryChartRequest,
    charts: Dict[str, Any] = Depends(get_synastry_charts_dependency)
):
    try:
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
    except KeyError:
         raise HTTPException(status_code=500, detail="Harita verisi işlenirken bir hata oluştu (gezegenler veya evler bulunamadı).")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sunucu içi hata: {str(e)}")


@router.post(
    "/aspects",
    summary="Sinastri Açıları",
    description="İki harita arasındaki gezegenlerin birbirleriyle yaptığı açıları listeler.",
    response_model=List[Dict[str, Any]] # Yanıt modelini de ekleyelim
)
def get_synastry_aspects(
    charts: Dict[str, Any] = Depends(get_synastry_charts_dependency)
):
    """
    Bu endpoint, artık iki haritanın gezegen verilerini alıp,
    doğru motor fonksiyonuna paslayarak aralarındaki açıları hesaplar.
    """
    try:
        p1_planets = charts['p1_data']['planets']
        p2_planets = charts['p2_data']['planets']
        
        # DOĞRU MOTOR FONKSİYONUNU, DOĞRU PARAMETRELERLE ÇAĞIRIYORUZ.
        synastry_aspects = calculate_synastry_aspects(p1_planets, p2_planets)
        
        return synastry_aspects
    except KeyError:
        raise HTTPException(status_code=500, detail="Harita verisi işlenirken bir hata oluştu (gezegenler bulunamadı).")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sunucu içi hata: {str(e)}")


@router.post(
    "/bi-wheel-chart",
    summary="Sinastri Haritası Görseli (Bi-Wheel)",
    description="İki doğum haritasını iç içe çizen profesyonel bir sinastri haritası (PNG) üretir."
)
def get_bi_wheel_chart_endpoint(
    request: SynastryChartRequest,
    charts: Dict[str, Any] = Depends(get_synastry_charts_dependency)
):
    try:
        aspects = calculate_synastry_aspects(charts['p1_data']['planets'], charts['p2_data']['planets'])
        image_bytes = draw_bi_wheel_chart(
            p1_data=charts['p1_data'],
            p2_data=charts['p2_data'],
            synastry_aspects=aspects,
            person1_name=request.person1.name or "Person 1",
            person2_name=request.person2.name or "Person 2"
        )
        return Response(content=image_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Harita çizimi hatası: {str(e)}")