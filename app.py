import re
import requests
import pandas as pd
import streamlit as st
from unicodedata import normalize

st.set_page_config(page_title="NBA Fantasy Verim Paneli", layout="wide", page_icon="🏀")

def clean_name(name):
    if not name:
        return ""
    name = normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8")
    name = name.lower()
    name = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", name)
    name = re.sub(r"[^a-z0-9]", "", name)
    return name.strip()

@st.cache_data(show_spinner=True, ttl=1800)
def fetch_data():
    # 1. Fantasy API - Canlı Fantezi Verileri
    url = "https://tr.nbafantasy.nba.com/api/bootstrap-static/"
    res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15).json()
    teams = {t["id"]: t.get("short_name", t["name"]) for t in res["teams"]}
    
    fan_list = []
    for el in res["elements"]:
        f_name = f"{el['first_name']} {el['second_name']}"
        cost = el.get("now_cost", el.get("cost", 0))
        # Form verisi API'de 10 katı olarak geldiği için 10'a bölüyoruz
        form_raw = float(el.get("form", 0.0) or 0.0)
        form_val = form_raw / 10.0 if form_raw > 50 else form_raw
        
        fan_list.append({
            "fantasy_id": el["id"],
            "full_name": f_name,
            "norm_name": clean_name(f_name),
            "team_abbr": teams.get(el["team"], "NBA"),
            "pos": "BC" if el["element_type"] == 1 else "FC",
            "price": float(cost) / 10.0,
            "form": form_val
        })
    df_f = pd.DataFrame(fan_list)

    # 2. NBA İstatistikleri (CSV)
    stats = pd.read_csv("nba_stats.csv")
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
    # NBA tarafında aynı isimde birden fazla satır varsa tekilleştir
    df_n = df_n.drop_duplicates(subset=["norm_name"], keep="first")

    # 3. Left Join ve Fantezi Havuzunu Birebir Koruma
    df_all = pd.merge(df_f, df_n, on="norm_name", how="left")
    # Fantezi ID'si bazında tekilleştir (516 oyuncuya sabitler)
    df_all = df_all.drop_duplicates(subset=["fantasy_id"], keep="first")
    
    df_all["gp"] = df_all["gp"].fillna(0).astype(int)
    df_all["min"] = df_all["min"].fillna(0.0)
    df_all["pts"] = df_all["pts"].fillna(0.0)
    df_all["reb"] = df_all["reb"].fillna(0.0)
    df_all["ast"] = df_all["ast"].fillna(0.0)
    df_all["stl"] = df_all["stl"].fillna(0.0)
    df_all["blk"] = df_all["blk"].fillna(0.0)
    df_all["fg_pct"] = df_all["fg_pct"].fillna(0.0)

    # FP Hesaplama
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

st.title("🏀 NBA Fantasy Tavan Bütçe & Verim Paneli (2026-27)")

with st.spinner("2026-27 sezonu verileri yükleniyor..."):
    try:
        df = fetch_data()
        st.success("2026-27 Sezonu Verileri Güncellendi!")
    except Exception as e:
        st.error(f"Hata oluştu: {e}")
        st.stop()

# Sol Filtre Paneli
st.sidebar.header("🎯 Filtreler")

pos_filter = st.sidebar.radio("Mevki", ["Tümü", "BC (Backcourt)", "FC (Frontcourt)"])

min_p = float(df["price"].min())
max_p = float(df["price"].max())
tavan_maas = st.sidebar.slider("Tavan Maaş Sınırı (M$)", min_value=min_p, max_value=max_p, value=max_p, step=0.5)

min_mac = st.sidebar.slider("Minimum Maç Sayısı (GP)", 0, 82, 0)
min_dk = st.sidebar.slider("Minimum Süre (Dk)", 0, 40, 0)
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