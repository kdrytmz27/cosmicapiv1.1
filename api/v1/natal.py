import json
from typing import Dict, Any, List

from fastapi import APIRouter, Response, Depends, HTTPException
from fastapi_cache.decorator import cache

from core.config import INTERPRETATION_PATH
from models.pydantic_models import BirthData
from services.astrology_engine import calculate_natal_data, get_zodiac_sign_details
from services.chart_drawer import draw_final_professional_chart

router = APIRouter()

def load_interpretations(file_name: str) -> Dict:
    try:
        with open(INTERPRETATION_PATH / file_name, 'r', encoding='utf-8') as f: return json.load(f)
    except FileNotFoundError: return {}

@cache(expire=600)
def get_natal_data_dependency(birth_data: BirthData) -> Dict[str, Any]:
    natal_data = calculate_natal_data(birth_data)
    if "error" in natal_data: raise HTTPException(status_code=400, detail=natal_data["error"])
    return natal_data

# --- GÜNCELLENMİŞ ENDPOINT ---
@router.post("/full-chart", summary="Tam Doğum Haritası Verisi", description="Bir doğum tarihine ait tüm astrolojik verileri (gezegenler, evler, açılar vb.) JSON formatında döndürür.")
def get_full_natal_chart(natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    main_points = {"ascendant": {**get_zodiac_sign_details(natal_data['ascmc'][0])}, "mc": {**get_zodiac_sign_details(natal_data['ascmc'][1])}}
    rich_houses = [{"house": i + 1, **get_zodiac_sign_details(cusp)} for i, cusp in enumerate(natal_data['house_cusps'][:12])]
    return {
        "main_points": main_points, "planets": natal_data['planets'],
        "houses": rich_houses, "aspects": natal_data['aspects'],
        "aspect_patterns": natal_data['aspect_patterns'],
        "house_rulers": natal_data.get("house_rulers", []),
        "balance": natal_data.get("balance", {}) # YENİ: Denge verisi eklendi
    }

@router.post("/wheel-chart", summary="Doğum Haritası Görseli", description="Profesyonel bir doğum haritası görselini (PNG formatında) üretir.")
def get_natal_wheel_chart(natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    chart_image_bytes = draw_final_professional_chart(natal_data)
    return Response(content=chart_image_bytes, media_type="image/png")

def _get_planet_from_map(planets_map: Dict, planet_name: str):
    data = planets_map.get(planet_name)
    if not data:
        raise HTTPException(status_code=404, detail=f"Haritada '{planet_name}' bilgisi bulunamadı.")
    return data

@router.post("/report/ascendant", summary="Yükselen Burç Raporu", description="Yükselen burcun detaylarını ve astrolojik yorumunu döndürür.")
def get_ascendant_report(natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    interpretations = load_interpretations("ascendant.json")
    ascendant_degree = natal_data['ascmc'][0]
    sign_info = get_zodiac_sign_details(ascendant_degree)
    interpretation = interpretations.get(sign_info['sign'], "Bu burç için yorum bulunamadı.")
    return {"report_type": "Ascendant Sign", **sign_info, "interpretation": interpretation}

@router.post("/report/mc-sign", summary="Tepe Noktası (MC) Burç Raporu", description="Tepe Noktası'nın (MC) bulunduğu burcun detaylarını ve kariyerle ilgili astrolojik yorumunu döndürür.")
def get_mc_sign_report(natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    interpretations = load_interpretations("mc_signs.json")
    mc_degree = natal_data['ascmc'][1]
    sign_info = get_zodiac_sign_details(mc_degree)
    interpretation = interpretations.get(sign_info['sign'], "Bu burç için yorum bulunamadı.")
    return {"report_type": "Midheaven (MC) Sign", **sign_info, "interpretation": interpretation}

@router.post("/report/sun-sign", summary="Güneş Burcu Raporu", description="Güneş burcunun detaylarını ve astrolojik yorumunu döndürür.")
def get_sun_sign_report(natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    planets_map = {p['planet']: p for p in natal_data['planets']}
    interpretations = load_interpretations("sun_sign.json")
    sun_data = _get_planet_from_map(planets_map, "Sun")
    interpretation = interpretations.get(sun_data['sign'], "Bu burç için yorum bulunamadı.")
    return {"report_type": "Sun Sign", **sun_data, "interpretation": interpretation}

@router.post("/report/moon-sign", summary="Ay Burcu Raporu", description="Ay burcunun detaylarını ve astrolojik yorumunu döndürür.")
def get_moon_sign_report(natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    planets_map = {p['planet']: p for p in natal_data['planets']}
    interpretations = load_interpretations("moon_sign.json")
    moon_data = _get_planet_from_map(planets_map, "Moon")
    interpretation = interpretations.get(moon_data['sign'], "Bu burç için yorum bulunamadı.")
    return {"report_type": "Moon Sign", **moon_data, "interpretation": interpretation}

@router.post("/report/planets-in-houses", summary="Gezegenlerin Evlerdeki Yorumu", description="Haritadaki her bir gezegenin bulunduğu eve göre astrolojik yorumunu listeler.")
def get_planets_in_houses_report(natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    interpretations = load_interpretations("planets_in_houses.json")
    report_list = []
    planets_to_interpret = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    for planet_data in natal_data['planets']:
        if planet_data['planet'] in planets_to_interpret:
            house_number = str(planet_data['house'])
            planet_interpretations = interpretations.get(planet_data['planet'], {})
            interpretation = planet_interpretations.get(house_number, "Bu gezegen/ev kombinasyonu için yorum bulunamadı.")
            report_list.append({"planet": planet_data['planet'], "house": planet_data['house'], "sign": planet_data['sign'], "interpretation": interpretation})
    return {"report_type": "Planets in Houses", "interpretations": report_list}

@router.post("/report/aspects", summary="Gezegenler Arası Açı Yorumları", description="Haritadaki gezegenler arasında oluşan önemli açıların astrolojik yorumlarını listeler.")
def get_aspects_report(natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    interpretations = load_interpretations("aspects.json")
    report_list = []
    aspect_list = natal_data.get("aspects", [])
    for aspect in aspect_list:
        p1, p2, aspect_name = aspect['planet1'], aspect['planet2'], aspect['aspect']
        sorted_planets = sorted([p1, p2])
        aspect_key = f"{sorted_planets[0]}-{sorted_planets[1]}"
        aspect_group = interpretations.get(aspect_key, {})
        interpretation = aspect_group.get(aspect_name, "Bu açı kalıbı için özel yorum bulunamadı.")
        if "bulunamadı" not in interpretation: report_list.append({**aspect, "interpretation": interpretation})
    return {"report_type": "Aspect Interpretations", "interpretations": report_list}

@router.post("/report/house-rulers-in-houses", summary="Ev Yöneticileri Raporu", description="Her bir evin yöneticisinin hangi evde olduğunu ve bunun ne anlama geldiğini yorumlar.")
def get_house_rulers_report(natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    interpretations = load_interpretations("house_rulers_in_houses.json")
    report_list = []
    house_rulers_data = natal_data.get("house_rulers", [])
    for ruler_info in house_rulers_data:
        managed_house = str(ruler_info.get("house"))
        ruler_in_house = str(ruler_info.get("ruler_in_house"))
        house_group = interpretations.get(managed_house, {})
        interpretation = house_group.get(ruler_in_house, "Bu ev yöneticiliği kombinasyonu için özel yorum bulunamadı.")
        if "bulunamadı" not in interpretation: report_list.append({**ruler_info, "interpretation": interpretation})
    return {"report_type": "House Rulerships", "interpretations": report_list}

@router.post("/report/retrogrades", summary="Retro Gezegenler Raporu", description="Doğum haritasında geri harekette (retro) olan gezegenleri ve bunların astrolojik anlamlarını listeler.")
def get_retrograde_planets_report(natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    interpretations = load_interpretations("retrograde_planets.json")
    report_list = []
    for planet_data in natal_data.get("planets", []):
        if planet_data.get("is_retrograde"):
            interpretation = interpretations.get(planet_data['planet'], "Bu retro gezegen için özel yorum bulunamadı.")
            if "bulunamadı" not in interpretation: report_list.append({"planet": planet_data['planet'], "interpretation": interpretation})
    return {"report_type": "Retrograde Planets", "interpretations": report_list}

@router.post("/report/north-node-sign", summary="Kuzey Ay Düğümü Raporu", description="Karmik yaşam yolunu gösteren Kuzey Ay Düğümü'nün burcunu ve anlamını yorumlar.")
def get_north_node_sign_report(natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    planets_map = {p['planet']: p for p in natal_data['planets']}
    interpretations = load_interpretations("north_node_in_signs.json")
    node_data = _get_planet_from_map(planets_map, "True Node")
    interpretation = interpretations.get(node_data['sign'], "Bu burç için yorum bulunamadı.")
    return {"report_type": "North Node in Sign", **node_data, "interpretation": interpretation}

@router.post("/report/lilith-sign", summary="Lilith (Kara Ay) Raporu", description="Bastırılmış gölge yönleri temsil eden Lilith'in burcunu ve anlamını yorumlar.")
def get_lilith_sign_report(natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    planets_map = {p['planet']: p for p in natal_data['planets']}
    interpretations = load_interpretations("lilith_in_signs.json")
    lilith_data = _get_planet_from_map(planets_map, "Lilith")
    interpretation = interpretations.get(lilith_data['sign'], "Bu burç için yorum bulunamadı.")
    return {"report_type": "Lilith in Sign", **lilith_data, "interpretation": interpretation}

@router.post("/report/chiron-sign", summary="Chiron (Yaralı Şifacı) Raporu", description="En derin yaraları ve şifa potansiyelini gösteren Chiron'un burcunu ve anlamını yorumlar.")
def get_chiron_sign_report(natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    planets_map = {p['planet']: p for p in natal_data['planets']}
    interpretations = load_interpretations("chiron_in_signs.json")
    chiron_data = _get_planet_from_map(planets_map, "Chiron")
    interpretation = interpretations.get(chiron_data['sign'], "Bu burç için yorum bulunamadı.")
    return {"report_type": "Chiron in Sign", **chiron_data, "interpretation": interpretation}

@router.post("/report/north-node-in-house", summary="Kuzey Ay Düğümü Ev Raporu", description="Karmik yaşam yolunun hangi hayat alanında gelişeceğini yorumlar.")
def get_north_node_in_house_report(natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    planets_map = {p['planet']: p for p in natal_data['planets']}
    interpretations = load_interpretations("north_node_in_houses.json")
    node_data = _get_planet_from_map(planets_map, "True Node")
    house_key = str(node_data.get('house', ''))
    interpretation = interpretations.get(house_key, "Bu ev konumu için yorum bulunamadı.")
    return {"report_type": "North Node in House", **node_data, "interpretation": interpretation}

@router.post("/report/lilith-in-house", summary="Lilith (Kara Ay) Ev Raporu", description="Bastırılmış gölge yönlerin hangi hayat alanında ortaya çıktığını yorumlar.")
def get_lilith_in_house_report(natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    planets_map = {p['planet']: p for p in natal_data['planets']}
    interpretations = load_interpretations("lilith_in_houses.json")
    lilith_data = _get_planet_from_map(planets_map, "Lilith")
    house_key = str(lilith_data.get('house', ''))
    interpretation = interpretations.get(house_key, "Bu ev konumu için yorum bulunamadı.")
    return {"report_type": "Lilith in House", **lilith_data, "interpretation": interpretation}

@router.post("/report/chiron-in-house", summary="Chiron (Yaralı Şifacı) Ev Raporu", description="En derin yaraların ve şifa potansiyelinin hangi hayat alanında olduğunu yorumlar.")
def get_chiron_in_house_report(natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    planets_map = {p['planet']: p for p in natal_data['planets']}
    interpretations = load_interpretations("chiron_in_houses.json")
    chiron_data = _get_planet_from_map(planets_map, "Chiron")
    house_key = str(chiron_data.get('house', ''))
    interpretation = interpretations.get(house_key, "Bu ev konumu için yorum bulunamadı.")
    return {"report_type": "Chiron in House", **chiron_data, "interpretation": interpretation}

# --- YENİ ENDPOINT ---
@router.post(
    "/report/balance",
    summary="Harita Dengesi Raporu (Insights)",
    description="Haritadaki gezegenlerin element ve nitelik dağılımını göstererek, haritanın genel karakteri hakkında bir özet sunar."
)
def get_balance_report(natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    """
    Astroloji motorundan gelen 'balance' verisini doğrudan kullanıcıya sunar.
    """
    balance_data = natal_data.get("balance")
    if not balance_data:
         raise HTTPException(status_code=404, detail="Harita için denge verisi hesaplanamadı.")
    
    return {
        "report_type": "Chart Balance (Insights)",
        "data": balance_data
    }