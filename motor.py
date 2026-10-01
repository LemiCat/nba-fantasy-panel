import re
import pandas as pd
import requests

def verileri_guncelle():
    STATIC_URL = "https://nbafantasy.nba.com/api/bootstrap-static/"
    FIXTURES_URL = "https://nbafantasy.nba.com/api/fixtures/"

    r_static = requests.get(STATIC_URL).json()
    r_fixtures = requests.get(FIXTURES_URL).json()

    elements = r_static["elements"]
    teams = {t["id"]: t["short_name"] for t in r_static["teams"]}

    positions = {}
    for et in r_static["element_types"]:
        et_id = et["id"]
        singular = et.get("singular_name_short", "").upper()
        if "G" in singular or et_id == 1:
            positions[et_id] = "BC"
        else:
            positions[et_id] = "FC"

    events = r_static["events"]
    gw_days_order = {}

    for ev in events:
        ev_id = ev["id"]
        name = ev.get("name", "")
        match = re.search(r"Gameweek\s+(\d+)\s+-\s+Day\s+(\d+)", name)
        if match:
            gw_num = int(match.group(1))
            day_num = int(match.group(2))
            if gw_num not in gw_days_order:
                gw_days_order[gw_num] = []
            gw_days_order[gw_num].append((day_num, ev_id))

    for gw in gw_days_order:
        gw_days_order[gw] = [ev_id for _, ev_id in sorted(gw_days_order[gw], key=lambda x: x[0])]

    fixtures_by_event = {}
    for f in r_fixtures:
        ev_id = f.get("event")
        if ev_id:
            fixtures_by_event.setdefault(ev_id, []).append(f)

    gw_day_counts = {gw: len(gw_days_order.get(gw, [])) for gw in range(1, 6)}

    team_gw_days = {}
    for gw in range(1, 6):
        team_gw_days[gw] = {t: [0] * gw_day_counts[gw] for t in teams.values()}
        for idx, ev_id in enumerate(gw_days_order.get(gw, [])):
            for f in fixtures_by_event.get(ev_id, []):
                ht = teams.get(f.get("team_h"))
                at = teams.get(f.get("team_a"))
                if ht: team_gw_days[gw][ht][idx] += 1
                if at: team_gw_days[gw][at][idx] += 1

    gw_team_matches = {t_code: {} for t_code in teams.values()}
    gw_team_b2b = {t_code: {} for t_code in teams.values()}

    for gw in range(1, 6):
        ev_ids = gw_days_order.get(gw, [])
        for t_code in teams.values():
            d_counts = []
            for ev_id in ev_ids:
                dfix = fixtures_by_event.get(ev_id, [])
                cnt = sum(1 for f in dfix if teams.get(f.get("team_h")) == t_code or teams.get(f.get("team_a")) == t_code)
                d_counts.append(cnt)
            gw_team_matches[t_code][f"gw{gw}_mac"] = sum(d_counts)
            has_b2b = any(d_counts[i] > 0 and d_counts[i+1] > 0 for i in range(len(d_counts)-1)) if len(d_counts) > 1 else False
            gw_team_b2b[t_code][f"gw{gw}_b2b"] = "Var" if has_b2b else "Yok"

    oyuncu_listesi = []

    for p in elements:
        if p.get("status") == "u":
            continue

        isim = f"{p['first_name']} {p['second_name']}".strip()
        t_code = teams.get(p["team"], "UNK")
        pos = positions.get(p["element_type"], "FC")
        player_code = p.get("code", "")

        current_cost = p.get("now_cost", 0) / 10.0
        # Fiyat Değişimi (Sezon başından bu yana olan net fark)
        cost_change = p.get("cost_change_start", 0) / 10.0
        purchase_cost = current_cost - cost_change

        selling_price = purchase_cost + (int((current_cost - purchase_cost) * 10 / 2) / 10.0) if current_cost > purchase_cost else current_cost

        status = p.get("status", "a")
        chance = p.get("chance_of_playing_next_round")
        if status == "i": durum = "Sakat"
        elif status == "d": durum = f"Şüpheli (%{chance})" if chance is not None else "Şüpheli"
        elif status == "s": durum = "Cezalı"
        else: durum = "Normal"

        kayit = {
            "id": p["id"],
            "code": player_code,
            "isim": isim,
            "takim": t_code,
            "pozisyon": pos,
            "fiyat": current_cost,
            "fiyat_degisim": cost_change,
            "satis_fiyati": selling_price,
            "sakatlik": status,
            "durum": durum,
            "mac_kacirma": "Normal",
            "dakika": 0.0, "ort_puan": 0.0, "sayi": 0.0, "ribaund": 0.0, "asist": 0.0, "top_calma": 0.0, "blok": 0.0,
            "f_dakika": 0.0, "f_ort_puan": 0.0, "f_sayi": 0.0, "f_ribaund": 0.0, "f_asist": 0.0, "f_top_calma": 0.0, "f_blok": 0.0
        }

        for d_idx, cnt in enumerate(team_gw_days[1].get(t_code, []), start=1):
            kayit[f"d{d_idx}"] = cnt

        for d_idx, cnt in enumerate(team_gw_days[2].get(t_code, []), start=1):
            kayit[f"gw2_d{d_idx}"] = cnt

        for gw in range(1, 6):
            kayit[f"gw{gw}_mac"] = gw_team_matches[t_code].get(f"gw{gw}_mac", 0)
            kayit[f"gw{gw}_b2b"] = gw_team_b2b[t_code].get(f"gw{gw}_b2b", "Yok")

        oyuncu_listesi.append(kayit)

    df = pd.DataFrame(oyuncu_listesi)
    df.to_csv("oyuncular.csv", index=False)
    return df

if __name__ == "__main__":
    verileri_guncelle()