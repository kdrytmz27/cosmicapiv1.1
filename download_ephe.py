import pyswisseph
import os

# pyswisseph kütüphanesinin ephemeris dosyalarını nereye kurması gerektiğini
# projemizin içindeki data/ephe klasörü olarak belirliyoruz.
# Bu, core/config.py dosyanızdaki EPHE_PATH ile aynı olmalı.
target_path = os.path.join(os.path.dirname(__file__), 'data', 'ephe')

print(f"Ephemeris dosyaları '{target_path}' dizinine indirilecek...")

# pyswisseph'in kendi indirme fonksiyonunu çağır
# path= parametresi, dosyaların nereye indirileceğini belirtir.
pyswisseph.download_ephemeris_files(path=target_path)

print("Ephemeris dosyalarının indirilmesi tamamlandı.")