import requests
import pandas as pd
import streamlit as st

# 1. Sayfa ve Tema Ayarları
st.set_page_config(page_title="NBA Fantasy Scout", layout="wide", page_icon="🏀", initial_sidebar_state="collapsed")

# 2. Özel CSS
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none;}
    
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 0rem !important;
    }
    
    .custom-header-container {
        display: flex;
        align-items: center;
        margin-bottom: 25px;
    }
    .nba-official-logo {
        height: 38px; 
        margin-right: 15px;
        border-radius: 2px;
    }
    .custom-header-container h1 {
        margin: 0;
        padding: 0;
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1.2;
        letter-spacing: -0.5px;
    }
    .header-thin {
        font-weight: 300;
        color: #94a3b8;
        letter-spacing: 1px;
    }
    .live-badge {
        display: inline-flex;
        align-items: center;
        background-color: rgba(239, 68, 68, 0.15); 
        border: 1px solid rgba(239, 68, 68, 0.4);
        color: #ef4444; 
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0.5px;
        margin-left: 20px; 
    }
    .blinking-dot {
        width: 8px;
        height: 8px;
        background-color: #ef4444;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse-animation 1.5s infinite;
    }
    @keyframes pulse-animation {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); opacity: 1; }
        70% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); opacity: 0.4; }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); opacity: 1; }
    }

    /* Espor Kartları */
    .esport-card {
        border-left: 3px solid #38bdf8;
        padding-left: 14px;
        margin-top: 5px;
        margin-bottom: 15px;
    }
    .esport-label {
        color: #94a3b8;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2.5px;
        margin-bottom: 4px;
    }
    .esport-value {
        color: #ffffff;
        font-size: 28px;
        font-weight: 900;
        letter-spacing: -0.5px;
        margin-bottom: 8px;
        line-height: 1.1;
    }
    .esport-pill {
        display: inline-flex;
        align-items: center;
        background-color: rgba(34, 197, 94, 0.15); 
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }

    /* Ghost Filtre Paneli */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div {
        background-color: rgba(255, 255, 255, 0.02) !important;
        border-top: none !important;
        border-left: none !important;
        border-right: none !important;
        border-bottom: 2px solid #1e293b !important;
        border-radius: 0px !important;
        transition: border-color 0.2s ease;
    }
    div[data-baseweb="select"] > div:focus-within, 
    div[data-baseweb="input"] > div:focus-within {
        border-bottom: 2px solid #38bdf8 !important;
        box-shadow: none !important;
    }
    div[data-baseweb="select"] div, div[data-baseweb="input"] input {
        color: #f8fafc !important;
        font-size: 13.5px !important;
    }
    .mini-label {
        color: #64748b;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.5px;
        margin-bottom: 2px;
        margin-top: 8px;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=True, ttl=900)
def fetch_live_fantasy_data():
    url = "https://tr.nbafantasy.nba.com/api/bootstrap-static/"
    res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15).json()
    teams = {t["id"]: t.get("short_name", t["name"]) for t in res["teams"]}
    
    # 1. ADIM: Takımların maksimum oynadığı maç sayısını bulmak için tarama
    raw_players = []
    team_max_games = {team_name: 0 for team_name in teams.values()}
    
    for el in res["elements"]:
        if el.get("status") in ["u"]:
            continue
            
        full_name = f"{el['first_name']} {el['second_name']}"
        team_name = teams.get(el["team"], "NBA")
        cost = float(el.get("now_cost", el.get("cost", 0))) / 10.0
        form_raw = float(el.get("form", 0.0) or 0.0)
        form_val = round(form_raw / 10.0, 1) if form_raw > 50 else round(form_raw, 1)
        tp_raw = float(el.get("total_points", 0.0) or 0.0)
        total_points = round(tp_raw / 10.0, 1) if tp_raw > 0 else 0.0
        ppg_raw = float(el.get("points_per_game", 0.0) or 0.0)
        ppg_val = round(ppg_raw / 10.0, 1) if ppg_raw > 50 else round(ppg_raw, 1)
        
        # Sadece sahaya çıktığı maçlar (Dakikası olanlar)
        gp = int(round(total_points / ppg_val)) if ppg_val > 0 else 0
        total_minutes = float(el.get("minutes", 0.0) or 0.0)
        
        # Takımın maç sayısını güncelle
        if gp > team_max_games[team_name]:
            team_max_games[team_name] = gp
            
        raw_players.append({
            "Oyuncu": full_name,
            "Mevki": "BC" if el["element_type"] == 1 else "FC",
            "Takım": team_name,
            "Fiyat (M$)": cost,
            "Toplam FP": total_points,
            "FP Ort. (PPG)": ppg_val,
            "Form": form_val,
            "Maç": gp,
            "Toplam Dk": total_minutes
        })
        
    # 2. ADIM: Saf verim ve devamlılık (availability) hesaplamaları
    player_list = []
    for p in raw_players:
        cost = p["Fiyat (M$)"]
        total_points = p["Toplam FP"]
        total_minutes = p["Toplam Dk"]
        gp = p["Maç"]
        team_games = team_max_games[p["Takım"]]
        
        # Devamlılık (%)
        availability = round((gp / team_games) * 100) if team_games > 0 else 0
        
        mpg = round(total_minutes / gp, 1) if gp > 0 else 0.0
        value_ratio = round(total_points / cost, 2) if cost > 0 else 0.0
        fp_per_min = round(total_points / total_minutes, 2) if total_minutes > 0 else 0.0
        
        player_list.append({
            "Oyuncu": p["Oyuncu"],
            "Mevki": p["Mevki"],
            "Takım": p["Takım"],
            "Fiyat (M$)": cost,
            "Toplam FP": total_points,
            "FP Ort. (PPG)": p["FP Ort. (PPG)"],
            "Form": p["Form"],
            "Value": value_ratio,
            "FP/Min": fp_per_min,
            "Maç": gp,
            "Dk/Maç": mpg,
            "Devamlılık": availability
        })
        
    df = pd.DataFrame(player_list)
    return df

st.markdown("""
    <div class="custom-header-container">
        <img src="https://upload.wikimedia.org/wikipedia/en/0/03/National_Basketball_Association_logo.svg" class="nba-official-logo" alt="NBA Logo">
        <h1>NBA FANTASY <span class="header-thin">SCOUT</span></h1>
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
# ANA EKRAN DÜZENİ
# ==========================================
main_col_left, main_col_right = st.columns([1.5, 1]) 

with main_col_left:
    st.write("") 
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_placeholder1 = metric_col1.empty()
    metric_placeholder2 = metric_col2.empty()
    metric_placeholder3 = metric_col3.empty()

with main_col_right:
    st.markdown('<div class="esport-label" style="margin-bottom:12px; color:#38bdf8;">R A D A R   F I L T E R S</div>', unsafe_allow_html=True)
    
    filt_col1, filt_col2 = st.columns([1.5, 1])
    with filt_col1:
        selected_players = st.multiselect(
            "Oyuncu",
            options=sorted(df["Oyuncu"].unique()),
            placeholder="Oyuncu ara...",
            label_visibility="collapsed"
        )
    with filt_col2:
        pos_filter = st.selectbox("Mevki", ["Tümü", "BC", "FC"], label_visibility="collapsed")
    
    num_col1, num_col2, num_col3 = st.columns(3)
    min_p_val = float(df["Fiyat (M$)"].min()) if not df.empty else 5.0
    max_p_val = float(df["Fiyat (M$)"].max()) if not df.empty else 23.0
    
    with num_col1:
        st.markdown('<div class="mini-label">MAX FİYAT</div>', unsafe_allow_html=True)
        tavan_maas = st.number_input("Max Fiyat", min_value=min_p_val, max_value=max_p_val, value=max_p_val, step=0.5, label_visibility="collapsed")
        
    with num_col2:
        st.markdown('<div class="mini-label">MİN MAÇ</div>', unsafe_allow_html=True)
        min_mac = st.number_input("Min Maç", min_value=0, max_value=82, value=0, step=1, label_visibility="collapsed")
        
    with num_col3:
        st.markdown('<div class="mini-label">MİN DK/MAÇ</div>', unsafe_allow_html=True)
        min_mpg = st.number_input("Min Dk/Maç", min_value=0.0, max_value=48.0, value=0.0, step=1.0, label_visibility="collapsed")

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
# ESPOR KARTLARI
# ==========================================
html_m1 = f"""
<div class="esport-card" style="border-left-color: #64748b;">
    <div class="esport-label">R A D A R   A C T I V E</div>
    <div class="esport-value">{len(sorted_table)}</div>
    <div class="esport-pill" style="background-color: rgba(100, 116, 139, 0.15); color: #94a3b8; border-color: rgba(100, 116, 139, 0.3);">
        ✓ {len(df)} OYUNCUDAN
    </div>
</div>
"""
metric_placeholder1.markdown(html_m1, unsafe_allow_html=True)

if not sorted_table.empty:
    best_value_row = sorted_table.iloc[0]
    html_m2 = f"""
    <div class="esport-card" style="border-left-color: #38bdf8;">
        <div class="esport-label">S C O U T   P I C K</div>
        <div class="esport-value">{best_value_row['Oyuncu']}</div>
        <div class="esport-pill">↑ {best_value_row['Value']:.2f} FP/$</div>
    </div>
    """
    metric_placeholder2.markdown(html_m2, unsafe_allow_html=True)
    
    best_form_row = sorted_table.loc[sorted_table['Form'].idxmax()]
    html_m3 = f"""
    <div class="esport-card" style="border-left-color: #f97316;">
        <div class="esport-label">F O R M   L E A D E R</div>
        <div class="esport-value">{best_form_row['Oyuncu']}</div>
        <div class="esport-pill" style="background-color: rgba(249, 115, 22, 0.15); color: #fb923c; border-color: rgba(249, 115, 22, 0.3);">
            🔥 {best_form_row['Form']:.1f} Form
        </div>
    </div>
    """
    metric_placeholder3.markdown(html_m3, unsafe_allow_html=True)
else:
    metric_placeholder2.markdown("""<div class="esport-card" style="border-left-color: #38bdf8;"><div class="esport-label">S C O U T   P I C K</div><div class="esport-value">-</div></div>""", unsafe_allow_html=True)
    metric_placeholder3.markdown("""<div class="esport-card" style="border-left-color: #f97316;"><div class="esport-label">F O R M   L E A D E R</div><div class="esport-value">-</div></div>""", unsafe_allow_html=True)

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
        "Dk/Maç": st.column_config.NumberColumn(format="%.1f"),
        "Devamlılık": st.column_config.NumberColumn("Devamlılık (%)", format="%d %%") # Yeni eklenen veri
    }
)