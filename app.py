import requests
import pandas as pd
import streamlit as st

# 1. Sayfa ve Tema Ayarları
st.set_page_config(page_title="NBA Fantasy Radar", layout="wide", page_icon="🏀", initial_sidebar_state="expanded")

# 2. Özel CSS
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        color: #38bdf8 !important;
        font-weight: 800 !important;
    }
    
    /* Özel HTML Tablo Stilleri */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        font-family: system-ui, -apple-system, sans-serif;
        color: #f8fafc;
        margin-top: 15px;
    }
    .custom-table th {
        background-color: #0f172a;
        color: #94a3b8;
        padding: 10px 8px;
        text-align: left;
        border-bottom: 2px solid #1e293b;
        font-weight: 600;
        white-space: nowrap;
    }
    .custom-table td {
        padding: 8px 8px;
        border-bottom: 1px solid #1e293b;
        vertical-align: middle;
    }
    .custom-table tr:hover {
        background-color: rgba(255, 255, 255, 0.05);
    }
    
    /* İnce Bar Grafikleri */
    .bar-container {
        width: 80px; 
        height: 6px; 
        background-color: #1e293b;
        border-radius: 3px;
        display: inline-block;
        margin-right: 8px;
        vertical-align: middle;
        overflow: hidden;
    }
    .bar-fill {
        height: 100%;
        border-radius: 3px;
    }
    .fill-form { background: linear-gradient(90deg, #ea580c, #f97316); }
    .fill-value { background: linear-gradient(90deg, #0284c7, #38bdf8); }
    .fill-fpmin { background: linear-gradient(90deg, #059669, #10b981); }
    .val-text { display: inline-block; width: 35px; text-align: right; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=True, ttl=900)
def fetch_live_fantasy_data():
    url = "https://tr.nbafantasy.nba.com/api/bootstrap-static/"
    res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15).json()
    teams = {t["id"]: t.get("short_name", t["name"]) for t in res["teams"]}
    
    player_list = []
    for el in res["elements"]:
        if el.get("status") in ["u"]:
            continue
            
        full_name = f"{el['first_name']} {el['second_name']}"
        cost = float(el.get("now_cost", el.get("cost", 0))) / 10.0
        
        form_raw = float(el.get("form", 0.0) or 0.0)
        form_val = round(form_raw / 10.0, 1) if form_raw > 50 else round(form_raw, 1)
        
        tp_raw = float(el.get("total_points", 0.0) or 0.0)
        total_points = round(tp_raw / 10.0, 1) if tp_raw > 0 else 0.0
        
        ppg_raw = float(el.get("points_per_game", 0.0) or 0.0)
        ppg_val = round(ppg_raw / 10.0, 1) if ppg_raw > 50 else round(ppg_raw, 1)
        
        gp = int(round(total_points / ppg_val)) if ppg_val > 0 else 0
        minutes = float(el.get("minutes", 0.0) or 0.0)
        
        value_ratio = round(total_points / cost, 2) if cost > 0 else 0.0
        fp_per_min = round(total_points / minutes, 2) if minutes > 0 else 0.0
        
        player_list.append({
            "Oyuncu": full_name,
            "Mevki": "BC" if el["element_type"] == 1 else "FC",
            "Takım": teams.get(el["team"], "NBA"),
            "Fiyat": cost,
            "Toplam FP": total_points,
            "FP Ort": ppg_val,
            "Form": form_val,
            "Value": value_ratio,
            "FP/Min": fp_per_min,
            "Maç": gp,
            "Dk": minutes
        })
        
    df = pd.DataFrame(player_list)
    return df

st.title("🏀 NBA Fantasy Radar & Verim Terminali")
st.caption("Canlı Sistem Aktif: Veriler arka planda otomatik güncellenir.")

try:
    df = fetch_live_fantasy_data()
except Exception as e:
    st.error(f"Veri çekme hatası: {e}")
    st.stop()

# ==========================================
# SOL MENÜ (Filtreler ve Sıralama)
# ==========================================
st.sidebar.header("🎯 Radar Filtreleri")

selected_players = st.sidebar.multiselect("🔍 Oyuncu Ara & Karşılaştır", options=sorted(df["Oyuncu"].unique()))
pos_filter = st.sidebar.radio("Mevki", ["Tümü", "BC", "FC"], horizontal=True)

min_p = float(df["Fiyat"].min()) if not df.empty else 5.0
max_p = float(df["Fiyat"].max()) if not df.empty else 23.0
tavan_maas = st.sidebar.slider("💰 Max Fiyat (M$)", min_value=min_p, max_value=max_p, value=max_p, step=0.5)

min_mac = st.sidebar.slider("🗓️ Min Maç", 0, 82, 0)
min_dk = st.sidebar.slider("⏱️ Min Süre (Dk)", 0, 150, 0)

# --- YENİ: SIRALAMA MOTORU ---
st.sidebar.markdown("---")
st.sidebar.header("🔀 Sıralama Ayarları")
sort_col = st.sidebar.selectbox(
    "Sıralama Ölçütü", 
    ["Value", "Toplam FP", "FP Ort", "Fiyat", "Form", "FP/Min", "Dk"]
)
sort_order = st.sidebar.radio("Yön", ["Yüksekten Düşüğe (Azalan)", "Düşükten Yükseğe (Artan)"])
is_ascending = True if sort_order == "Düşükten Yükseğe (Artan)" else False

# ==========================================
# FİLTRELEME VE SIRALAMA UYGULAMASI
# ==========================================
if selected_players:
    filtered = df[df["Oyuncu"].isin(selected_players)]
else:
    filtered = df[(df["Fiyat"] <= tavan_maas) & (df["Maç"] >= min_mac) & (df["Dk"] >= min_dk)]
    if pos_filter == "BC": filtered = filtered[filtered["Mevki"] == "BC"]
    elif pos_filter == "FC": filtered = filtered[filtered["Mevki"] == "FC"]

# Tabloyu seçilen kritere göre dinamik sırala
sorted_table = filtered.sort_values(by=sort_col, ascending=is_ascending)

# Dinamik Üst Metrikler
col1, col2, col3 = st.columns(3)
col1.metric("Filtrelenen Oyuncu", len(sorted_table))

if not sorted_table.empty:
    # Value metriği için her zaman en yüksek değere sahip oyuncuyu bul
    best_value_row = filtered.loc[filtered["Value"].idxmax()]
    col2.metric("🏆 En Yüksek Value", f"{best_value_row['Oyuncu']}", f"{best_value_row['Value']:.2f} FP/$")
    avg_price = sorted_table["Fiyat"].mean()
    col3.metric("Ortalama Maliyet (Liste)", f"{avg_price:.1f} M$")
else:
    col2.metric("🏆 En Yüksek Value", "-", "-")
    col3.metric("Ortalama Maliyet", "-")

# ==========================================
# HTML TABLO RENDER 
# ==========================================
html_table = "<table class='custom-table'><thead><tr>"
html_table += "<th>Oyuncu</th><th>Mevki</th><th>Takım</th><th>Fiyat</th><th>Top FP</th><th>FP Ort</th>"
html_table += "<th>🔥 Form</th><th>💎 Value</th><th>⚡ FP/Min</th><th>Maç</th><th>Dk</th>"
html_table += "</tr></thead><tbody>"

for _, row in sorted_table.iterrows():
    pct_form = min((row['Form'] / 80) * 100, 100)
    pct_value = min((row['Value'] / 30) * 100, 100)
    pct_fpmin = min((row['FP/Min'] / 2.0) * 100, 100)
    
    html_table += f"<tr>"
    html_table += f"<td><strong>{row['Oyuncu']}</strong></td>"
    html_table += f"<td>{row['Mevki']}</td>"
    html_table += f"<td>{row['Takım']}</td>"
    html_table += f"<td>{row['Fiyat']:.1f} M$</td>"
    html_table += f"<td>{row['Toplam FP']:.1f}</td>"
    html_table += f"<td>{row['FP Ort']:.1f}</td>"
    
    html_table += f"<td><div class='bar-container'><div class='bar-fill fill-form' style='width:{pct_form}%'></div></div><span class='val-text'>{row['Form']:.1f}</span></td>"
    html_table += f"<td><div class='bar-container'><div class='bar-fill fill-value' style='width:{pct_value}%'></div></div><span class='val-text'>{row['Value']:.2f}</span></td>"
    html_table += f"<td><div class='bar-container'><div class='bar-fill fill-fpmin' style='width:{pct_fpmin}%'></div></div><span class='val-text'>{row['FP/Min']:.2f}</span></td>"
    
    html_table += f"<td>{int(row['Maç'])}</td>"
    html_table += f"<td>{row['Dk']:.1f}</td>"
    html_table += "</tr>"

html_table += "</tbody></table>"

st.markdown(html_table, unsafe_allow_html=True)