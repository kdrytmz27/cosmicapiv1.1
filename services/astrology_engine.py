import swisseph as swe
from datetime import datetime
import pytz
from timezonefinder import TimezoneFinder
from typing import Dict, Any, List
import itertools

from models.pydantic_models import BirthData
from core.config import (
    EPHE_PATH, ZODIAC_SIGNS, ZODIAC_GLYPHS, SIGN_TO_ELEMENT,
    SIGN_TO_MODALITY, SIGN_RULERS, PLANET_NUMBERS, ASPECTS,
    DECLINATION_ASPECTS
)

# ... (Bu dosyadaki diğer tüm yardımcı fonksiyonlar, `calculate_natal_data`'ya kadar aynı kalıyor) ...
def format_declination(dec: float) -> str:
    direction = "N" if dec >= 0 else "S"; dec = abs(dec); degrees = int(dec); minutes = int((dec - degrees) * 60)
    return f"{degrees:02d}° {direction} {minutes:02d}'"
def get_zodiac_sign_details(degree: float) -> Dict[str, Any]:
    sign_index = int(degree / 30); degree_in_sign = degree % 30; sign_name = ZODIAC_SIGNS[sign_index]
    return {"sign": sign_name, "sign_glyph": ZODIAC_GLYPHS[sign_index], "degree": int(degree_in_sign),
            "minute": int((degree_in_sign - int(degree_in_sign)) * 60), "element": SIGN_TO_ELEMENT.get(sign_name),
            "modality": SIGN_TO_MODALITY.get(sign_name)}
def _find_planet_in_house(planet_longitude: float, house_cusps: List[float]) -> int:
    for i in range(12):
        house_start = house_cusps[i]; house_end = house_cusps[i + 1] if i < 11 else house_cusps[0]
        if house_start > house_end:
            if planet_longitude >= house_start or planet_longitude < house_end: return i + 1
        else:
            if house_start <= planet_longitude < house_end: return i + 1
    return 0
def calculate_aspects(planets_and_points: list) -> List[Dict[str, Any]]:
    found_aspects = []
    for p1, p2 in itertools.combinations(planets_and_points, 2):
        angle = abs(p1['longitude'] - p2['longitude'])
        if angle > 180: angle = 360 - angle
        for aspect_name, aspect_info in ASPECTS.items():
            orb = round(abs(angle - aspect_info['angle']), 2)
            if orb <= aspect_info['orb']:
                nature = "N/A"
                if p1.get('speed') is not None and p2.get('speed') is not None:
                    p1_speed = p1.get('speed', 0.0); p2_speed = p2.get('speed', 0.0)
                    p_fast = p1 if abs(p1_speed) > abs(p2_speed) else p2; p_slow = p2 if abs(p1_speed) > abs(p2_speed) else p1
                    future_lon_fast = (p_fast['longitude'] + (p_fast.get('speed', 0.0) * 0.01)) % 360
                    future_lon_slow = (p_slow['longitude'] + (p_slow.get('speed', 0.0) * 0.01)) % 360
                    future_angle = abs(future_lon_fast - future_lon_slow)
                    if future_angle > 180: future_angle = 360 - future_angle
                    future_orb = abs(future_angle - aspect_info['angle'])
                    nature = "Separating"
                    if future_orb < orb: nature = "Applying"
                found_aspects.append({"planet1": p1['planet'], "aspect": aspect_name, "planet2": p2['planet'], "orb": orb, "type": aspect_info['type'], "nature": nature})
                break
    return found_aspects
def recognize_aspect_patterns(planets: List[Dict], aspects: List[Dict]) -> List[Dict]:
    patterns, sign_counts, house_counts = [], {}, {}
    for p in planets:
        sign, house = p['sign'], p['house']
        sign_counts[sign] = sign_counts.get(sign, []) + [p['planet']]
        house_counts[house] = house_counts.get(house, []) + [p['planet']]
    for sign, p_list in sign_counts.items():
        if len(p_list) >= 3: patterns.append({"pattern": "Stellium", "type": "Sign", "location": sign, "planets": p_list})
    for house, p_list in house_counts.items():
        if len(p_list) >= 3: patterns.append({"pattern": "Stellium", "type": "House", "location": f"House {house}", "planets": p_list})
    trines = [a for a in aspects if a['aspect'] == 'Trine']
    for p1, p2, p3 in itertools.combinations(planets, 3):
        p_names = {p1['planet'], p2['planet'], p3['planet']}
        if any(a for a in trines if {p1['planet'], p2['planet']}.issubset(a.values())) and \
           any(a for a in trines if {p1['planet'], p3['planet']}.issubset(a.values())) and \
           any(a for a in trines if {p2['planet'], p3['planet']}.issubset(a.values())):
            if not any(p.get('pattern') == 'Grand Trine' and set(p.get('planets')) == p_names for p in patterns):
                patterns.append({"pattern": "Grand Trine", "planets": sorted(list(p_names)), "element": SIGN_TO_ELEMENT.get(p1['sign'])})
    oppositions = [a for a in aspects if a['aspect'] == 'Opposition']
    squares = [a for a in aspects if a['aspect'] == 'Square']
    for opp in oppositions:
        p1_opp, p2_opp = opp['planet1'], opp['planet2']
        for apex_planet in planets:
            p_apex = apex_planet['planet']
            if p_apex in [p1_opp, p2_opp]: continue
            if any(a for a in squares if {p1_opp, p_apex}.issubset(a.values())) and \
               any(a for a in squares if {p2_opp, p_apex}.issubset(a.values())):
                p_names = {p1_opp, p2_opp, p_apex}
                if not any(p.get('pattern') == 'T-Square' and set(p.get('planets')) == p_names for p in patterns):
                    patterns.append({"pattern": "T-Square", "planets": sorted(list(p_names)), "apex_planet": p_apex})
    return patterns
def calculate_synastry_aspects(planets1: List[Dict], planets2: List[Dict]) -> List[Dict]:
    SYNASTRY_MAJOR_ASPECTS = {k: v for k, v in ASPECTS.items() if v['type'] == 'Major'}
    synastry_aspects = []
    for p1 in planets1:
        for p2 in planets2:
            angle = abs(p1['longitude'] - p2['longitude'])
            if angle > 180: angle = 360 - angle
            for aspect_name, aspect_info in SYNASTRY_MAJOR_ASPECTS.items():
                orb = round(abs(angle - aspect_info['angle']), 2)
                if orb <= aspect_info['orb']:
                    synastry_aspects.append({"planet1": p1['planet'], "aspect": aspect_name, "planet2": p2['planet'], "orb": orb})
                    break
    return synastry_aspects
def _find_house_rulers(house_cusps: List[float], planets: List[Dict], rulership_system: str) -> List[Dict]:
    rulerships = []
    planets_map = {p['planet']: p for p in planets}
    for i in range(12):
        house_num = i + 1; cusp_sign_details = get_zodiac_sign_details(house_cusps[i]); cusp_sign = cusp_sign_details['sign']
        ruler_info = SIGN_RULERS.get(cusp_sign)
        if not ruler_info: continue
        ruler_planet_name = ruler_info['traditional']
        if rulership_system == 'modern' and ruler_info['modern'] is not None: ruler_planet_name = ruler_info['modern']
        ruler_planet_data = planets_map.get(ruler_planet_name)
        if ruler_planet_data:
            ruler_in_house = ruler_planet_data.get('house')
            rulerships.append({"house": house_num, "sign": cusp_sign, "ruler_planet": ruler_planet_name,
                               "ruler_in_house": ruler_in_house, "rulership_system_used": rulership_system})
    return rulerships
def calculate_declination_aspects(planets: List[Dict]) -> List[Dict]:
    found_aspects = []; orb = DECLINATION_ASPECTS["Parallel"]["orb"]
    for p1, p2 in itertools.combinations(planets, 2):
        if 'declination' not in p1 or 'declination' not in p2 or p1['planet'] == 'Part of Fortune' or p2['planet'] == 'Part of Fortune': continue
        dec1 = p1['declination']; dec2 = p2['declination']
        if (dec1 >= 0 and dec2 >= 0) or (dec1 < 0 and dec2 < 0):
            if abs(dec1 - dec2) <= orb:
                found_aspects.append({"planet1": p1['planet'], "aspect": "Parallel", "planet2": p2['planet'],
                                      "orb": round(abs(dec1 - dec2), 2), "type": "Declination", "nature": "N/A"})
        else:
            if abs(abs(dec1) - abs(dec2)) <= orb:
                found_aspects.append({"planet1": p1['planet'], "aspect": "Contra-Parallel", "planet2": p2['planet'],
                                      "orb": round(abs(abs(dec1) - abs(dec2)), 2), "type": "Declination", "nature": "N/A"})
    return found_aspects

# --- YENİ FONKSİYON ---
def _calculate_balance(planets_with_details: List[Dict]) -> Dict[str, Any]:
    """
    Haritanın element (Ateş, Toprak, Hava, Su) ve nitelik (Öncü, Sabit, Değişken)
    dengesini hesaplar.
    """
    elements = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}
    modalities = {'Cardinal': 0, 'Fixed': 0, 'Mutable': 0}
    
    # Denge hesaplamasına dahil edilmeyecek astrolojik noktalar.
    # Genellikle sadece 10 ana gezegen (Güneş-Plüton) sayılır.
    planets_for_balance = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    
    for p in planets_with_details:
        if p['planet'] in planets_for_balance:
            if p.get('element'):
                elements[p['element']] += 1
            if p.get('modality'):
                modalities[p['modality']] += 1
                
    return {"elements": elements, "modalities": modalities}
# --- BİTTİ ---

def calculate_natal_data(birth_data: BirthData) -> Dict[str, Any]:
    # ... (tüm hesaplamaların başı aynı kalıyor) ...
    tf = TimezoneFinder(); timezone_str = tf.timezone_at(lng=birth_data.lon, lat=birth_data.lat)
    if not timezone_str: return {"error": "Geçersiz koordinatlar için zaman dilimi bulunamadı."}
    local_tz = pytz.timezone(timezone_str); naive_dt = datetime.combine(birth_data.date, birth_data.time)
    local_dt = local_tz.localize(naive_dt); utc_dt = local_tz.normalize(local_dt).astimezone(pytz.utc)
    julian_day_utc = swe.utc_to_jd(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour, utc_dt.minute, utc_dt.second, 1)[0]
    swe.set_ephe_path(str(EPHE_PATH))
    raw_planets = []; planet_longitudes = {}
    for name, num in PLANET_NUMBERS.items():
        pos_data, ret_flag = swe.calc_ut(julian_day_utc, num, 0) if name == 'Lilith' else swe.calc_ut(julian_day_utc, num, swe.FLG_SPEED)
        if ret_flag < 0: continue
        longitude = pos_data[0]
        eq_data, ret_flag_eq = swe.calc_ut(julian_day_utc, num, swe.FLG_EQUATORIAL)
        declination = eq_data[1] if ret_flag_eq >= 0 else 0.0
        is_retrograde, speed = False, 0.0
        if len(pos_data) > 3 and name != 'Lilith':
            speed = pos_data[3]
            if name not in ['True Node', 'Sun', 'Moon'] and speed < 0: is_retrograde = True
        raw_planets.append({"planet": name, "longitude": longitude, "is_retrograde": is_retrograde, "speed": speed,
                            "declination": declination, "declination_formatted": format_declination(declination)})
        planet_longitudes[name] = longitude
    try:
        house_cusps_raw, ascmc = swe.houses(julian_day_utc, birth_data.lat, birth_data.lon, bytes(birth_data.house_system.value, "utf-8"))
    except swe.Error as e: return {"error": f"Evler hesaplanamadı. Detay: {e}"}
    asc_longitude = ascmc[0]; sun_longitude = planet_longitudes.get('Sun', 0); moon_longitude = planet_longitudes.get('Moon', 0)
    horizon_diff = (sun_longitude - asc_longitude + 360) % 360; is_day_chart = 0 <= horizon_diff < 180
    if is_day_chart: fortune_longitude = (asc_longitude + moon_longitude - sun_longitude + 360) % 360
    else: fortune_longitude = (asc_longitude + sun_longitude - moon_longitude + 360) % 360
    raw_planets.append({"planet": "Part of Fortune", "longitude": fortune_longitude, "is_retrograde": False,
                        "speed": 0.0, "declination": 0.0, "declination_formatted": "N/A"})
    planets_with_details = []
    for p in raw_planets:
        details = get_zodiac_sign_details(p['longitude'])
        house = _find_planet_in_house(p['longitude'], list(house_cusps_raw))
        planets_with_details.append({**p, **details, "house": house})

    # ... (açı, açı kalıpları, ev yöneticileri hesaplamaları aynı kalıyor) ...
    planet_to_planet_aspects = calculate_aspects(planets_with_details)
    aspect_patterns = recognize_aspect_patterns(planets_with_details, planet_to_planet_aspects)
    all_points_for_aspects = planets_with_details + [{"planet": "Ascendant", "longitude": ascmc[0], "speed": None},{"planet": "Midheaven", "longitude": ascmc[1], "speed": None}]
    longitude_aspects = calculate_aspects(all_points_for_aspects)
    declination_aspects = calculate_declination_aspects(planets_with_details)
    all_aspects = longitude_aspects + declination_aspects
    house_rulers = _find_house_rulers(list(house_cusps_raw), planets_with_details, birth_data.rulership_system.value)

    # --- YENİ: Denge (Insights) verisini hesapla ---
    balance_data = _calculate_balance(planets_with_details)
    
    # --- GÜNCELLEME: Dönen sonuca `balance` verisini ekle ---
    return {
        "planets": planets_with_details, "house_cusps": list(house_cusps_raw), "ascmc": list(ascmc),
        "aspects": all_aspects,
        "aspect_patterns": aspect_patterns,
        "house_rulers": house_rulers,
        "balance": balance_data # YENİ VERİ
    }