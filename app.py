import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="NBA Fantasy Verim Paneli", layout="wide", page_icon="🏀")

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
        
        # Form ve Toplam Puan
        form_raw = float(el.get("form", 0.0) or 0.0)
        form_val = round(form_raw / 10.0, 1) if form_raw > 50 else round(form_raw, 1)
        
        tp_raw = float(el.get("total_points", 0.0) or 0.0)
        total_points = round(tp_raw / 10.0, 1) if tp_raw > 0 else 0.0
        
        # Sezonluk Maç Başına Ortalama (PPG / FP Ortalaması)
        ppg_raw = float(el.get("points_per_game", 0.0) or 0.0)
        ppg_val = round(ppg_raw / 10.0, 1) if ppg_raw > 50 else round(ppg_raw, 1)
        
        # Maç Sayısı (GP)
        gp = int(round(total_points / ppg_val)) if ppg_val > 0 else 0
        
        minutes = float(el.get("minutes", 0.0) or 0.0)
        
        # Kutu istatistikleri
        pts = float(el.get("pts", el.get("points", 0.0)) or 0.0)
        reb = float(el.get("rebounds", 0.0) or 0.0)
        ast = float(el.get("assists", 0.0) or 0.0)
        stl = float(el.get("steals", 0.0) or 0.0)
        blk = float(el.get("blocks", 0.0) or 0.0)
        
        # Değer ve Verim Oranları (FP ve PPG bazlı)
        value_ratio = round(total_points / cost, 2) if cost > 0 else 0.0
        fp_per_min = round(total_points / minutes, 2) if minutes > 0 else 0.0
        
        player_list.append({
            "Oyuncu": full_name,
            "Mevki": "BC" if el["element_type"] == 1 else "FC",
            "Takım": teams.get(el["team"], "NBA"),
            "Fiyat (M$)": cost,
            "Toplam FP": total_points,
            "FP Ort. (PPG)": ppg_val,
            "Form (Son Maçlar)": form_val,
            "Value (FP/$)": value_ratio,
            "FP/Min": fp_per_min,
            "Maç": gp,
            "Dakika": minutes,
            "Sayı": pts,
            "Reb": reb,
            "Ast": ast,
            "Top Çalma": stl,
            "Blok": blk
        })
        
    df = pd.DataFrame(player_list)
    return df

st.title("🏀 NBA Fantasy Tavan Bütçe & Verim Paneli (Canlı)")

with st.spinner("Canlı fantezi verileri yükleniyor..."):
    try:
        df = fetch_live_fantasy_data()
        st.success("Canlı Sistem Aktif: Veriler Otomatik Güncelleniyor!")
    except Exception as e:
        st.error(f"Hata oluştu: {e}")
        st.stop()

# Sol Filtreler
st.sidebar.header("🎯 Filtreler")

pos_filter = st.sidebar.radio("Mevki", ["Tümü", "BC (Backcourt)", "FC (Frontcourt)"])

min_p = float(df["Fiyat (M$)"].min()) if not df.empty else 5.0
max_p = float(df["Fiyat (M$)"].max()) if not df.empty else 23.0
tavan_maas = st.sidebar.slider("Tavan Maaş Sınırı (M$)", min_value=min_p, max_value=max_p, value=max_p, step=0.5)

min_mac = st.sidebar.slider("Minimum Maç Sayısı (GP)", 0, 82, 0)
min_dk = st.sidebar.slider("Minimum Süre (Dk)", 0, 50, 0)
arama = st.sidebar.text_input("Oyuncu İsmi Ara")

# Filtreleri uygula
filtered = df[
    (df["Fiyat (M$)"] <= tavan_maas) & 
    (df["Maç"] >= min_mac) &
    (df["Dakika"] >= min_dk)
]

if pos_filter == "BC (Backcourt)":
    filtered = filtered[filtered["Mevki"] == "BC"]
elif pos_filter == "FC (Frontcourt)":
    filtered = filtered[filtered["Mevki"] == "FC"]

if arama:
    filtered = filtered[filtered["Oyuncu"].str.contains(arama, case=False)]

sorted_table = filtered.sort_values(by="Toplam FP", ascending=False)

st.metric("Kriterlere Uyan Oyuncu Sayısı", len(sorted_table))

view_cols = [
    "Oyuncu", "Mevki", "Takım", "Fiyat (M$)", "Toplam FP", "FP Ort. (PPG)", 
    "Form (Son Maçlar)", "Value (FP/$)", "FP/Min", "Maç", "Dakika", "Sayı", "Reb", "Ast", "Top Çalma", "Blok"
]

st.dataframe(
    sorted_table[view_cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Fiyat (M$)": st.column_config.NumberColumn(format="%.1f M$"),
        "Toplam FP": st.column_config.NumberColumn(format="%.1f"),
        "FP Ort. (PPG)": st.column_config.NumberColumn(format="%.1f"),
        "Form (Son Maçlar)": st.column_config.NumberColumn(format="%.1f"),
        "Value (FP/$)": st.column_config.NumberColumn(format="%.2f"),
        "FP/Min": st.column_config.NumberColumn(format="%.2f"),
        "Maç": st.column_config.NumberColumn(format="%d"),
        "Dakika": st.column_config.NumberColumn(format="%.1f"),
        "Sayı": st.column_config.NumberColumn(format="%.1f"),
        "Reb": st.column_config.NumberColumn(format="%.1f"),
        "Ast": st.column_config.NumberColumn(format="%.1f"),
        "Top Çalma": st.column_config.NumberColumn(format="%.1f"),
        "Blok": st.column_config.NumberColumn(format="%.1f")
    }
)