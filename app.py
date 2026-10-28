import requests
import pandas as pd
import streamlit as st

# 1. Sayfa ve Tema Ayarları
st.set_page_config(page_title="NBA Fantasy Radar", layout="wide", page_icon="🏀", initial_sidebar_state="collapsed")

# 2. Özel CSS: Arayüzü Uygulamaya (App) Dönüştür ve Animasyonlar Ekle
st.markdown("""
    <style>
    /* Streamlit varsayılan üst menü ve alt bilgiyi gizle */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none;}
    
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 0rem !important;
    }
    
    div[data-testid="stVerticalBlock"] > div > h1 {
        padding-bottom: 0px !important;
        margin-bottom: -15px !important;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #38bdf8 !important;
        font-weight: 800 !important;
    }
    
    div[data-testid="stExpander"] {
        margin-top: -10px !important;
    }
    
    div[data-baseweb="select"] {
        margin-bottom: -10px !important;
    }

    /* --- YENİ: BAŞLIK VE CANLI YAYIN (LIVE) ROZETİ --- */
    .custom-header-container {
        display: flex;
        align-items: center;
        margin-bottom: 25px; /* Alt metni sildiğimiz için biraz boşluk bırakıyoruz */
    }
    
    .custom-header-container h1 {
        margin: 0;
        padding: 0;
        font-size: 2.25rem;
        font-weight: 700;
        line-height: 1.2;
    }

    .live-badge {
        display: inline-flex;
        align-items: center;
        background-color: rgba(239, 68, 68, 0.15); /* Yarı saydam kırmızı arka plan */
        border: 1px solid rgba(239, 68, 68, 0.4);
        color: #ef4444; /* Parlak kırmızı */
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0.5px;
        margin-left: 18px; /* Başlıktan biraz uzaklaştır */
    }

    .blinking-dot {
        width: 8px;
        height: 8px;
        background-color: #ef4444;
        border-radius: 50%;
        margin-right: 8px;
        /* Nabız (Pulse) Animasyonu */
        animation: pulse-animation 1.5s infinite;
    }

    @keyframes pulse-animation {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); opacity: 1; }
        70% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); opacity: 0.4; }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); opacity: 1; }
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

# 3. YENİ BAŞLIK VE CANLI ROZETİ (Özel HTML/CSS ile)
st.markdown("""
    <div class="custom-header-container">
        <h1>🏀 NBA Fantasy Radar & Verim Terminali</h1>
        <div class="live-badge">
            <div class="blinking-dot"></div> LIVE
        </div>
    </div>
""", unsafe_allow_html=True)

try:
    df = fetch_live_fantasy_data()
except Exception as e:
    st.error(f"Veri çekme hatası: {e}")
    st.stop()

# ==========================================
# ANA EKRAN DÜZENİ: Sol %65, Sağ %35
# ==========================================
main_col_left, main_col_right = st.columns([1.8, 1])

with main_col_left:
    st.write("") 
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_placeholder1 = metric_col1.empty()
    metric_placeholder2 = metric_col2.empty()
    metric_placeholder3 = metric_col3.empty()

with main_col_right:
    st.markdown("<h5 style='margin-bottom:10px; margin-top:5px; color:#f8fafc;'>🎯 Radar Filtreleri</h5>", unsafe_allow_html=True)
    
    filt_col1, filt_col2 = st.columns([1.5, 1])
    with filt_col1:
        selected_players = st.multiselect(
            "🔍 Oyuncu",
            options=sorted(df["Oyuncu"].unique()),
            help="İsim yazıp arayın.",
            label_visibility="collapsed"
        )
    with filt_col2:
        pos_filter = st.selectbox("🏀 Mevki", ["Tümü", "BC", "FC"], label_visibility="collapsed")
    
    with st.expander("⚙️ Sayısal Filtreler", expanded=False):
        min_p = float(df["Fiyat (M$)"].min()) if not df.empty else 5.0
        max_p = float(df["Fiyat (M$)"].max()) if not df.empty else 23.0
        tavan_maas = st.slider("Max Fiyat (M$)", min_value=min_p, max_value=max_p, value=max_p, step=0.5)
        
        sld_col1, sld_col2 = st.columns(2)
        with sld_col1:
            min_mac = st.slider("Min Maç (GP)", 0, 82, 0)
        with sld_col2:
            min_mpg = st.slider("Min Dk/Maç", 0, 48, 0)

# ==========================================
# FİLTRELEME MANTIĞI
# ==========================================
if selected_players:
    filtered = df[df["Oyuncu"].isin(selected_players)]
else:
    filtered = df[
        (df["Fiyat (M$)"] <= tavan_maas) & 
        (df["Maç"] >= min_mac) &
        (df["Dk/Maç"] >= min_mpg)
    ]
    if pos_filter == "BC":
        filtered = filtered[filtered["Mevki"] == "BC"]
    elif pos_filter == "FC":
        filtered = filtered[filtered["Mevki"] == "FC"]

sorted_table = filtered.sort_values(by="Value", ascending=False)

# ==========================================
# METRİKLERİ DOLDURMA
# ==========================================
metric_placeholder1.metric("Filtrelenen Oyuncu", len(sorted_table))

if not sorted_table.empty:
    best_value_player = sorted_table.iloc[0]["Oyuncu"]
    best_value_score = sorted_table.iloc[0]["Value"]
    metric_placeholder2.metric("🏆 En Yüksek Value", f"{best_value_player}", f"{best_value_score:.2f} FP/$")
    
    best_form_row = sorted_table.loc[sorted_table['Form'].idxmax()]
    metric_placeholder3.metric("🔥 En Formda", f"{best_form_row['Oyuncu']}", f"{best_form_row['Form']:.1f} Form")
else:
    metric_placeholder2.metric("🏆 En Yüksek Value", "-", "-")
    metric_placeholder3.metric("🔥 En Formda", "-", "-")

# ==========================================
# ANA TABLO
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)
st.dataframe(
    sorted_table,
    use_container_width=True,
    hide_index=True,
    height=600,
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