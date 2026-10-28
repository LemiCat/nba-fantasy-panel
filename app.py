import requests
import pandas as pd
import streamlit as st

# 1. Sayfa ve Tema Ayarları
st.set_page_config(page_title="NBA Fantasy Radar", layout="wide", page_icon="🏀", initial_sidebar_state="expanded")

# 2. Özel CSS: Arayüzü Uygulamaya (App) Dönüştür
st.markdown("""
    <style>
    /* Streamlit varsayılan üst menü (Hamburger) ve alt bilgiyi gizle */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Üst boşluğu azalt */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
    }
    
    /* Metrik kutularını daha şık ve belirgin yap */
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        color: #38bdf8 !important;
        font-weight: 800 !important;
    }
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
        
        # Sadece bütçe ve verim odaklı veriler tutuldu
        player_list.append({
            "Oyuncu": full_name,
            "Mevki": "BC" if el["element_type"] == 1 else "FC",
            "Takım": teams.get(el["team"], "NBA"),
            "Fiyat (M$)": cost,
            "Toplam FP": total_points,
            "FP Ort. (PPG)": ppg_val,
            "Form": form_val,
            "Value (FP/$)": value_ratio,
            "FP/Min": fp_per_min,
            "Maç": gp,
            "Dakika": minutes
        })
        
    df = pd.DataFrame(player_list)
    return df

# 3. Başlık ve Veri Çekme
st.title("🏀 NBA Fantasy Radar & Verim Terminali")
st.caption("Canlı Sistem Aktif: Veriler arka planda otomatik güncellenir. Sıralamak için sütun başlıklarına tıklayabilirsiniz.")

try:
    df = fetch_live_fantasy_data()
except Exception as e:
    st.error(f"Veri çekme hatası: {e}")
    st.stop()

# 4. SOL MENÜ (Sidebar)
st.sidebar.header("🎯 Radar Filtreleri")

selected_players = st.sidebar.multiselect(
    "🔍 Oyuncu Ara & Karşılaştır",
    options=sorted(df["Oyuncu"].unique()),
    help="İsim yazarak arayın. Birden fazla seçerek kıyaslayın."
)

pos_filter = st.sidebar.radio("Mevki", ["Tümü", "BC (Backcourt)", "FC (Frontcourt)"], horizontal=True)

min_p = float(df["Fiyat (M$)"].min()) if not df.empty else 5.0
max_p = float(df["Fiyat (M$)"].max()) if not df.empty else 23.0
tavan_maas = st.sidebar.slider("💰 Maksimum Fiyat (M$)", min_value=min_p, max_value=max_p, value=max_p, step=0.5)

min_mac = st.sidebar.slider("🗓️ Minimum Maç (GP)", 0, 82, 0)
min_dk = st.sidebar.slider("⏱️ Minimum Süre (Dk)", 0, 150, 0)

# 5. FİLTRELEME MANTIĞI
if selected_players:
    filtered = df[df["Oyuncu"].isin(selected_players)]
else:
    filtered = df[
        (df["Fiyat (M$)"] <= tavan_maas) & 
        (df["Maç"] >= min_mac) &
        (df["Dakika"] >= min_dk)
    ]
    if pos_filter == "BC (Backcourt)":
        filtered = filtered[filtered["Mevki"] == "BC"]
    elif pos_filter == "FC (Frontcourt)":
        filtered = filtered[filtered["Mevki"] == "FC"]

# Varsayılan olarak Value'ye göre azalan sırala
sorted_table = filtered.sort_values(by="Value (FP/$)", ascending=False)

# 6. DİNAMİK ÜST METRİKLER
col1, col2, col3 = st.columns(3)
col1.metric("Filtrelenen Oyuncu", len(sorted_table))

if not sorted_table.empty:
    best_value_player = sorted_table.iloc[0]["Oyuncu"]
    best_value_score = sorted_table.iloc[0]["Value (FP/$)"]
    col2.metric("🏆 En Yüksek Value", f"{best_value_player}", f"{best_value_score:.2f} FP/$")
    
    avg_price = sorted_table["Fiyat (M$)"].mean()
    col3.metric("Ortalama Maliyet (Liste)", f"{avg_price:.1f} M$")
else:
    col2.metric("🏆 En Yüksek Value", "-", "-")
    col3.metric("Ortalama Maliyet", "-")

# 7. ANA TABLO - STANDART STREAMLIT DATAFRAME
st.dataframe(
    sorted_table,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Fiyat (M$)": st.column_config.NumberColumn(format="%.1f M$"),
        "Toplam FP": st.column_config.NumberColumn(format="%.1f"),
        "FP Ort. (PPG)": st.column_config.NumberColumn(format="%.1f"),
        "Form": st.column_config.NumberColumn("🔥 Form", format="%.1f"),
        "Value (FP/$)": st.column_config.NumberColumn("💎 Value", format="%.2f"),
        "FP/Min": st.column_config.NumberColumn("⚡ FP/Min", format="%.2f"),
        "Maç": st.column_config.NumberColumn(format="%d"),
        "Dakika": st.column_config.NumberColumn(format="%.1f")
    }
)