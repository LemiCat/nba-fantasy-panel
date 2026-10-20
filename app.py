import re
import requests
import pandas as pd
import streamlit as st
from unicodedata import normalize
from nba_api.stats.endpoints import leaguedashplayerstats

st.set_page_config(page_title="NBA Fantasy Verim Paneli", layout="wide", page_icon="🏀")

def clean_name(name):
    if not name:
        return ""
    name = normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8")
    name = name.lower()
    name = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", name)
    name = re.sub(r"[^a-z0-9]", "", name)
    return name.strip()

@st.cache_data(show_spinner=True)
def fetch_data():
    # 1. Fantasy API - Takım Kısaltmaları ve Form Verisi
    url = "https://tr.nbafantasy.nba.com/api/bootstrap-static/"
    res = requests.get(url, timeout=15).json()
    teams = {t["id"]: t.get("short_name", t["name"]) for t in res["teams"]}
    
    fan_list = []
    for el in res["elements"]:
        f_name = f"{el['first_name']} {el['second_name']}"
        cost = el.get("now_cost", el.get("cost", 0))
        # Form: Fantezi API'sindeki son maçlar performans ortalaması
        form_val = float(el.get("form", 0.0) or 0.0)
        
        fan_list.append({
            "full_name": f_name,
            "norm_name": clean_name(f_name),
            "team_abbr": teams.get(el["team"], "NBA"),
            "pos": "BC" if el["element_type"] == 1 else "FC",
            "price": float(cost) / 10.0,
            "form": form_val
        })
    df_f = pd.DataFrame(fan_list)

    # 2. NBA API
    stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season="2024-25",
        per_mode_detailed="PerGame",
        timeout=30
    ).get_data_frames()[0]
    
    cols = {
        "PLAYER_NAME": "nba_name",
        "GP": "gp",
        "MIN": "min",
        "PTS": "pts",
        "REB": "reb",
        "AST": "ast",
        "STL": "stl",
        "BLK": "blk",
        "FG_PCT": "fg_pct"
    }
    df_n = stats[list(cols.keys())].rename(columns=cols)
    df_n["norm_name"] = df_n["nba_name"].apply(clean_name)

    # 3. Hesaplamalar
    df_all = pd.merge(df_f, df_n, on="norm_name", how="inner")
    
    # Formül: PTS + REB + 2*AST + 3*STL + 3*BLK
    df_all["FP"] = (
        df_all["pts"] * 1.0 +
        df_all["reb"] * 1.0 +
        df_all["ast"] * 2.0 +
        df_all["stl"] * 3.0 +
        df_all["blk"] * 3.0
    ).round(1)
    
    df_all["Value (FP/$)"] = (df_all["FP"] / df_all["price"].replace(0, 1.0)).round(2)
    df_all["FP/Min"] = (df_all["FP"] / df_all["min"].replace(0, 1.0)).round(2)
    df_all["FG%"] = (df_all["fg_pct"] * 100).round(1)
    
    return df_all

st.title("🏀 NBA Fantasy Tavan Bütçe & Verim Paneli")

# Veri yükleme
with st.spinner("NBA istatistikleri ve form durumları yükleniyor..."):
    try:
        df = fetch_data()
        st.success("Veriler güncellendi!")
    except Exception as e:
        st.error(f"Hata oluştu: {e}")
        st.stop()

# Sol Filtre Paneli
st.sidebar.header("🎯 Filtreler")

pos_filter = st.sidebar.radio("Mevki", ["Tümü", "BC (Backcourt)", "FC (Frontcourt)"])

min_p = float(df["price"].min())
max_p = float(df["price"].max())
tavan_maas = st.sidebar.slider("Tavan Maaş Sınırı (M$)", min_value=min_p, max_value=max_p, value=max_p, step=0.5)

# Sahte verim patlamalarını engelleyen filtreler
min_mac = st.sidebar.slider("Minimum Maç Sayısı (GP)", 1, 82, 15)
min_dk = st.sidebar.slider("Minimum Süre (Dk)", 0, 40, 15)
arama = st.sidebar.text_input("Oyuncu İsmi Ara")

# Filtreleri uygula
filtered = df[
    (df["price"] <= tavan_maas) & 
    (df["gp"] >= min_mac) & 
    (df["min"] >= min_dk)
]

if pos_filter == "BC (Backcourt)":
    filtered = filtered[filtered["pos"] == "BC"]
elif pos_filter == "FC (Frontcourt)":
    filtered = filtered[filtered["pos"] == "FC"]

if arama:
    filtered = filtered[filtered["full_name"].str.contains(arama, case=False)]

sorted_table = filtered.sort_values(by="Value (FP/$)", ascending=False)

# Görünüm Sütunları
view_cols = [
    "full_name", "pos", "team_abbr", "price", "FP", "form",
    "Value (FP/$)", "FP/Min", "gp", "min", "pts", "reb", "ast", "stl", "blk", "FG%"
]

st.metric("Kriterlere Uyan Oyuncu Sayısı", len(sorted_table))

st.dataframe(
    sorted_table[view_cols].rename(columns={
        "full_name": "Oyuncu",
        "pos": "Mevki",
        "team_abbr": "Takım",
        "price": "Fiyat (M$)",
        "form": "Form (Son Maçlar)",
        "gp": "Maç",
        "min": "Dakika",
        "pts": "Sayı",
        "reb": "Reb",
        "ast": "Ast",
        "stl": "Top Çalma",
        "blk": "Blok"
    }),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Fiyat (M$)": st.column_config.NumberColumn(format="%.1f M$"),
        "FP": st.column_config.NumberColumn(format="%.1f"),
        "Form (Son Maçlar)": st.column_config.NumberColumn(format="%.1f"),
        "Value (FP/$)": st.column_config.NumberColumn(format="%.2f"),
        "FP/Min": st.column_config.NumberColumn(format="%.2f"),
        "Dakika": st.column_config.NumberColumn(format="%.1f"),
        "Sayı": st.column_config.NumberColumn(format="%.1f"),
        "Reb": st.column_config.NumberColumn(format="%.1f"),
        "Ast": st.column_config.NumberColumn(format="%.1f"),
        "Top Çalma": st.column_config.NumberColumn(format="%.1f"),
        "Blok": st.column_config.NumberColumn(format="%.1f"),
        "FG%": st.column_config.NumberColumn(format="%.1f%%")
    }
)