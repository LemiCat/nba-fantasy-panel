import pandas as pd

DAY_COLS_GW1 = ["d1", "d2", "d3", "d4", "d5", "d6"]
DAY_COLS_GW2 = ["gw2_d1", "gw2_d2", "gw2_d3", "gw2_d4", "gw2_d5", "gw2_d6"]


def hesapla_efektif_mac(kadro_10_df, day_cols=DAY_COLS_GW1):
  toplam = 0
  for d in day_cols:
    if d not in kadro_10_df.columns:
      continue
    maci_olanlar = kadro_10_df[kadro_10_df[d] > 0]
    bc_count = len(maci_olanlar[maci_olanlar["pozisyon"] == "BC"])
    fc_count = len(maci_olanlar[maci_olanlar["pozisyon"] == "FC"])
    opt1 = min(bc_count, 3) + min(fc_count, 2)
    opt2 = min(bc_count, 2) + min(fc_count, 3)
    toplam += min(5, max(opt1, opt2))
  return toplam


# Hızlı simülasyon motoru (Saf Python - 0.1 saniye)
def _hizli_efektif_hesapla(gunluk_bc_sayilari, gunluk_fc_sayilari):
  toplam = 0
  for bc, fc in zip(gunluk_bc_sayilari, gunluk_fc_sayilari):
    opt1 = (bc if bc < 3 else 3) + (fc if fc < 2 else 2)
    opt2 = (bc if bc < 2 else 2) + (fc if fc < 3 else 3)
    cikan = opt1 if opt1 > opt2 else opt2
    toplam += cikan if cikan < 5 else 5
  return toplam


def transferleri_hesapla(
    df, kadro_df, satilacaklar, kalan_kasa, secilen_kadro_isimler, aktif_gw=1
):
  if not satilacaklar:
    return []

  df = df.copy()
  df["fiyat"] = pd.to_numeric(df["fiyat"], errors="coerce").fillna(4.5)

  satilan_df = kadro_df[kadro_df["isim"].isin(satilacaklar)].copy()
  kalacak_df = kadro_df[~kadro_df["isim"].isin(satilacaklar)].copy()

  satis_geliri = float(satilan_df["fiyat"].sum())
  toplam_butce = round(float(kalan_kasa) + satis_geliri, 2)

  gerekli_pozisyonlar = satilan_df["pozisyon"].tolist()
  mevcut_takim_sayilari = kalacak_df["takim"].value_counts().to_dict()
  haric_isimler = set(secilen_kadro_isimler)

  mac_col = f"gw{aktif_gw}_mac"
  day_cols = DAY_COLS_GW1 if aktif_gw == 1 else DAY_COLS_GW2
  satilan_dokum = " + ".join(
      [f"{r['isim']} ({r['fiyat']}M)" for _, r in satilan_df.iterrows()]
  )

  # Baz kadronun gün gün BC ve FC sayıları
  base_bc = [
      len(kalacak_df[(kalacak_df[d] > 0) & (kalacak_df["pozisyon"] == "BC")])
      for d in day_cols
  ]
  base_fc = [
      len(kalacak_df[(kalacak_df[d] > 0) & (kalacak_df["pozisyon"] == "FC")])
      for d in day_cols
  ]

  # Sadece sakat olmayan ve takımda yer almayan adaylar
  adaylar = df[
      (~df["isim"].isin(haric_isimler)) & (df["sakatlik"] != "i")
  ].copy()

  # Günlük maç dizilerini aday nesnesine gömüyoruz
  aday_kayitlari = []
  for _, r in adaylar.iterrows():
    m_days = [int(r.get(d, 0) > 0) for d in day_cols]
    aday_kayitlari.append({
        "isim": r["isim"],
        "takim": r["takim"],
        "pozisyon": r["pozisyon"],
        "fiyat": float(r["fiyat"]),
        "mac_sayisi": int(r.get(mac_col, 0)),
        "m_days": m_days,
    })

  oneriler = []

  # --- 1 OYUNCU TRANSFERİ ---
  if len(satilacaklar) == 1:
    pos = gerekli_pozisyonlar[0]
    uygun = [
        p
        for p in aday_kayitlari
        if p["pozisyon"] == pos and p["fiyat"] <= toplam_butce
    ]

    for p in uygun:
      if mevcut_takim_sayilari.get(p["takim"], 0) < 2:
        kalan = round(toplam_butce - p["fiyat"], 1)
        cur_bc = list(base_bc)
        cur_fc = list(base_fc)
        for i in range(len(day_cols)):
          if p["m_days"][i]:
            if pos == "BC":
              cur_bc[i] += 1
            else:
              cur_fc[i] += 1

        efektif_mac = _hizli_efektif_hesapla(cur_bc, cur_fc)
        baslik = (
            f"{p['isim']} ({p['takim']} - {p['fiyat']}M) ➔ Toplam"
            f" {p['mac_sayisi']} Maç (Sahada: {efektif_mac} Maç)"
        )
        skor = (efektif_mac * 1000) + (p["mac_sayisi"] * 10) + p["fiyat"]

        oneriler.append({
            "baslik": baslik,
            "skor": skor,
            "efektif_mac": efektif_mac,
            "gelen_dokum": f"{p['isim']} ({p['fiyat']}M)",
            "gelen_maliyet": p["fiyat"],
            "satilan_dokum": satilan_dokum,
            "satilan_gelir": satis_geliri,
            "kalan_butce": kalan,
            "isimler": [p["isim"]],
        })

  # --- 2 OYUNCU TRANSFERİ ---
  elif len(satilacaklar) == 2:
    pos1, pos2 = gerekli_pozisyonlar[0], gerekli_pozisyonlar[1]

    # Bütçe filtresi ile adayları alıyoruz (başta kesinti yapmadan!)
    pool1 = [
        p
        for p in aday_kayitlari
        if p["pozisyon"] == pos1 and p["fiyat"] <= (toplam_butce - 4.5)
    ]
    pool2 = [
        p
        for p in aday_kayitlari
        if p["pozisyon"] == pos2 and p["fiyat"] <= (toplam_butce - 4.5)
    ]

    # Hız için maç ve fiyata göre sıralayıp en iyi 70'er adayı alıyoruz
    pool1.sort(key=lambda x: (x["mac_sayisi"], x["fiyat"]), reverse=True)
    pool2.sort(key=lambda x: (x["mac_sayisi"], x["fiyat"]), reverse=True)
    pool1 = pool1[:70]
    pool2 = pool2[:70]

    if pos1 == pos2:
      n = len(pool1)
      for i in range(n):
        p1 = pool1[i]
        for j in range(i + 1, n):
          p2 = pool1[j]
          maliyet = round(p1["fiyat"] + p2["fiyat"], 2)
          if maliyet > toplam_butce:
            continue

          t1, t2 = p1["takim"], p2["takim"]
          if (
              (t1 == t2 and mevcut_takim_sayilari.get(t1, 0) >= 1)
              or mevcut_takim_sayilari.get(t1, 0) >= 2
              or mevcut_takim_sayilari.get(t2, 0) >= 2
          ):
            continue

          kalan = round(toplam_butce - maliyet, 1)
          cur_bc = list(base_bc)
          cur_fc = list(base_fc)
          for k in range(len(day_cols)):
            ek_bc = (
                (p1["m_days"][k] if pos1 == "BC" else 0)
                + (p2["m_days"][k] if pos2 == "BC" else 0)
            )
            ek_fc = (
                (p1["m_days"][k] if pos1 == "FC" else 0)
                + (p2["m_days"][k] if pos2 == "FC" else 0)
            )
            cur_bc[k] += ek_bc
            cur_fc[k] += ek_fc

          efektif_mac = _hizli_efektif_hesapla(cur_bc, cur_fc)
          top_m = p1["mac_sayisi"] + p2["mac_sayisi"]

          baslik = (
              f"{p1['isim']} ({p1['fiyat']}M) + {p2['isim']} ({p2['fiyat']}M) ➔"
              f" Toplam {top_m} Maç (Sahada: {efektif_mac} Maç)"
          )
          skor = (efektif_mac * 1000) + (top_m * 10) + maliyet

          oneriler.append({
              "baslik": baslik,
              "skor": skor,
              "efektif_mac": efektif_mac,
              "gelen_dokum": (
                  f"{p1['isim']} ({p1['fiyat']}M) + {p2['isim']} ({p2['fiyat']}M)"
              ),
              "gelen_maliyet": maliyet,
              "satilan_dokum": satilan_dokum,
              "satilan_gelir": satis_geliri,
              "kalan_butce": kalan,
              "isimler": [p1["isim"], p2["isim"]],
          })
    else:
      for p1 in pool1:
        for p2 in pool2:
          if p1["isim"] == p2["isim"]:
            continue
          maliyet = round(p1["fiyat"] + p2["fiyat"], 2)
          if maliyet > toplam_butce:
            continue

          t1, t2 = p1["takim"], p2["takim"]
          if (
              (t1 == t2 and mevcut_takim_sayilari.get(t1, 0) >= 1)
              or mevcut_takim_sayilari.get(t1, 0) >= 2
              or mevcut_takim_sayilari.get(t2, 0) >= 2
          ):
            continue

          kalan = round(toplam_butce - maliyet, 1)
          cur_bc = list(base_bc)
          cur_fc = list(base_fc)
          for k in range(len(day_cols)):
            ek_bc = (
                (p1["m_days"][k] if pos1 == "BC" else 0)
                + (p2["m_days"][k] if pos2 == "BC" else 0)
            )
            ek_fc = (
                (p1["m_days"][k] if pos1 == "FC" else 0)
                + (p2["m_days"][k] if pos2 == "FC" else 0)
            )
            cur_bc[k] += ek_bc
            cur_fc[k] += ek_fc

          efektif_mac = _hizli_efektif_hesapla(cur_bc, cur_fc)
          top_m = p1["mac_sayisi"] + p2["mac_sayisi"]

          baslik = (
              f"{p1['isim']} ({p1['fiyat']}M) + {p2['isim']} ({p2['fiyat']}M) ➔"
              f" Toplam {top_m} Maç (Sahada: {efektif_mac} Maç)"
          )
          skor = (efektif_mac * 1000) + (top_m * 10) + maliyet

          oneriler.append({
              "baslik": baslik,
              "skor": skor,
              "efektif_mac": efektif_mac,
              "gelen_dokum": (
                  f"{p1['isim']} ({p1['fiyat']}M) + {p2['isim']} ({p2['fiyat']}M)"
              ),
              "gelen_maliyet": maliyet,
              "satilan_dokum": satilan_dokum,
              "satilan_gelir": satis_geliri,
              "kalan_butce": kalan,
              "isimler": [p1["isim"], p2["isim"]],
          })

  # En yüksek skora sahip ilk 5 alternatif
  return sorted(oneriler, key=lambda x: x["skor"], reverse=True)[:5]