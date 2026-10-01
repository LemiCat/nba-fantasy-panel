import itertools
import pandas as pd

def get_day_cols(df, gw=1):
    prefix = "d" if gw == 1 else "gw2_d"
    cols = [c for c in df.columns if c.startswith(prefix) and c[len(prefix):].isdigit()]
    return sorted(cols, key=lambda x: int(x[len(prefix):]))

def hesapla_efektif_mac(kadro_df, day_cols):
    toplam_sahada = 0
    for day_col in day_cols:
        if day_col not in kadro_df.columns:
            continue
        maci_olanlar = kadro_df[kadro_df[day_col] > 0]
        if maci_olanlar.empty:
            continue

        bc_count = len(maci_olanlar[maci_olanlar["pozisyon"] == "BC"])
        fc_count = len(maci_olanlar[maci_olanlar["pozisyon"] == "FC"])

        opt1 = min(bc_count, 3) + min(fc_count, 2)
        opt2 = min(bc_count, 2) + min(fc_count, 3)
        toplam_sahada += min(5, max(opt1, opt2))

    return toplam_sahada

def transferleri_hesapla(df, kadro_df, satilacak_isimler, kasa, suanki_kadro_isimler, aktif_gw=1):
    satilanlar_df = kadro_df[kadro_df["isim"].isin(satilacak_isimler)]
    kalan_kadro_df = kadro_df[~kadro_df["isim"].isin(satilacak_isimler)]

    k_sayisi = len(satilacak_isimler)
    if k_sayisi not in [1, 2]:
        return []

    gelen_butce = satilanlar_df["fiyat"].sum()
    toplam_butce = round(gelen_butce + kasa, 1)
    gerekli_pozisyonlar = sorted(satilanlar_df["pozisyon"].tolist())

    havuz = df[(~df["isim"].isin(suanki_kadro_isimler)) & (df["durum"] != "Sakat") & (df["sakatlik"] != "u")].copy()
    day_cols = get_day_cols(df, aktif_gw)
    gw_mac_col = f"gw{aktif_gw}_mac"

    oneriler = []

    if k_sayisi == 1:
        pos = gerekli_pozisyonlar[0]
        adaylar = havuz[(havuz["pozisyon"] == pos) & (havuz["fiyat"] <= toplam_butce)].copy()

        for _, p in adaylar.iterrows():
            gecici_kadro = pd.concat([kalan_kadro_df, pd.DataFrame([p])])
            if gecici_kadro["takim"].value_counts().max() > 2:
                continue

            sahada_mac = hesapla_efektif_mac(gecici_kadro, day_cols)
            kalan_b = round(toplam_butce - p["fiyat"], 1)

            oneriler.append({
                "baslik": f"{p['isim']} ({p['takim']} - {p['fiyat']}M) -> Toplam {p[gw_mac_col]} Mac (Sahada: {sahada_mac} Mac)",
                "kalan_butce": kalan_b,
                "sahada_mac": sahada_mac,
                "toplam_mac": p[gw_mac_col],
                "toplam_fiyat": p["fiyat"],
                "isimler": [p["isim"]],
                "takimlar": [p["takim"]]
            })

    elif k_sayisi == 2:
        pos1, pos2 = gerekli_pozisyonlar[0], gerekli_pozisyonlar[1]

        if pos1 == pos2:
            adaylar = havuz[havuz["pozisyon"] == pos1]
            kombinasyonlar = list(itertools.combinations(adaylar.iterrows(), 2))
        else:
            adaylar1 = havuz[havuz["pozisyon"] == pos1]
            adaylar2 = havuz[havuz["pozisyon"] == pos2]
            kombinasyonlar = list(itertools.product(adaylar1.iterrows(), adaylar2.iterrows()))

        for (_, p1), (_, p2) in kombinasyonlar:
            maliyet = round(p1["fiyat"] + p2["fiyat"], 1)
            if maliyet > toplam_butce:
                continue

            gecici_kadro = pd.concat([kalan_kadro_df, pd.DataFrame([p1, p2])])
            if gecici_kadro["takim"].value_counts().max() > 2:
                continue

            sahada_mac = hesapla_efektif_mac(gecici_kadro, day_cols)
            kalan_b = round(toplam_butce - maliyet, 1)
            top_mac = p1[gw_mac_col] + p2[gw_mac_col]

            oneriler.append({
                "baslik": f"{p1['isim']} ({p1['fiyat']}M) + {p2['isim']} ({p2['fiyat']}M) -> Toplam {top_mac} Mac (Sahada: {sahada_mac} Mac)",
                "kalan_butce": kalan_b,
                "sahada_mac": sahada_mac,
                "toplam_mac": top_mac,
                "toplam_fiyat": maliyet,
                "isimler": [p1["isim"], p2["isim"]],
                "takimlar": [p1["takim"], p2["takim"]]
            })

    if not oneriler:
        return []

    oneriler = sorted(oneriler, key=lambda x: (x["sahada_mac"], x["toplam_mac"], x["toplam_fiyat"]), reverse=True)

    filtrelenmis_oneriler = []
    gorulen_takimlar = set()

    for o in oneriler:
        ana_takim = o["takimlar"][0]
        if ana_takim not in gorulen_takimlar:
            filtrelenmis_oneriler.append(o)
            gorulen_takimlar.add(ana_takim)
        if len(filtrelenmis_oneriler) == 5:
            break

    if len(filtrelenmis_oneriler) < 5:
        for o in oneriler:
            if o not in filtrelenmis_oneriler:
                filtrelenmis_oneriler.append(o)
            if len(filtrelenmis_oneriler) == 5:
                break

    return filtrelenmis_oneriler