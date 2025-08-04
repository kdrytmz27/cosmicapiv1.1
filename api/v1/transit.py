from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple # YENİ: `Tuple` import edildi
from collections import defaultdict

import swisseph as swe
from fastapi import APIRouter, Depends, HTTPException

from models.pydantic_models import BirthData
from api.v1.natal import get_natal_data_dependency, load_interpretations
from core.config import PLANET_NUMBERS, TRANSIT_ASPECTS, PLANET_ASSOCIATIONS

router = APIRouter()

# --- DEĞİŞİKLİK: Fonksiyonun dönüş tipi modern standartlara uygun hale getirildi ---
def _calculate_active_transits(natal_data: Dict[str, Any]) -> Tuple[List[Dict], datetime]:
    """
    Doğum haritası gezegenleri ile anlık transit gezegenler arasındaki açıları hesaplayan
    yardımcı fonksiyon. Kod tekrarını önlemek için ana mantık buraya taşındı.
    Dönüş Tipi: (Açı Listesi, Zaman Damgası) şeklinde bir tuple.
    """
    now_utc = datetime.now(timezone.utc)
    julian_day_now = swe.utc_to_jd(now_utc.year, now_utc.month, now_utc.day,
                                  now_utc.hour, now_utc.minute, now_utc.second, 1)[0]
    transiting_planet_names = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    transit_planets = []
    for name in transiting_planet_names:
        planet_number = PLANET_NUMBERS.get(name)
        if planet_number is not None:
            pos_data, ret_flag = swe.calc_ut(julian_day_now, planet_number, swe.FLG_SPEED)
            if ret_flag >= 0:
                transit_planets.append({"planet": f"Transit {name}", "longitude": pos_data[0]})
    transit_aspects = []
    for t_planet in transit_planets:
        for n_planet in natal_data['planets']:
            angle = abs(t_planet['longitude'] - n_planet['longitude'])
            if angle > 180: angle = 360 - angle
            for aspect_name, aspect_info in TRANSIT_ASPECTS.items():
                if aspect_info['angle'] - aspect_info['orb'] <= angle <= aspect_info['angle'] + aspect_info['orb']:
                    transit_aspects.append({
                        "transit_planet": t_planet['planet'], "aspect": aspect_name,
                        "natal_planet": n_planet['planet'],
                        "orb": round(abs(angle - aspect_info['angle']), 2)
                    })
                    break
    return transit_aspects, now_utc
# --- DEĞİŞİKLİK SONU ---

def generate_daily_horoscope(active_transits: List[Dict], interpretations: Dict) -> Dict[str, Any]:
    horoscope_by_category = defaultdict(list)
    for transit in active_transits:
        transit_planet_name_full = transit.get('transit_planet', '')
        if not transit_planet_name_full: continue
        
        parts = transit_planet_name_full.split(" ")
        if len(parts) < 2: continue
        
        transit_planet_name = parts[1]
        natal_planet_name = transit['natal_planet']
        aspect = transit['aspect']
        
        key = f"Transit {transit_planet_name}-Natal {natal_planet_name}"
        aspect_interpretations = interpretations.get(key, {}).get(aspect)
        
        if aspect_interpretations:
            for category, text in aspect_interpretations.items():
                if isinstance(text, list):
                    horoscope_by_category[category].extend(text)
                else:
                    horoscope_by_category[category].append(text)

    lucky_aspect = None; min_orb = 100
    for transit in active_transits:
        transit_planet_name_full = transit.get('transit_planet', '')
        if not transit_planet_name_full: continue
        parts = transit_planet_name_full.split(" ")
        if len(parts) < 2: continue
        transit_planet = parts[1]
        aspect = transit['aspect']
        if transit_planet in ["Jupiter", "Venus"] and aspect in ["Conjunction", "Trine", "Sextile"]:
            if transit['orb'] < min_orb:
                min_orb = transit['orb']
                lucky_aspect = transit
    if lucky_aspect:
        lucky_planet_name = lucky_aspect['transit_planet'].split(" ")[1]
        planet_luck_info = PLANET_ASSOCIATIONS.get(lucky_planet_name)
        if planet_luck_info:
            horoscope_by_category['luck'].append(f"Şanslı Renginiz: {planet_luck_info['color']}")
            horoscope_by_category['luck'].append(f"Şanslı Sayınız: {planet_luck_info['number']}")

    final_horoscope = {}
    for category, texts in horoscope_by_category.items():
        if category == 'luck':
            final_horoscope[category] = sorted(list(set(texts)))
        else:
            final_horoscope[category] = " ".join(texts)
    return final_horoscope

@router.post("/daily-aspects", summary="Günlük Ham Transit Açıları", description="Bir doğum haritasının, mevcut anın gezegenleriyle yaptığı ham açı verilerini listeler.")
def get_daily_transits(birth_data: BirthData, natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    active_transits, transit_time = _calculate_active_transits(natal_data)
    return {"birth_data": birth_data.dict(), "transit_time_utc": transit_time.isoformat(), "active_transits": active_transits}

@router.post("/daily-horoscope", summary="Kişiye Özel Günlük Burç Yorumu", description="Aktif transitleri analiz ederek, kişiye özel günlük yorum oluşturur.")
def get_daily_horoscope(birth_data: BirthData, natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)):
    active_transits, transit_time = _calculate_active_transits(natal_data)
    if not active_transits:
        return {"birth_data": birth_data.dict(), "transit_time_utc": transit_time.isoformat(), "horoscope": {"personal": "Bugün için özel bir gezegen etkileşimi bulunmuyor. Sakin bir gün geçirebilirsiniz."}}
    interpretations = load_interpretations("daily_transits.json")
    if not interpretations:
        raise HTTPException(status_code=500, detail="Günlük transit yorum dosyası 'daily_transits.json' bulunamadı veya boş.")
    horoscope_report = generate_daily_horoscope(active_transits, interpretations)
    return {"birth_data": birth_data.dict(), "transit_time_utc": transit_time.isoformat(), "horoscope": horoscope_report, "contributing_transits": active_transits}