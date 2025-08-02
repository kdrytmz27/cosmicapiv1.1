from pydantic import BaseModel, Field
from enum import Enum
from datetime import date as DateType, time as TimeType

class HouseSystem(str, Enum):
    PLACIDUS = "P"
    KOCH = "K"
    REGIOMONTANUS = "R"
    CAMPANUS = "C"
    EQUAL_FROM_ASC = "A"
    WHOLE_SIGN = "W"
    PORPHYRY = "O"
    ALCABITIUS = "B"
    TOPOCENTRIC = "T"
    MERIDIAN = "M"
    VEHLOW_EQUAL = "V"
    POLI_EQUATORIAL = "G"

# --- YENİ: Yöneticilik Sistemi için Seçenekler ---
class RulershipSystem(str, Enum):
    """
    Ev yöneticilerini belirlemek için kullanılacak astrolojik sistemi tanımlar.
    - TRADITIONAL: Sadece 7 geleneksel gezegeni kullanır.
    - MODERN: Dış gezegenleri (Uranüs, Neptün, Plüton) de yönetici olarak dahil eder.
    """
    TRADITIONAL = "traditional"
    MODERN = "modern"
# --- BİTTİ ---

class BirthData(BaseModel):
    date: DateType = Field(..., example="1990-01-01", description="Doğum tarihi (YYYY-MM-DD formatında).")
    time: TimeType = Field(..., example="12:00", description="Doğum saati (HH:MM formatında).")
    
    lat: float = Field(..., example=41.0, description="Enlem (Latitude) değeri.")
    lon: float = Field(..., example=29.0, description="Boylam (Longitude) değeri.")
    
    house_system: HouseSystem = Field(default=HouseSystem.PLACIDUS, title="Ev Sistemi")
    
    # --- YENİ ALAN EKLENDİ ---
    # Kullanıcının hangi yönetici sistemini kullanmak istediğini seçmesini sağlar.
    # Varsayılan olarak 'MODERN' ayarlanmıştır, çünkü bu daha yaygın bir kullanımdır.
    rulership_system: RulershipSystem = Field(
        default=RulershipSystem.MODERN,
        title="Yöneticilik Sistemi",
        description="Ev yöneticileri için kullanılacak sistem (geleneksel veya modern)."
    )
    # --- BİTTİ ---

class SynastryData(BaseModel):
    person1: BirthData
    person2: BirthData