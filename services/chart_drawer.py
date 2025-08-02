import io
from typing import List, Dict, Any
import matplotlib
# 'AGG' backend'i, bir grafik arayüzü olmadan (sunucu ortamı için ideal)
# dosyaya çizim yapmamızı sağlar.
matplotlib.use('AGG')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Wedge

# Gerekli tüm sabitler ve yardımcı fonksiyonlar merkezi yerlerden import ediliyor.
from core.config import (
    PLANET_GLYPHS, ASPECT_COLORS, ASPECT_GLYPHS, ELEMENT_COLORS,
    SIGN_TO_ELEMENT, ZODIAC_GLYPHS, ZODIAC_SIGNS
)
from services.astrology_engine import get_zodiac_sign_details


def draw_final_professional_chart(natal_data: Dict[str, Any]) -> bytes:
    """
    Verilen natal harita verileriyle detaylı, profesyonel bir doğum haritası görseli oluşturur
    ve bu görseli PNG formatında byte olarak döndürür.
    """
    # --- 1. FIGÜR VE YERLEŞİM AYARLARI ---
    # Genel font ayarları ve çizim alanı (figure) oluşturulması
    plt.rcParams['font.family'] = 'sans-serif'
    # 'Segoe UI Symbol' fontu, astrolojik glifleri (sembolleri) düzgün göstermek için önemlidir.
    plt.rcParams['font.sans-serif'] = ['Segoe UI Symbol', 'Arial']
    fig = plt.figure(figsize=(17, 10), facecolor='white')
    # `gridspec` ile çizim alanını ızgaralara bölerek farklı panelleri (harita, tablolar) yerleştiriyoruz.
    gs = fig.add_gridspec(10, 4)
    # Ana harita çemberi, ızgaranın sol yarısını kaplayacak.
    ax_chart = fig.add_subplot(gs[:, 0:2])
    ax_chart.set_xlim(-1.5, 1.5)
    ax_chart.set_ylim(-1.5, 1.5)
    ax_chart.set_aspect('equal') # Çemberin tam yuvarlak görünmesini sağlar.
    ax_chart.axis('off') # Eksenleri (x,y) gizler.

    # --- 2. ZODYAK ÇEMBERİ VE DERECELER ---
    # 360 derecelik çember üzerine derece çentikleri çizilir.
    for i in range(360):
        rad = np.deg2rad(180 - i) # Matplotlib radyan cinsinden ve saat yönünün tersine çalışır.
        linewidth = 0.5 if i % 5 != 0 else 1.0
        length = 0.03 if i % 5 != 0 else 0.06
        if i % 10 == 0: length = 0.09 # Her 10 derecede bir daha belirgin çentik.
        ax_chart.plot([1.0 * np.cos(rad), (1.0+length) * np.cos(rad)], [1.0 * np.sin(rad), (1.0+length) * np.sin(rad)], color='gray', lw=linewidth, zorder=1)
        if i % 10 == 0: # Her 10 derecede bir derece sayısı yazılır.
            ax_chart.text(1.18 * np.cos(rad), 1.18 * np.sin(rad), str(i % 30), ha='center', va='center', fontsize=7, color='black', rotation = -i + 90)

    # 12 Zodyak burcu için renkli dilimler (wedge) çizilir.
    for i in range(12):
        start_angle, end_angle = 180 - (i * 30 + 30), 180 - (i * 30)
        sign_name = ZODIAC_SIGNS[i]
        element = SIGN_TO_ELEMENT[sign_name]
        color = ELEMENT_COLORS[element] # Burcun elementine göre renk seçilir.
        wedge = Wedge((0,0), 1.0, start_angle, end_angle, facecolor=color, edgecolor='darkgray', lw=0.5, zorder=0)
        ax_chart.add_artist(wedge)
        # Her burcun ortasına kendi glifi (sembolü) yerleştirilir.
        glyph_angle = i * 30 + 15
        glyph_rad = np.deg2rad(180 - glyph_angle)
        ax_chart.text(0.9 * np.cos(glyph_rad), 0.9 * np.sin(glyph_rad), ZODIAC_GLYPHS[i], ha='center', va='center', fontsize=18, zorder=1)

    # --- 3. EV (HOUSE) ÇİZGİLERİ ---
    house_circle = plt.Circle((0, 0), 0.8, color='black', fill=False, lw=0.5, zorder=2)
    ax_chart.add_artist(house_circle)
    for i, cusp_deg in enumerate(natal_data['house_cusps'][:12]):
        rad = np.deg2rad(180 - cusp_deg)
        is_major_cusp = (i == 0 or i == 3 or i == 6 or i == 9) # ASC, IC, DSC, MC
        color = 'black' if is_major_cusp else 'darkgray'
        linewidth = 1.0 if is_major_cusp else 0.4
        ax_chart.plot([0, 0.8 * np.cos(rad)], [0, 0.8 * np.sin(rad)], color=color, linestyle='-', lw=linewidth, zorder=3)
        # Her evin ortasına ev numarası yazılır.
        house_mid_angle_deg = cusp_deg + ( (natal_data['house_cusps'][i+1 if i<11 else 0] - cusp_deg + 360) % 360 ) / 2
        num_rad = np.deg2rad(180 - house_mid_angle_deg)
        ax_chart.text(0.72 * np.cos(num_rad), 0.72 * np.sin(num_rad), str(i+1), ha='center', va='center', fontsize=10, color='gray', zorder=4, bbox=dict(facecolor='white', edgecolor='none', boxstyle='circle,pad=0.2'))

    # --- 4. AÇI (ASPECT) ÇİZGİLERİ VE GEZEGENLER ---
    # Açı çizgilerinin çizileceği iç çember alanı.
    inner_circle = plt.Circle((0, 0), 0.6, color='white', fill=True, zorder=4)
    ax_chart.add_artist(inner_circle)
    aspects = natal_data.get('aspects', [])
    planet_coords = {p['planet']: (np.cos(np.deg2rad(180 - p['longitude'])), np.sin(np.deg2rad(180 - p['longitude']))) for p in natal_data['planets']}
    aspect_circle_radius = 0.6
    for aspect in aspects:
        p1_name, p2_name = aspect['planet1'], aspect['planet2']
        if p1_name not in planet_coords or p2_name not in planet_coords: continue
        color = ASPECT_COLORS.get(aspect['aspect'], 'gray')
        linestyle = '-' if aspect.get('type') in ['Major', 'Creative'] else '--' # Minör açılar kesikli çizgi
        x1, y1 = (coord * aspect_circle_radius for coord in planet_coords[p1_name])
        x2, y2 = (coord * aspect_circle_radius for coord in planet_coords[p2_name])
        ax_chart.plot([x1, x2], [y1, y2], color=color, lw=0.8, alpha=0.9, zorder=5, linestyle=linestyle)

    # Gezegen glifleri (sembolleri) haritaya yerleştirilir.
    for planet in natal_data['planets']:
        p_name, p_deg = planet['planet'], planet['longitude']
        rad = np.deg2rad(180 - p_deg)
        ax_chart.text(0.65 * np.cos(rad), 0.65 * np.sin(rad), PLANET_GLYPHS.get(p_name, '?'), ha='center', va='center', fontsize=14, color='black', weight='bold', zorder=6)

    # --- 5. BİLGİ PANELLERİ (SAĞ TARAF) ---
    # Gezegen Konumları Paneli
    ax_planets = fig.add_subplot(gs[0:5, 2])
    ax_planets.axis('off')
    ax_planets.text(-0.1, 1.0, "Gezegen Konumları", weight="bold", fontsize=12)
    y_pos = 0.9
    for p in natal_data['planets']:
        retro = " R" if p['is_retrograde'] else ""
        planet_text = f"{PLANET_GLYPHS.get(p['planet'], '?')}  {p['planet']}"
        pos_text = f"{p['degree']:02d}° {p['sign_glyph']} {p['minute']:02d}'{retro}"
        house_text = f"{p['house']}. Ev"
        ax_planets.text(-0.1, y_pos, planet_text, ha='left', va='center', fontsize=10)
        ax_planets.text(0.35, y_pos, pos_text, ha='left', va='center', fontsize=10)
        ax_planets.text(0.75, y_pos, house_text, ha='right', va='center', fontsize=10)
        y_pos -= 0.05

    # Ev Başlangıçları Paneli
    ax_houses = fig.add_subplot(gs[5:10, 2])
    ax_houses.axis('off')
    ax_houses.text(-0.1, 1.0, "Ev Başlangıçları", weight="bold", fontsize=12)
    y_pos = 0.9
    for i, cusp_deg in enumerate(natal_data['house_cusps'][:12]):
        details = get_zodiac_sign_details(cusp_deg)
        house_text = f"{i+1}. Ev"
        pos_text = f"{details['degree']:02d}° {details['sign_glyph']} {details['minute']:02d}'"
        ax_houses.text(0.0, y_pos, house_text, ha='left', va='center', fontsize=10)
        ax_houses.text(0.4, y_pos, pos_text, ha='left', va='center', fontsize=10)
        y_pos -= 0.08

    # Element & Nitelik Dengesi Paneli
    ax_summary = fig.add_subplot(gs[0:3, 3])
    ax_summary.axis('off')
    ax_summary.text(0, 1.0, "Element & Nitelik", weight="bold", fontsize=12)
    elements = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}
    modalities = {'Cardinal': 0, 'Fixed': 0, 'Mutable': 0}
    # Denge hesaplamasına dahil edilmeyecek astrolojik noktalar
    excluded_for_balance = ['True Node', 'Part of Fortune', 'Lilith', 'Chiron', 'Ceres', 'Pallas', 'Juno', 'Vesta']
    for p in natal_data['planets']:
        if p['planet'] not in excluded_for_balance:
            if p.get('element'): elements[p['element']] += 1
            if p.get('modality'): modalities[p['modality']] += 1
    summary_data = { 'Ateş (Fire)': elements['Fire'], 'Toprak (Earth)': elements['Earth'], 'Hava (Air)': elements['Air'], 'Su (Water)': elements['Water'], '': '', 'Öncü (Cardinal)': modalities['Cardinal'], 'Sabit (Fixed)': modalities['Fixed'], 'Değişken (Mutable)': modalities['Mutable'] }
    y_pos = 0.85
    for key, value in summary_data.items():
        if key == '': y_pos -= 0.02; continue # Boşluk için
        ax_summary.text(0.1, y_pos, key, ha='left', va='center', fontsize=10)
        ax_summary.text(0.8, y_pos, str(value), ha='right', va='center', fontsize=10, weight='bold')
        y_pos -= 0.08

    # Açı Tablosu (Aspect Grid) Paneli
    ax_grid = fig.add_subplot(gs[3:10, 3])
    ax_grid.axis('off')
    ax_grid.set_title("Açı Tablosu", weight="bold", fontsize=12, ha='center')
    # Tabloda gösterilecek ana gezegenler
    grid_planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
    grid_size = len(grid_planets)
    for i, p_row_name in enumerate(grid_planets):
        ax_grid.text(-0.5, -i, PLANET_GLYPHS.get(p_row_name, '?'), ha='center', va='center', fontsize=11)
        ax_grid.text(i, 0.5, PLANET_GLYPHS.get(p_row_name, '?'), ha='center', va='center', fontsize=11)
    for aspect in aspects:
        p1, p2 = aspect['planet1'], aspect['planet2']
        if p1 in grid_planets and p2 in grid_planets:
            idx1, idx2 = grid_planets.index(p1), grid_planets.index(p2)
            if idx1 == idx2: continue
            if idx1 < idx2: idx1, idx2 = idx2, idx1 # Tablonun sadece alt üçgenini doldurmak için
            aspect_glyph = ASPECT_GLYPHS.get(aspect['aspect'], '')
            color = ASPECT_COLORS.get(aspect['aspect'], 'black')
            ax_grid.text(idx2, -idx1, aspect_glyph, ha='center', va='center', fontsize=10, color=color)
    ax_grid.set_xlim(-1, grid_size)
    ax_grid.set_ylim(-grid_size -1, 1)
    ax_grid.set_aspect('equal')

    # --- 6. GÖRSELİ KAYDETME VE DÖNDÜRME ---
    fig.tight_layout(pad=1.0, h_pad=0.5, w_pad=3.0)
    buf = io.BytesIO() # Görseli diske değil, hafızadaki bir tampona (buffer) kaydet
    plt.savefig(buf, format='png', dpi=200, facecolor='white')
    plt.close(fig) # Hafızada yer kaplamaması için figürü kapat
    buf.seek(0) # Buffer'ın okuma imlecini başa al
    return buf.getvalue() # Buffer'ın içeriğini byte olarak döndür


def draw_synastry_biwheel_chart(p1_data: Dict[str, Any], p2_data: Dict[str, Any], synastry_aspects: List[Dict[str, Any]]) -> bytes:
    """
    İki doğum haritasını iç içe (bi-wheel) çizen ve aralarındaki sinastri açılarını
    gösteren profesyonel bir harita üretir.
    """
    # --- 1. FIGÜR VE YERLEŞİM AYARLARI ---
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Segoe UI Symbol', 'Arial']
    fig = plt.figure(figsize=(17, 10), facecolor='white')
    gs = fig.add_gridspec(10, 4)
    ax_chart = fig.add_subplot(gs[:, 0:2])
    ax_chart.set_xlim(-1.1, 1.1)
    ax_chart.set_ylim(-1.1, 1.1)
    ax_chart.set_aspect('equal')
    ax_chart.axis('off')

    # --- 2. DIŞ ÇEMBER (KİŞİ 2) - ZODYAK VE EVLER ---
    # Zodyak halkası
    for i in range(12):
        start_angle, end_angle = 180 - (i * 30 + 30), 180 - (i * 30)
        sign_name = ZODIAC_SIGNS[i]
        element = SIGN_TO_ELEMENT[sign_name]
        color = ELEMENT_COLORS[element]
        wedge = Wedge((0,0), 1.0, start_angle, end_angle, facecolor=color, edgecolor='darkgray', lw=0.5, zorder=0)
        ax_chart.add_artist(wedge)
    # Burç çizgileri ve glifleri
    for i in range(12):
        angle = i * 30
        rad = np.deg2rad(180 - angle)
        ax_chart.plot([0.8 * np.cos(rad), 1.0 * np.cos(rad)], [0.8 * np.sin(rad), 1.0 * np.sin(rad)], color='#FFFFFF', lw=1.5, zorder=1)
        glyph_angle = i * 30 + 15
        glyph_rad = np.deg2rad(180 - glyph_angle)
        ax_chart.text(0.9 * np.cos(glyph_rad), 0.9 * np.sin(glyph_rad), ZODIAC_GLYPHS[i], ha='center', va='center', fontsize=18, zorder=1)

    # Kişi 2'nin ev çizgileri (dış çemberde)
    for i, cusp_deg in enumerate(p2_data['house_cusps'][:12]):
        rad = np.deg2rad(180 - cusp_deg)
        is_major_cusp = (i in [0, 3, 6, 9])
        color = 'black' if is_major_cusp else 'darkgray'
        linewidth = 1.0 if is_major_cusp else 0.4
        # Ev çizgileri, gezegenlerin olduğu alandan (0.8) başlar
        ax_chart.plot([0.8 * np.cos(rad), 1.0 * np.cos(rad)], [0.8 * np.sin(rad), 1.0 * np.sin(rad)], color=color, linestyle='-', lw=linewidth, zorder=3)
        house_mid_angle_deg = cusp_deg + ( (p2_data['house_cusps'][i+1 if i<11 else 0] - cusp_deg + 360) % 360 ) / 2
        num_rad = np.deg2rad(180 - house_mid_angle_deg)
        ax_chart.text(0.88 * np.cos(num_rad), 0.88 * np.sin(num_rad), str(i+1), ha='center', va='center', fontsize=10, color='gray', zorder=4, bbox=dict(facecolor='white', edgecolor='none', boxstyle='circle,pad=0.2'))
    
    # İç ve dış çemberi ayıran çizgi
    divider_circle = plt.Circle((0, 0), 0.5, color='black', fill=False, lw=0.7, zorder=3)
    ax_chart.add_artist(divider_circle)
    # İç çemberin arka planını beyaz yapar
    inner_fill = plt.Circle((0,0), 0.5, color='white', fill=True, zorder=2)
    ax_chart.add_artist(inner_fill)

    # --- 3. GEZEGENLER (İÇ VE DIŞ) ---
    # Dış Çember Gezegenleri (Kişi 2 - Mavi)
    for planet in p2_data['planets']:
        rad = np.deg2rad(180 - planet['longitude'])
        ax_chart.text(0.65 * np.cos(rad), 0.65 * np.sin(rad), PLANET_GLYPHS.get(planet['planet'], '?'), ha='center', va='center', fontsize=14, color='blue', weight='bold', zorder=4)
    # İç Çember Gezegenleri (Kişi 1 - Kırmızı)
    for planet in p1_data['planets']:
        rad = np.deg2rad(180 - planet['longitude'])
        ax_chart.text(0.35 * np.cos(rad), 0.35 * np.sin(rad), PLANET_GLYPHS.get(planet['planet'], '?'), ha='center', va='center', fontsize=14, color='red', weight='bold', zorder=4)

    # --- 4. SİNASTRİ AÇILARI ---
    # Her bir gezegenin koordinatlarını kendi çemberine göre hesapla
    p1_coords = {p['planet']: (0.30 * np.cos(np.deg2rad(180 - p['longitude'])), 0.30 * np.sin(np.deg2rad(180 - p['longitude']))) for p in p1_data['planets']}
    p2_coords = {p['planet']: (0.70 * np.cos(np.deg2rad(180 - p['longitude'])), 0.70 * np.sin(np.deg2rad(180 - p['longitude']))) for p in p2_data['planets']}
    for aspect in synastry_aspects:
        p1_name, p2_name = aspect['planet1'], aspect['planet2']
        if p1_name not in p1_coords or p2_name not in p2_coords: continue
        color = ASPECT_COLORS.get(aspect['aspect'], 'gray')
        x1, y1 = p1_coords[p1_name]
        x2, y2 = p2_coords[p2_name]
        ax_chart.plot([x1, x2], [y1, y2], color=color, lw=0.7, alpha=0.8, zorder=1)

    # --- 5. BİLGİ PANELLERİ ---
    # Kişi 1 (İç Çember) Bilgi Paneli
    ax_p1 = fig.add_subplot(gs[0:5, 2])
    ax_p1.axis('off')
    ax_p1.text(0, 1.0, "Kişi 1 (İç - Kırmızı)", weight="bold", fontsize=12, color='red')
    y_pos = 0.9
    for p in p1_data['planets']:
        retro = " R" if p['is_retrograde'] else ""
        planet_text = f"{PLANET_GLYPHS.get(p['planet'], '?')}  {p['planet']}"
        pos_text = f"{p['degree']:02d}° {p['sign_glyph']} {p['minute']:02d}'{retro}"
        ax_p1.text(0, y_pos, planet_text, ha='left', va='center', fontsize=10)
        ax_p1.text(0.5, y_pos, pos_text, ha='left', va='center', fontsize=10)
        y_pos -= 0.05
    
    # Kişi 2 (Dış Çember) Bilgi Paneli
    ax_p2 = fig.add_subplot(gs[5:10, 2])
    ax_p2.axis('off')
    ax_p2.text(0, 1.0, "Kişi 2 (Dış - Mavi)", weight="bold", fontsize=12, color='blue')
    y_pos = 0.9
    for p in p2_data['planets']:
        retro = " R" if p['is_retrograde'] else ""
        planet_text = f"{PLANET_GLYPHS.get(p['planet'], '?')}  {p['planet']}"
        pos_text = f"{p['degree']:02d}° {p['sign_glyph']} {p['minute']:02d}'{retro}"
        house_text = f"{p['house']}. Ev"
        ax_p2.text(0, y_pos, planet_text, ha='left', va='center', fontsize=10)
        ax_p2.text(0.5, y_pos, pos_text, ha='left', va='center', fontsize=10)
        ax_p2.text(0.95, y_pos, house_text, ha='right', va='center', fontsize=10)
        y_pos -= 0.05

    # Sinastri Açı Tablosu (Aspect Grid)
    ax_grid = fig.add_subplot(gs[:, 3])
    ax_grid.axis('off')
    ax_grid.set_title("Sinastri Açıları", weight="bold", fontsize=12, ha='center')
    grid_planets_p1 = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'Asc', 'MC']
    grid_planets_p2 = grid_planets_p1[:]
    for i, p1_name in enumerate(grid_planets_p1):
        ax_grid.text(-0.5, -i, PLANET_GLYPHS.get(p1_name, p1_name[:3]), ha='center', va='center', fontsize=11, color='red')
    for j, p2_name in enumerate(grid_planets_p2):
        ax_grid.text(j, 0.5, PLANET_GLYPHS.get(p2_name, p2_name[:3]), ha='center', va='center', fontsize=11, color='blue')
    for aspect in synastry_aspects:
        p1, p2 = aspect['planet1'], aspect['planet2']
        if p1 in grid_planets_p1 and p2 in grid_planets_p2:
            idx1, idx2 = grid_planets_p1.index(p1), grid_planets_p2.index(p2)
            aspect_glyph = ASPECT_GLYPHS.get(aspect['aspect'], '')
            color = ASPECT_COLORS.get(aspect['aspect'], 'black')
            ax_grid.text(idx2, -idx1, aspect_glyph, ha='center', va='center', fontsize=10, color=color)
    ax_grid.set_xlim(-1, len(grid_planets_p2))
    ax_grid.set_ylim(-len(grid_planets_p1) -1, 1)
    ax_grid.set_aspect('equal')

    # --- 6. GÖRSELİ KAYDETME VE DÖNDÜRME ---
    fig.tight_layout(pad=1.0, h_pad=0.5, w_pad=2.0)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200, facecolor='white')
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()