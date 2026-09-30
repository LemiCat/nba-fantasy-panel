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

# --- GELİŞMİŞ NBA DARK THEME CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background-color: #0a0e17;
        color: #e2e8f0;
    }
    
    .nba-header {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 6px 0 18px 0;
        border-bottom: 1px solid #1e293b;
        margin-bottom: 20px;
    }
    .nba-header-title {
        font-size: 1.75rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #ffffff, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .metric-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 14px 18px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .metric-card:hover {
        border-color: #374151;
        transform: translateY(-2px);
    }
    .metric-label {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #94a3b8;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.35rem;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1.2;
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 4px;
    }
    .metric-sub.success { color: #10b981; }
    .metric-sub.danger { color: #ef4444; }

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        letter-spacing: 0.3px;
    }
    .badge-out { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-dtd { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-active { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-b2b { background: rgba(234, 88, 12, 0.15); color: #fb923c; border: 1px solid rgba(234, 88, 12, 0.3); }
    .badge-waste { background: rgba(239, 68, 68, 0.12); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.25); }
    .badge-clean { background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.25); }
    .badge-pos { background: #1e293b; color: #cbd5e1; border: 1px solid #334155; font-size: 0.7rem; }

    .budget-info-box {
        background: #111827;
        border: 1px solid #1e293b;
        border-left: 4px solid #38bdf8;
        border-radius: 8px;
        padding: 10px 16px;
        margin: 12px 0 16px 0;
        font-size: 0.88rem;
    }

    div[data-testid="column"] button[kind="secondary"] {
        padding: 3px 6px !important;
        font-size: 0.75rem !important;
        min-height: 28px !important;
        line-height: 1 !important;
        border-radius: 6px !important;
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
    with st.spinner("NBA verileri alınıyor..."):
        df = motor.verileri_guncelle()
else:
    try:
        df = pd.read_csv("oyuncular.csv")
        if "code" not in df.columns:
            df = motor.verileri_guncelle()
    except Exception:
        df = motor.verileri_guncelle()

all_names = sorted(df["isim"].unique().tolist())

# --- 2. MENAJER PROFİL SİSTEMİ (EKLEME & SİLME) ---
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

# Header Bar & Menajer Kontrolü
c_head, c_mgr, c_del, c_sync = st.columns([2.5, 1.5, 0.4, 0.7])
with c_head:
    st.markdown("""
    <div class="nba-header">
        <span style="font-size:2rem;">🏀</span>
        <div>
            <h1 class="nba-header-title">NBA FANTASY KARAR DESTEK</h1>
            <span style="font-size:0.75rem; color:#64748b; font-weight:600;">CANLI KADRO VE FİKSTÜR OPTİMİZASYON MERKEZİ</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c_mgr:
    secilen_profil = st.selectbox(
        "Menajer:",
        options=profiller + ["➕ Yeni Menajer Ekle..."],
        index=0,
        label_visibility="collapsed"
    )
    if secilen_profil == "➕ Yeni Menajer Ekle...":
        yeni_ad = st.text_input("Yeni İsim:", placeholder="Örn: Mehmet")
        if st.button("Kaydet", use_container_width=True):
            if yeni_ad and yeni_ad not in profiller:
                profiller.append(yeni_ad)
                with open(PROFILLER_DOSYASI, "w", encoding="utf-8") as f:
                    json.dump(profiller, f, ensure_ascii=False, indent=2)
                st.rerun()

with c_del:
    if secilen_profil != "➕ Yeni Menajer Ekle..." and len(profiller) > 1:
        if st.button("🗑️", help=f"'{secilen_profil}' menajerini ve kadrosunu sil"):
            profiller.remove(secilen_profil)
            with open(PROFILLER_DOSYASI, "w", encoding="utf-8") as f:
                json.dump(profiller, f, ensure_ascii=False, indent=2)
            k_file = f"kadro_{secilen_profil.lower()}.json"
            if os.path.exists(k_file):
                os.remove(k_file)
            st.rerun()

with c_sync:
    if st.button("🔄 Güncelle", help="NBA API'sinden en güncel verileri çeker", use_container_width=True):
        with st.spinner("Güncelleniyor..."):
            df = motor.verileri_guncelle()
            st.success("Hazır!")
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

kadro_df_gecici = df[df["isim"].isin(suanki_kadro_isimler)]
takim_sayilari = kadro_df_gecici["takim"].value_counts().to_dict()

# --- OYUNCU DETAY POP-UP MODAL ---
@st.dialog("Oyuncu Profili", width="large")
def oyuncu_popup(isim):
    p = df[df["isim"] == isim].iloc[0]
    p_code = str(p.get("code", "")).replace(".0", "").strip()
    t_code = p.get("takim", "")
    
    foto_url = f"https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{p_code}.png" if p_code else None
    logo_url = TEAM_LOGOS.get(t_code, None)

    c_img, c_info, c_status = st.columns([1.8, 3.2, 2])
    
    with c_img:
        if foto_url:
            st.image(foto_url, width=170)
        else:
            st.markdown("👤 *Fotoğraf Yok*")
            
    with c_info:
        st.markdown(f"<h2 style='margin:0 0 6px 0;'>{p['isim']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<span class='badge badge-pos'>{p['pozisyon']}</span> <strong style='font-size:1.1rem; margin-left:8px;'>{p['fiyat']}M</strong>", unsafe_allow_html=True)
        st.write("")
        if logo_url:
            st.image(logo_url, width=65)
            
    with c_status:
        st.write("")
        if p["durum"] == "Sakat":
            st.markdown("<span class='badge badge-out'>OUT • SAKAT</span>", unsafe_allow_html=True)
        elif "Şüpheli" in p["durum"]:
            st.markdown(f"<span class='badge badge-dtd'>ŞÜPHELİ • {p['durum']}</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge badge-active'>ACTIVE • SAĞLIKLI</span>", unsafe_allow_html=True)
            
        st.write("")
        if p.get("mac_kacirma") == "Sık Maç Kaçırıyor":
            st.markdown("<span class='badge badge-waste'>DEVAMSIZLIK RİSKİ</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge badge-clean'>İSTİKRARLI</span>", unsafe_allow_html=True)

    st.markdown("---")
    
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
                st.error(f"🚫 Takım Kotası Dolu: Zaten 2 {oyuncunun_takimi} oyuncusu var.")
            else:
                if st.button("🟢 Bu Oyuncuyu Kadroya Ekle", use_container_width=True):
                    suanki_kadro_isimler.append(isim)
                    kadroyu_kaydet()
                    st.rerun()

    st.markdown("---")
    st.markdown("##### 📅 FİKSTÜR VE B2B YÜKÜ")
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        st.metric(label=f"Bu Hafta (GW{GW_NOW})", value=f"{p[f'gw{GW_NOW}_mac']} Maç", delta=f"B2B: {p[f'gw{GW_NOW}_b2b']}", delta_color="off")
    with f_col2:
        st.metric(label=f"Gelecek Hafta (GW{GW_NEXT})", value=f"{p[f'gw{GW_NEXT}_mac']} Maç", delta=f"B2B: {p[f'gw{GW_NEXT}_b2b']}", delta_color="off")

    st.markdown("---")
    st.markdown("##### 📊 SEZON VE FORM KARŞILAŞTIRMASI (SON 5 MAÇ)")
    
    def format_delta(sezon_val, form_val):
        if sezon_val == 0 and form_val == 0: return "—"
        fark = round(form_val - sezon_val, 1)
        return f"+{fark}" if fark > 0 else f"{fark}" if fark < 0 else "0.0"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Süre (Dk)", f"{p.get('f_dakika', 0.0):.1f}", delta=format_delta(p.get("dakika", 0.0), p.get("f_dakika", 0.0)))
    c2.metric("Puan", f"{p.get('f_ort_puan', 0.0):.1f}", delta=format_delta(p.get("ort_puan", 0.0), p.get("f_ort_puan", 0.0)))
    c3.metric("Sayı", f"{p.get('f_sayi', 0.0):.1f}", delta=format_delta(p.get("sayi", 0.0), p.get("f_sayi", 0.0)))
    c4.metric("Asist", f"{p.get('f_asist', 0.0):.1f}", delta=format_delta(p.get("asist", 0.0), p.get("f_asist", 0.0)))

    c5, c6, c7 = st.columns(3)
    c5.metric("Ribaund", f"{p.get('f_ribaund', 0.0):.1f}", delta=format_delta(p.get("ribaund", 0.0), p.get("f_ribaund", 0.0)))
    c6.metric("Top Çalma", f"{p.get('f_top_calma', 0.0):.1f}", delta=format_delta(p.get("top_calma", 0.0), p.get("f_top_calma", 0.0)))
    c7.metric("Blok", f"{p.get('f_blok', 0.0):.1f}", delta=format_delta(p.get("blok", 0.0), p.get("f_blok", 0.0)))

# --- ÜST OYUNCU ARAMA ---
search_col1, search_col2 = st.columns([5, 1])
with search_col1:
    secilen_oyuncu = st.selectbox(
        "Oyuncu Ara:",
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

st.write("")

kadro_df = df[df["isim"].isin(suanki_kadro_isimler)].copy()
bc_toplam = len(kadro_df[kadro_df["pozisyon"] == "BC"])
fc_toplam = len(kadro_df[kadro_df["pozisyon"] == "FC"])
fazla_takimlar = [t for t, c in kadro_df["takim"].value_counts().items() if c > 2]

# --- GW2 İSRAF HESAPLAMA ---
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

# --- 3. SCOREBOARD METRİK ŞERİDİ ---
harcanan = round(kadro_df["fiyat"].sum(), 1)
kasa = round(100.0 - harcanan, 1)
efektif_gw1 = hesaplayici.hesapla_efektif_mac(kadro_df, hesaplayici.DAY_COLS_GW1) if len(kadro_df) == 10 else 0
efektif_gw2 = hesaplayici.hesapla_efektif_mac(kadro_df, hesaplayici.DAY_COLS_GW2) if len(kadro_df) == 10 else 0

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
        <div class="metric-label">Kullanılabilir Kasa</div>
        <div class="metric-value">{kasa:.1f}M</div>
        <div class="metric-sub {kasa_cls}">{'Bütçe Dengeli' if kasa >= 0 else 'Bütçe Aşıldı'}</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    mevki_ok = (bc_toplam == 5 and fc_toplam == 5)
    mevki_cls = "success" if mevki_ok else "danger"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Mevki Dengesi</div>
        <div class="metric-value">{bc_toplam} BC / {fc_toplam} FC</div>
        <div class="metric-sub {mevki_cls}">{'5 BC - 5 FC Tam' if mevki_ok else 'Dengesiz Dağılım'}</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Sahada Maç (GW1)</div>
        <div class="metric-value">{efektif_gw1} / 30</div>
        <div class="metric-sub">Bu Hafta Aktif</div>
    </div>
    """, unsafe_allow_html=True)

with m5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Sahada Maç (GW2)</div>
        <div class="metric-value">{efektif_gw2} / 30</div>
        <div class="metric-sub">Gelecek Hafta Aktif</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# --- 4. KADRO YÖNETİMİ VE TABLO ---
st.markdown(f"#### 📋 {aktif_menajer.upper()} KADROSU")

if len(kadro_df) < 10:
    st.warning(f"Kadronuzda {10 - len(kadro_df)} oyuncu eksik.")
elif bc_toplam != 5 or fc_toplam != 5:
    st.error(f"Mevki Dağılımı Hatası: Kadro 5 BC ve 5 FC olmalıdır (Şu an: {bc_toplam} BC / {fc_toplam} FC).")

if fazla_takimlar:
    for t_hatali in fazla_takimlar:
        st.error(f"Takım Limiti Aşımı: {t_hatali} takımından {kadro_df['takim'].value_counts()[t_hatali]} oyuncu var (Max 2).")

sort_col1, _ = st.columns([2.5, 3.5])
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
        index=0,
        label_visibility="collapsed"
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

h1, h2, h3, h4, h5, h6, h7 = st.columns([2.5, 0.8, 1.0, 1.1, 1.1, 2.4, 1.1])
with h1: st.caption("OYUNCU")
with h2: st.caption("MEVKİ")
with h3: st.caption("FİYAT")
with h4: st.caption(f"GW{GW_NOW}")
with h5: st.caption(f"GW{GW_NEXT}")
with h6: st.caption("DURUM / GW2 İSRAF")
with h7: st.caption("İŞLEM")

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
        st.markdown(f"<span class='badge badge-pos'>{p['pozisyon']}</span>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"**{p['fiyat']}M**")
    with c4:
        b2b1_badge = f"<span class='badge badge-b2b'>B2B</span>" if p[f"gw{GW_NOW}_b2b"] == "Var ⚠️" else ""
        st.markdown(f"**{p[f'gw{GW_NOW}_mac']}** {b2b1_badge}", unsafe_allow_html=True)
    with c5:
        b2b2_badge = f"<span class='badge badge-b2b'>B2B</span>" if p[f"gw{GW_NEXT}_b2b"] == "Var ⚠️" else ""
        st.markdown(f"**{p[f'gw{GW_NEXT}_mac']}** {b2b2_badge}", unsafe_allow_html=True)
    with c6:
        rozetler = []
        if p["durum"] == "Sakat":
            rozetler.append("<span class='badge badge-out'>OUT</span>")
        elif "Şüpheli" in p["durum"]:
            rozetler.append("<span class='badge badge-dtd'>ŞÜPHELİ</span>")
        
        israf_sayisi = p.get("gw2_israf", 0)
        if israf_sayisi > 0:
            rozetler.append(f"<span class='badge badge-waste'>{israf_sayisi} BENCH</span>")
        else:
            rozetler.append("<span class='badge badge-clean'>TAM KATKI</span>")

        st.markdown(" ".join(rozetler), unsafe_allow_html=True)
        
    with c7:
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            if st.button("Detay", key=f"k_view_{idx}", help="Profili Aç", use_container_width=True):
                oyuncu_popup(p["isim"])
        with b_col2:
            if st.button("Çıkar", key=f"k_del_{idx}", help="Kadrodan Çıkar", use_container_width=True):
                suanki_kadro_isimler.remove(p["isim"])
                kadroyu_kaydet()
                st.rerun()
            
    st.markdown("<hr style='margin:4px 0 6px 0; border-color:#172033;'>", unsafe_allow_html=True)

st.write("")

# --- 5. GÜNLÜK MAÇ & SAHAYA ÇIKIŞ MATRİSİ ---
def matris_olustur(day_cols_list):
    matris_data = []
    for d_idx, day_col in enumerate(day_cols_list, start=1):
        maci_olanlar = kadro_df[kadro_df[day_col] > 0] if day_col in kadro_df.columns else pd.DataFrame()
        if maci_olanlar.empty:
            matris_data.append({"Gün": f"Day {d_idx}", "Maçı Olan": 0, "Sahaya Çıkan": "0/5 Boş", "BC": "—", "FC": "—"})
            continue

        bc_oynayanlar = maci_olanlar[maci_olanlar["pozisyon"] == "BC"]["isim"].tolist()
        fc_oynayanlar = maci_olanlar[maci_olanlar["pozisyon"] == "FC"]["isim"].tolist()
        bc_count, fc_count = len(bc_oynayanlar), len(fc_oynayanlar)

        opt1 = min(bc_count, 3) + min(fc_count, 2)
        opt2 = min(bc_count, 2) + min(fc_count, 3)
        sahaya_cikan = min(5, max(opt1, opt2))

        durum_badge = f"{sahaya_cikan}/5 Dolu" if sahaya_cikan == 5 else f"{sahaya_cikan}/5 Eksik"
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

with st.expander("📅 GÜNLÜK MAÇ VE SAHA DAĞILIM MATRİSİ", expanded=True):
    tab_gw1, tab_gw2 = st.tabs(["Bu Hafta (GW1)", "Gelecek Hafta (GW2)"])
    with tab_gw1:
        st.dataframe(matris_olustur(hesaplayici.DAY_COLS_GW1), use_container_width=True, hide_index=True)
    with tab_gw2:
        st.dataframe(matris_olustur(hesaplayici.DAY_COLS_GW2), use_container_width=True, hide_index=True)

st.write("")

# --- 6. TRANSFER SİMÜLATÖRÜ (SADELEŞTİRİLMİŞ & BÜTÇE ŞERİTLİ) ---
st.markdown("#### 🔄 AKILLI TRANSFER SİMÜLATÖRÜ")

if len(kadro_df) != 10:
    st.info("Transfer simülasyonu için kadronuzda tam 10 oyuncu bulunmalıdır.")
elif bc_toplam != 5 or fc_toplam != 5:
    st.error("Kadronuzu 5 BC ve 5 FC kuralına uygun hale getiriniz.")
elif fazla_takimlar:
    st.error("Aynı takımdan en fazla 2 oyuncu kuralını sağlayınız.")
else:
    sim_gw_col1, _ = st.columns([2.5, 3.5])
    with sim_gw_col1:
        hedef_gw = st.radio("Optimizasyon Hedefi:", [f"Bu Hafta (GW{GW_NOW})", f"Gelecek Hafta (GW{GW_NEXT})"], horizontal=True)
        aktif_hedef_num = GW_NOW if "GW1" in hedef_gw else GW_NEXT

    satilacaklar = st.multiselect(
        "Takımdan Çıkarmak İstediğiniz Oyuncular (Max 2):",
        options=suanki_kadro_isimler,
        max_selections=2
    )

    if st.button("Alternatifleri Hesapla 🚀"):
        if not satilacaklar:
            st.info("Lütfen en az bir oyuncu seçin.")
        else:
            oneriler = hesaplayici.transferleri_hesapla(df, kadro_df, satilacaklar, kasa, suanki_kadro_isimler, aktif_gw=aktif_hedef_num)
            if oneriler:
                st.session_state["son_oneriler"] = oneriler
                st.session_state["aktif_satilanlar"] = satilacaklar
            else:
                st.session_state.pop("son_oneriler", None)
                st.error("Kriterlere uygun alternatif bulunamadı.")

    if "son_oneriler" in st.session_state:
        # Satılan oyuncuların özet bütçesi (TEK BİR KUTUDA)
        aktif_satilan_df = kadro_df[kadro_df["isim"].isin(st.session_state["aktif_satilanlar"])]
        satilan_gelir_toplam = aktif_satilan_df["fiyat"].sum()
        kullanilabilir_toplam = round(satilan_gelir_toplam + kasa, 1)
        satilan_isimler_str = " + ".join([f"{row['isim']} ({row['fiyat']}M)" for _, row in aktif_satilan_df.iterrows()])

        st.markdown(f"""
        <div class="budget-info-box">
            💼 <strong>Transfer Bütçesi Özeti:</strong> Çıkarılan: <strong>{satilan_isimler_str}</strong> (Gelir: <strong>+{satilan_gelir_toplam:.1f}M</strong>) 
            • Mevcut Kasa: <strong>{kasa:.1f}M</strong> • Toplam Harcanabilir Bütçe: <strong style="color:#38bdf8;">{kullanilabilir_toplam:.1f}M</strong>
        </div>
        """, unsafe_allow_html=True)

        for idx, o in enumerate(st.session_state["son_oneriler"], start=1):
            c_yazi, c_butonlar = st.columns([3.2, 1.8])
            with c_yazi:
                st.markdown(f"**#{idx} {o['baslik']}**")
                st.caption(f"💵 Transfer Sonrası Kalan Kasa: **{o['kalan_butce']}M**")
            
            with c_butonlar:
                btn_cols = st.columns(len(o.get("isimler", [])) + 1)
                for b_idx, p_name in enumerate(o.get("isimler", [])):
                    with btn_cols[b_idx]:
                        kisa_ad = p_name.split()[-1]
                        if st.button(f"🔍 {kisa_ad}", key=f"sim_view_{idx}_{b_idx}"):
                            oyuncu_popup(p_name)
                
                with btn_cols[-1]:
                    if st.button("✅ Uygula", key=f"apply_{idx}", help="Transferi kadroya uygula"):
                        satilan_liste = st.session_state.get("aktif_satilanlar", satilacaklar)
                        yeni_liste = [n for n in suanki_kadro_isimler if n not in satilan_liste]
                        yeni_liste.extend(o["isimler"])
                        st.session_state[f"kadro_{aktif_menajer}"] = yeni_liste
                        kadroyu_kaydet()
                        st.session_state.pop("son_oneriler", None)
                        st.success("Transfer uygulandı!")
                        st.rerun()