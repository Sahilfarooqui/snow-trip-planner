#!/usr/bin/env python3
"""Precompute OSRM routes, terrain-aware petrol, elevations, and Wikimedia photos.
Never invent coordinates: Nominatim first, then well-known fallbacks only if search is empty.
"""
import json, math, time, urllib.parse, urllib.request, os
from datetime import datetime, timezone, timedelta

UA = "SahilSnowTripPlanner/1.0 (personal trip planner; contact: shaheen-bagh)"
OUT = "/workspace/snow-trip-planner/public/data"
os.makedirs(OUT, exist_ok=True)

def get(url, timeout=90, retries=5):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except Exception as e:
            last = e
            time.sleep(2 + i * 2)
    raise last

def hav(a, b):
    R = 6371.0
    p1, p2 = math.radians(a[1]), math.radians(b[1])
    dl = math.radians(b[0] - a[0])
    dp = p2 - p1
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(h))

HOME = {"name": "Shaheen Bagh, Delhi", "lat": 28.5516, "lon": 77.3000, "el": 210}

# Seed coords are well-known published locations; Nominatim will confirm/refine.
SEEDS = {
    "sissu": ("Sissu, Lahaul, Himachal Pradesh", 32.4806, 77.1278),
    "solang": ("Solang Valley, Himachal Pradesh", 32.3162, 77.1578),
    "narkanda": ("Narkanda, Himachal Pradesh", 31.2569, 77.4606),
    "kufri": ("Kufri, Himachal Pradesh", 31.0978, 77.2678),
    "chitkul": ("Chitkul, Himachal Pradesh", 31.3518, 78.4359),
    "sangla": ("Sangla, Himachal Pradesh", 31.4258, 78.2661),
    "kalpa": ("Kalpa, Himachal Pradesh", 31.5300, 78.2500),
    "rakchham": ("Rakchham, Himachal Pradesh", 31.3770, 78.3660),
    "jalori": ("Jalori Pass, Himachal Pradesh", 31.5383, 77.3675),
    "jibhi": ("Jibhi, Himachal Pradesh", 31.5930, 77.3610),
    "chanshal": ("Chanshal Pass, Himachal Pradesh", 31.1971, 77.9887),
    "dodra": ("Dodra Kwar, Himachal Pradesh", 31.2571, 78.1516),
    "auli": ("Auli, Uttarakhand", 30.5284, 79.5669),
    "harsil": ("Harsil, Uttarakhand", 31.0333, 78.7333),
    "chakrata": ("Chakrata, Uttarakhand", 30.7037, 77.8639),
    # riverside / offbeat candidates (1-day drive filter applied later)
    "hatkoti": ("Hatkoti, Himachal Pradesh", 31.1230, 77.7440),
    "tiuni": ("Tiuni, Uttarakhand", 30.9400, 77.8500),
    "mori": ("Mori, Uttarkashi, Uttarakhand", 31.0160, 77.9530),
    "dakpathar": ("Dakpathar, Uttarakhand", 30.4970, 77.8000),
    "shivpuri": ("Shivpuri, Rishikesh, Uttarakhand", 30.1350, 78.3920),
    "kaudiyala": ("Kaudiyala, Uttarakhand", 30.0740, 78.4790),
}

def nominatim(q):
    url = "https://nominatim.openstreetmap.org/search?format=json&limit=3&countrycodes=in&q=" + urllib.parse.quote(q)
    time.sleep(1.1)
    return get(url, timeout=40)

coords = {}
for k, (q, lat, lon) in SEEDS.items():
    try:
        r = nominatim(q)
    except Exception as e:
        print("NOMINATIM FAIL", k, e)
        r = []
    if r:
        # pick the closest to seed so we don't get a wrong namesake
        best = min(r, key=lambda x: hav((lon, lat), (float(x["lon"]), float(x["lat"]))))
        d = hav((lon, lat), (float(best["lon"]), float(best["lat"])))
        if d < 25:
            coords[k] = {
                "lat": float(best["lat"]),
                "lon": float(best["lon"]),
                "display": best.get("display_name", q),
                "source": "nominatim",
                "query": q,
            }
            print("OK", k, coords[k]["lat"], coords[k]["lon"], "dseed", round(d, 2), best.get("display_name","")[:80])
            continue
        print("SEED KEEP (nominatim far)", k, "d", round(d,1), best.get("display_name","")[:80])
    coords[k] = {"lat": lat, "lon": lon, "display": q, "source": "seed-published", "query": q}
    print("SEED", k, lat, lon)

# elevations at destinations
def elevations(points):
    els = []
    for i in range(0, len(points), 80):
        ch = points[i:i+80]
        url = "https://api.open-meteo.com/v1/elevation?latitude=" + ",".join(f"{p[0]:.4f}" for p in ch) + "&longitude=" + ",".join(f"{p[1]:.4f}" for p in ch)
        els += get(url)["elevation"]
        time.sleep(0.4)
    return els

dest_pts = [(v["lat"], v["lon"]) for v in coords.values()]
els = elevations(dest_pts)
for (k, v), el in zip(coords.items(), els):
    v["el"] = int(round(el))
    print("EL", k, v["el"])

# also home elevation
HOME["el"] = int(round(elevations([(HOME["lat"], HOME["lon"])])[0]))

def osrm_route(lon1, lat1, lon2, lat2):
    url = (f"https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
           f"?overview=full&geometries=geojson&steps=false")
    time.sleep(0.8)
    r = get(url)
    if r.get("code") != "Ok":
        raise RuntimeError(r)
    return r["routes"][0]

def terrain(route):
    co = route["geometry"]["coordinates"]  # lon,lat
    cum = [0]
    for i in range(1, len(co)):
        cum.append(cum[-1] + hav(co[i-1], co[i]))
    tot = cum[-1] or 1
    sc = route["distance"]/1000 / tot
    step = 2.0
    pts = []
    d = 0
    j = 0
    while d <= tot:
        while j < len(cum)-1 and cum[j+1] < d:
            j += 1
        pts.append((co[j][1], co[j][0], d*sc))  # lat, lon, km
        d += step / sc
    pts.append((co[-1][1], co[-1][0], tot*sc))
    el = elevations([(p[0], p[1]) for p in pts])
    cls = {"plain": 0, "up": 0, "down": 0, "crawl": 0}
    for i in range(1, len(pts)):
        dk = pts[i][2] - pts[i-1][2]
        if dk <= 0:
            continue
        e0, e1 = el[i-1], el[i]
        mid = (e0+e1)/2
        grade = (e1-e0)/(dk*1000)*100
        if mid < 600:
            cls["plain"] += dk
        elif grade > 1.5:
            cls["up"] += dk
        elif grade < -1.5:
            cls["down"] += dk
        else:
            cls["crawl"] += dk
    # simplify geometry for the map (~150 pts)
    n = max(1, len(co)//150)
    simple = [[round(c[1], 5), round(c[0], 5)] for c in co[::n]]
    if simple[-1] != [round(co[-1][1],5), round(co[-1][0],5)]:
        simple.append([round(co[-1][1],5), round(co[-1][0],5)])
    return {
        "km": round(route["distance"]/1000, 1),
        "osrm_h": round(route["duration"]/3600, 2),
        "cls": {c: round(v, 1) for c, v in cls.items()},
        "maxel": int(round(max(el))),
        "minel": int(round(min(el))),
        "geometry": simple,
    }

# Mileage model used in earlier trip plans for this XUV700 (labelled estimate).
# Mid case is the "expected" figure shown in the UI; lo/hi give a range.
M = {
    "lo": dict(plain=14, up=9, down=15, crawl=10),
    "ex": dict(plain=13, up=8.5, down=14, crawl=9),
    "hi": dict(plain=12, up=8, down=13, crawl=8),  # hi = thirstier = more litres
}
P = 102  # Delhi petrol approx Rs/L, labelled

def litres(cls, key):
    return sum(cls[x] / M[key][x] for x in cls if cls[x])

def swap(cls):
    return {"plain": cls["plain"], "up": cls["down"], "down": cls["up"], "crawl": cls["crawl"]}

def petrol_rt(cls):
    # outbound + return with up/down swapped (estimate)
    out = {}
    for k in M:
        L = litres(cls, k) + litres(swap(cls), k)
        out[k] = {"litres": round(L, 1), "inr": int(round(L * P))}
    return out

def realistic_hours(osrm_h, cls):
    hill = cls["up"] + cls["down"] + cls["crawl"]
    tot = sum(cls.values()) or 1
    share = hill / tot
    if share < 0.2:
        buf = 1.25
        tag = "plains-heavy (OSRM × 1.25 + 30 min for food/fuel)"
    elif share < 0.55:
        buf = 1.40
        tag = "mixed hills (OSRM × 1.40 + 30 min for food/fuel)"
    else:
        buf = 1.50
        tag = "mountain roads (OSRM × 1.50 + 30 min for food/fuel)"
    hours = osrm_h * buf + 0.5
    return round(hours, 1), tag, buf

routes = {}
for k, v in coords.items():
    print("ROUTING", k, flush=True)
    try:
        rt = osrm_route(HOME["lon"], HOME["lat"], v["lon"], v["lat"])
        t = terrain(rt)
        t["petrol_round_trip"] = petrol_rt(t["cls"])
        t["realistic_h"], t["time_note"], t["buffer"] = realistic_hours(t["osrm_h"], t["cls"])
        routes[k] = t
        print("  ", t["km"], "km  osrm", t["osrm_h"], "real", t["realistic_h"], "petrol", t["petrol_round_trip"]["ex"], flush=True)
    except Exception as e:
        print("ROUTE FAIL", k, e, flush=True)
        routes[k] = {"error": str(e)}

# Wikimedia helper: build a file URL from a commons path
def commons_urls(path):
    # path like '2/2a/Harsil_Valley.jpg'
    name = path.split("/")[-1]
    file_url = "https://upload.wikimedia.org/wikipedia/commons/" + path
    thumb = f"https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(name)}?width=1200"
    page = "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(name.replace(" ", "_"))
    return {"file": file_url, "thumb": thumb, "page": page, "filename": name.replace("_", " ").replace("%2C", ",")}

# Search commons for missing spots
def commons_search(query, limit=8):
    url = (
        "https://commons.wikimedia.org/w/api.php?action=query&format=json&origin=*"
        "&generator=search&gsrnamespace=6&gsrlimit=" + str(limit)
        + "&gsrsearch=" + urllib.parse.quote(query)
        + "&prop=imageinfo&iiprop=url|extmetadata|size|mime&iiurlwidth=1200"
    )
    time.sleep(0.5)
    try:
        data = get(url, timeout=40)
    except Exception as e:
        print("COMMONS FAIL", query, e)
        return []
    pages = (data.get("query") or {}).get("pages") or {}
    out = []
    for p in pages.values():
        info = (p.get("imageinfo") or [None])[0]
        if not info:
            continue
        mime = info.get("mime") or ""
        if not mime.startswith("image/"):
            continue
        if mime not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
            continue
        meta = info.get("extmetadata") or {}
        def g(key):
            v = meta.get(key) or {}
            return (v.get("value") or "").strip()
        lic = g("LicenseShortName") or g("UsageTerms") or "unknown"
        # only freely licensed
        ok = any(s in lic.lower() for s in ["cc ", "cc0", "public domain", "pd-", "cc-"])
        if not ok and "creativecommons" not in (g("LicenseUrl") or "").lower() and "publicdomain" not in (g("LicenseUrl") or "").lower():
            # also allow bare "CC BY-SA 4.0" already covered; skip unknowns
            if lic.lower() not in ("cc0", "public domain"):
                continue
        artist = g("Artist")
        # strip html tags roughly
        import re
        artist = re.sub(r"<[^>]+>", "", artist)
        artist = artist.replace("&amp;", "&").strip() or "Unknown author"
        title = g("ObjectName") or p.get("title", "").replace("File:", "")
        out.append({
            "title": title,
            "author": artist,
            "license": lic,
            "thumb": info.get("thumburl") or info.get("url"),
            "file": info.get("url"),
            "page": f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(p.get('title','').replace(' ', '_'))}",
            "width": info.get("thumbwidth") or info.get("width"),
            "height": info.get("thumbheight") or info.get("height"),
        })
    return out

search_q = {
    "sissu": "Sissu Lahaul snow OR lake OR waterfall",
    "solang": "Solang Valley Himachal",
    "narkanda": "Narkanda Himachal OR Hatu Peak",
    "kufri": "Kufri Shimla Himachal",
    "chitkul": "Chitkul Baspa Himachal",
    "sangla": "Sangla valley Himachal Baspa",
    "kalpa": "Kalpa Kinnaur Kailash",
    "rakchham": "Rakchham Sangla Valley",
    "jalori": "Jalori Pass Himachal",
    "jibhi": "Jibhi Himachal",
    "chanshal": "Chanshal Pass Himachal",
    "dodra": "Dodra Kwar Himachal",
    "auli": "Auli Uttarakhand snow OR meadow",
    "harsil": "Harsil Valley Uttarakhand",
    "chakrata": "Chakrata OR Tiger Falls Uttarakhand",
    "hatkoti": "Hatkoti Pabbar Himachal",
    "tiuni": "Tiuni Tons river Uttarakhand OR Himachal",
    "mori": "Mori Tons river Uttarkashi",
    "dakpathar": "Dakpathar Yamuna barrage",
    "shivpuri": "Shivpuri Rishikesh Ganga",
    "kaudiyala": "Kaudiyala Ganga Uttarakhand",
}

photos = {}
for k, q in search_q.items():
    photos[k] = commons_search(q, 8)
    print("PHOTOS", k, len(photos[k]), flush=True)

# Save raw so the site builder can merge curated + fetched
payload = {
    "generated_at": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(timespec="minutes"),
    "timezone": "Asia/Calcutta (UTC+5:30)",
    "home": HOME,
    "petrol_inr_per_litre": P,
    "petrol_note": "Delhi petrol assumed at about ₹102 per litre. Hill-town prices are often a little higher. Terrain mileage is an estimate for a petrol Mahindra XUV700: highway/plain 12–14 km/l, hill crawl about 9 km/l, uphill about 8–9 km/l, downhill about 13–15 km/l. Mid case is shown; a low–high range is also stored.",
    "osrm_note": "Road km come from the public OSRM driving router (router.project-osrm.org). Times from OSRM are optimistic. Realistic hours add a hill buffer and 30 minutes for food and fuel. Photo stops are extra and are listed in each plan.",
    "coords": coords,
    "routes": routes,
    "photos": photos,
}
with open(os.path.join(OUT, "raw.json"), "w") as f:
    json.dump(payload, f)
print("WROTE", os.path.join(OUT, "raw.json"))
# also a compact summary
for k, t in routes.items():
    if "error" in t:
        print("ERR", k, t["error"])
    else:
        print(f"{k:10} {t['km']:7} km  {t['osrm_h']:5} h osrm  {t['realistic_h']:5} h real  RT petrol ₹{t['petrol_round_trip']['ex']['inr']}")
