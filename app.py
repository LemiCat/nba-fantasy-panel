import requests
import pandas as pd
import streamlit as st

# 1. Sayfa ve Tema Ayarları
st.set_page_config(page_title="NBA Fantasy Radar", layout="wide", page_icon="🏀", initial_sidebar_state="expanded")

# 2. Özel CSS: Yan Menüyü ve Arayüzü Uygulamaya Dönüştür
st.markdown("""
    <style>
    /* Streamlit varsayılan üst menü (Hamburger) ve alt bilgiyi gizle */
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
    
    /* --- YAN MENÜ (SIDEBAR) MODERNLEŞTİRMESİ --- */
    /* Yan menü arka planını ana sayfa ile aynı renk yap */
    [data-testid="stSidebar"] {
        background-color: #0b0f19 !important;
        border-right: 1px solid #1e293b !important;
    }
    
    /* Yan menüdeki başlık ve metinleri daha şık hale getir */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #f8fafc !important;
        font-weight: 600 !important;
    }
    
    /* Kaydırıcı (Slider) çubuklarındaki uyumsuz kırmızıyı siber mavi yap */
    div.stSlider > div > div > div > div {
        background-color: #38bdf8 !important;
    }
    div.stSlider > div > div > div > div > div {
        background-color: #0284c7 !important;
        border-color: #0284c7 !important;
        box-shadow: 0 0 5px rgba(56, 189, 248, 0.5) !important;
    }
    
    /* Açılır-Kapanır Menü (Expander) arka planını belirginleştir */
    [data-testid="stExpander"] {
        background-color: #0f172a !important;
        border: 1px solid #1e293b !important;
        border-radius: 8px !important;
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
        
        total_minutes = float(el.get("minutes", 0.0) or 0.0)
        mpg = round(total_minutes / gp, 1) if gp > 0 else 0.0
        
        value_ratio = round(total_points / cost, 2) if cost > 0 else 0.0
        fp_per_min = round(total_points / total_minutes, 2) if total_minutes > 0 else 0.0
        
        player_list.append({
            "Oyuncu": full_name,
            "Mevki": "BC" if el["element_type"] == 1 else "FC",
            "Takım": teams.get(el["team"], "NBA"),
            "Fiyat (M$)": cost,
            "Toplam FP": total_points,
            "FP Ort. (PPG)": ppg_val,
            "Form": form_val,
            "Value": value_ratio,
            "FP/Min": fp_per_min,
            "Maç": gp,
            "Dk/Maç": mpg
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

# Radyo butonu yerine Dropdown (Açılır Menü) kullanıldı
pos_filter = st.sidebar.selectbox("🏀 Mevki", ["Tümü", "BC (Backcourt)", "FC (Frontcourt)"])

st.sidebar.markdown("---")

# Kaydırıcılar kalabalık yapmasın diye Expander (Açılır/Kapanır Kutu) içine alındı
with st.sidebar.expander("⚙️ Detaylı İstatistik Filtreleri", expanded=True):
    min_p = float(df["Fiyat (M$)"].min()) if not df.empty else 5.0
    max_p = float(df["Fiyat (M$)"].max()) if not df.empty else 23.0
    tavan_maas = st.slider("💰 Maksimum Fiyat (M$)", min_value=min_p, max_value=max_p, value=max_p, step=0.5)

    min_mac = st.slider("🗓️ Minimum Maç (GP)", 0, 82, 0)
    min_mpg = st.slider("⏱️ Min Süre (Dk/Maç)", 0, 48, 0)

# 5. FİLTRELEME MANTIĞI
if selected_players:
    filtered = df[df["Oyuncu"].isin(selected_players)]
else:
    filtered = df[
        (df["Fiyat (M$)"] <= tavan_maas) & 
        (df["Maç"] >= min_mac) &
        (df["Dk/Maç"] >= min_mpg)
    ]
    if pos_filter == "BC (Backcourt)":
        filtered = filtered[filtered["Mevki"] == "BC"]
    elif pos_filter == "FC (Frontcourt)":
        filtered = filtered[filtered["Mevki"] == "FC"]

sorted_table = filtered.sort_values(by="Value", ascending=False)

# 6. DİNAMİK ÜST METRİKLER
col1, col2, col3 = st.columns(3)
col1.metric("Filtrelenen Oyuncu", len(sorted_table))

if not sorted_table.empty:
    best_value_player = sorted_table.iloc[0]["Oyuncu"]
    best_value_score = sorted_table.iloc[0]["Value"]
    col2.metric("🏆 En Yüksek Value", f"{best_value_player}", f"{best_value_score:.2f} FP/$")
    
    best_form_row = sorted_table.loc[sorted_table['Form'].idxmax()]
    col3.metric("🔥 En Formda (Hot Streak)", f"{best_form_row['Oyuncu']}", f"{best_form_row['Form']:.1f} Form")
else:
    col2.metric("🏆 En Yüksek Value", "-", "-")
    col3.metric("🔥 En Formda (Hot Streak)", "-", "-")

# 7. ANA TABLO
st.dataframe(
    sorted_table,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Fiyat (M$)": st.column_config.NumberColumn(format="%.1f M$"),
        "Toplam FP": st.column_config.NumberColumn(format="%.1f"),
        "FP Ort. (PPG)": st.column_config.NumberColumn(format="%.1f"),
        "Form": st.column_config.NumberColumn("🔥 Form", format="%.1f"),
        "Value": st.column_config.NumberColumn("💎 Value (FP/$)", format="%.2f"),
        "FP/Min": st.column_config.NumberColumn("⚡ FP/Min", format="%.2f"),
        "Maç": st.column_config.NumberColumn(format="%d"),
        "Dk/Maç": st.column_config.NumberColumn(format="%.1f")
    }
)