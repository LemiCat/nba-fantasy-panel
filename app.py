import requests
import pandas as pd
import streamlit as st

# 1. Sayfa ve Tema Ayarları
st.set_page_config(page_title="NBA Fantasy Radar", layout="wide", page_icon="🏀", initial_sidebar_state="collapsed")

# 2. Özel CSS: Arayüzü Uygulamaya (App) Dönüştür ve Sıkıştır
st.markdown("""
    <style>
    /* Streamlit varsayılan üst menü ve alt bilgiyi gizle */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none;}
    
    /* Üstten ve alttan tüm gereksiz boşlukları tamamen sil */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 0rem !important;
    }
    
    /* Ana başlık boşluğunu sıkıştır */
    div[data-testid="stVerticalBlock"] > div > h1 {
        padding-bottom: 0px !important;
        margin-bottom: -15px !important;
    }
    
    /* Metrik kutularının hizasını düzelt */
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #38bdf8 !important;
        font-weight: 800 !important;
    }
    
    /* Expander (Açılır Menü) boşluklarını azalt */
    div[data-testid="stExpander"] {
        margin-top: -10px !important;
    }
    
    /* Selectbox ve Multiselect iç boşluklarını küçült */
    div[data-baseweb="select"] {
        margin-bottom: -10px !important;
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

st.title("🏀 NBA Fantasy Radar & Verim Terminali")
st.caption("Canlı Sistem Aktif: Veriler otomatik güncellenir. Sıralamak için sütun başlıklarına tıklayın.")

try:
    df = fetch_live_fantasy_data()
except Exception as e:
    st.error(f"Veri çekme hatası: {e}")
    st.stop()

# ==========================================
# ANA EKRAN DÜZENİ: Sol %65, Sağ %35
# ==========================================
main_col_left, main_col_right = st.columns([1.8, 1])

# SOL TARAF: Metrik Kartları
with main_col_left:
    st.write("") # Dikey hizalamayı sağ tarafla eşitlemek için ufak bir boşluk
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_placeholder1 = metric_col1.empty()
    metric_placeholder2 = metric_col2.empty()
    metric_placeholder3 = metric_col3.empty()

# SAĞ TARAF: Filtre Paneli (Boşluksuz ve Kutudan Bağımsız Düzen)
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