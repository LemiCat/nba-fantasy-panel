import json
import os
import streamlit as st
import pandas as pd
import hesaplayici
import motor

st.set_page_config(
    page_title="NBA Fantasy Simulator", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- SIFIR EMOJI - GELİŞMİŞ NBA ARAYÜZ CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background-color: #090d16;
        color: #e2e8f0;
    }
    
    /* Header Alanı */
    .nba-header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 4px 0 16px 0;
        border-bottom: 1px solid #1e293b;
        margin-bottom: 20px;
    }
    .nba-brand {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .nba-title-text {
        font-size: 1.85rem;
        font-weight: 900;
        letter-spacing: 0.5px;
        color: #ffffff;
        margin: 0;
        line-height: 1.1;
    }
    .nba-subtitle-text {
        font-size: 0.72rem;
        color: #64748b;
        font-weight: 700;
        letter-spacing: 1px;
    }

    /* Scoreboard Metrik Kartları */
    .metric-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }
    .metric-label {
        font-size: 0.70rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #94a3b8;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.35rem;
        font-weight: 900;
        color: #f8fafc;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.74rem;
        color: #64748b;
        margin-top: 4px;
        font-weight: 600;
    }
    .metric-sub.success { color: #10b981; }
    .metric-sub.danger { color: #ef4444; }

    /* Mevki Renkleri (BC Mavi, FC Turuncu) */
    .badge-bc {
        background: rgba(56, 189, 248, 0.16);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.4);
        font-weight: 800;
        font-size: 0.72rem;
        padding: 3px 8px;
        border-radius: 6px;
    }
    .badge-fc {
        background: rgba(251, 146, 60, 0.16);
        color: #fb923c;
        border: 1px solid rgba(251, 146, 60, 0.4);
        font-weight: 800;
        font-size: 0.72rem;
        padding: 3px 8px;
        border-radius: 6px;
    }

    /* Durum Rozetleri */
    .badge-out { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); font-weight:700; font-size:0.72rem; padding:3px 8px; border-radius:6px; }
    .badge-dtd { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); font-weight:700; font-size:0.72rem; padding:3px 8px; border-radius:6px; }
    .badge-active { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); font-weight:700; font-size:0.72rem; padding:3px 8px; border-radius:6px; }
    .badge-b2b { background: rgba(234, 88, 12, 0.15); color: #fb923c; border: 1px solid rgba(234, 88, 12, 0.3); font-weight:700; font-size:0.72rem; padding:3px 8px; border-radius:6px; }
    .badge-waste { background: rgba(239, 68, 68, 0.12); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.25); font-weight:700; font-size:0.72rem; padding:3px 8px; border-radius:6px; }
    .badge-clean { background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.25); font-weight:700; font-size:0.72rem; padding:3px 8px; border-radius:6px; }

    /* Buton Renklendirmeleri */
    .btn-detay > button {
        background-color: #0284c7 !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 0.75rem !important;
        padding: 4px 8px !important;
    }
    .btn-detay > button:hover {
        background-color: #0369a1 !important;
    }
    .btn-cikar > button {
        background-color: #991b1b !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 0.75rem !important;
        padding: 4px 8px !important;
    }
    .btn-cikar > button:hover {
        background-color: #7f1d1d !important;
    }
    .btn-guncelle > button {
        background-color: #1e3a8a !important;
        color: #60a5fa !important;
        border: 1px solid #2563eb !important;
        font-weight: 800 !important;
        font-size: 0.78rem !important;
        letter-spacing: 0.5px !important;
    }

    /* Bütçe Özeti Kutusu */
    .budget-info-box {
        background: #111827;
        border: 1px solid #1e293b;
        border-left: 4px solid #38bdf8;
        border-radius: 8px;
        padding: 10px 16px;
        margin: 12px 0 16px 0;
        font-size: 0.88rem;
    }
</style>
""", unsafe_allow_html=True)

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

# --- 1. VERİ YÜKLEME ---
if not os.path.exists("oyuncular.csv"):
    with st.spinner("NBA verileri aliniyor..."):
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
            if not profiller: profiller = ["Bilal"]
    except Exception:
        profiller = ["Bilal"]
else:
    profiller = ["Bilal"]

default_names = [
    "Tyrese Maxey", "Jordan Poole", "Ajay Mitchell", "Tre Mann", "Nikola Topic",
    "Joel Embiid", "Zion Williamson", "Walker Kessler", "Jusuf Nurkic", "Tolu Smith"
]

# --- HEADER BÖLÜMÜ (NBA LOGOSU İLE) ---
c_head, c_mgr, c_del, c_sync = st.columns([2.6, 1.4, 0.4, 0.8])
with c_head:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:14px; padding:2px 0;">
        <img src="https://cdn.nba.com/logos/leagues/logo-nba.svg" height="42" style="display:inline-block; vertical-align:middle;">
        <div>
            <h1 class="nba-title-text">NBA FANTASY SIMULATOR</h1>
            <div class="nba-subtitle-text">KADRO VE FIKSTUR OPTIMIZASYON MERKEZI</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c_mgr:
    secilen_profil = st.selectbox(
        "Menajer:",
        options=profiller + ["+ Yeni Menajer Ekle..."],
        index=0,
        label_visibility="collapsed"
    )
    if secilen_profil == "+ Yeni Menajer Ekle...":
        yeni_ad = st.text_input("Yeni Isim:", placeholder="Orn: Mehmet")
        if st.button("Kaydet", use_container_width=True):
            if yeni_ad and yeni_ad not in profiller:
                profiller.append(yeni_ad)
                with open(PROFILLER_DOSYASI, "w", encoding="utf-8") as f:
                    json.dump(profiller, f, ensure_ascii=False, indent=2)
                st.rerun()

with c_del:
    if secilen_profil != "+ Yeni Menajer Ekle..." and len(profiller) > 1:
        if st.button("Sil", help=f"'{secilen_profil}' menajerini ve kadrosunu sil", use_container_width=True):
            profiller.remove(secilen_profil)
            with open(PROFILLER_DOSYASI, "w", encoding="utf-8") as f:
                json.dump(profiller, f, ensure_ascii=False, indent=2)
            k_file = f"kadro_{secilen_profil.lower()}.json"
            if os.path.exists(k_file):
                os.remove(k_file)
            st.rerun()

with c_sync:
    st.markdown('<div class="btn-guncelle">', unsafe_allow_html=True)
    if st.button("GUNCELLE", help="NBA API'sinden en guncel verileri ceker", use_container_width=True):
        with st.spinner("Guncelleniyor..."):
            df = motor.verileri_guncelle()
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

aktif_menajer = profiller[0] if secilen_profil == "+ Yeni Menajer Ekle..." else secilen_profil
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

kadro_df_gecici = df[df["isim"].isin(suanki_kadro_isimler)]
takim_sayilari = kadro_df_gecici["takim"].value_counts().to_dict()

# --- OYUNCU DETAY POP-UP MODAL ---
@st.dialog("Oyuncu Profili", width="large")
def oyuncu_popup(isim):
    p = df[df["isim"] == isim].iloc[0]
    p_code = str(p.get("code", "")).replace(".0", "").strip()
    t_code = p.get("takim", "")
    pos = p.get("pozisyon", "FC")
    
    foto_url = f"https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{p_code}.png" if p_code else None
    logo_url = TEAM_LOGOS.get(t_code, None)

    c_img, c_info, c_status = st.columns([1.8, 3.2, 2])
    
    with c_img:
        if foto_url:
            st.image(foto_url, width=170)
        else:
            st.markdown("*Fotograf Yok*")
            
    with c_info:
        st.markdown(f"<h2 style='margin:0 0 6px 0;'>{p['isim']}</h2>", unsafe_allow_html=True)
        pos_badge = f"<span class='badge-bc'>BC</span>" if pos == "BC" else f"<span class='badge-fc'>FC</span>"
        st.markdown(f"{pos_badge} <strong style='font-size:1.1rem; margin-left:8px;'>{p['fiyat']}M</strong>", unsafe_allow_html=True)
        st.write("")
        if logo_url:
            st.image(logo_url, width=65)
            
    with c_status:
        st.write("")
        if p["durum"] == "Sakat":
            st.markdown("<span class='badge-out'>OUT - SAKAT</span>", unsafe_allow_html=True)
        elif "Şüpheli" in p["durum"]:
            st.markdown(f"<span class='badge-dtd'>SUPHELI - {p['durum']}</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-active'>ACTIVE - SAGLIKLI</span>", unsafe_allow_html=True)
            
        st.write("")
        if p.get("mac_kacirma") == "Sık Maç Kaçırıyor":
            st.markdown("<span class='badge-waste'>DEVAMSIZLIK RISKI</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge-clean'>ISTIKRARLI</span>", unsafe_allow_html=True)

    st.markdown("---")
    
    btn_c1, _ = st.columns([2.5, 2])
    with btn_c1:
        if isim in suanki_kadro_isimler:
            if st.button("Bu Oyuncuyu Kadrodan Cikar", use_container_width=True):
                suanki_kadro_isimler.remove(isim)
                kadroyu_kaydet()
                st.rerun()
        else:
            oyuncunun_takimi = p["takim"]
            takimdaki_mevcut_sayi = takim_sayilari.get(oyuncunun_takimi, 0)
            
            if len(suanki_kadro_isimler) >= 10:
                st.caption("Kadro dolu (10/10). Eklemek icin birini cikarmalisiniz.")
            elif takimdaki_mevcut_sayi >= 2:
                st.error(f"Takim Kotasi Dolu: Zaten 2 {oyuncunun_takimi} oyuncusu var.")
            else:
                if st.button("Bu Oyuncuyu Kadroya Ekle", use_container_width=True):
                    suanki_kadro_isimler.append(isim)
                    kadroyu_kaydet()
                    st.rerun()

    st.markdown("---")
    st.markdown("##### FIKSTUR VE B2B YUKU")
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        st.metric(label=f"Bu Hafta (GW{GW_NOW})", value=f"{p[f'gw{GW_NOW}_mac']} Mac", delta=f"B2B: {p[f'gw{GW_NOW}_b2b']}", delta_color="off")
    with f_col2:
        st.metric(label=f"Gelecek Hafta (GW{GW_NEXT})", value=f"{p[f'gw{GW_NEXT}_mac']} Mac", delta=f"B2B: {p[f'gw{GW_NEXT}_b2b']}", delta_color="off")

    st.markdown("---")
    st.markdown("##### SEZON VE FORM KARSILASTIRMASI (SON 5 MAC)")
    
    def format_delta(sezon_val, form_val):
        if sezon_val == 0 and form_val == 0: return "-"
        fark = round(form_val - sezon_val, 1)
        return f"+{fark}" if fark > 0 else f"{fark}" if fark < 0 else "0.0"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sure (Dk)", f"{p.get('f_dakika', 0.0):.1f}", delta=format_delta(p.get("dakika", 0.0), p.get("f_dakika", 0.0)))
    c2.metric("Puan", f"{p.get('f_ort_puan', 0.0):.1f}", delta=format_delta(p.get("ort_puan", 0.0), p.get("f_ort_puan", 0.0)))
    c3.metric("Sayi", f"{p.get('f_sayi', 0.0):.1f}", delta=format_delta(p.get("sayi", 0.0), p.get("f_sayi", 0.0)))
    c4.metric("Asist", f"{p.get('f_asist', 0.0):.1f}", delta=format_delta(p.get("asist", 0.0), p.get("f_asist", 0.0)))

    c5, c6, c7 = st.columns(3)
    c5.metric("Ribaund", f"{p.get('f_ribaund', 0.0):.1f}", delta=format_delta(p.get("ribaund", 0.0), p.get("f_ribaund", 0.0)))
    c6.metric("Top Calma", f"{p.get('f_top_calma', 0.0):.1f}", delta=format_delta(p.get("top_calma", 0.0), p.get("f_top_calma", 0.0)))
    c7.metric("Blok", f"{p.get('f_blok', 0.0):.1f}", delta=format_delta(p.get("blok", 0.0), p.get("f_blok", 0.0)))

# --- TEK TIKLA ARAMA & OTOMATIK POP-UP (BUTONSUZ) ---
secilen_oyuncu = st.selectbox(
    "Oyuncu Ara:",
    options=["--- Oyuncu Ara veya Sec ---"] + all_names,
    index=0,
    label_visibility="collapsed"
)

if secilen_oyuncu != "--- Oyuncu Ara veya Sec ---":
    oyuncu_popup(secilen_oyuncu)

st.write("")

kadro_df = df[df["isim"].isin(suanki_kadro_isimler)].copy()
bc_toplam = len(kadro_df[kadro_df["pozisyon"] == "BC"])
fc_toplam = len(kadro_df[kadro_df["pozisyon"] == "FC"])
fazla_takimlar = [t for t, c in kadro_df["takim"].value_counts().items() if c > 2]

# Dinamik Gün Kolonları
day_cols_gw1 = hesaplayici.get_day_cols(df, 1)
day_cols_gw2 = hesaplayici.get_day_cols(df, 2)

# GW2 İsraf Hesaplama
oyuncu_israf = {isim: 0 for isim in suanki_kadro_isimler}
if len(kadro_df) == 10:
    for day_col in day_cols_gw2:
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

# --- 3. SCOREBOARD METRİK ŞERİDİ ---
harcanan = round(kadro_df["fiyat"].sum(), 1)
kasa = round(100.0 - harcanan, 1)
efektif_gw1 = hesaplayici.hesapla_efektif_mac(kadro_df, day_cols_gw1) if len(kadro_df) == 10 else 0
efektif_gw2 = hesaplayici.hesapla_efektif_mac(kadro_df, day_cols_gw2) if len(kadro_df) == 10 else 0

m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Kadro Maliyeti</div>
        <div class="metric-value">{harcanan:.1f}M</div>
        <div class="metric-sub">{len(kadro_df)} / 10 Oyuncu</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    kasa_cls = "success" if kasa >= 0 else "danger"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Kullanilabilir Kasa</div>
        <div class="metric-value">{kasa:.1f}M</div>
        <div class="metric-sub {kasa_cls}">{'Butce Dengeli' if kasa >= 0 else 'Butce Asildi'}</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    mevki_ok = (bc_toplam == 5 and fc_toplam == 5)
    mevki_cls = "success" if mevki_ok else "danger"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Mevki Dengesi</div>
        <div class="metric-value"><span style="color:#38bdf8;">{bc_toplam} BC</span> / <span style="color:#fb923c;">{fc_toplam} FC</span></div>
        <div class="metric-sub {mevki_cls}">{'5 BC - 5 FC Tam' if mevki_ok else 'Dengesiz Dagitim'}</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Sahada Mac (GW1)</div>
        <div class="metric-value">{efektif_gw1} / {len(day_cols_gw1)*5}</div>
        <div class="metric-sub">Bu Hafta Aktif</div>
    </div>
    """, unsafe_allow_html=True)

with m5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Sahada Mac (GW2)</div>
        <div class="metric-value">{efektif_gw2} / {len(day_cols_gw2)*5}</div>
        <div class="metric-sub">Gelecek Hafta Aktif</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# --- 4. KADRO YÖNETİMİ VE TABLO ---
st.markdown(f"#### {aktif_menajer.upper()} KADROSU")

if len(kadro_df) < 10:
    st.warning(f"Kadronuzda {10 - len(kadro_df)} oyuncu eksik.")
elif bc_toplam != 5 or fc_toplam != 5:
    st.error(f"Mevki Hatasi: Kadro 5 BC ve 5 FC olmalidir (Su an: {bc_toplam} BC / {fc_toplam} FC).")

if fazla_takimlar:
    for t_hatali in fazla_takimlar:
        st.error(f"Takim Limiti Asimi: {t_hatali} takimindan {kadro_df['takim'].value_counts()[t_hatali]} oyuncu var (Max 2).")

sort_col1, _ = st.columns([2.5, 3.5])
with sort_col1:
    sirala_kriter = st.selectbox(
        "Sirala:",
        options=[
            "GW2 En Cok Cakisanlar (Once Satilacaklar)",
            "Fiyat (Pahalidan Ucuza)",
            "Fiyat (Ucuzdan Pahaliya)",
            "Mevki (BC Once)",
            "Mevki (FC Once)",
            f"GW{GW_NOW} Mac Sayisi (Coktan Aza)",
            f"GW{GW_NEXT} Mac Sayisi (Coktan Aza)"
        ],
        index=0,
        label_visibility="collapsed"
    )

if sirala_kriter == "GW2 En Cok Cakisanlar (Once Satilacaklar)":
    kadro_df = kadro_df.sort_values(by=["gw2_israf", "fiyat"], ascending=[False, False])
elif sirala_kriter == "Fiyat (Pahalidan Ucuza)":
    kadro_df = kadro_df.sort_values(by="fiyat", ascending=False)
elif sirala_kriter == "Fiyat (Ucuzdan Pahaliya)":
    kadro_df = kadro_df.sort_values(by="fiyat", ascending=True)
elif sirala_kriter == "Mevki (BC Once)":
    kadro_df = kadro_df.sort_values(by=["pozisyon", "fiyat"], ascending=[True, False])
elif sirala_kriter == "Mevki (FC Once)":
    kadro_df = kadro_df.sort_values(by=["pozisyon", "fiyat"], ascending=[False, False])
elif sirala_kriter == f"GW{GW_NOW} Mac Sayisi (Coktan Aza)":
    kadro_df = kadro_df.sort_values(by=[f"gw{GW_NOW}_mac", "fiyat"], ascending=[False, False])
elif sirala_kriter == f"GW{GW_NEXT} Mac Sayisi (Coktan Aza)":
    kadro_df = kadro_df.sort_values(by=[f"gw{GW_NEXT}_mac", "fiyat"], ascending=[False, False])

h1, h2, h3, h4, h5, h6, h7 = st.columns([2.5, 0.8, 1.0, 1.1, 1.1, 2.4, 1.1])
with h1: st.caption("OYUNCU")
with h2: st.caption("MEVKI")
with h3: st.caption("FIYAT")
with h4: st.caption(f"GW{GW_NOW}")
with h5: st.caption(f"GW{GW_NEXT}")
with h6: st.caption("DURUM / GW2 ISRAF")
with h7: st.caption("ISLEM")

st.markdown("<hr style='margin:2px 0 10px 0; border-color:#1e293b;'>", unsafe_allow_html=True)

for idx, p in kadro_df.iterrows():
    c1, c2, c3, c4, c5, c6, c7 = st.columns([2.5, 0.8, 1.0, 1.1, 1.1, 2.4, 1.1])
    
    with c1:
        t_logo = TEAM_LOGOS.get(p['takim'], "")
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:8px;">
            <img src="{t_logo}" width="22" style="vertical-align:middle;">
            <strong>{p['isim']}</strong>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        pos_badge = f"<span class='badge-bc'>BC</span>" if p['pozisyon'] == "BC" else f"<span class='badge-fc'>FC</span>"
        st.markdown(pos_badge, unsafe_allow_html=True)
    with c3:
        st.markdown(f"**{p['fiyat']}M**")
    with c4:
        b2b1_badge = f"<span class='badge-b2b'>B2B</span>" if p[f"gw{GW_NOW}_b2b"] == "Var" else ""
        st.markdown(f"**{p[f'gw{GW_NOW}_mac']}** {b2b1_badge}", unsafe_allow_html=True)
    with c5:
        b2b2_badge = f"<span class='badge-b2b'>B2B</span>" if p[f"gw{GW_NEXT}_b2b"] == "Var" else ""
        st.markdown(f"**{p[f'gw{GW_NEXT}_mac']}** {b2b2_badge}", unsafe_allow_html=True)
    with c6:
        rozetler = []
        if p["durum"] == "Sakat":
            rozetler.append("<span class='badge-out'>OUT</span>")
        elif "Şüpheli" in p["durum"]:
            rozetler.append("<span class='badge-dtd'>SUPHELI</span>")
        
        israf_sayisi = p.get("gw2_israf", 0)
        if israf_sayisi > 0:
            rozetler.append(f"<span class='badge-waste'>{israf_sayisi} BENCH</span>")
        else:
            rozetler.append("<span class='badge-clean'>TAM KATKI</span>")

        st.markdown(" ".join(rozetler), unsafe_allow_html=True)
        
    with c7:
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            st.markdown('<div class="btn-detay">', unsafe_allow_html=True)
            if st.button("Detay", key=f"k_view_{idx}", help="Profili Ac", use_container_width=True):
                oyuncu_popup(p["isim"])
            st.markdown('</div>', unsafe_allow_html=True)
        with b_col2:
            st.markdown('<div class="btn-cikar">', unsafe_allow_html=True)
            if st.button("Cikar", key=f"k_del_{idx}", help="Kadrodan Cikar", use_container_width=True):
                suanki_kadro_isimler.remove(p["isim"])
                kadroyu_kaydet()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
    st.markdown("<hr style='margin:4px 0 6px 0; border-color:#172033;'>", unsafe_allow_html=True)

st.write("")

# --- 5. GÜNLÜK MAÇ & SAHAYA ÇIKIŞ MATRİSİ (SABİT AÇIK & RENK SKALALI) ---
def renkli_doluluk_badge(sahaya_cikan):
    renk_map = {
        5: ("#059669", "#ecfdf5"),  # Tam Zümrüt Yeşili
        4: ("#65a30d", "#f7fee7"),  # Fıstık / Sarımtırak Yeşil
        3: ("#ca8a04", "#fefce8"),  # Sarı
        2: ("#ea580c", "#fff7ed"),  # Turuncu
        1: ("#dc2626", "#fef2f2"),  # Kıpkırmızı
        0: ("#18181b", "#71717a")   # Siyah / Kömür
    }
    bg, fg = renk_map.get(sahaya_cikan, ("#18181b", "#ffffff"))
    return f"""<span style="background-color:{bg}; color:{fg}; font-weight:900; font-size:0.8rem; padding:4px 10px; border-radius:6px; display:inline-block; text-align:center; min-width:44px;">{sahaya_cikan}/5</span>"""

def render_matris_html(day_cols_list):
    html = """
    <table style="width:100%; border-collapse:collapse; background:#0f172a; border-radius:8px; overflow:hidden; font-size:0.85rem;">
        <thead>
            <tr style="border-bottom:1px solid #1e293b; color:#94a3b8; text-align:left;">
                <th style="padding:10px 14px;">GUN</th>
                <th style="padding:10px 14px;">MACI OLAN</th>
                <th style="padding:10px 14px; text-align:center;">SAHA DOLULUK</th>
                <th style="padding:10px 14px;">BC OYUNCULARI</th>
                <th style="padding:10px 14px;">FC OYUNCULARI</th>
            </tr>
        </thead>
        <tbody>
    """
    for d_idx, day_col in enumerate(day_cols_list, start=1):
        maci_olanlar = kadro_df[kadro_df[day_col] > 0] if day_col in kadro_df.columns else pd.DataFrame()
        if maci_olanlar.empty:
            html += f"""
            <tr style="border-bottom:1px solid #172033;">
                <td style="padding:8px 14px; font-weight:700;">Day {d_idx}</td>
                <td style="padding:8px 14px; color:#64748b;">0</td>
                <td style="padding:8px 14px; text-align:center;">{renkli_doluluk_badge(0)}</td>
                <td style="padding:8px 14px; color:#475569;">-</td>
                <td style="padding:8px 14px; color:#475569;">-</td>
            </tr>
            """
            continue

        bc_oynayanlar = maci_olanlar[maci_olanlar["pozisyon"] == "BC"]["isim"].tolist()
        fc_oynayanlar = maci_olanlar[maci_olanlar["pozisyon"] == "FC"]["isim"].tolist()
        bc_count, fc_count = len(bc_oynayanlar), len(fc_oynayanlar)

        opt1 = min(bc_count, 3) + min(fc_count, 2)
        opt2 = min(bc_count, 2) + min(fc_count, 3)
        sahaya_cikan = min(5, max(opt1, opt2))

        bc_kisalar = [f"<span style='color:#38bdf8;'>{ad.split()[-1]}</span>" for ad in bc_oynayanlar]
        fc_kisalar = [f"<span style='color:#fb923c;'>{ad.split()[-1]}</span>" for ad in fc_oynayanlar]

        html += f"""
        <tr style="border-bottom:1px solid #172033;">
            <td style="padding:8px 14px; font-weight:700;">Day {d_idx}</td>
            <td style="padding:8px 14px; font-weight:700;">{bc_count + fc_count}</td>
            <td style="padding:8px 14px; text-align:center;">{renkli_doluluk_badge(sahaya_cikan)}</td>
            <td style="padding:8px 14px;">{', '.join(bc_kisalar) if bc_kisalar else '-'}</td>
            <td style="padding:8px 14px;">{', '.join(fc_kisalar) if fc_kisalar else '-'}</td>
        </tr>
        """
    html += "</tbody></table>"
    return html

st.markdown("#### GUNLUK MAC VE SAHA DAGILIM MATRISI")
tab_gw1, tab_gw2 = st.tabs(["Bu Hafta (GW1)", "Gelecek Hafta (GW2)"])
with tab_gw1:
    st.markdown(render_matris_html(day_cols_gw1), unsafe_allow_html=True)
with tab_gw2:
    st.markdown(render_matris_html(day_cols_gw2), unsafe_allow_html=True)

st.write("")

# --- 6. TRANSFER SİMÜLATÖRÜ (KOMPAKT & SEMBOLSÜZ/METİN BUTONLU) ---
st.markdown("#### AKILLI TRANSFER SIMULATORU")

if len(kadro_df) != 10:
    st.info("Transfer simulasyonu icin kadronuzda tam 10 oyuncu bulunmalidir.")
elif bc_toplam != 5 or fc_toplam != 5:
    st.error("Kadronuzu 5 BC ve 5 FC kuralina uygun hale getiriniz.")
elif fazla_takimlar:
    st.error("Ayni takimdan en fazla 2 oyuncu kuralini saglayiniz.")
else:
    sim_gw_col1, _ = st.columns([2.5, 3.5])
    with sim_gw_col1:
        hedef_gw = st.radio("Optimizasyon Hedefi:", [f"Bu Hafta (GW{GW_NOW})", f"Gelecek Hafta (GW{GW_NEXT})"], horizontal=True)
        aktif_hedef_num = GW_NOW if "GW1" in hedef_gw else GW_NEXT

    satilacaklar = st.multiselect(
        "Takimdan Cikarmak Istediginiz Oyuncular (Max 2):",
        options=suanki_kadro_isimler,
        max_selections=2
    )

    if st.button("Alternatifleri Hesapla"):
        if not satilacaklar:
            st.info("Lutfen en az bir oyuncu secin.")
        else:
            oneriler = hesaplayici.transferleri_hesapla(df, kadro_df, satilacaklar, kasa, suanki_kadro_isimler, aktif_gw=aktif_hedef_num)
            if oneriler:
                st.session_state["son_oneriler"] = oneriler
                st.session_state["aktif_satilanlar"] = satilacaklar
            else:
                st.session_state.pop("son_oneriler", None)
                st.error("Kriterlere uygun alternatif bulunamadi.")

    if "son_oneriler" in st.session_state:
        aktif_satilan_df = kadro_df[kadro_df["isim"].isin(st.session_state["aktif_satilanlar"])]
        satilan_gelir_toplam = aktif_satilan_df["fiyat"].sum()
        kullanilabilir_toplam = round(satilan_gelir_toplam + kasa, 1)
        satilan_isimler_str = " + ".join([f"{row['isim']} ({row['fiyat']}M)" for _, row in aktif_satilan_df.iterrows()])

        st.markdown(f"""
        <div class="budget-info-box">
            <strong>Transfer Butcesi Ozeti:</strong> Cikarilan: <strong>{satilan_isimler_str}</strong> (Gelir: <strong>+{satilan_gelir_toplam:.1f}M</strong>) 
            - Mevcut Kasa: <strong>{kasa:.1f}M</strong> - Toplam Harcanabilir Butce: <strong style="color:#38bdf8;">{kullanilabilir_toplam:.1f}M</strong>
        </div>
        """, unsafe_allow_html=True)

        for idx, o in enumerate(st.session_state["son_oneriler"], start=1):
            c_yazi, c_butonlar = st.columns([3.2, 1.8])
            with c_yazi:
                st.markdown(f"**#{idx} {o['baslik']}**")
                st.caption(f"Transfer Sonrasi Kalan Kasa: **{o['kalan_butce']}M**")
            
            with c_butonlar:
                btn_cols = st.columns(len(o.get("isimler", [])) + 1)
                for b_idx, p_name in enumerate(o.get("isimler", [])):
                    with btn_cols[b_idx]:
                        kisa_ad = p_name.split()[-1]
                        st.markdown('<div class="btn-detay">', unsafe_allow_html=True)
                        if st.button(kisa_ad, key=f"sim_view_{idx}_{b_idx}", use_container_width=True):
                            oyuncu_popup(p_name)
                        st.markdown('</div>', unsafe_allow_html=True)
                
                with btn_cols[-1]:
                    if st.button("Uygula", key=f"apply_{idx}", help="Transferi kadroya uygula", use_container_width=True):
                        satilan_liste = st.session_state.get("aktif_satilanlar", satilacaklar)
                        yeni_liste = [n for n in suanki_kadro_isimler if n not in satilan_liste]
                        yeni_liste.extend(o["isimler"])
                        st.session_state[f"kadro_{aktif_menajer}"] = yeni_liste
                        kadroyu_kaydet()
                        st.session_state.pop("son_oneriler", None)
                        st.rerun()