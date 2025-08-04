from datetime import datetime, timezone
from typing import Dict, Any, List

import swisseph as swe
from fastapi import APIRouter, Depends, HTTPException

# Gerekli modeller, bağımlılıklar ve merkezi sabitler import ediliyor.
from models.pydantic_models import BirthData
from api.v1.natal import get_natal_data_dependency, load_interpretations # Yorum yükleyiciyi de import ediyoruz
from core.config import PLANET_NUMBERS, TRANSIT_ASPECTS

# --- YENİ: Motorumuzdaki "Usta Şef" fonksiyonunu import ediyoruz ---
from services.astrology_engine import generate_daily_horoscope

router = APIRouter()


def _calculate_active_transits(natal_data: Dict[str, Any]) -> (List[Dict], datetime):
    """
    Doğum haritası gezegenleri ile anlık transit gezegenler arasındaki açıları hesaplayan
    yardımcı fonksiyon. Kod tekrarını önlemek için ana mantık buraya taşındı.
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


@router.post(
    "/daily-aspects",
    summary="Günlük Ham Transit Açıları",
    description="Bir doğum haritasının, mevcut anın gezegenleriyle yaptığı ham açı verilerini listeler. Yorum içermez."
)
def get_daily_transits(
    birth_data: BirthData,
    natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)
):
    active_transits, transit_time = _calculate_active_transits(natal_data)
    
    return {
        "birth_data": birth_data.dict(),
        "transit_time_utc": transit_time.isoformat(),
        "active_transits": active_transits
    }


# --- YENİ VE ANA ENDPOINT ---
@router.post(
    "/daily-horoscope",
    summary="Kişiye Özel Günlük Burç Yorumu",
    description="Aktif transitleri analiz ederek, kişiye özel olarak 'kişisel', 'duygusal', 'profesyonel' gibi kategorilerde bütünsel bir günlük yorum oluşturur."
)
def get_daily_horoscope(
    birth_data: BirthData,
    natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)
):
    """
    Önce aktif transitleri hesaplar, sonra bu transitleri ve yorumları "Usta Şef"
    fonksiyonumuza göndererek sentezlenmiş bir günlük rapor alır.
    """
    # 1. Ham transit verisini hesapla
    active_transits, transit_time = _calculate_active_transits(natal_data)
    
    if not active_transits:
        return {
            "birth_data": birth_data.dict(),
            "transit_time_utc": transit_time.isoformat(),
            "horoscope": {"personal": "Bugün için özel bir gezegen etkileşimi bulunmuyor. Sakin bir gün geçirebilirsiniz."}
        }
        
    # 2. Yorum "Tarif Defteri"ni yükle
    interpretations = load_interpretations("daily_transits.json")
    if not interpretations:
        raise HTTPException(status_code=500, detail="Günlük transit yorum dosyası 'daily_transits.json' bulunamadı veya boş.")
        
    # 3. Veriyi ve yorumları "Usta Şef"e göndererek sentezlenmiş raporu al
    horoscope_report = generate_daily_horoscope(active_transits, interpretations)
    
    return {
        "birth_data": birth_data.dict(),
        "transit_time_utc": transit_time.isoformat(),
        "horoscope": horoscope_report,
        "contributing_transits": active_transits # İsteğe bağlı: Yorumu hangi transitlerin oluşturduğunu göster
    }