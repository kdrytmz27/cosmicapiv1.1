from pathlib import Path
import swisseph as swe

# --- GÜVENLİK AYARLARI ---
API_KEY = "COSMIC_API_SECRET_KEY_12345"


# --- TEMEL PROJE YOLLARI ---
BASE_DIR = Path(__file__).parent.parent
EPHE_PATH = BASE_DIR / "data" / "ephe"
INTERPRETATION_PATH = BASE_DIR / "data" / "interpretations"


# --- GÖRSEL HARİTA SABİTLERİ (CHART CONSTANTS) ---
# ... (Bu bölümdeki tüm sabitler HİÇBİR DEĞİŞİKLİK OLMADAN AYNI KALIYOR) ...
PLANET_GLYPHS = {
    'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀', 'Mars': '♂',
    'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅', 'Neptune': '♆', 'Pluto': '♇',
    'True Node': '☊', 'Chiron': '⚷', 'Ceres': '⚳', 'Pallas': '⚴',
    'Juno': '⚵', 'Vesta': '⚶', 'Lilith': '⚸', 'Part of Fortune': '⊕'
}
ZODIAC_GLYPHS = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']
ASPECT_GLYPHS = {
    "Conjunction": "☌", "Sextile": "⚹", "Square": "□", "Trine": "△", "Opposition": "☍",
    "Quincunx": "⚻", "Semi-Sextile": "⚺", "Semi-Square": "∠", "Sesquiquadrate": "⚼",
    "Quintile": "Q", "Biquintile": "bQ"
}
ELEMENT_COLORS = {'Fire': '#FFDDC1', 'Earth': '#D4EDDA', 'Air': '#FFFACD', 'Water': '#D1E8FF'}
ASPECT_COLORS = {
    "Conjunction": "#4CBB17", "Sextile": "#43A6C6", "Square": "#C41E3A", "Trine": "#0067A5",
    "Opposition": "#FF4433", "Quincunx": "#A9A9A9", "Semi-Sextile": "#77DD77",
    "Semi-Square": "#FFB347", "Sesquiquadrate": "#FFB347", "Quintile": "#43A6C6",
    "Biquintile": "#05386B"
}


# --- ASTROLOJİ HESAPLAMA SABİTLERİ (ENGINE CONSTANTS) ---
ZODIAC_SIGNS = ["Koç", "Boğa", "İkizler", "Yengeç", "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova", "Balık"]
# ... (SIGN_TO_ELEMENT ve SIGN_TO_MODALITY aynı kalıyor) ...
SIGN_TO_ELEMENT = {
    'Koç': 'Fire', 'Aslan': 'Fire', 'Yay': 'Fire', 'Boğa': 'Earth', 'Başak': 'Earth', 'Oğlak': 'Earth',
    'İkizler': 'Air', 'Terazi': 'Air', 'Kova': 'Air', 'Yengeç': 'Water', 'Akrep': 'Water', 'Balık': 'Water'
}
SIGN_TO_MODALITY = {
    'Koç': 'Cardinal', 'Yengeç': 'Cardinal', 'Terazi': 'Cardinal', 'Oğlak': 'Cardinal',
    'Boğa': 'Fixed', 'Aslan': 'Fixed', 'Akrep': 'Fixed', 'Kova': 'Fixed',
    'İkizler': 'Mutable', 'Başak': 'Mutable', 'Yay': 'Mutable', 'Balık': 'Mutable'
}
SIGN_RULERS = {
    "Koç":     {"traditional": "Mars",    "modern": None}, "Boğa":    {"traditional": "Venus",   "modern": None},
    "İkizler": {"traditional": "Mercury", "modern": None}, "Yengeç":  {"traditional": "Moon",    "modern": None},
    "Aslan":   {"traditional": "Sun",     "modern": None}, "Başak":   {"traditional": "Mercury", "modern": None},
    "Terazi":  {"traditional": "Venus",   "modern": None}, "Akrep":   {"traditional": "Mars",    "modern": "Pluto"},
    "Yay":     {"traditional": "Jupiter", "modern": None}, "Oğlak":   {"traditional": "Saturn",  "modern": None},
    "Kova":    {"traditional": "Saturn",  "modern": "Uranus"}, "Balık":   {"traditional": "Jupiter", "modern": "Neptune"}
}

PLANET_NUMBERS = {
    'Sun': swe.SUN, 'Moon': swe.MOON, 'Mercury': swe.MERCURY, 'Venus': swe.VENUS, 'Mars': swe.MARS,
    'Jupiter': swe.JUPITER, 'Saturn': swe.SATURN, 'Uranus': swe.URANUS, 'Neptune': swe.NEPTUNE, 'Pluto': swe.PLUTO,
    'True Node': swe.TRUE_NODE, 'Chiron': 15,
    'Lilith': swe.OSCU_APOG,
    'Ceres': swe.AST_OFFSET + 1, 'Pallas': swe.AST_OFFSET + 2, 'Juno': swe.AST_OFFSET + 3, 'Vesta': swe.AST_OFFSET + 4
}

ASPECTS = {
    "Conjunction": {"angle": 0, "orb": 8, "type": "Major"}, "Opposition": {"angle": 180, "orb": 8, "type": "Major"},
    "Trine": {"angle": 120, "orb": 8, "type": "Major"}, "Square": {"angle": 90, "orb": 8, "type": "Major"},
    "Sextile": {"angle": 60, "orb": 6, "type": "Major"}, "Quincunx": {"angle": 150, "orb": 3, "type": "Minor"},
    "Semi-Sextile": {"angle": 30, "orb": 2, "type": "Minor"}, "Semi-Square": {"angle": 45, "orb": 2, "type": "Minor"},
    "Sesquiquadrate": {"angle": 135, "orb": 2, "type": "Minor"}, "Quintile": {"angle": 72, "orb": 2, "type": "Creative"},
    "Biquintile": {"angle": 144, "orb": 2, "type": "Creative"}
}

TRANSIT_ASPECTS = {
    "Conjunction": {"angle": 0, "orb": 5}, "Sextile": {"angle": 60, "orb": 4},
    "Square": {"angle": 90, "orb": 5}, "Trine": {"angle": 120, "orb": 5},
    "Opposition": {"angle": 180, "orb": 5}
}

# --- YENİ: Deklinasyon Açıları İçin Ayarlar ---
# Paralel ve Kontra-Paralel açıları için kullanılacak orb (tolerans) değeri.
# Genellikle 1.0 ila 1.2 derece arasında kullanılır.
DECLINATION_ASPECTS = {
    "Parallel": {"orb": 1.2, "type": "Declination"},
    "Contra-Parallel": {"orb": 1.2, "type": "Declination"}
}
# --- BİTTİ ---