#!/usr/bin/env python3
"""Build public/data/spots.json from raw OSRM data + curated, verified notes.
Photos: keep only Wikimedia images whose title clearly matches the place.
No invented hotels, restaurants, prices or links.
"""
import json, math, os, re, time, urllib.parse, urllib.request
from html import unescape
from pathlib import Path

RAW = json.load(open("/workspace/snow-trip-planner/public/data/raw.json"))
OUT = Path("/workspace/snow-trip-planner/public/data/spots.json")
UA = "SahilSnowTripPlanner/1.0"
P = RAW["petrol_inr_per_litre"]

def get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def strip_html(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return unescape(s).replace("\n", " ").strip()

def hav(a, b):
    # a,b = (lat, lon)
    R = 6371.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dl = math.radians(b[1] - a[1]); dp = p2 - p1
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))

def from_path(path, author, license_, title):
    name = path.split("/")[-1]
    plain = urllib.parse.unquote(name)
    page = "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(plain.replace(" ", "_"))
    thumb = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(plain) + "?width=1200"
    file_url = "https://upload.wikimedia.org/wikipedia/commons/" + path
    return {
        "title": title,
        "author": author,
        "license": license_,
        "thumb": thumb,
        "file": file_url,
        "page": page,
    }

# Previously vetted Commons files from earlier trip research
KNOWN = {
    "harsil": [
        from_path("2/2a/Harsil_Valley.jpg","Harshit SR","CC BY-SA 4.0","Harsil Valley"),
        from_path("6/63/Harsil_Valley%2C_Uttarkashi%2C_Uttarakhand.jpg","Harshit SR","CC BY-SA 4.0","Harsil Valley, Uttarkashi, Uttarakhand"),
        from_path("f/f1/Harshil_view.jpg","Amit.pratap1988","CC BY-SA 3.0","Harshil view"),
        from_path("a/ae/Harsil_village.jpg","Sanjeev travelgrapher","CC BY-SA 4.0","Harsil village"),
        from_path("d/d0/Harshil.jpg","Shariful Islam (Geologist)","CC BY-SA 4.0","Harshil"),
    ],
    "chakrata": [
        from_path("3/33/Chakrata.jpg","Manojpanchal90","CC BY-SA 4.0","Chakrata"),
        from_path("f/f6/Chakrata_nice_wather.jpg","Mustkeem Ahamad","CC BY-SA 4.0","Chakrata"),
        from_path("c/ca/Deoban.jpg","Puneetcps","CC BY-SA 4.0","Deoban"),
        from_path("d/d9/Tiger_Fall_Uttrakhand_India.jpg","Daniel Romanson","CC BY-SA 4.0","Tiger Fall, Uttarakhand"),
        from_path("e/e3/The_50_meter_roaring_Tiger_Fall_Chktrata.jpg","Daniel Romanson","CC BY-SA 4.0","Tiger Falls, Chakrata"),
    ],
    "chanshal": [
        from_path("5/50/Chanshal_Himadri_range.jpg","Abhay tanta","CC BY 4.0","Chanshal Himadri range"),
        from_path("b/bb/Chanshal_pass.jpg","Prithvijeet Singh Thakur","CC BY-SA 4.0","Chanshal pass"),
        from_path("c/c2/Chanshal_peak.jpg","Prithvijeet Singh Thakur","CC BY-SA 4.0","Chanshal peak"),
        from_path("1/16/Snow_and_slush_enroute_Dodra_Kwar_%2831459216875%29.jpg","Ashish Gupta","CC BY 2.0","Snow and slush enroute Dodra Kwar"),
    ],
    "jalori": [
        from_path("6/6c/Himalayan_range_from_Jalori_Pass.jpg","Prabhmeet Singh","CC BY-SA 4.0","Himalayan range from Jalori Pass"),
        from_path("0/0f/GHNP_view_from_Jalori_pass.jpg","Manish57335","CC BY-SA 4.0","GHNP view from Jalori pass"),
        from_path("f/ff/Jalori_Pass.jpg","Manish57335","CC BY-SA 4.0","Jalori Pass"),
        from_path("b/b1/Serolsar_Lake.jpg","Sukhjiwan Singh","CC BY-SA 4.0","Serolsar Lake"),
        from_path("0/0d/Raghupur_Fort_01.jpg","Gannu03","CC BY-SA 4.0","Raghupur Fort"),
    ],
    "kalpa": [
        from_path("5/58/Kinnaur_Kailash_from_Kalpa_on_june_2015.jpg","Goutam1962","CC BY-SA 4.0","Kinnaur Kailash from Kalpa"),
        from_path("e/ee/Kalpa_Village.jpg","Sapna Sony","CC BY-SA 4.0","Kalpa Village"),
        from_path("d/d2/Kalpa-14-Kinnaur_Kailash-gje.jpg","Gerd Eichmann","CC BY-SA 4.0","Kinnaur Kailash from Kalpa"),
        from_path("5/50/Roghi_village_kalpa.jpg","Rahulraees","CC BY-SA 4.0","Roghi village, Kalpa"),
        from_path("1/1d/Kalpa_suicide_point.jpg","Rahulraees","CC BY-SA 4.0","Viewpoint near Kalpa (Suicide Point)"),
    ],
    "rakchham": [
        from_path("d/d2/Rakchham_Village%2C_Sangla_Valley.JPG","Manojkhurana","CC BY-SA 3.0","Rakchham Village, Sangla Valley"),
    ],
    "sangla": [
        from_path("a/ad/Baspa_Valley_at_Sangla%2C_Himachal_Pradesh%2C_India.jpg","UnpetitproleX","CC BY-SA 4.0","Baspa Valley at Sangla"),
        from_path("5/5a/Sangla_valley.jpg","Smathur910","CC BY-SA 4.0","Sangla valley"),
        from_path("c/c3/Snowy_morning_in_Sangla%2C_Himachal_Pradesh%2C_India.jpg","UnpetitproleX","CC BY-SA 4.0","Snowy morning in Sangla"),
        from_path("6/68/Orchards_in_snow%2C_Sangla%2C_Himachal_Pradesh%2C_India.jpg","UnpetitproleX","CC BY-SA 4.0","Orchards in snow, Sangla"),
        from_path("c/c9/Kamru_fort_%2CSangla.jpg","Rahulraees","CC BY-SA 4.0","Kamru fort, Sangla"),
    ],
    "hatkoti": [
        from_path("8/8d/Varun_Shiv_Kapur%2C_Hateshwari_Temple_in_Hatkoti.jpg","Varun Shiv Kapur","CC BY 4.0","Hatkoti (file also shows Hateshwari temple)"),
        # skip using temple as a feature photo — use river and town only from search
    ],
    "dakpathar": [
        from_path("e/ea/Dakpathar_Barrage_in_Dakpathar_01.jpg","Pinakpani","CC BY-SA 4.0","Dakpathar Barrage"),
        from_path("c/c0/Dakpathar_barrage_on_Yamuna_river_01.jpg","Pinakpani","CC BY-SA 4.0","Dakpathar barrage on the Yamuna"),
    ],
}

# Drop the temple-primary Hatkoti file from the default set
KNOWN["hatkoti"] = []

NEEDLES = {
    "sissu": ["sissu", "sissu lake", "ghepan", "atal tunnel"],
    "solang": ["solang"],
    "narkanda": ["narkanda", "hatu peak"],
    "kufri": ["kufri"],
    "chitkul": ["chitkul", "chitkul"],
    "sangla": ["sangla", "baspa", "kamru", "karchham", "karcham"],
    "kalpa": ["kalpa", "kinnaur kailash", "roghi"],
    "rakchham": ["rakchham", "rakcham", "rakchham"],
    "jalori": ["jalori", "serolsar", "raghupur"],
    "jibhi": ["jibhi"],
    "chanshal": ["chanshal", "dodra"],
    "dodra": ["dodra"],
    "auli": ["auli"],
    "harsil": ["harsil", "harshil"],
    "chakrata": ["chakrata", "tiger fall", "tiger falls", "deoban"],
    "hatkoti": ["hatkoti", "pabbar"],
    "tiuni": ["tiuni", "tyuni", "tuini"],
    "mori": ["mori"],
    "dakpathar": ["dakpathar", "dak pathar", "dakpatthar"],
    "shivpuri": ["shivpuri"],
    "kaudiyala": ["kaudiyala", "kaudiyala"],
}

TEMPLE_ONLY = re.compile(r"\b(temple|temples|mandir)\b", re.I)
# keep landscapes that only mention a distant peak shrine in passing? If title is clearly a temple close-up, skip.
SKIP_IF = re.compile(r"hatu temple|hatkoti temple|prahat|hateshwari|temple architecture in chitkul|kashi viswanath|gangotri temple", re.I)

def ok_photo(place, p):
    blob = " ".join([p.get("title") or "", p.get("file") or "", p.get("page") or "", p.get("thumb") or ""]).lower()
    if SKIP_IF.search(blob):
        return False
    if TEMPLE_ONLY.search(p.get("title") or "") and not any(n in (p.get("title") or "").lower() for n in ["valley", "peak", "range", "from kalpa", "view"]):
        return False
    for n in NEEDLES.get(place, [place]):
        if n.lower() in blob:
            return True
    return False

def dedupe(photos):
    seen = set(); out = []
    for p in photos:
        key = (p.get("page") or p.get("file") or p.get("title") or "").lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out

def commons_search(query, limit=10):
    url = (
        "https://commons.wikimedia.org/w/api.php?action=query&format=json"
        "&generator=search&gsrnamespace=6&gsrlimit=" + str(limit)
        + "&gsrsearch=" + urllib.parse.quote(query)
        + "&prop=imageinfo&iiprop=url|extmetadata|mime&iiurlwidth=1200"
    )
    time.sleep(0.45)
    try:
        data = get(url)
    except Exception as e:
        print("commons fail", query, e)
        return []
    pages = (data.get("query") or {}).get("pages") or {}
    out = []
    for pg in pages.values():
        info = (pg.get("imageinfo") or [None])[0]
        if not info or not str(info.get("mime") or "").startswith("image/"):
            continue
        meta = info.get("extmetadata") or {}
        def g(k):
            return strip_html((meta.get(k) or {}).get("value") or "")
        lic = g("LicenseShortName") or g("UsageTerms") or ""
        low = lic.lower()
        if not any(s in low for s in ["cc ", "cc0", "cc-by", "public domain", "pd "]):
            if "public domain" not in low and "cc0" not in low:
                continue
        title = g("ObjectName") or (pg.get("title") or "").replace("File:", "")
        out.append({
            "title": title,
            "author": g("Artist") or "Unknown author",
            "license": lic or "see Commons file page",
            "thumb": info.get("thumburl") or info.get("url"),
            "file": info.get("url"),
            "page": "https://commons.wikimedia.org/wiki/" + urllib.parse.quote((pg.get("title") or "").replace(" ", "_")),
        })
    return out

# Extra targeted searches for weak places
EXTRA_Q = {
    "auli": ["Auli Uttarakhand", "Auli Joshimath", "Auli ski Uttarakhand", "Gorson Bugyal Auli", "Auli ropeway"],
    "mori": ["Mori Uttarkashi", "Mori Tons river", "Netwar Mori Uttarakhand"],
    "tiuni": ["Tiuni Uttarakhand", "Tyuni Dehradun", "Tiuni Tons"],
    "rakchham": ["Rakchham Village Sangla", "Rakcham Kinnaur"],
    "dodra": ["Dodra Kwar", "Dodra-Kwar Himachal"],
    "shivpuri": ["Shivpuri Rishikesh Ganga", "Shivpuri rafting Ganges"],
    "kaudiyala": ["Kaudiyala Ganga", "Kaudiyala Rishikesh"],
    "sissu": ["Sissu Lake Lahaul", "Sissu waterfall Himachal", "Atal Tunnel north portal Sissu"],
    "harsil": ["Harsil village", "Harsil Valley Uttarakhand", "Bagori Harsil"],
}

extra_photos = {k: [] for k in EXTRA_Q}
for k, qs in EXTRA_Q.items():
    for q in qs:
        extra_photos[k].extend(commons_search(q, 8))
        print("extra", k, q, "now", len(extra_photos[k]))

# Waypoints used only if they lie close to the measured route (so we do not invent a path)
WAYPOINTS = [
    ("Murthal", 29.027, 77.073),
    ("Ambala", 30.378, 76.780),
    ("Chandigarh (bypass)", 30.694, 76.851),
    ("Solan", 30.9045, 77.0967),
    ("Shimla", 31.1046, 77.1734),
    ("Theog", 31.119, 77.358),
    ("Narkanda", 31.2548, 77.4613),
    ("Rampur Bushahr", 31.4493, 77.6307),
    ("Karcham", 31.501, 78.174),
    ("Reckong Peo", 31.537, 78.268),
    ("Mandi", 31.708, 76.932),
    ("Aut", 31.731, 77.206),
    ("Banjar", 31.637, 77.344),
    ("Manali", 32.2396, 77.1887),
    ("Atal Tunnel (north side)", 32.407, 77.148),
    ("Dehradun", 30.3165, 78.0322),
    ("Rishikesh", 30.0869, 78.2676),
    ("Devprayag", 30.146, 78.599),
    ("Karnaprayag", 30.264, 79.217),
    ("Joshimath", 30.5553, 79.5640),
    ("Haridwar", 29.9457, 78.1642),
    ("Chamba (Uttarakhand)", 30.346, 78.394),
    ("Uttarkashi", 30.7268, 78.4354),
    ("Vikasnagar", 30.4686, 77.7756),
    ("Paonta Sahib", 30.436, 77.624),
    ("Tiuni", 30.9431, 77.8485),
    ("Rohru", 31.202, 77.752),
    ("Hatkoti", 31.1308, 77.7457),
    ("Chakrata", 30.7013, 77.8703),
    ("Sangla", 31.4259, 78.2637),
    ("Rakchham", 31.3923, 78.3538),
    ("Kalpa", 31.5332, 78.2498),
    ("Jibhi", 31.5923, 77.3526),
    ("Shivpuri", 30.135, 78.392),
    ("Kaudiyala", 30.0747, 78.5018),
    ("Dakpathar", 30.4949, 77.7929),
]

def legs_for(geom, total_km, dest_name, dest_lat, dest_lon):
    """geom is [lat,lon] along the OSRM route, already scaled to road km in spacing only approximately.
    Compute cumulative haversine and scale to total_km.
    """
    if not geom or len(geom) < 2:
        return []
    cum = [0.0]
    for i in range(1, len(geom)):
        cum.append(cum[-1] + hav(tuple(geom[i-1]), tuple(geom[i])))
    tot = cum[-1] or 1
    scale = total_km / tot
    found = []
    for name, lat, lon in WAYPOINTS:
        if name.lower() == dest_name.lower() or name.split(" (")[0].lower() == dest_name.lower():
            continue
        best = min(range(len(geom)), key=lambda i: hav(tuple(geom[i]), (lat, lon)))
        d = hav(tuple(geom[best]), (lat, lon))
        if d <= 6.0:
            found.append((cum[best]*scale, name, d))
    # unique names, keep earliest occurrence
    found.sort()
    uniq = []
    seen = set()
    for km, name, d in found:
        if name in seen:
            continue
        # skip very early points < 15 km (still in Delhi) except nothing
        if km < 20:
            continue
        # skip points extremely close to destination
        if total_km - km < 8:
            continue
        seen.add(name)
        uniq.append((round(km, 1), name))
    # build legs from home through uniq to dest
    points = [(0.0, "Shaheen Bagh")] + uniq + [(round(total_km, 1), dest_name)]
    # drop consecutive too-close (<12 km) intermediate towns (keep earlier)
    cleaned = [points[0]]
    for p in points[1:-1]:
        if p[0] - cleaned[-1][0] >= 18:
            cleaned.append(p)
    if points[-1][0] - cleaned[-1][0] < 8 and len(cleaned) > 1:
        cleaned[-1] = points[-1]
    else:
        cleaned.append(points[-1])
    legs = []
    for i in range(1, len(cleaned)):
        a, b = cleaned[i-1], cleaned[i]
        legs.append({"from": a[1], "to": b[1], "km": round(b[0]-a[0], 1), "at_km": b[0]})
    return legs

# Side trips (measured OSRM, this session)
SIDES = {
    "jalori_jibhi": [
        {"from": "Jibhi", "to": "Jalori Pass", "km": 13.1, "osrm_h": 0.15, "note": "Estimate about 30–45 min in real hill traffic if the pass is open."}
    ],
    "chanshal": [
        {"from": "Chanshal Pass", "to": "Dodra Kwar", "km": 35.9, "osrm_h": 0.99, "note": "About 1.5–2 hours extra, only if the pass is officially open."}
    ],
    "kaudiyala": [
        {"from": "Shivpuri", "to": "Kaudiyala", "km": 20.9, "osrm_h": 0.52, "note": "Same Ganges road; about 45–70 min."}
    ],
    "chitkul": [
        {"from": "Sangla", "to": "Chitkul", "km": 23.7, "osrm_h": 0.44, "note": "Via Rakchham, about 1–1.5 hours with photo stops."}
    ],
    "sangla": [
        {"from": "Sangla", "to": "Rakchham", "km": 13.0, "osrm_h": 0.26, "note": "Short valley drive, about 30–45 min."},
        {"from": "Sangla", "to": "Chitkul", "km": 23.7, "osrm_h": 0.44, "note": "About 1–1.5 hours with stops."}
    ],
    "kalpa": [
        {"from": "Kalpa", "to": "Sangla", "km": 48.1, "osrm_h": 0.74, "note": "Via Karcham, about 1.5–2 hours."}
    ],
    "rakchham": [
        {"from": "Sangla", "to": "Rakchham", "km": 13.0, "osrm_h": 0.26, "note": "About 30–45 min."},
        {"from": "Rakchham", "to": "Chitkul", "km": 10.7, "osrm_h": 0.18, "note": "Short last stretch; about 20–40 min when clear. (23.7 − 13.0 km from Sangla legs.)"}
    ],
}

# Don't invent the rakchham-chitkul osrm if I subtracted - 23.7-13.0=10.7 is geometric from two routes from Sangla, not a direct measurement. I should not include an invented time.
# I'll omit the subtracted rakchham-chitkul side or label it clearly as derived, not measured.
SIDES["rakchham"] = [
    {"from": "Sangla", "to": "Rakchham", "km": 13.0, "osrm_h": 0.26, "note": "Measured driving route, about 30–45 min in real time."},
    {"from": "Sangla", "to": "Chitkul", "km": 23.7, "osrm_h": 0.44, "note": "Rakchham sits on this same road."},
]

CURATED = {
"sissu": dict(
    name="Sissu / Atal Tunnel", region="Lahaul, Himachal", kind="snow",
    visited=True, visited_note="You went last year. Listed so you can still compare snow.",
    snow_months="Typically November to March; some years it starts in late October.",
    safety="Atal Tunnel is usually kept open. After fresh snow, police sometimes let only 4×4 cars with chains go beyond Solang towards the Rohtang/Sissu side. Carry chains in a 2WD SUV and fill fuel in Manali. Check Manali traffic police the night before.",
    stay_where="Sissu or Manali (Manali has more cheap beds if Sissu is full or the last road is badly snowed).",
    food_stops=["Murthal / NH44 dhabas","Mandi","Manali (last big town — eat and fill fuel here)"],
    photo_spots=[
        {"name":"Sissu Lake","what":"The small lake below the village, often the postcard shot after a fresh fall."},
        {"name":"Atal Tunnel north portal","what":"The Lahaul-side mouth of the tunnel, with high walls of rock and, in season, snow."},
        {"name":"Sissu waterfall","what":"A roadside waterfall near the village — pretty after snow or a cold spell, can ice up."},
        {"name":"Ghepan / Ghepantrashi views","what":"High lake and peak views above Sissu if the path is clear. Do not walk this in a whiteout."},
    ],
    plan_days=3,
    plan=[
        {"day":1,"title":"Shaheen Bagh to Manali","body":"Long plains-then-hills day (about 10–11 hours with food and photo buffers). Leave at dawn. Eat at a NH44 dhaba, then Mandi or Aut. Night in Manali so you are not crossing to Lahaul in the dark."},
        {"day":2,"title":"Atal Tunnel, Sissu, and back to a bed","body":"Manali to Sissu is much shorter. Go through the tunnel in daylight. Walk the lake and waterfall, take photos, and turn around if police limit 2WD traffic. Night in Sissu if rooms are open, otherwise back to Manali."},
        {"day":3,"title":"Home, or one extra snow morning","body":"If the sky is clear, a short morning walk, then the long drive home. Do not start the Delhi stretch after mid-afternoon."},
    ],
    stay_search="Sissu Himachal OR Manali dorm / homestay",
    toll_rt=1500, toll_note="Estimate for the Delhi–Mandi–Manali Fastag corridor, round trip. Check your Fastag SMS for the real total.",
    corridor="Delhi → NH44 / Chandigarh belt → Mandi → Manali → Atal Tunnel → Sissu",
),
"solang": dict(
    name="Solang Valley", region="near Manali, Himachal", kind="snow",
    visited=False,
    snow_months="Typically December to March.",
    safety="The Manali–Solang road is usually fine for a 2WD SUV when it is clear and ploughed. After fresh snow it can close or become chains-only. Weekends are very crowded. Do not drive onto ski slopes or packed-snow side tracks.",
    stay_where="Solang or Manali.",
    food_stops=["Murthal / NH44 dhabas","Mandi","Manali"],
    photo_spots=[
        {"name":"Solang nala meadow","what":"The open valley floor — snow, paragliders in season, and the classic Manali-side snow shot."},
        {"name":"Road into the valley","what":"Good wide views as you enter Solang; easier parking off the busiest clump."},
    ],
    plan_days=3,
    plan=[
        {"day":1,"title":"Shaheen Bagh to Manali","body":"Same long approach as Sissu. Leave at dawn. Night in Manali or Solang."},
        {"day":2,"title":"Solang in daylight","body":"Go up in the morning before the parking fills. Walk the meadow, take photos, and come down if the crowd or ice gets messy. You can add Sissu the same day only if roads and police allow, and you start early."},
        {"day":3,"title":"Drive home","body":"Long day back to Shaheen Bagh. Start early."},
    ],
    stay_search="Solang Valley OR Manali homestay",
    toll_rt=1500, toll_note="Estimate for the Delhi–Manali Fastag corridor, round trip. Check your Fastag SMS for the real total.",
    corridor="Delhi → NH44 → Mandi → Manali → Solang",
),
"narkanda": dict(
    name="Narkanda", region="Shimla hills, Himachal", kind="snow",
    visited=False,
    snow_months="Typically December to February. More reliable than Kufri, less than Kinnaur or Lahaul.",
    safety="The NH5 town road is usually kept open. The spur to Hatu Peak is steeper and ices over; a 2WD SUV may need chains after snow, or you can skip Hatu and stay in town. Fill fuel before the last climb.",
    stay_where="Narkanda town.",
    food_stops=["Murthal / NH44 dhabas","Solan","Theog or Narkanda"],
    photo_spots=[
        {"name":"Hatu Peak","what":"A high viewpoint above town. Go only if the road is clear. The peak road is the icy bit."},
        {"name":"Narkanda ridgeline and orchards","what":"Apple country around town — quiet snow shots after a fall, without the Kufri crowd."},
        {"name":"Tani Jubbar Lake","what":"A small lake a short drive from town, often mentioned by travellers. Confirm the side road is clear before you go."},
    ],
    plan_days=2,
    plan=[
        {"day":1,"title":"Shaheen Bagh to Narkanda","body":"About a full day with stops (realistic one-way around 9 hours). Leave early. Photo stop at a viewpoint after Solan or Theog if the light is good. Night in Narkanda."},
        {"day":2,"title":"Hatu (if open) and drive home","body":"Morning at Hatu Peak or the orchards, then the long drive back. If you want a slower trip, add a night and come home on day 3."},
    ],
    stay_search="Narkanda homestay",
    toll_rt=1200, toll_note="Estimate for the Delhi–Solan–Shimla Fastag corridor, round trip. Check your Fastag SMS.",
    corridor="Delhi → NH44 → Solan → Shimla / Theog → Narkanda",
),
"kufri": dict(
    name="Kufri", region="above Shimla, Himachal", kind="snow",
    visited=False,
    snow_months="Typically December to February, but snow here is less reliable than at higher places on this list.",
    safety="Closest snow belt to Delhi on this list. Roads are busy and can be icy. A 2WD SUV is usually fine to the main market when the road is clear. Parking is tight. Do not follow ponies or crowd vehicles onto snow banks.",
    stay_where="Kufri or Shimla (Shimla has more cheap beds).",
    food_stops=["Murthal / NH44 dhabas","Solan","Shimla"],
    photo_spots=[
        {"name":"Kufri ridge / Mahasu Peak side","what":"Wide Himalayan views on a clear day, a short walk or local ride from the market."},
        {"name":"Green Valley viewpoint, on the way","what":"A known roadside view between Shimla and Kufri."},
        {"name":"Fagu","what":"A quieter ridge a little beyond Kufri, useful if the Kufri parking is packed."},
    ],
    plan_days=2,
    plan=[
        {"day":1,"title":"Shaheen Bagh to Kufri or Shimla","body":"Realistic one-way about 7–8 hours with stops. Night up in Kufri, or in Shimla if rooms are cheaper."},
        {"day":2,"title":"Morning views, then home","body":"Walk the ridge early, before the day-crowd. Drive back after lunch. A same-day Delhi–Kufri–Delhi dash is possible but makes a very long, tiring day."},
    ],
    stay_search="Kufri OR Shimla hostel / homestay",
    toll_rt=1200, toll_note="Estimate for the Delhi–Solan–Shimla Fastag corridor, round trip. Check your Fastag SMS.",
    corridor="Delhi → NH44 → Solan → Shimla → Kufri",
),
"chitkul": dict(
    name="Chitkul", region="Baspa valley, Kinnaur", kind="snow",
    visited=True, visited_note="You stayed at a riverfront cottage here on 8 November 2026.",
    snow_months="Typically November to March. The village is high, so it can get snow earlier than Sangla.",
    safety="Long drive: NH5 into the Sangla valley road, which is narrow with drop-offs. Last reliable petrol is usually around Reckong Peo or Bhabanagar — fill up. After heavy snow the valley road can close. A 2WD SUV is commonly used when the road is clear and ploughed. Do not push through fresh unploughed snow. There is little help after Karcham at night.",
    stay_where="Chitkul village (riverfront and village homestays). Rakchham is the fallback if the last stretch is bad.",
    food_stops=["Solan","Narkanda or Rampur Bushahr","Reckong Peo / Karcham (last proper market)"],
    photo_spots=[
        {"name":"Baspa riverfront","what":"The open river beside the village — the shot you already know."},
        {"name":"Village lanes and wooden houses","what":"Walk, don't drive, the inner lanes."},
        {"name":"Meadows at the edge of the village","what":"Short walks up-valley; turn back if cloud or wind builds."},
        {"name":"Road between Rakchham and Chitkul","what":"Baspa views all the way. Stop only in safe lay-bys."},
    ],
    plan_days=4,
    plan=[
        {"day":1,"title":"Shaheen Bagh to Rampur or Reckong Peo","body":"Do not try to reach Chitkul in one shot (realistic one-way is about 15–16 hours). Break at Rampur Bushahr or Reckong Peo / Kalpa. Photo stops: a Satluj view after Rampur, and Karcham if you still have light."},
        {"day":2,"title":"Into the Baspa valley, night at Chitkul","body":"Karcham to Sangla, Rakchham and Chitkul, with short photo stops. Arrive in daylight. Walk the riverfront in the evening if the weather is kind."},
        {"day":3,"title":"A slow day in the village","body":"Morning walk and photos. If you must start home the same afternoon, leave by 11:00 so you are not on NH5 after dark. A calmer plan is one full day here and a night back at Kalpa or Rampur."},
        {"day":4,"title":"Drive towards Delhi","body":"A full, tiring return. Split it if you can (Rampur or Solan). You already know this road from the November trip."},
    ],
    stay_search="Chitkul homestay OR Chitkul river cottage",
    toll_rt=1400, toll_note="Estimate for the Delhi–Solan–Shimla Fastag corridor, round trip. Your November trip Fastag recharge was ₹500 — that may not have been the full toll total. Use your Fastag statement if you have it.",
    corridor="Delhi → Solan → Shimla / Narkanda → Rampur Bushahr → Karcham → Sangla → Chitkul",
),
"sangla": dict(
    name="Sangla", region="Baspa valley, Kinnaur", kind="snow",
    visited=False,
    snow_months="Typically December to March.",
    safety="Same valley road as Chitkul, a little lower and busier. Fill petrol at Reckong Peo or Bhabanagar. A 2WD SUV is usually fine when the road is ploughed. Do not drive the last Chitkul stretch after a fresh, unploughed fall.",
    stay_where="Sangla or nearby Batseri.",
    food_stops=["Solan","Rampur Bushahr","Reckong Peo / Karcham"],
    photo_spots=[
        {"name":"Baspa Valley from Sangla","what":"Wide orchard and river views, especially after snow."},
        {"name":"Kamru Fort","what":"An old fort above the village — a short walk, not a highway stop."},
        {"name":"Batseri village","what":"A pretty wooden village a short drive up-valley towards Rakchham."},
        {"name":"Road to Rakchham and Chitkul","what":"Easy add-on if the road is clear."},
    ],
    plan_days=3,
    plan=[
        {"day":1,"title":"Shaheen Bagh to Rampur or Kalpa / Reckong Peo","body":"Same first day as the Chitkul drive. Do not push all the way in one go (one-way is about 15 hours realistic)."},
        {"day":2,"title":"Sangla, Batseri, maybe Chitkul","body":"Arrive in daylight. Walk Kamru if you want, then the valley. Chitkul is about 24 km further — a half-day add-on, not a night drive."},
        {"day":3,"title":"Start home, or add a night","body":"A 3-day trip means a very long day 3. A 4-day trip is kinder."},
    ],
    stay_search="Sangla OR Batseri homestay",
    toll_rt=1400, toll_note="Estimate for the Delhi–Solan Fastag corridor, round trip. Check your Fastag SMS.",
    corridor="Delhi → Solan → Narkanda → Rampur → Karcham → Sangla",
),
"kalpa": dict(
    name="Kalpa", region="Kinnaur, Himachal", kind="snow",
    visited=False,
    snow_months="Typically December to March.",
    safety="Kalpa sits on a steep spur above Reckong Peo, off NH5. The village road can be icy. A 2WD SUV is usually fine when it is clear. Fill fuel in Reckong Peo. After heavy snow, walk the last icy lanes rather than forcing the car.",
    stay_where="Kalpa village.",
    food_stops=["Solan","Rampur Bushahr","Reckong Peo"],
    photo_spots=[
        {"name":"Kinnaur Kailash from Kalpa","what":"The classic dawn or dusk view of the Kailash massif across the valley."},
        {"name":"Kalpa village and orchards","what":"Wooden houses and apple trees, with the big peaks behind."},
        {"name":"Roghi village","what":"A short drive / walk, known for cliff-edge views. The road is narrow."},
        {"name":"Suicide Point viewpoint","what":"A named cliff viewpoint near Kalpa. Stay behind the edge; it is a drop, not a playground."},
    ],
    plan_days=3,
    plan=[
        {"day":1,"title":"Shaheen Bagh to Kalpa or Reckong Peo","body":"A long day (realistic one-way about 15 hours). Leave at dawn, or split with a night at Rampur. Arrive before dark — the spur road is not a night drive if it is icy."},
        {"day":2,"title":"Views, Roghi, optional Sangla","body":"Sunrise on Kailash if the sky is clear. Roghi in the late morning. Sangla is about 48 km via Karcham if you want a second valley."},
        {"day":3,"title":"Drive toward Delhi","body":"Start early. Break at Solan if you tire."},
    ],
    stay_search="Kalpa Kinnaur homestay",
    toll_rt=1400, toll_note="Estimate for the Delhi–Solan Fastag corridor, round trip. Check your Fastag SMS.",
    corridor="Delhi → Solan → Narkanda → Rampur → Reckong Peo → Kalpa",
),
"rakchham": dict(
    name="Rakchham", region="Baspa valley, Kinnaur", kind="snow",
    visited=False,
    snow_months="Typically November to March.",
    safety="Sits on the Sangla–Chitkul road. Same fuel and closure advice as Chitkul. A quiet base if Chitkul rooms are full or the last stretch is in poor shape. 2WD is usually fine when the road is ploughed.",
    stay_where="Rakchham village.",
    food_stops=["Solan","Rampur Bushahr","Reckong Peo / Karcham","Sangla"],
    photo_spots=[
        {"name":"Rakchham village and meadows","what":"Open fields around the houses, with high walls of rock and snow."},
        {"name":"Baspa river","what":"Short walks along the river. The road to Chitkul is the photo strip."},
        {"name":"Chitkul day trip","what":"Just up the same road when it is clear."},
    ],
    plan_days=3,
    plan=[
        {"day":1,"title":"Shaheen Bagh to Rampur or Sangla side","body":"Split the long NH5 drive. Do not aim for Rakchham after dark."},
        {"day":2,"title":"Meadows and a Chitkul run","body":"Walk the village in the morning. If the road is open, go to Chitkul for a few hours and return."},
        {"day":3,"title":"Drive toward Delhi","body":"Early start. A fourth day is more comfortable."},
    ],
    stay_search="Rakchham OR Rakcham homestay",
    toll_rt=1400, toll_note="Estimate for the Delhi–Solan Fastag corridor, round trip. Check your Fastag SMS.",
    corridor="Delhi → Solan → Rampur → Karcham → Sangla → Rakchham",
),
"jalori_jibhi": dict(
    name="Jalori Pass / Jibhi", region="Banjar / Inner Seraj, Himachal", kind="snow",
    visited=False,
    snow_months="The pass (about 3,140 m) often holds snow from December to March and is often closed then. Jibhi village is much lower (about 1,780 m) and gets less snow.",
    safety="In winter, drive to Jibhi via Aut and Banjar. Do not plan to cross Jalori Pass after snowfall — it is often shut. A 2WD SUV is usually fine to Jibhi when the Banjar road is open. Carry chains only if you go up towards Shoja or the pass, and turn back if the road is not ploughed.",
    stay_where="Jibhi (the usual bed base). Shoja is higher and closer to the pass, only if that road is open.",
    food_stops=["Murthal / NH44 dhabas","Mandi or Aut","Banjar / Jibhi"],
    photo_spots=[
        {"name":"Jibhi river and wooden bridges","what":"The village stream, footbridges and walkways — easy, close to your stay."},
        {"name":"Jibhi waterfall","what":"A short walk from the village. Can be slippery after rain or ice."},
        {"name":"Jalori Pass","what":"Big Himalayan views, only if the pass is officially open."},
        {"name":"Serolsar Lake","what":"A forest lake walk from the pass, when the pass itself is open. Not a last-light outing."},
        {"name":"Raghupur Fort","what":"A ridge walk from the Shoja / Jalori side, in clear weather."},
    ],
    plan_days=3,
    plan=[
        {"day":1,"title":"Shaheen Bagh to Jibhi, via Aut–Banjar","body":"Realistic one-way about 10 hours with stops. Leave early. Do not come in over Jalori in winter. Night in Jibhi."},
        {"day":2,"title":"Village walks, or the pass if it is open","body":"Waterfall and river in the morning. Only drive up to Jalori if locals and the road status say it is open. Serolsar is an extra walk from the pass, not a rushed add-on."},
        {"day":3,"title":"Drive home the same Aut–Banjar way","body":"Start early. The plains stretch after Mandi is long."},
    ],
    stay_search="Jibhi homestay",
    toll_rt=1400, toll_note="Estimate for the Delhi–Mandi Fastag corridor, round trip. Check your Fastag SMS.",
    corridor="Delhi → NH44 → Mandi → Aut → Banjar → Jibhi (Jalori Pass is a 13 km side road, only if open)",
    route_from="jibhi",
    extra_coords=["jalori"],
),
"chanshal": dict(
    name="Chanshal / Dodra Kwar", region="Rohru hills, Himachal", kind="snow",
    visited=False,
    snow_months="The pass (about 3,760 m) can hold snow from November into spring, and is often closed for a long mid-winter stretch. Dodra Kwar, beyond the pass, can be cut off.",
    safety="This is the highest road on the list. A 2WD SUV should not attempt Chanshal Pass with fresh or packed snow. Go only when Rohru locals and the local administration say the pass is open and ploughed or dry. There is almost no recovery once you are on the top. Dodra Kwar is a further 36 km after the pass.",
    stay_where="Rohru, or a village on the near side of the pass (for example Larot) if you find a bed. Do not plan a Dodra night unless the pass is firmly open both ways.",
    food_stops=["Dehradun or Vikasnagar","Chakrata or Rohru (last proper town before the pass)"],
    photo_spots=[
        {"name":"Chanshal Pass","what":"A huge high meadow and Himalayan wall, in the short season the road is open."},
        {"name":"Road to the pass","what":"Climbing views above Rohru. Stop only in safe cut-outs."},
        {"name":"Dodra Kwar valley","what":"A remote inhabited valley on the far side — only as an extra if the pass is open and you have daylight to return, or a confirmed bed."},
    ],
    plan_days=3,
    plan=[
        {"day":1,"title":"Shaheen Bagh to Rohru","body":"Realistic one-way to the pass is about 9–10 hours, so sleep in Rohru (or nearby) rather than climbing late. The usual approach is via Vikasnagar / the Chakrata–Rohru belt."},
        {"day":2,"title":"The pass, only if it is open","body":"Leave early. If the pass is shut or icy, stay lower and walk around Rohru / the Pabbar, or visit Hatkoti. If it is open and dry, go up, take photos, and come down in daylight unless you have a confirmed Dodra plan."},
        {"day":3,"title":"Drive home","body":"Full day back to Shaheen Bagh. Start early."},
    ],
    stay_search="Rohru OR Larot OR Chanshal homestay",
    toll_rt=1300, toll_note="Estimate for the Delhi–Dehradun expressway plus hill roads, round trip. Check your Fastag SMS.",
    corridor="Delhi → Dehradun expressway → Vikasnagar → towards Rohru → Chanshal Pass",
),
"auli": dict(
    name="Auli", region="above Joshimath, Uttarakhand", kind="snow",
    visited=False,
    snow_months="Typically December to March (it is a ski meadow).",
    safety="Drive to Joshimath, then either the Auli road or the ropeway. After snow, the Auli road may need chains or may close; the ropeway is the safer way up if it is running. Check the Joshimath road status the night before. Fill fuel in Joshimath. A 2WD SUV is usually fine to Joshimath when that highway is open.",
    stay_where="Auli (if the road or ropeway is running) or Joshimath.",
    food_stops=["Dehradun or Rishikesh","A town along the river highway (for example Karnaprayag)","Joshimath (last proper town)"],
    photo_spots=[
        {"name":"Auli meadows","what":"Open snow slopes and big mountain views in season."},
        {"name":"Gorson Bugyal","what":"A known meadow walk beyond Auli, in clear, stable weather only."},
        {"name":"Joshimath ropeway","what":"The cable car itself is the view, if it is operating. Confirm timings the night before."},
    ],
    plan_days=3,
    plan=[
        {"day":1,"title":"Shaheen Bagh to Joshimath","body":"Realistic one-way about 15 hours — too long for one comfortable day. Break at Rishikesh or along the river highway, or leave at a very early hour and accept a late arrival. Do not climb the Auli road in the dark after snow."},
        {"day":2,"title":"Auli meadows","body":"Up by road or ropeway. Walk, photograph, and come down before the last ropeway if that is your only way back."},
        {"day":3,"title":"Drive toward Delhi","body":"Another long day. Split it if you can."},
    ],
    stay_search="Auli OR Joshimath homestay",
    toll_rt=1200, toll_note="Estimate for the Delhi–Dehradun expressway plus the onward highway, round trip. Check your Fastag SMS.",
    corridor="Delhi → Dehradun expressway → Rishikesh → river highway → Joshimath → Auli",
),
"harsil": dict(
    name="Harsil", region="Bhagirathi valley, Uttarakhand", kind="snow",
    visited=False,
    snow_months="Typically December to March.",
    safety="Beyond Uttarkashi on the Gangotri road, along the Bhagirathi river. The road can close after heavy snow or landslides. A 2WD SUV is usually fine when the road is open and ploughed. Fill fuel in Uttarkashi. There may be checkpoints. This page is about the valley and riverside villages, not a temple run.",
    stay_where="Harsil, or nearby Bagori / Dharali if you find a bed.",
    food_stops=["Dehradun or Rishikesh","Uttarkashi (last proper town — eat and fill fuel)"],
    photo_spots=[
        {"name":"Harsil village and orchards","what":"The main valley floor, apple trees, and the river."},
        {"name":"Bagori village","what":"A wooden village a few kilometres away, often quieter."},
        {"name":"Bhagirathi river banks","what":"Short riverside walks. The water is very cold; stay off the rocks in spate."},
        {"name":"Dharali","what":"Another small valley settlement on the same road, useful for a short wander."},
    ],
    plan_days=3,
    plan=[
        {"day":1,"title":"Shaheen Bagh to Uttarkashi or Harsil","body":"Realistic one-way about 9–10 hours. You can reach Harsil the same day if you leave at dawn and the road is open. Otherwise night in Uttarkashi and go up in the morning."},
        {"day":2,"title":"Valley villages and the river","body":"Walk Harsil, Bagori and the riverside in daylight. This is a slow valley, not a checklist."},
        {"day":3,"title":"Drive home","body":"Full day back. Start early."},
    ],
    stay_search="Harsil OR Bagori OR Dharali homestay",
    toll_rt=1200, toll_note="Estimate for the Delhi–Dehradun expressway plus the onward highway, round trip. Check your Fastag SMS.",
    corridor="Delhi → Dehradun expressway → towards Uttarkashi → Harsil",
),
"chakrata": dict(
    name="Chakrata", region="Jaunsar, Uttarakhand", kind="snow",
    visited=False,
    snow_months="Typically December to February, and not every year — it is the lowest ‘snow’ town on the main list, so treat snow as a bonus, not a promise.",
    safety="Closest high village from Shaheen Bagh. Forest roads can be narrow and foggy. A 2WD SUV is usually fine in clear weather. After a rare snow, roads ice over. The Tiger Falls spur is a side road — go in daylight. Fill fuel in Dehradun or Vikasnagar.",
    stay_where="Chakrata town.",
    food_stops=["A stop on the Dehradun expressway or in Dehradun","Vikasnagar / Dakpathar","Chakrata"],
    photo_spots=[
        {"name":"Tiger Falls","what":"A tall waterfall a short drive and a walk from town. The path can be wet and slippery."},
        {"name":"Deoban","what":"A forest ridgeline with long views, a drive from Chakrata. Go only in clear weather; fog comes in fast."},
        {"name":"Chilmiri Neck","what":"A known sunset viewpoint above town."},
        {"name":"Moila / Budher side","what":"A longer forest outing from Chakrata. Only with time and a clear road; it is not a rushed evening trip."},
    ],
    plan_days=2,
    plan=[
        {"day":1,"title":"Shaheen Bagh to Chakrata, falls in the afternoon","body":"Realistic one-way about 6 hours, so a late-morning start still works. See Tiger Falls in daylight. Night in Chakrata."},
        {"day":2,"title":"Deoban or Chilmiri, then home","body":"A ridge walk or viewpoint in the morning, then drive back to Shaheen Bagh the same afternoon."},
    ],
    stay_search="Chakrata homestay",
    toll_rt=1200, toll_note="Estimate for the Delhi–Dehradun expressway, round trip. Check your Fastag SMS.",
    corridor="Delhi → Dehradun expressway → Vikasnagar → Chakrata",
),
"hatkoti": dict(
    name="Hatkoti", region="Pabbar river, Himachal", kind="riverside",
    visited=False,
    snow_months="The village itself is about 1,420 m, so it is not a snow destination. Higher roads towards Rohru and Chanshal may have snow in mid-winter.",
    safety="A Pabbar river village on the Jubbal–Rohru belt. The hill road is fine for a 2WD SUV in dry weather. After heavy rain, watch for slips. This is a riverside stop, not a high-pass drive.",
    stay_where="Hatkoti or nearby Jubbal / Rohru.",
    food_stops=["Dehradun or Vikasnagar","A town on the way (Jubbal or Rohru)"],
    photo_spots=[
        {"name":"Pabbar river at Hatkoti","what":"The river running through the valley — the reason to come."},
        {"name":"Village and valley views","what":"Terraces and the wide Pabbar valley in afternoon light."},
    ],
    plan_days=2,
    plan=[
        {"day":1,"title":"Shaheen Bagh to Hatkoti","body":"Realistic one-way about 8 hours. Arrive for a late-afternoon river walk. Night in or near Hatkoti."},
        {"day":2,"title":"Slow morning, then home","body":"River light in the morning, then the drive back. You can add Rohru if you have extra time and energy."},
    ],
    stay_search="Hatkoti OR Jubbal OR Rohru homestay",
    toll_rt=1300, toll_note="Estimate for the Delhi–Dehradun expressway plus hill roads, round trip. Check your Fastag SMS.",
    corridor="Delhi → Dehradun expressway → towards the Pabbar valley → Hatkoti",
),
"tiuni": dict(
    name="Tiuni", region="Tons river, Uttarakhand–HP border", kind="riverside",
    visited=False,
    snow_months="The town is about 935 m, so snow in the bazaar is uncommon. Higher side-roads can see winter snow.",
    safety="On the Tons, on the Paonta–Rohru road (NH707). Hill road with some rough stretches, fine for a 2WD SUV in dry weather. Fill fuel before the long hill section (Dehradun / Paonta / Vikasnagar). Services in town are modest.",
    stay_where="Tiuni (also spelled Tyuni).",
    food_stops=["Dehradun or Paonta Sahib","Tiuni"],
    photo_spots=[
        {"name":"Tons river at Tiuni","what":"The river and the border-town valley. Walk the banks in daylight."},
        {"name":"NH707 valley road","what":"Wooded river-road views on the way in. Stop only where there is a safe shoulder."},
    ],
    plan_days=2,
    plan=[
        {"day":1,"title":"Shaheen Bagh to Tiuni","body":"Realistic one-way about 7–8 hours. Evening by the Tons. Night in Tiuni."},
        {"day":2,"title":"Morning river, then home — or continue to Mori","body":"Mori is a little further up the Tons if you want a quieter village. Otherwise drive back the same day."},
    ],
    stay_search="Tiuni OR Tyuni Uttarakhand homestay",
    toll_rt=1200, toll_note="Estimate for the Delhi–Dehradun expressway plus hill roads, round trip. Check your Fastag SMS.",
    corridor="Delhi → Dehradun expressway or Paonta belt → NH707 → Tiuni",
),
"mori": dict(
    name="Mori", region="Tons river, Uttarkashi", kind="riverside",
    visited=False,
    snow_months="The village is about 1,180 m, so it is a river destination, not a snow bowl. Higher forests around Govind Pashu Vihar get winter snow.",
    safety="An offbeat Tons village past Tiuni, in the Govind Pashu Vihar area. The valley road is narrow. A 2WD SUV is usually fine in dry weather. Services are limited — fill fuel at the last proper pump you pass (often before or at the Tiuni / Purola side; check on the day). Do not drive this road at night in rain.",
    stay_where="Mori, or a riverside camp if you find one with a real listing that day.",
    food_stops=["Dehradun or Paonta Sahib","Tiuni (last small market before Mori)"],
    photo_spots=[
        {"name":"Tons river at Mori","what":"Clear river, stones and forest walls — the main reason to come."},
        {"name":"Valley road along the Tons","what":"Short walks from the village. This is a quiet stretch, not a sightseeing bus route."},
    ],
    plan_days=2,
    plan=[
        {"day":1,"title":"Shaheen Bagh to Mori","body":"Realistic one-way about 8 hours. Arrive in daylight. Night by the river."},
        {"day":2,"title":"River morning, then home","body":"A slow morning, then the same road back. Three days would be kinder if you want longer walks."},
    ],
    stay_search="Mori Uttarkashi OR Mori Tons homestay",
    toll_rt=1200, toll_note="Estimate for the Delhi–Dehradun expressway plus hill roads, round trip. Check your Fastag SMS.",
    corridor="Delhi → towards Tiuni → Mori on the Tons",
),
"kaudiyala": dict(
    name="Shivpuri & Kaudiyala", region="Ganges, beyond Rishikesh", kind="riverside",
    visited=False,
    snow_months="River-level (about 370–440 m). No snow here. Come for the Ganges, not for a white landscape.",
    safety="The Rishikesh–Badrinath river road is usually open and is fine for a 2WD SUV. Weekends are busy with rafting traffic. Park only in safe, obvious spots. This is not a snow drive.",
    stay_where="Shivpuri or Kaudiyala (riverside camps and guesthouses — verify a live listing; names change often).",
    food_stops=["A stop on the Dehradun expressway or in Rishikesh","Shivpuri / Kaudiyala"],
    photo_spots=[
        {"name":"Ganges at Shivpuri","what":"The first big river beach stretch after Rishikesh, popular for rafting put-ins."},
        {"name":"Ganges at Kaudiyala","what":"A quieter bend about 21 km further up the same road, with steep green walls."},
        {"name":"River road viewpoints","what":"Several lay-bys between the two villages. Take photos off the live carriageway."},
    ],
    plan_days=2,
    plan=[
        {"day":1,"title":"Shaheen Bagh to Shivpuri, on to Kaudiyala","body":"Realistic one-way about 5–6 hours, so an easy afternoon arrival. Walk the river, stay the night."},
        {"day":2,"title":"Morning on the Ganges, then home","body":"You can also treat this as a long day trip, but a night by the river is calmer."},
    ],
    stay_search="Kaudiyala OR Shivpuri Rishikesh camp / guesthouse",
    toll_rt=1100, toll_note="Estimate for the Delhi–Dehradun expressway, round trip. Check your Fastag SMS.",
    corridor="Delhi → Dehradun expressway → Rishikesh → Shivpuri → Kaudiyala",
    route_from="kaudiyala",
    extra_coords=["shivpuri"],
),
}

# Combine photos
def collect_photos(raw_key, aliases=None):
    aliases = aliases or [raw_key]
    acc = []
    for a in aliases:
        acc += [p for p in RAW["photos"].get(a, []) if ok_photo(a, p)]
        acc += [p for p in extra_photos.get(a, []) if ok_photo(a, p)]
        acc += KNOWN.get(a, [])
    # second pass: filter by any alias needles
    needles = []
    for a in aliases:
        needles += NEEDLES.get(a, [a])
    out = []
    for p in acc:
        blob = " ".join([p.get("title") or "", p.get("file") or "", p.get("page") or ""]).lower()
        if SKIP_IF.search(blob):
            continue
        if any(n.lower() in blob for n in needles):
            # clean author/title
            p = dict(p)
            p["title"] = strip_html(p.get("title") or "")
            p["author"] = strip_html(p.get("author") or "Unknown author")
            out.append(p)
    return dedupe(out)[:8]

spots = []
# Display order
ORDER = [
    "sissu","solang","narkanda","kufri","chitkul","sangla","kalpa","rakchham",
    "jalori_jibhi","chanshal","auli","harsil","chakrata",
    "hatkoti","tiuni","mori","kaudiyala",
]

for sid in ORDER:
    meta = CURATED[sid]
    rk = meta.get("route_from", sid if sid in RAW["routes"] else None)
    if sid == "jalori_jibhi":
        rk = "jibhi"
    if sid == "kaudiyala":
        rk = "kaudiyala"
    rt = RAW["routes"][rk]
    co = RAW["coords"][rk]
    photos = collect_photos(rk, {
        "jalori_jibhi": ["jibhi","jalori"],
        "chanshal": ["chanshal","dodra"],
        "kaudiyala": ["kaudiyala","shivpuri"],
        "sangla": ["sangla"],
        "harsil": ["harsil"],
        "auli": ["auli"],
    }.get(sid, [rk]))

    geom = rt["geometry"]
    dest_name = meta["name"].split(" / ")[0].split("&")[0].strip()
    if sid == "jalori_jibhi":
        dest_name = "Jibhi"
    if sid == "kaudiyala":
        dest_name = "Kaudiyala"
    if sid == "chanshal":
        dest_name = "Chanshal Pass"
    legs = legs_for(geom, rt["km"], dest_name, co["lat"], co["lon"])

    el = co["el"]
    # For combined places, also expose the high point elevation
    extra_el = None
    if sid == "jalori_jibhi":
        extra_el = {"label": "Jalori Pass", "el": RAW["coords"]["jalori"]["el"], "lat": RAW["coords"]["jalori"]["lat"], "lon": RAW["coords"]["jalori"]["lon"]}
    if sid == "chanshal":
        extra_el = {"label": "Dodra Kwar", "el": RAW["coords"]["dodra"]["el"], "lat": RAW["coords"]["dodra"]["lat"], "lon": RAW["coords"]["dodra"]["lon"],
                    "km": RAW["routes"]["dodra"]["km"], "realistic_h": RAW["routes"]["dodra"]["realistic_h"]}

    spots.append({
        "id": sid,
        "name": meta["name"],
        "region": meta["region"],
        "kind": meta["kind"],
        "visited": bool(meta.get("visited")),
        "visited_note": meta.get("visited_note"),
        "lat": co["lat"],
        "lon": co["lon"],
        "elevation_m": el,
        "extra": extra_el,
        "one_way_km": rt["km"],
        "osrm_hours": rt["osrm_h"],
        "realistic_hours": rt["realistic_h"],
        "time_note": rt["time_note"],
        "terrain": rt["cls"],
        "route_min_m": rt["minel"],
        "route_max_m": rt["maxel"],
        "petrol_round_trip": rt["petrol_round_trip"],
        "geometry": geom,
        "legs": legs,
        "side_trips": SIDES.get(sid, []),
        "snow_months": meta["snow_months"],
        "safety": meta["safety"],
        "stay_where": meta["stay_where"],
        "stay_search": meta["stay_search"],
        "stay_disclaimer": "No live room or price is listed here. Search Booking.com or Airbnb for a bed-only room, dorm or homestay. Names and rates change, so only trust a listing you open yourself.",
        "food_stops": meta["food_stops"],
        "food_disclaimer": "These are towns on the way where travellers usually eat — not booked restaurants. I have not verified any named dhaba. Look around and check recent reviews the same day.",
        "photo_spots": meta["photo_spots"],
        "photos": photos,
        "plan_days": meta["plan_days"],
        "plan": meta["plan"],
        "toll_rt_estimate": meta["toll_rt"],
        "toll_note": meta["toll_note"],
        "corridor": meta["corridor"],
    })
    print(sid, "photos", len(photos), "legs", len(legs), [l["to"] for l in legs], "el", el)

home = {
    "generated_at": RAW["generated_at"],
    "timezone": "Asia/Calcutta (UTC+5:30)",
    "home": RAW["home"],
    "vehicle": "Petrol Mahindra XUV700",
    "mileage_note": RAW["petrol_note"],
    "osrm_note": RAW["osrm_note"],
    "petrol_inr_per_litre": P,
    "budget_defaults": {
        "meal_per_person_per_day": 350,
        "meal_note": "Assumption for 3 cheap meals a day, about ₹350 per person per day. Change it if your group eats more or less.",
        "bed_per_person_per_night": 700,
        "bed_note": "A typical cheap hill homestay or dorm bed is often around ₹500–800 in the quieter season. ₹700 is only a planning figure, not a quote.",
        "people": 3,
    },
    "tips": [
        {"title":"Do not get stuck","body":"A 2WD XUV700 is fine on a ploughed, open road. It is not a snow-plough. If the road is unploughed, or police say 4×4 and chains only, turn around. Carry chains, a torch, water and a full tank."},
        {"title":"Check the road the night before","body":"Look at the latest update from the local police, district administration or BRO for that stretch (Manali, Kinnaur, Joshimath, Uttarkashi, Rohru). A Friday plan can be wrong by Saturday morning."},
        {"title":"Times on this site are honest-but-slow","body":"The raw router times are optimistic. The ‘realistic’ hours already add a hill buffer and 30 minutes for food and fuel. Photo stops are extra, and are written into each day plan."},
        {"title":"Fuel, not just scenery","body":"Fill up in the last proper town — often Manali, Reckong Peo / Bhabanagar, Joshimath, Uttarkashi, Rohru or Vikasnagar. Do not count on a pump in a high village."},
    ],
    "forecast_note": "Snow figures come live from the Open-Meteo weather model, using each place’s real elevation. They are model estimates, not a person standing in the village. A short flurry can be missed; a forecast can be wrong. The time on the grid is when this page last fetched the data.",
    "spots": spots,
}

OUT.write_text(json.dumps(home, ensure_ascii=False, separators=(",", ":")))
print("WROTE", OUT, "bytes", OUT.stat().st_size)
