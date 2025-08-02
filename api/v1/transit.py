from datetime import datetime, timezone
from typing import Dict, Any

import swisseph as swe
from fastapi import APIRouter, Depends

# Gerekli modeller, bağımlılıklar ve merkezi sabitler import ediliyor.
from models.pydantic_models import BirthData
from api.v1.natal import get_natal_data_dependency # Natal veriyi verimli çeken bağımlılığı import ediyoruz.
from core.config import PLANET_NUMBERS, TRANSIT_ASPECTS

router = APIRouter()

@router.post(
    "/daily-aspects",
    summary="Günlük Transit Açıları",
    description="Bir doğum haritasının, mevcut anın gezegen konumlarıyla (transitler) yaptığı önemli açıları listeler."
)
def get_daily_transits(
    birth_data: BirthData,
    natal_data: Dict[str, Any] = Depends(get_natal_data_dependency)
):
    """
    Doğum haritası gezegenleri ile anlık transit gezegenler arasındaki açıları hesaplar.
    """
    # 1. Anlık Zamanı ve Julian Günü'nü Hesapla
    now_utc = datetime.now(timezone.utc)
    # Swiss Ephemeris'in kullanacağı zaman formatı olan Julian Day'e çevir.
    julian_day_now = swe.utc_to_jd(
        now_utc.year, now_utc.month, now_utc.day,
        now_utc.hour, now_utc.minute, now_utc.second,
        1 # Gregorian takvim
    )[0]

    # 2. Transit Gezegenlerin Konumlarını Hesapla
    # Sadece ana gök cisimlerini transit olarak hesaplamak için bir liste.
    transiting_planet_names = [
        'Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter',
        'Saturn', 'Uranus', 'Neptune', 'Pluto'
    ]
    
    transit_planets = []
    for name in transiting_planet_names:
        planet_number = PLANET_NUMBERS[name]
        # swe.calc_ut ile gezegenin anlık pozisyonunu (boylam, hız vb.) hesapla
        pos = swe.calc_ut(julian_day_now, planet_number, swe.FLG_SPEED)
        transit_planets.append({
            "planet": f"Transit {name}",
            "longitude": pos[0][0]
        })

    # 3. Transit Açılarını Hesapla
    # KALDIRILDI: ASPECTS sözlüğü artık merkezi config'den 'TRANSIT_ASPECTS' olarak geliyor.
    transit_aspects = []
    for t_planet in transit_planets:
        for n_planet in natal_data['planets']:
            # İki gezegen arasındaki en kısa açıyı (0-180 derece) bul
            angle = abs(t_planet['longitude'] - n_planet['longitude'])
            if angle > 180:
                angle = 360 - angle

            for aspect_name, aspect_info in TRANSIT_ASPECTS.items():
                # Açının, belirlenen orb (tolerans) içinde olup olmadığını kontrol et
                if aspect_info['angle'] - aspect_info['orb'] <= angle <= aspect_info['angle'] + aspect_info['orb']:
                    transit_aspects.append({
                        "transit_planet": t_planet['planet'],
                        "aspect": aspect_name,
                        "natal_planet": n_planet['planet'],
                        "orb": round(abs(angle - aspect_info['angle']), 2) # Tam orb değerini ekle
                    })
                    break # İlk uygun açıyı bulunca diğerlerini kontrol etme

    return {
        "birth_data": birth_data.dict(),
        "transit_time_utc": now_utc.isoformat(),
        "active_transits": transit_aspects
    }