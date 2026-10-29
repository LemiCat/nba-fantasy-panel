import requests
import pandas as pd
import streamlit as st
import datetime

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
    
    /* --- BAŞLIK, LOGO VE ROZETLER --- */
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
    
    .player-count-badge {
        display: inline-flex;
        align-items: center;
        background-color: rgba(148, 163, 184, 0.08); 
        border: 1px solid rgba(148, 163, 184, 0.2);
        color: #94a3b8; 
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 1px;
        margin-left: 10px; 
    }

    /* --- 4'LÜ ESPOR METRİK KARTLARI --- */
    .esport-card {
        border-left: 3px solid #38bdf8;
        padding-left: 12px;
        margin-top: 5px;
        margin-bottom: 15px;
    }
    .esport-label {
        color: #94a3b8;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 2.0px;
        margin-bottom: 4px;
    }
    .esport-value {
        color: #ffffff;
        font-size: 20px;
        font-weight: 900;
        letter-spacing: -0.5px;
        margin-bottom: 8px;
        line-height: 1.1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .esport-pill {
        display: inline-flex;
        align-items: center;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
        border: 1px solid;
    }

    /* --- GHOST FİLTRE PANELİ VE RESET BUTONU CSS --- */
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
    
    /* İkonik Siber Reset Butonu */
    div[data-testid="stButton"] button {
        background-color: rgba(239, 68, 68, 0.05) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        color: #ef4444 !important;
        font-weight: 900 !important;
        font-size: 18px !important;
        transition: all 0.3s ease;
        padding: 0px !important;
        height: 38px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    div[data-testid="stButton"] button:hover {
        background-color: rgba(239, 68, 68, 0.2) !important;
        border: 1px solid rgba(239, 68, 68, 0.8) !important;
        color: #ffffff !important;
    }
    div[data-testid="stButton"] button:active {
        background-color: #ef4444 !important;
        color: #ffffff !important;
    }
    
    /* --- BORSA / SKOR BANDI (TICKER) CSS --- */
    .ticker-container {
        width: 100%;
        overflow: hidden;
        background-color: rgba(15, 23, 42, 0.4); 
        border-top: 1px solid rgba(56, 189, 248, 0.15);
        border-bottom: 1px solid rgba(56, 189, 248, 0.15);
        padding: 6px 0;
        margin-top: 10px;
        margin-bottom: 20px;
        position: relative;
        display: flex;
        align-items: center;
        border-radius: 2px;
    }
    .ticker-label {
        background-color: #ef4444;
        color: #ffffff;
        font-size: 11px;
        font-weight: 900;
        letter-spacing: 1px;
        padding: 6px 14px;
        position: absolute;
        left: 0;
        z-index: 10;
        height: 100%;
        display: flex;
        align-items: center;
        border-right: 2px solid #0f172a;
    }
    .ticker-content {
        white-space: nowrap;
        animation: ticker 50s linear infinite;
        color: #94a3b8;
        font-family: monospace;
        font-size: 14px;
        font-weight: 600;
        padding-left: 100%;
        display: flex;
        align-items: center;
    }
    .ticker-content:hover {
        animation-play-state: paused;
    }
    .score-hl {
        color: #f8fafc;
        font-weight: 800;
        margin: 0 4px;
        background: rgba(255,255,255,0.05);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 13px;
    }
    .time-hl {
        color: #7dd3fc;
        font-weight: 800;
        margin: 0 4px;
        background: rgba(56, 189, 248, 0.1);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 13px;
    }
    .ticker-logo {
        height: 22px;
        width: auto;
        vertical-align: middle;
        margin: 0 6px;
    }
    .ticker-category {
        color: #e2e8f0;
        font-weight: 800;
        letter-spacing: 1px;
        margin: 0 15px;
    }
    @keyframes ticker {
        0% { transform: translateX(0); }
        100% { transform: translateX(-100%); }
    }
    </style>
""", unsafe_allow_html=True)

TEAM_LOGOS = {
    "ATL": "https://a.espncdn.com/i/teamlogos/nba/500/atl.png", "BOS": "https://a.espncdn.com/i/teamlogos/nba/500/bos.png",
    "BKN": "https://a.espncdn.com/i/teamlogos/nba/500/bkn.png", "CHA": "https://a.espncdn.com/i/teamlogos/nba/500/cha.png",
    "CHI": "https://a.espncdn.com/i/teamlogos/nba/500/chi.png", "CLE": "https://a.espncdn.com/i/teamlogos/nba/500/cle.png",
    "DAL": "https://a.espncdn.com/i/teamlogos/nba/500/dal.png", "DEN": "https://a.espncdn.com/i/teamlogos/nba/500/den.png",
    "DET": "https://a.espncdn.com/i/teamlogos/nba/500/det.png", "GSW": "https://a.espncdn.com/i/teamlogos/nba/500/gs.png", 
    "HOU": "https://a.espncdn.com/i/teamlogos/nba/500/hou.png", "IND": "https://a.espncdn.com/i/teamlogos/nba/500/ind.png",
    "LAC": "https://a.espncdn.com/i/teamlogos/nba/500/lac.png", "LAL": "https://a.espncdn.com/i/teamlogos/nba/500/lal.png",
    "MEM": "https://a.espncdn.com/i/teamlogos/nba/500/mem.png", "MIA": "https://a.espncdn.com/i/teamlogos/nba/500/mia.png",
    "MIL": "https://a.espncdn.com/i/teamlogos/nba/500/mil.png", "MIN": "https://a.espncdn.com/i/teamlogos/nba/500/min.png",
    "NOP": "https://a.espncdn.com/i/teamlogos/nba/500/no.png",  "NYK": "https://a.espncdn.com/i/teamlogos/nba/500/ny.png", 
    "OKC": "https://a.espncdn.com/i/teamlogos/nba/500/okc.png", "ORL": "https://a.espncdn.com/i/teamlogos/nba/500/orl.png",
    "PHI": "https://a.espncdn.com/i/teamlogos/nba/500/phi.png", "PHX": "https://a.espncdn.com/i/teamlogos/nba/500/phx.png",
    "POR": "https://a.espncdn.com/i/teamlogos/nba/500/por.png", "SAC": "https://a.espncdn.com/i/teamlogos/nba/500/sac.png",
    "SAS": "https://a.espncdn.com/i/teamlogos/nba/500/sa.png",  "TOR": "https://a.espncdn.com/i/teamlogos/nba/500/tor.png",
    "UTA": "https://a.espncdn.com/i/teamlogos/nba/500/utah.png", "WAS": "https://a.espncdn.com/i/teamlogos/nba/500/was.png"
}

def get_nba_matchday(kickoff_str):
    try:
        dt = datetime.datetime.strptime(kickoff_str, "%Y-%m-%dT%H:%M:%SZ")
        dt_et = dt - datetime.timedelta(hours=5)
        return dt_et.strftime("%Y-%m-%d")
    except Exception:
        return ""

@st.cache_data(show_spinner=True, ttl=900)
def fetch_live_fantasy_data():
    url = "https://tr.nbafantasy.nba.com/api/bootstrap-static/"
    res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15).json()
    teams = {t["id"]: t.get("short_name", t["name"]) for t in res["teams"]}
    
    ticker_html_text = ""
    try:
        url_fix = "https://tr.nbafantasy.nba.com/api/fixtures/"
        res_fix = requests.get(url_fix, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10).json()
        
        valid_fixtures = [m for m in res_fix if m.get('kickoff_time')]
        valid_fixtures.sort(key=lambda x: x['kickoff_time'])
        
        finished_matches = [m for m in valid_fixtures if m.get('finished')]
        upcoming_matches = [m for m in valid_fixtures if not m.get('finished')]
        
        recent_finished = []
        next_upcoming = []
        
        if finished_matches:
            last_match_date = get_nba_matchday(finished_matches[-1]['kickoff_time'])
            recent_finished = [m for m in finished_matches if get_nba_matchday(m['kickoff_time']) == last_match_date]
            
        if upcoming_matches:
            first_match_date = get_nba_matchday(upcoming_matches[0]['kickoff_time'])
            next_upcoming = [m for m in upcoming_matches if get_nba_matchday(m['kickoff_time']) == first_match_date]
            
        ticker_items = []
        
        if recent_finished:
            ticker_items.append("<span class='ticker-category'>[ SON MAÇ GÜNÜ ]</span>")
            for m in recent_finished:
                h_team = teams.get(m['team_h'], "EV")
                a_team = teams.get(m['team_a'], "DEP")
                h_logo = TEAM_LOGOS.get(h_team, "")
                a_logo = TEAM_LOGOS.get(a_team, "")
                
                h_img = f"<img src='{h_logo}' class='ticker-logo'>" if h_logo else ""
                a_img = f"<img src='{a_logo}' class='ticker-logo'>" if a_logo else ""
                h_score = m.get('team_h_score', 0)
                a_score = m.get('team_a_score', 0)
                
                ticker_items.append(f"{h_team} {h_img} <span class='score-hl'>{h_score} - {a_score}</span> {a_img} {a_team}")
        
        if recent_finished and next_upcoming:
            ticker_items.append(" &nbsp;&nbsp;&nbsp;✦&nbsp;&nbsp;&nbsp; ")
            
        if next_upcoming:
            ticker_items.append("<span class='ticker-category'>[ SIRADAKİ MAÇ GÜNÜ ]</span>")
            for m in next_upcoming:
                h_team = teams.get(m['team_h'], "EV")
                a_team = teams.get(m['team_a'], "DEP")
                h_logo = TEAM_LOGOS.get(h_team, "")
                a_logo = TEAM_LOGOS.get(a_team, "")
                
                h_img = f"<img src='{h_logo}' class='ticker-logo'>" if h_logo else ""
                a_img = f"<img src='{a_logo}' class='ticker-logo'>" if a_logo else ""
                
                kickoff = m.get('kickoff_time')
                time_str = "VS"
                if kickoff:
                    try:
                        dt = datetime.datetime.strptime(kickoff, "%Y-%m-%dT%H:%M:%SZ")
                        dt = dt + datetime.timedelta(hours=3) 
                        time_str = dt.strftime("%H:%M")
                    except Exception:
                        pass
                
                ticker_items.append(f"{h_team} {h_img} <span class='time-hl'>{time_str}</span> {a_img} {a_team}")
                
        ticker_html_text = " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ".join(ticker_items)
        
    except Exception:
        ticker_html_text = "CANLI SKOR BAĞLANTISI BEKLENİYOR..."
    
    team_max_games = {team_name: 0 for team_name in teams.values()}
    for el in res["elements"]:
        if el.get("status") in ["u"]:
            continue
        team_name = teams.get(el["team"], "NBA")
        tp_raw = float(el.get("total_points", 0.0) or 0.0)
        tp = round(tp_raw / 10.0, 1)
        ppg_raw = float(el.get("points_per_game", 0.0) or 0.0)
        ppg = round(ppg_raw / 10.0, 1)
        gp = int(round(tp / ppg)) if ppg > 0 else 0
        if gp > team_max_games[team_name]:
            team_max_games[team_name] = gp

    player_list = []
    for el in res["elements"]:
        if el.get("status") in ["u"]:
            continue
            
        full_name = f"{el['first_name']} {el['second_name']}"
        team_name = teams.get(el["team"], "NBA")
        cost = float(el.get("now_cost", el.get("cost", 0))) / 10.0
        
        form_raw = float(el.get("form", 0.0) or 0.0)
        form_val = round(form_raw / 10.0, 1)
        
        tp_raw = float(el.get("total_points", 0.0) or 0.0)
        total_points = round(tp_raw / 10.0, 1)
        
        ppg_raw = float(el.get("points_per_game", 0.0) or 0.0)
        ppg_val = round(ppg_raw / 10.0, 1)
        
        gp = int(round(total_points / ppg_val)) if ppg_val > 0 else 0
        team_games = team_max_games[team_name]

        if gp > 0 and team_games > 0 and gp < team_games:
            form_val = round(form_val * (team_games / gp), 1)
            
        total_minutes = float(el.get("minutes", 0.0) or 0.0)
        mpg = round(total_minutes / gp, 1) if gp > 0 else 0.0
        value_ratio = round(total_points / cost, 2) if cost > 0 else 0.0
        firsat_index = round(form_val / cost, 2) if cost > 0 else 0.0
        
        availability = int(round((gp / team_games) * 100)) if team_games > 0 else 0
        
        player_list.append({
            "Oyuncu": full_name,
            "Mevki": "BC" if el["element_type"] == 1 else "FC",
            "Takım": team_name,
            "Fiyat (M$)": cost,
            "Dk/Maç": mpg,
            "Maç (Dev%)": f"{gp} (%{availability})",
            "Toplam FP": total_points,
            "FP Ort. (PPG)": ppg_val,
            "Form": form_val,
            "Value": value_ratio,
            "Fırsat": firsat_index,
            "_Mac_Siralama": gp
        })
        
    df = pd.DataFrame(player_list)
    return df, ticker_html_text

try:
    df, ticker_text = fetch_live_fantasy_data()
except Exception as e:
    st.error(f"Veri çekme hatası: {e}")
    st.stop()

# Reset Fonksiyonu - Callback
min_p_val = float(df["Fiyat (M$)"].min()) if not df.empty else 5.0
max_p_val = float(df["Fiyat (M$)"].max()) if not df.empty else 23.0

def reset_filters():
    st.session_state["search_player"] = []
    st.session_state["filter_pos"] = "Tümü"
    st.session_state["max_price"] = max_p_val
    st.session_state["min_game"] = 0
    st.session_state["min_min"] = 0.0

header_placeholder = st.empty()
main_col_left, main_col_right = st.columns([1.7, 1]) 

with main_col_left:
    st.write("") 
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_placeholder1 = metric_col1.empty()
    metric_placeholder2 = metric_col2.empty()
    metric_placeholder3 = metric_col3.empty()
    metric_placeholder4 = metric_col4.empty()

with main_col_right:
    st.markdown('<div class="esport-label" style="margin-bottom:12px; color:#38bdf8;">R A D A R   F I L T E R S</div>', unsafe_allow_html=True)
    
    filt_col1, filt_col2 = st.columns([1.5, 1])
    with filt_col1:
        selected_players = st.multiselect(
            "Oyuncu",
            options=sorted(df["Oyuncu"].unique()),
            placeholder="Oyuncu ara...",
            label_visibility="collapsed",
            key="search_player"
        )
    with filt_col2:
        pos_filter = st.selectbox("Mevki", ["Tümü", "BC", "FC"], label_visibility="collapsed", key="filter_pos")
    
    # İkon butonuna göre çok daraltılmış 4. Sütun (0.2 oran)
    num_col1, num_col2, num_col3, btn_col = st.columns([1, 1, 1, 0.25])
    
    with num_col1:
        st.markdown('<div class="mini-label">MAX FİYAT</div>', unsafe_allow_html=True)
        tavan_maas = st.number_input("Max Fiyat", min_value=min_p_val, max_value=max_p_val, value=max_p_val, step=0.5, label_visibility="collapsed", key="max_price")
        
    with num_col2:
        st.markdown('<div class="mini-label">MİN MAÇ</div>', unsafe_allow_html=True)
        min_mac = st.number_input("Min Maç", min_value=0, max_value=82, value=0, step=1, label_visibility="collapsed", key="min_game")
        
    with num_col3:
        st.markdown('<div class="mini-label">MİN DK/MAÇ</div>', unsafe_allow_html=True)
        min_mpg = st.number_input("Min Dk/Maç", min_value=0.0, max_value=48.0, value=0.0, step=1.0, label_visibility="collapsed", key="min_min")

    with btn_col:
        st.markdown('<div class="mini-label" style="color:transparent; pointer-events:none;">X</div>', unsafe_allow_html=True)
        st.button("↺", use_container_width=True, on_click=reset_filters)

# ==========================================
# FİLTRELEME MANTIĞI
# ==========================================
if selected_players:
    filtered = df[df["Oyuncu"].isin(selected_players)]
else:
    filtered = df[
        (df["Fiyat (M$)"] <= st.session_state.get("max_price", tavan_maas)) & 
        (df["_Mac_Siralama"] >= st.session_state.get("min_game", min_mac)) &
        (df["Dk/Maç"] >= st.session_state.get("min_min", min_mpg))
    ]
    current_pos = st.session_state.get("filter_pos", pos_filter)
    if current_pos == "BC":
        filtered = filtered[filtered["Mevki"] == "BC"]
    elif current_pos == "FC":
        filtered = filtered[filtered["Mevki"] == "FC"]

sorted_table = filtered.sort_values(by="Fırsat", ascending=False)

header_placeholder.markdown(f"""
    <div class="custom-header-container">
        <img src="https://upload.wikimedia.org/wikipedia/en/0/03/National_Basketball_Association_logo.svg" class="nba-official-logo" alt="NBA Logo">
        <h1>NBA FANTASY <span class="header-thin">SCOUT</span></h1>
        <div class="live-badge">
            <div class="blinking-dot"></div> LIVE
        </div>
        <div class="player-count-badge">
            ⌖ {len(sorted_table)}
        </div>
    </div>
""", unsafe_allow_html=True)

if not sorted_table.empty:
    best_ppg_row = sorted_table.loc[sorted_table['FP Ort. (PPG)'].idxmax()]
    metric_placeholder1.markdown(f"""
    <div class="esport-card" style="border-left-color: #a855f7;">
        <div class="esport-label">P P G   L E A D E R</div>
        <div class="esport-value" title="{best_ppg_row['Oyuncu']}">{best_ppg_row['Oyuncu']}</div>
        <div class="esport-pill" style="background-color: rgba(168, 85, 247, 0.15); color: #c084fc; border-color: rgba(168, 85, 247, 0.3);">
            AVG | {best_ppg_row['FP Ort. (PPG)']:.1f}
        </div>
    </div>
    """, unsafe_allow_html=True)

    best_form_row = sorted_table.loc[sorted_table['Form'].idxmax()]
    metric_placeholder2.markdown(f"""
    <div class="esport-card" style="border-left-color: #f97316;">
        <div class="esport-label">F O R M   L E A D E R</div>
        <div class="esport-value" title="{best_form_row['Oyuncu']}">{best_form_row['Oyuncu']}</div>
        <div class="esport-pill" style="background-color: rgba(249, 115, 22, 0.15); color: #fb923c; border-color: rgba(249, 115, 22, 0.3);">
            FRM | {best_form_row['Form']:.1f}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    best_value_row = sorted_table.loc[sorted_table['Value'].idxmax()]
    metric_placeholder3.markdown(f"""
    <div class="esport-card" style="border-left-color: #10b981;">
        <div class="esport-label">V A L U E   L E A D E R</div>
        <div class="esport-value" title="{best_value_row['Oyuncu']}">{best_value_row['Oyuncu']}</div>
        <div class="esport-pill" style="background-color: rgba(16, 185, 129, 0.15); color: #34d399; border-color: rgba(16, 185, 129, 0.3);">
            VAL | {best_value_row['Value']:.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)

    best_firsat_row = sorted_table.loc[sorted_table['Fırsat'].idxmax()]
    metric_placeholder4.markdown(f"""
    <div class="esport-card" style="border-left-color: #38bdf8;">
        <div class="esport-label">S C O U T   P I C K</div>
        <div class="esport-value" title="{best_firsat_row['Oyuncu']}">{best_firsat_row['Oyuncu']}</div>
        <div class="esport-pill" style="background-color: rgba(56, 189, 248, 0.15); color: #7dd3fc; border-color: rgba(56, 189, 248, 0.3);">
            SCT | {best_firsat_row['Fırsat']:.2f}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div class="ticker-container">
    <div class="ticker-label">NBA SKOR</div>
    <div class="ticker-content">
        {ticker_text}
    </div>
</div>
""", unsafe_allow_html=True)

def style_ppg(val): return 'background-color: rgba(168, 85, 247, 0.15); color: #c084fc; font-weight: 700;'
def style_form(val): return 'background-color: rgba(249, 115, 22, 0.15); color: #fb923c; font-weight: 700;'
def style_value(val): return 'background-color: rgba(16, 185, 129, 0.15); color: #34d399; font-weight: 700;'
def style_firsat(val): return 'background-color: rgba(56, 189, 248, 0.15); color: #7dd3fc; font-weight: 700;'

columns_to_show = ["Oyuncu", "Mevki", "Takım", "Fiyat (M$)", "Dk/Maç", "Maç (Dev%)", "Toplam FP", "FP Ort. (PPG)", "Form", "Value", "Fırsat"]
display_table = sorted_table[columns_to_show]

try:
    styled_table = display_table.style\
        .map(style_ppg, subset=['FP Ort. (PPG)'])\
        .map(style_form, subset=['Form'])\
        .map(style_value, subset=['Value'])\
        .map(style_firsat, subset=['Fırsat'])
except AttributeError:
    styled_table = display_table.style\
        .applymap(style_ppg, subset=['FP Ort. (PPG)'])\
        .applymap(style_form, subset=['Form'])\
        .applymap(style_value, subset=['Value'])\
        .applymap(style_firsat, subset=['Fırsat'])

st.dataframe(
    styled_table,
    use_container_width=True,
    hide_index=True,
    height=600,
    column_config={
        "Fiyat (M$)": st.column_config.NumberColumn(format="%.1f M$"),
        "Dk/Maç": st.column_config.NumberColumn(format="%.1f"),
        "Maç (Dev%)": st.column_config.TextColumn("Maç (Dev%)", width="small"),
        "Toplam FP": st.column_config.NumberColumn(format="%.1f"),
        "FP Ort. (PPG)": st.column_config.NumberColumn(format="%.1f"),
        "Form": st.column_config.NumberColumn("Form", format="%.1f"),
        "Value": st.column_config.NumberColumn("Value (FP/$)", format="%.2f"),
        "Fırsat": st.column_config.NumberColumn("Fırsat", format="%.2f")
    }
)