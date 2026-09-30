import json
import os
import streamlit as st
import pandas as pd
import hesaplayici
import motor

st.set_page_config(
    page_title="NBA Fantasy Karar Paneli", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

TEAM_LOGOS = {
    "ATL": "https://cdn.nba.com/logos/nba/1610612737/primary/L/logo.svg",
    "BOS": "https://cdn.nba.com/logos/nba/1610612738/primary/L/logo.svg",
    "BKN": "https://cdn.nba.com/logos/nba/1610612751/primary/L/logo.svg",
    "CHA": "https://cdn.nba.com/logos/nba/1610612766/primary/L/logo.svg",
    "CHI": "https://cdn.nba.com/logos/nba/1610612741/primary/L/logo.svg",
    "CLE": "https://cdn.nba.com/logos/nba/1610612739/primary/L/logo.svg",
    "DAL": "https://cdn.nba.com/logos/nba/1610612742/primary/L/logo.svg",
    "DEN": "https://cdn.nba.com/logos/nba/1610612743/primary/L/logo.svg",
    "DET": "https://cdn.nba.com/logos/nba/1610612765/primary/L/logo.svg",
    "GSW": "https://cdn.nba.com/logos/nba/1610612744/primary/L/logo.svg",
    "HOU": "https://cdn.nba.com/logos/nba/1610612745/primary/L/logo.svg",
    "IND": "https://cdn.nba.com/logos/nba/1610612754/primary/L/logo.svg",
    "LAC": "https://cdn.nba.com/logos/nba/1610612746/primary/L/logo.svg",
    "LAL": "https://cdn.nba.com/logos/nba/1610612747/primary/L/logo.svg",
    "MEM": "https://cdn.nba.com/logos/nba/1610612763/primary/L/logo.svg",
    "MIA": "https://cdn.nba.com/logos/nba/1610612748/primary/L/logo.svg",
    "MIL": "https://cdn.nba.com/logos/nba/1610612749/primary/L/logo.svg",
    "MIN": "https://cdn.nba.com/logos/nba/1610612750/primary/L/logo.svg",
    "NOP": "https://cdn.nba.com/logos/nba/1610612740/primary/L/logo.svg",
    "NYK": "https://cdn.nba.com/logos/nba/1610612752/primary/L/logo.svg",
    "OKC": "https://cdn.nba.com/logos/nba/1610612760/primary/L/logo.svg",
    "ORL": "https://cdn.nba.com/logos/nba/1610612753/primary/L/logo.svg",
    "PHI": "https://cdn.nba.com/logos/nba/1610612755/primary/L/logo.svg",
    "PHX": "https://cdn.nba.com/logos/nba/1610612756/primary/L/logo.svg",
    "POR": "https://cdn.nba.com/logos/nba/1610612757/primary/L/logo.svg",
    "SAC": "https://cdn.nba.com/logos/nba/1610612758/primary/L/logo.svg",
    "SAS": "https://cdn.nba.com/logos/nba/1610612759/primary/L/logo.svg",
    "TOR": "https://cdn.nba.com/logos/nba/1610612761/primary/L/logo.svg",
    "UTA": "https://cdn.nba.com/logos/nba/1610612762/primary/L/logo.svg",
    "WAS": "https://cdn.nba.com/logos/nba/1610612764/primary/L/logo.svg"
}

# --- 1. VERİ KONTROLÜ ---
if not os.path.exists("oyuncular.csv"):
    with st.spinner("İlk çalıştırma için oyuncu verileri çekiliyor..."):
        df = motor.verileri_guncelle()
else:
    try:
        df = pd.read_csv("oyuncular.csv")
        if "code" not in df.columns:
            df = motor.verileri_guncelle()
    except Exception:
        df = motor.verileri_guncelle()

all_names = sorted(df["isim"].unique().tolist())

# --- 2. MENAJER PROFİL SİSTEMİ ---
PROFILLER_DOSYASI = "profiller.json"
if os.path.exists(PROFILLER_DOSYASI):
    try:
        with open(PROFILLER_DOSYASI, "r", encoding="utf-8") as f:
            profiller = json.load(f)
    except Exception:
        profiller = ["Bilal"]
else:
    profiller = ["Bilal"]

default_names = [
    "Tyrese Maxey", "Jordan Poole", "Ajay Mitchell", "Tre Mann", "Nikola Topic",
    "Joel Embiid", "Zion Williamson", "Walker Kessler", "Jusuf Nurkic", "Tolu Smith"
]

# --- ÜST BAŞLIK VE MENAJER KONTROLLERİ ---
col_baslik, col_menajer, col_guncelle = st.columns([2.5, 1.8, 1])

with col_baslik:
    st.title("🏀 NBA Fantasy Karar Paneli")

with col_menajer:
    secilen_profil = st.selectbox(
        "👤 Menajer / Takım Profili:",
        options=profiller + ["➕ Yeni Menajer Ekle..."],
        index=0
    )
    if secilen_profil == "➕ Yeni Menajer Ekle...":
        yeni_ad = st.text_input("Yeni Menajer İsmi:", placeholder="Örn: Mehmet")
        if st.button("Menajeri Kaydet"):
            if yeni_ad and yeni_ad not in profiller:
                profiller.append(yeni_ad)
                with open(PROFILLER_DOSYASI, "w", encoding="utf-8") as f:
                    json.dump(profiller, f, ensure_ascii=False, indent=2)
                st.rerun()

with col_guncelle:
    st.write("")
    if st.button("🔄 Verileri Güncelle", help="NBA API'sinden en güncel verileri çeker"):
        with st.spinner("NBA API'sinden güncel veriler çekiliyor..."):
            df = motor.verileri_guncelle()
            st.success("✅ Veriler güncellendi!")
            st.rerun()

aktif_menajer = profiller[0] if secilen_profil == "➕ Yeni Menajer Ekle..." else secilen_profil
KADRO_DOSYASI = f"kadro_{aktif_menajer.lower()}.json"

if f"kadro_{aktif_menajer}" not in st.session_state:
    if os.path.exists(KADRO_DOSYASI):
        try:
            with open(KADRO_DOSYASI, "r", encoding="utf-8") as f:
                kayitli = json.load(f)
                valid = [n for n in kayitli if n in all_names]
                st.session_state[f"kadro_{aktif_menajer}"] = valid if len(valid) == 10 else default_names
        except Exception:
            st.session_state[f"kadro_{aktif_menajer}"] = default_names
    else:
        st.session_state[f"kadro_{aktif_menajer}"] = default_names

suanki_kadro_isimler = st.session_state[f"kadro_{aktif_menajer}"]

def kadroyu_kaydet():
    with open(KADRO_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(suanki_kadro_isimler, f, ensure_ascii=False, indent=2)

GW_NOW = 1
GW_NEXT = 2

# Mevcut kadronun takımları ve takım başına oyuncu sayısı
kadro_df_gecici = df[df["isim"].isin(suanki_kadro_isimler)]
takim_sayilari = kadro_df_gecici["takim"].value_counts().to_dict()

# --- OYUNCU DETAY POP-UP MODAL ---
@st.dialog("Oyuncu Detay Kartı", width="large")
def oyuncu_popup(isim):
    p = df[df["isim"] == isim].iloc[0]
    p_code = str(p.get("code", "")).replace(".0", "").strip()
    t_code = p.get("takim", "")
    
    foto_url = f"https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{p_code}.png" if p_code else None
    logo_url = TEAM_LOGOS.get(t_code, None)

    c_img, c_info, c_status = st.columns([2, 3.5, 2])
    
    with c_img:
        if foto_url:
            st.image(foto_url, width=180)
        else:
            st.markdown("👤 *Fotoğraf Yok*")
            
    with c_info:
        st.markdown(f"# {p['isim']}")
        st.markdown(f"### `{t_code}` • `{p['pozisyon']}` • **{p['fiyat']}M**")
        if logo_url:
            st.image(logo_url, width=75)
            
    with c_status:
        st.write("")
        if p["durum"] == "Sakat":
            st.error("🔴 Sakat")
        elif "Şüpheli" in p["durum"]:
            st.warning(f"🟡 {p['durum']}")
        else:
            st.success("🟢 Sağlıklı")
            
        if p.get("mac_kacirma") == "Sık Maç Kaçırıyor":
            st.error("⚠️ Sık Kaçırıyor")
        else:
            st.info("🛡️ Düzenli")

    st.markdown("---")
    
    # Kadro Ekleme / Çıkarma Butonu (TAKIM KOTASI KONTROLÜ İLE)
    btn_c1, _ = st.columns([2.5, 2])
    with btn_c1:
        if isim in suanki_kadro_isimler:
            if st.button("❌ Bu Oyuncuyu Kadrodan Çıkar", use_container_width=True):
                suanki_kadro_isimler.remove(isim)
                kadroyu_kaydet()
                st.rerun()
        else:
            oyuncunun_takimi = p["takim"]
            takimdaki_mevcut_sayi = takim_sayilari.get(oyuncunun_takimi, 0)
            
            if len(suanki_kadro_isimler) >= 10:
                st.caption("⚠️ Kadro dolu (10/10). Eklemek için birini çıkarmalısınız.")
            elif takimdaki_mevcut_sayi >= 2:
                st.error(f"🚫 **Takım Kotası Dolu:** Kadronuzda zaten 2 `{oyuncunun_takimi}` oyuncusu var! (Kural: Max 2)")
            else:
                if st.button("🟢 Bu Oyuncuyu Kadroya Ekle", use_container_width=True):
                    suanki_kadro_isimler.append(isim)
                    kadroyu_kaydet()
                    st.rerun()

    st.markdown("---")
    st.markdown("### 📅 Yaklaşan Fikstür")
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        st.metric(label=f"Bu Hafta (GW{GW_NOW})", value=f"{p[f'gw{GW_NOW}_mac']} Maç", delta=f"B2B: {p[f'gw{GW_NOW}_b2b']}", delta_color="off")
    with f_col2:
        st.metric(label=f"Gelecek Hafta (GW{GW_NEXT})", value=f"{p[f'gw{GW_NEXT}_mac']} Maç", delta=f"B2B: {p[f'gw{GW_NEXT}_b2b']}", delta_color="off")

    st.markdown("---")
    st.markdown("### 📊 Performans & Form Eğilimi (Son 5 Maç)")
    
    def format_delta(sezon_val, form_val):
        if sezon_val == 0 and form_val == 0: return "—"
        fark = round(form_val - sezon_val, 1)
        return f"+{fark}" if fark > 0 else f"{fark}" if fark < 0 else "0.0"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Süre (Dk)", f"{p.get('f_dakika', 0.0):.1f}", delta=format_delta(p.get("dakika", 0.0), p.get("f_dakika", 0.0)))
    c2.metric("Fantezi Puanı", f"{p.get('f_ort_puan', 0.0):.1f}", delta=format_delta(p.get("ort_puan", 0.0), p.get("f_ort_puan", 0.0)))
    c3.metric("Sayı", f"{p.get('f_sayi', 0.0):.1f}", delta=format_delta(p.get("sayi", 0.0), p.get("f_sayi", 0.0)))
    c4.metric("Asist", f"{p.get('f_asist', 0.0):.1f}", delta=format_delta(p.get("asist", 0.0), p.get("f_asist", 0.0)))

    c5, c6, c7 = st.columns(3)
    c5.metric("Ribaund", f"{p.get('f_ribaund', 0.0):.1f}", delta=format_delta(p.get("ribaund", 0.0), p.get("f_ribaund", 0.0)))
    c6.metric("Top Çalma", f"{p.get('f_top_calma', 0.0):.1f}", delta=format_delta(p.get("top_calma", 0.0), p.get("f_top_calma", 0.0)))
    c7.metric("Blok", f"{p.get('f_blok', 0.0):.1f}", delta=format_delta(p.get("blok", 0.0), p.get("f_blok", 0.0)))

# --- ÜST ARAMA ÇUBUĞU ---
search_col1, search_col2 = st.columns([5, 1])
with search_col1:
    secilen_oyuncu = st.selectbox(
        "Tüm NBA Havuzunda Oyuncu Ara:",
        options=["--- Oyuncu Ara veya İncele ---"] + all_names,
        index=0,
        label_visibility="collapsed"
    )
with search_col2:
    if st.button("🔍 İncele", use_container_width=True):
        if secilen_oyuncu != "--- Oyuncu Ara veya İncele ---":
            oyuncu_popup(secilen_oyuncu)

if secilen_oyuncu != "--- Oyuncu Ara veya İncele ---":
    if st.session_state.get("son_aranan") != secilen_oyuncu:
        st.session_state["son_aranan"] = secilen_oyuncu
        oyuncu_popup(secilen_oyuncu)

st.markdown("---")

kadro_df = df[df["isim"].isin(suanki_kadro_isimler)].copy()
bc_toplam = len(kadro_df[kadro_df["pozisyon"] == "BC"])
fc_toplam = len(kadro_df[kadro_df["pozisyon"] == "FC"])

# Takım Sınırı Aşımı Kontrolü
fazla_takimlar = [t for t, c in kadro_df["takim"].value_counts().items() if c > 2]

# --- GW2 ÇAKIŞMA / İSRAF HESAPLAMA ---
oyuncu_israf = {isim: 0 for isim in suanki_kadro_isimler}
if len(kadro_df) == 10:
    for day_col in hesaplayici.DAY_COLS_GW2:
        maci_olanlar = kadro_df[kadro_df[day_col] > 0]
        bc_ler = maci_olanlar[maci_olanlar["pozisyon"] == "BC"].sort_values(by="fiyat", ascending=False)["isim"].tolist()
        fc_ler = maci_olanlar[maci_olanlar["pozisyon"] == "FC"].sort_values(by="fiyat", ascending=False)["isim"].tolist()
        
        if len(bc_ler) >= 3 and len(fc_ler) >= 2:
            sahadaki_bc, sahadaki_fc = bc_ler[:3], fc_ler[:2]
        elif len(bc_ler) >= 2 and len(fc_ler) >= 3:
            sahadaki_bc, sahadaki_fc = bc_ler[:2], fc_ler[:3]
        else:
            sahadaki_bc, sahadaki_fc = bc_ler[:3], fc_ler[:3]
            
        sahadakiler = set(sahadaki_bc + sahadaki_fc)
        for isim in (bc_ler + fc_ler):
            if isim not in sahadakiler:
                oyuncu_israf[isim] += 1

kadro_df["gw2_israf"] = kadro_df["isim"].map(oyuncu_israf).fillna(0).astype(int)

# --- ÜST METRİKLER ---
harcanan = round(kadro_df["fiyat"].sum(), 1)
kasa = round(100.0 - harcanan, 1)
efektif_gw1 = hesaplayici.hesapla_efektif_mac(kadro_df, hesaplayici.DAY_COLS_GW1) if len(kadro_df) == 10 else 0
efektif_gw2 = hesaplayici.hesapla_efektif_mac(kadro_df, hesaplayici.DAY_COLS_GW2) if len(kadro_df) == 10 else 0

col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns([1.1, 1, 1.2, 1.2, 1.2])
with col_k1:
    st.metric("Kadro Maliyeti", f"{harcanan:.1f}M", f"{len(kadro_df)}/10 Oyuncu", delta_color="off")
with col_k2:
    st.metric("Serbest Kasa", f"{kasa:.1f}M", "Kullanılabilir", delta_color="normal" if kasa >= 0 else "inverse")
with col_k3:
    if bc_toplam == 5 and fc_toplam == 5:
        st.metric("Mevki Dengesi", f"{bc_toplam} BC / {fc_toplam} FC", "✅ Kurala Uygun", delta_color="normal")
    else:
        st.metric("Mevki Dengesi", f"{bc_toplam} BC / {fc_toplam} FC", "⚠️ Hatalı Dağılım", delta_color="inverse")
with col_k4:
    st.metric("Sahada Maç (GW1)", f"{efektif_gw1} / 30", "Bu Hafta Aktif", delta_color="off")
with col_k5:
    st.metric("Sahada Maç (GW2)", f"{efektif_gw2} / 30", "Gelecek Hafta Aktif", delta_color="off")

st.markdown("---")

# --- AKTİF KADRO TABLOSU ---
st.subheader(f"📋 {aktif_menajer} Kadrosu ({len(kadro_df)} / 10)")

# Eksik Kadro, Mevki Uyarısı veya Takım Limiti Uyarıları
if len(kadro_df) < 10:
    st.warning(f"⚠️ Kadronuzda eksik var ({len(kadro_df)}/10). Yukarıdaki arama çubuğundan oyuncu ekleyebilirsiniz.")
elif bc_toplam != 5 or fc_toplam != 5:
    st.error(f"⚠️ **Mevki Uyarısı:** Kadronuzda **{bc_toplam} BC** ve **{fc_toplam} FC** bulunuyor. Kadro tam **5 BC** ve **5 FC** olmalıdır!")

if fazla_takimlar:
    for t_hatali in fazla_takimlar:
        st.error(f"🚫 **Takım Limiti Uyarısı:** Kadronuzda `{t_hatali}` takımından **{kadro_df['takim'].value_counts()[t_hatali]} oyuncu** var! Resmi kurala göre bir takımdan en fazla 2 oyuncu alınabilir.")

sort_col1, _ = st.columns([2, 4])
with sort_col1:
    sirala_kriter = st.selectbox(
        "Sıralama Ölçütü:",
        options=[
            "GW2 En Çok Çakışanlar (Önce Satılacaklar)",
            "Fiyat (Pahalıdan Ucuza)",
            "Fiyat (Ucuzdan Pahalıya)",
            "Mevki (BC Önce)",
            "Mevki (FC Önce)",
            f"GW{GW_NOW} Maç Sayısı (Çoktan Aza)",
            f"GW{GW_NEXT} Maç Sayısı (Çoktan Aza)"
        ],
        index=0
    )

if sirala_kriter == "GW2 En Çok Çakışanlar (Önce Satılacaklar)":
    kadro_df = kadro_df.sort_values(by=["gw2_israf", "fiyat"], ascending=[False, False])
elif sirala_kriter == "Fiyat (Pahalıdan Ucuza)":
    kadro_df = kadro_df.sort_values(by="fiyat", ascending=False)
elif sirala_kriter == "Fiyat (Ucuzdan Pahalıya)":
    kadro_df = kadro_df.sort_values(by="fiyat", ascending=True)
elif sirala_kriter == "Mevki (BC Önce)":
    kadro_df = kadro_df.sort_values(by=["pozisyon", "fiyat"], ascending=[True, False])
elif sirala_kriter == "Mevki (FC Önce)":
    kadro_df = kadro_df.sort_values(by=["pozisyon", "fiyat"], ascending=[False, False])
elif sirala_kriter == f"GW{GW_NOW} Maç Sayısı (Çoktan Aza)":
    kadro_df = kadro_df.sort_values(by=[f"gw{GW_NOW}_mac", "fiyat"], ascending=[False, False])
elif sirala_kriter == f"GW{GW_NEXT} Maç Sayısı (Çoktan Aza)":
    kadro_df = kadro_df.sort_values(by=[f"gw{GW_NEXT}_mac", "fiyat"], ascending=[False, False])

h_c1, h_c2, h_c3, h_c4, h_c5, h_c6, h_c7 = st.columns([2.3, 0.9, 1.0, 1.3, 1.3, 2.5, 0.7])
with h_c1: st.caption("**OYUNCU / TAKIM**")
with h_c2: st.caption("**MEVKİ**")
with h_c3: st.caption("**FİYAT**")
with h_c4: st.caption(f"**GW{GW_NOW} (B2B)**")
with h_c5: st.caption(f"**GW{GW_NEXT} (B2B)**")
with h_c6: st.caption("**DURUM / GW2 ÇAKIŞMA RAPORU**")
with h_c7: st.caption("**İŞLEM**")

st.divider()

for idx, p in kadro_df.iterrows():
    c1, c2, c3, c4, c5, c6, c7 = st.columns([2.3, 0.9, 1.0, 1.3, 1.3, 2.5, 0.7])
    
    with c1:
        st.markdown(f"**{p['isim']}**  \n`{p['takim']}`")
    with c2:
        st.markdown(f"**{p['pozisyon']}**")
    with c3:
        st.markdown(f"**{p['fiyat']}M**")
    with c4:
        b2b1_icon = "⚠️" if p[f"gw{GW_NOW}_b2b"] == "Var ⚠️" else ""
        st.markdown(f"**{p[f'gw{GW_NOW}_mac']}** {b2b1_icon}")
    with c5:
        b2b2_icon = "⚠️" if p[f"gw{GW_NEXT}_b2b"] == "Var ⚠️" else ""
        st.markdown(f"**{p[f'gw{GW_NEXT}_mac']}** {b2b2_icon}")
    with c6:
        alarmlar = []
        if p["durum"] == "Sakat": alarmlar.append("🔴 Sakat")
        elif "Şüpheli" in p["durum"]: alarmlar.append(f"🟡 {p['durum']}")
        if p.get("mac_kacirma") == "Sık Maç Kaçırıyor": alarmlar.append("⚠️ Devamsız")
        
        israf_sayisi = p.get("gw2_israf", 0)
        if israf_sayisi > 0:
            alarmlar.append(f"⚠️ **{israf_sayisi} Maçı Bench'te Çöp**")
        else:
            alarmlar.append("💎 **0 Çakışma (Tam Katkı)**")

        st.markdown(" | ".join(alarmlar))
        
    with c7:
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            if st.button("🔍", key=f"k_view_{idx}", help="Profili Aç"):
                oyuncu_popup(p["isim"])
        with b_col2:
            if st.button("❌", key=f"k_del_{idx}", help="Kadrodan Çıkar"):
                suanki_kadro_isimler.remove(p["isim"])
                kadroyu_kaydet()
                st.rerun()
            
    st.divider()

# --- GÜNLÜK MAÇ & SAHAYA ÇIKIŞ MATRİSİ ---
def matris_olustur(day_cols_list):
    matris_data = []
    for d_idx, day_col in enumerate(day_cols_list, start=1):
        maci_olanlar = kadro_df[kadro_df[day_col] > 0] if day_col in kadro_df.columns else pd.DataFrame()
        if maci_olanlar.empty:
            matris_data.append({"Gün": f"Day {d_idx}", "Maçı Olan": 0, "Sahaya Çıkan": "0/5 Boş ❌", "BC": "—", "FC": "—"})
            continue

        bc_oynayanlar = maci_olanlar[maci_olanlar["pozisyon"] == "BC"]["isim"].tolist()
        fc_oynayanlar = maci_olanlar[maci_olanlar["pozisyon"] == "FC"]["isim"].tolist()
        bc_count, fc_count = len(bc_oynayanlar), len(fc_oynayanlar)

        opt1 = min(bc_count, 3) + min(fc_count, 2)
        opt2 = min(bc_count, 2) + min(fc_count, 3)
        sahaya_cikan = min(5, max(opt1, opt2))

        durum_badge = f"{sahaya_cikan}/5 Dolu ✅" if sahaya_cikan == 5 else f"{sahaya_cikan}/5 Eksik ⚠️"
        bc_kisalar = [ad.split()[-1] for ad in bc_oynayanlar]
        fc_kisalar = [ad.split()[-1] for ad in fc_oynayanlar]

        matris_data.append({
            "Gün": f"Day {d_idx}",
            "Maçı Olan": bc_count + fc_count,
            "Sahaya Çıkan": durum_badge,
            "BC Oyuncuları": ", ".join(bc_kisalar) if bc_kisalar else "—",
            "FC Oyuncuları": ", ".join(fc_kisalar) if fc_kisalar else "—"
        })
    return pd.DataFrame(matris_data)

with st.expander("📅 Günlük Maç Dağılımı ve Saha Doluluk Matrisi", expanded=True):
    tab_gw1, tab_gw2 = st.tabs(["📅 Bu Hafta (Gameweek 1)", "📅 Gelecek Hafta (Gameweek 2)"])
    with tab_gw1:
        st.dataframe(matris_olustur(hesaplayici.DAY_COLS_GW1), use_container_width=True, hide_index=True)
    with tab_gw2:
        st.dataframe(matris_olustur(hesaplayici.DAY_COLS_GW2), use_container_width=True, hide_index=True)

st.markdown("---")

# --- TRANSFER SİMÜLATÖRÜ ---
st.subheader("🔄 Akıllı Transfer Simülatörü")

if len(kadro_df) != 10:
    st.info("Transfer simülasyonu için kadronuzda tam 10 oyuncu bulunmalıdır.")
elif bc_toplam != 5 or fc_toplam != 5:
    st.error("Transfer simülatörünü çalıştırmadan önce kadronuzu 5 BC ve 5 FC kuralına uygun hale getiriniz.")
elif fazla_takimlar:
    st.error("Transfer simülatörünü çalıştırmadan önce aynı takımdan en fazla 2 oyuncu kuralını sağlayınız.")
else:
    sim_gw_col1, _ = st.columns([2, 3])
    with sim_gw_col1:
        hedef_gw = st.radio("Optimizasyon Hedefi:", [f"Bu Hafta (GW{GW_NOW})", f"Gelecek Hafta (GW{GW_NEXT})"], horizontal=True)
        aktif_hedef_num = GW_NOW if "GW1" in hedef_gw else GW_NEXT

    satilacaklar = st.multiselect(
        "Takımdan Çıkarmak İstediğiniz Oyuncular (Max 2):",
        options=suanki_kadro_isimler,
        max_selections=2
    )

    if st.button("En İyi Alternatifleri Getir 🚀"):
        if not satilacaklar:
            st.info("Lütfen takımdan satmak istediğiniz en az bir oyuncu seçin.")
        else:
            oneriler = hesaplayici.transferleri_hesapla(df, kadro_df, satilacaklar, kasa, suanki_kadro_isimler, aktif_gw=aktif_hedef_num)
            if oneriler:
                st.session_state["son_oneriler"] = oneriler
                st.session_state["aktif_satilanlar"] = satilacaklar
            else:
                st.session_state.pop("son_oneriler", None)
                st.error("Bütçe, mevki veya takım sınırına uygun alternatif bulunamadı!")

    if "son_oneriler" in st.session_state:
        st.success("Alternatifler:")
        for idx, o in enumerate(st.session_state["son_oneriler"], start=1):
            c_yazi, c_butonlar = st.columns([3, 2])
            with c_yazi:
                st.markdown(f"**#{idx} {o['baslik']}**")
                st.caption(f"🔴 **Satılan:** {o['satilan_dokum']} (+{o['satilan_gelir']}M) | "
                           f"🟢 **Alınan:** {o['gelen_dokum']} (-{o['gelen_maliyet']}M) | "
                           f"💵 **Kalan Kasa:** **{o['kalan_butce']}M**")
            
            with c_butonlar:
                btn_cols = st.columns(len(o.get("isimler", [])) + 1)
                for b_idx, p_name in enumerate(o.get("isimler", [])):
                    with btn_cols[b_idx]:
                        kisa_ad = p_name.split()[-1]
                        if st.button(f"🔍 {kisa_ad}", key=f"sim_view_{idx}_{b_idx}"):
                            oyuncu_popup(p_name)
                
                with btn_cols[-1]:
                    if st.button("✅ Uygula", key=f"apply_{idx}", help="Bu transferi doğrudan kadrona uygula"):
                        satilan_liste = st.session_state.get("aktif_satilanlar", satilacaklar)
                        yeni_liste = [n for n in suanki_kadro_isimler if n not in satilan_liste]
                        yeni_liste.extend(o["isimler"])
                        st.session_state[f"kadro_{aktif_menajer}"] = yeni_liste
                        kadroyu_kaydet()
                        st.session_state.pop("son_oneriler", None)
                        st.success("Transfer kadroya başarıyla uygulandı!")
                        st.rerun()