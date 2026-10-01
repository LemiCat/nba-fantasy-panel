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

def hesapla_efektif_mac_hizli(kadro_records, day_cols):
    toplam_sahada = 0
    for day_col in day_cols:
        bc_count = 0
        fc_count = 0
        for p in kadro_records:
            if p.get(day_col, 0) > 0:
                if p["pozisyon"] == "BC":
                    bc_count += 1
                else:
                    fc_count += 1
        
        if bc_count == 0 and fc_count == 0:
            continue

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

    day_cols = get_day_cols(df, aktif_gw)
    gw_mac_col = f"gw{aktif_gw}_mac"

    # Sakat veya listeden çıkarılmış olmayan tüm oyuncular
    havuz = df[
        (~df["isim"].isin(suanki_kadro_isimler)) & 
        (df["durum"] != "Sakat") & 
        (df["sakatlik"] != "u")
    ].copy()

    kalan_records = kalan_kadro_df.to_dict("records")
    kalan_takim_sayilari = {}
    for p in kalan_records:
        kalan_takim_sayilari[p["takim"]] = kalan_takim_sayilari.get(p["takim"], 0) + 1

    oneriler = []

    if k_sayisi == 1:
        pos = gerekli_pozisyonlar[0]
        adaylar = havuz[(havuz["pozisyon"] == pos) & (havuz["fiyat"] <= toplam_butce)].copy()

        for _, p in adaylar.iterrows():
            p_dict = p.to_dict()
            if kalan_takim_sayilari.get(p_dict["takim"], 0) >= 2:
                continue

            gecici_kadro = kalan_records + [p_dict]
            sahada_mac = hesapla_efektif_mac_hizli(gecici_kadro, day_cols)
            kalan_b = round(toplam_butce - p_dict["fiyat"], 1)

            oneriler.append({
                "baslik": f"{p_dict['isim']} ({p_dict['takim']} - {p_dict['fiyat']}M) ➔ Toplam {p_dict[gw_mac_col]} Maç (Sahada: {sahada_mac} Maç)",
                "kalan_butce": kalan_b,
                "sahada_mac": sahada_mac,
                "toplam_mac": p_dict[gw_mac_col],
                "toplam_fiyat": p_dict["fiyat"],
                "isimler": [p_dict["isim"]],
                "takimlar": [p_dict["takim"]]
            })

    elif k_sayisi == 2:
        pos1, pos2 = gerekli_pozisyonlar[0], gerekli_pozisyonlar[1]

        # En ucuz oyuncu en az 4.5M olabileceği için tavan fiyat
        max_tekil_fiyat = toplam_butce - 4.5

        if pos1 == pos2:
            # Aynı mevkiden iki oyuncu satılıyorsa
            adaylar = havuz[(havuz["pozisyon"] == pos1) & (havuz["fiyat"] <= max_tekil_fiyat)]
            aday_records = adaylar.to_dict("records")
            kombinasyonlar = list(itertools.combinations(aday_records, 2))
        else:
            # Farklı mevkilerden iki oyuncu satılıyorsa
            adaylar1 = havuz[(havuz["pozisyon"] == pos1) & (havuz["fiyat"] <= max_tekil_fiyat)].to_dict("records")
            adaylar2 = havuz[(havuz["pozisyon"] == pos2) & (havuz["fiyat"] <= max_tekil_fiyat)].to_dict("records")
            kombinasyonlar = list(itertools.product(adaylar1, adaylar2))

        for p1_dict, p2_dict in kombinasyonlar:
            maliyet = round(p1_dict["fiyat"] + p2_dict["fiyat"], 1)
            if maliyet > toplam_butce:
                continue

            # Takım sınırları kontrolü
            t1, t2 = p1_dict["takim"], p2_dict["takim"]
            
            # Eğer iki transfer aynı takımdansa ve kadroda zaten o takımdan varsa geç
            if t1 == t2 and kalan_takim_sayilari.get(t1, 0) >= 1:
                continue
            if kalan_takim_sayilari.get(t1, 0) >= 2 or kalan_takim_sayilari.get(t2, 0) >= 2:
                continue

            gecici_kadro = kalan_records + [p1_dict, p2_dict]
            sahada_mac = hesapla_efektif_mac_hizli(gecici_kadro, day_cols)
            kalan_b = round(toplam_butce - maliyet, 1)
            top_mac = p1_dict[gw_mac_col] + p2_dict[gw_mac_col]

            oneriler.append({
                "baslik": f"{p1_dict['isim']} ({p1_dict['fiyat']}M) + {p2_dict['isim']} ({p2_dict['fiyat']}M) ➔ Toplam {top_mac} Maç (Sahada: {sahada_mac} Maç)",
                "kalan_butce": kalan_b,
                "sahada_mac": sahada_mac,
                "toplam_mac": top_mac,
                "toplam_fiyat": maliyet,
                "isimler": [p1_dict["isim"], p2_dict["isim"]],
                "takimlar": [t1, t2]
            })

    if not oneriler:
        return []

    # En yüksek sahada maç ve en verimli bütçe sıralaması
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