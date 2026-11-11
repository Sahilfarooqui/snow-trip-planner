
/* Snow Trip Planner — static client. Forecast is fetched live from Open-Meteo. */
const $ = (sel, el = document) => el.querySelector(sel);
const app = $("#app");
let DATA = null;
let WX = { forecast: {}, archive: {}, fetchedAt: null, error: null };
let mapRef = null;

const rupee = (n) => "₹" + Math.round(n).toLocaleString("en-IN");
const fmtH = (h) => (Math.round(h * 10) / 10) + " h";
const fmtKm = (km) => (Math.round(km * 10) / 10) + " km";

function istStamp(d = new Date()) {
  return new Intl.DateTimeFormat("en-IN", {
    timeZone: "Asia/Calcutta",
    weekday: "short", day: "numeric", month: "short", year: "numeric",
    hour: "numeric", minute: "2-digit", hour12: true
  }).format(d) + " IST (Asia/Calcutta, UTC+5:30)";
}

function shortDay(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d, 6, 0, 0));
  return new Intl.DateTimeFormat("en-IN", { timeZone: "Asia/Calcutta", weekday: "short", day: "numeric", month: "short" }).format(dt);
}

function snowClass(cm) {
  if (cm == null || Number.isNaN(cm)) return "s-none";
  if (cm <= 0) return "s-none";
  if (cm < 0.5) return "s-trace";
  if (cm < 5) return "s-light";
  if (cm < 15) return "s-mid";
  if (cm < 30) return "s-heavy";
  return "s-very";
}
function snowLabel(cm) {
  if (cm == null || Number.isNaN(cm)) return "—";
  if (cm <= 0) return "0";
  if (cm < 0.1) return "trace";
  return (Math.round(cm * 10) / 10) + " cm";
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function routeFromHash() {
  const h = (location.hash || "#/").replace(/^#/, "") || "/";
  const m = h.match(/^\/spot\/([^/?]+)/);
  if (m) return { page: "spot", id: decodeURIComponent(m[1]), section: null };
  const sec = h.replace(/^\//, "");
  return { page: "home", id: null, section: sec || null };
}

function allForecastPoints() {
  const pts = [];
  for (const s of DATA.spots) {
    for (const p of s.forecast_points) pts.push({ spotId: s.id, ...p });
  }
  return pts;
}

async function fetchOpenMeteo() {
  const pts = allForecastPoints();
  const tz = "Asia/Kolkata";
  try {
    const forecastReqs = pts.map((p) => {
      const u = new URL("https://api.open-meteo.com/v1/forecast");
      u.searchParams.set("latitude", p.lat);
      u.searchParams.set("longitude", p.lon);
      u.searchParams.set("elevation", p.elevation_m);
      u.searchParams.set("daily", "snowfall_sum,temperature_2m_min,temperature_2m_max,precipitation_probability_max");
      u.searchParams.set("timezone", tz);
      u.searchParams.set("forecast_days", "7");
      return fetch(u).then((r) => {
        if (!r.ok) throw new Error("forecast " + r.status);
        return r.json().then((j) => ({ key: p.id, data: j }));
      });
    });
    const today = new Date();
    const end = new Date(today.getTime() - 1 * 24 * 3600 * 1000);
    const start = new Date(today.getTime() - 14 * 24 * 3600 * 1000);
    const iso = (d) => new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Calcutta", year: "numeric", month: "2-digit", day: "2-digit" }).format(d);
    const archiveReqs = pts.map((p) => {
      const u = new URL("https://archive-api.open-meteo.com/v1/archive");
      u.searchParams.set("latitude", p.lat);
      u.searchParams.set("longitude", p.lon);
      u.searchParams.set("elevation", p.elevation_m);
      u.searchParams.set("start_date", iso(start));
      u.searchParams.set("end_date", iso(end));
      u.searchParams.set("daily", "snowfall_sum,temperature_2m_min,temperature_2m_max");
      u.searchParams.set("timezone", tz);
      return fetch(u).then((r) => {
        if (!r.ok) throw new Error("archive " + r.status);
        return r.json().then((j) => ({ key: p.id, data: j }));
      });
    });
    const [fRes, aRes] = await Promise.all([
      Promise.allSettled(forecastReqs),
      Promise.allSettled(archiveReqs)
    ]);
    const forecast = {}, archive = {};
    for (const r of fRes) if (r.status === "fulfilled") forecast[r.value.key] = r.value.data;
    for (const r of aRes) if (r.status === "fulfilled") archive[r.value.key] = r.value.data;
    WX = {
      forecast, archive,
      fetchedAt: new Date(),
      error: (Object.keys(forecast).length ? null : "The live forecast could not be loaded. Refresh, or try again in a minute.")
    };
  } catch (e) {
    WX.error = "The live forecast could not be loaded. " + (e.message || "");
  }
}

function renderNav(active) {
  document.querySelectorAll(".nav a").forEach((a) => {
    const href = a.getAttribute("href");
    const is = (active === "home" && href === "#/") || (active !== "home" && href === "#/" + active);
    if (is) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
}

function cardHTML(s) {
  const photo = (s.photos && s.photos[0]) ? s.photos[0].thumb : "";
  const pet = s.petrol_round_trip.ex.inr;
  const petLo = s.petrol_round_trip.lo.inr;
  const petHi = s.petrol_round_trip.hi.inr;
  return `<a class="card" href="#/spot/${encodeURIComponent(s.id)}">
    <div class="ph" style="${photo ? `background-image:url('${esc(photo)}')` : ""}">
      ${s.visited ? `<span class="badge">Already visited</span>` : (s.kind === "riverside" ? `<span class="badge">Riverside</span>` : "")}
    </div>
    <div class="body">
      <h3>${esc(s.name)}</h3>
      <div class="region">${esc(s.region)} · ${s.elevation_m.toLocaleString("en-IN")} m</div>
      <div class="stats">
        <div class="stat"><b>${fmtKm(s.one_way_km)}</b><span>one way</span></div>
        <div class="stat"><b>${fmtH(s.realistic_hours)}</b><span>drive, realistic</span></div>
        <div class="stat"><b>${rupee(pet)}</b><span>round-trip petrol</span></div>
        <div class="stat"><b>${s.plan_days} days</b><span>suggested trip</span></div>
      </div>
      <div class="est">Estimate ${rupee(petLo)}–${rupee(petHi)}</div>
      <div class="safety-one">${esc(s.snow_months)}</div>
    </div>
  </a>`;
}

function tableHTML(spots) {
  return `<div class="table-wrap desktop-only"><table class="data-table">
    <thead><tr>
      <th>Place</th><th>Height</th><th>One way</th><th>Drive (realistic)</th>
      <th>Round-trip petrol</th><th>Usual snow</th><th>2WD note</th>
    </tr></thead>
    <tbody>
      ${spots.map((s) => `<tr>
        <td><a href="#/spot/${encodeURIComponent(s.id)}"><strong>${esc(s.name)}</strong></a>
          ${s.visited ? " <span class='badge'>Visited</span>" : ""}<br>
          <span class="region">${esc(s.region)}</span></td>
        <td>${s.elevation_m.toLocaleString("en-IN")} m${s.extra && s.extra.el ? `<br><span class="region">${esc(s.extra.label)} ${s.extra.el.toLocaleString("en-IN")} m</span>` : ""}</td>
        <td>${fmtKm(s.one_way_km)}</td>
        <td>${fmtH(s.realistic_hours)}<br><span class="region">Router: ${fmtH(s.osrm_hours)}</span></td>
        <td>${rupee(s.petrol_round_trip.ex.inr)}<br><span class="region">${rupee(s.petrol_round_trip.lo.inr)}–${rupee(s.petrol_round_trip.hi.inr)}</span></td>
        <td>${esc(s.snow_months)}</td>
        <td>${esc(s.safety)}</td>
      </tr>`).join("")}
    </tbody>
  </table></div>`;
}

function weatherRows(kind) {
  const pack = kind === "forecast" ? WX.forecast : WX.archive;
  const snowSpots = DATA.spots.filter((s) => s.kind === "snow");
  const rows = [];
  let dates = [];
  for (const s of snowSpots) {
    for (const p of s.forecast_points) {
      const w = pack[p.id];
      if (w && w.daily && w.daily.time) {
        if (!dates.length) dates = w.daily.time.slice();
        rows.push({ spot: s, point: p, daily: w.daily });
      } else {
        rows.push({ spot: s, point: p, daily: null });
      }
    }
  }
  if (!dates.length) return `<p class="note">${esc(WX.error || "Weather is still loading…")}</p>`;
  const head = `<tr><th class="place">Place</th>${dates.map((d) => `<th>${esc(shortDay(d))}</th>`).join("")}</tr>`;
  const body = rows.map((r) => {
    const label = r.point.name + (r.spot.forecast_points.length > 1 ? "" : "") + (r.spot.visited ? " · visited" : "");
    if (!r.daily) {
      return `<tr><td class="place"><a href="#/spot/${encodeURIComponent(r.spot.id)}">${esc(label)}</a></td>${dates.map(() => `<td>—</td>`).join("")}</tr>`;
    }
    const cells = r.daily.time.map((_, i) => {
      const cm = r.daily.snowfall_sum[i];
      const tmin = r.daily.temperature_2m_min?.[i];
      const tmax = r.daily.temperature_2m_max?.[i];
      const t = (tmin != null && tmax != null) ? `<span class="temp">${Math.round(tmin)}° / ${Math.round(tmax)}°</span>` : "";
      return `<td><div class="cell ${snowClass(cm)}">${snowLabel(cm)}${t}</div></td>`;
    }).join("");
    return `<tr><td class="place"><a href="#/spot/${encodeURIComponent(r.spot.id)}">${esc(r.point.name)}</a><div class="region">${r.point.elevation_m.toLocaleString("en-IN")} m</div></td>${cells}</tr>`;
  }).join("");
  return `<div class="legend">
    <span><i class="swatch s-none"></i> 0</span>
    <span><i class="swatch s-trace"></i> trace</span>
    <span><i class="swatch s-light"></i> under 5 cm</span>
    <span><i class="swatch s-mid"></i> 5–15 cm</span>
    <span><i class="swatch s-heavy"></i> 15–30 cm</span>
    <span><i class="swatch s-very"></i> 30 cm or more</span>
  </div>
  <div class="snow-wrap"><table class="snow-table"><thead>${head}</thead><tbody>${body}</tbody></table></div>`;
}

function budgetOf(spot, people, days, meal, bed, toll) {
  const nights = Math.max(0, days - 1);
  const petrol = spot.petrol_round_trip.ex.inr;
  const petrolLo = spot.petrol_round_trip.lo.inr;
  const petrolHi = spot.petrol_round_trip.hi.inr;
  const meals = meal * people * days;
  const stay = bed * people * nights;
  const shared = petrol + toll;
  const total = shared + meals + stay;
  const pp = total / people;
  return { nights, petrol, petrolLo, petrolHi, meals, stay, toll, shared, total, pp, people, days };
}

function budgetFormHTML(spotId, opts = {}) {
  const defaults = DATA.budget_defaults;
  const spots = DATA.spots;
  const people = opts.people ?? defaults.people;
  const days = opts.days ?? (spots.find((s) => s.id === spotId)?.plan_days || 3);
  const meal = opts.meal ?? defaults.meal_per_person_per_day;
  const bed = opts.bed ?? defaults.bed_per_person_per_night;
  const spot = spots.find((s) => s.id === spotId) || spots[0];
  const toll = opts.toll ?? spot.toll_rt_estimate;
  const b = budgetOf(spot, Number(people), Number(days), Number(meal), Number(bed), Number(toll));
  return `<div class="budget" id="budget">
    <h2>Trip budget</h2>
    <p class="sub">Pick a place and the number of people. Figures are planning estimates, not a quote. Change any number — the total updates at once.</p>
    <form class="form" id="budget-form" onsubmit="return false">
      <label><span>Place</span>
        <select name="spot">${spots.map((s) => `<option value="${esc(s.id)}" ${s.id === spot.id ? "selected" : ""}>${esc(s.name)}</option>`).join("")}</select>
      </label>
      <label><span>People</span><input name="people" type="number" min="1" max="7" value="${esc(people)}"></label>
      <label><span>Days on the trip</span><input name="days" type="number" min="1" max="14" value="${esc(days)}"></label>
      <label><span>Meals, per person per day (₹)</span><input name="meal" type="number" min="0" step="10" value="${esc(meal)}"></label>
      <label><span>Bed, per person per night (₹)</span><input name="bed" type="number" min="0" step="50" value="${esc(bed)}"></label>
      <label><span>Tolls, round trip (₹)</span><input name="toll" type="number" min="0" step="50" value="${esc(toll)}"></label>
    </form>
    <div class="totals">
      <div><span>Petrol (mid)</span><b>${rupee(b.petrol)}</b><small>range ${rupee(b.petrolLo)}–${rupee(b.petrolHi)}</small></div>
      <div><span>Tolls</span><b>${rupee(b.toll)}</b></div>
      <div><span>Meals (all)</span><b>${rupee(b.meals)}</b></div>
      <div><span>Beds (${b.nights} night${b.nights === 1 ? "" : "s"})</span><b>${rupee(b.stay)}</b></div>
      <div class="big"><span>Whole trip</span><b>${rupee(b.total)}</b></div>
      <div class="big"><span>Each person (${b.people})</span><b>${rupee(b.pp)}</b></div>
    </div>
    <p class="assumptions">
      ${esc(DATA.mileage_note)} Petrol used here is the mid case at about ₹${DATA.petrol_inr_per_litre} per litre, for a round trip, with uphill and downhill swapped on the way home.
      ${esc(spot.toll_note)}
      ${esc(defaults.meal_note)} ${esc(defaults.bed_note)}
      Meals are counted for every calendar day. Beds are counted for days minus one (so a 2-day trip has 1 night). Local side-drives after you arrive are not included.
    </p>
  </div>`;
}

function bindBudget() {
  const form = $("#budget-form");
  if (!form) return;
  form.dataset.currentSpot = new FormData(form).get("spot");
  const redraw = () => {
    const fd = new FormData(form);
    const id = fd.get("spot");
    const spot = DATA.spots.find((x) => x.id === id);
    const changedPlace = id !== form.dataset.currentSpot;
    const box = $("#budget");
    box.outerHTML = budgetFormHTML(id, {
      people: Number(fd.get("people")),
      days: changedPlace && spot ? spot.plan_days : Number(fd.get("days")),
      meal: Number(fd.get("meal")),
      bed: Number(fd.get("bed")),
      toll: changedPlace && spot ? spot.toll_rt_estimate : Number(fd.get("toll"))
    });
    bindBudget();
  };
  form.addEventListener("change", redraw);
}

function renderHome(section) {
  renderNav(section && ["rivers", "budget", "tips"].includes(section) ? section : "home");
  const snow = DATA.spots.filter((s) => s.kind === "snow");
  const rivers = DATA.spots.filter((s) => s.kind === "riverside");
  const stamp = WX.fetchedAt
    ? `Fetched ${istStamp(WX.fetchedAt)}. Open-Meteo model estimate, using each place’s real height.`
    : "Fetching the live forecast…";
  app.innerHTML = `
    <section class="hero">
      <h1>Plan a snow — or river — drive from Shaheen Bagh.</h1>
      <p class="lead">Built for a petrol Mahindra XUV700 and 2–3 friends. Open a place to see the route, a day-by-day plan, photos, food-stop towns and a budget you can split.</p>
      <div class="pills">
        <span class="pill">Home: Shaheen Bagh, Delhi</span>
        <span class="pill">City mileage about 10–11 km/l</span>
        <span class="pill">Highway about 12–14 km/l, less uphill</span>
        <span class="pill">Delhi petrol assumed at ₹${DATA.petrol_inr_per_litre}/L</span>
      </div>
    </section>

    <section class="section" id="forecast">
      <h2>This week’s snow</h2>
      <p class="stamp">${esc(stamp)}</p>
      <p class="sub">${esc(DATA.forecast_note)}</p>
      ${weatherRows("forecast")}
    </section>

    <section class="section" id="past">
      <h2>Snow in the last 14 days</h2>
      <p class="sub">From the Open-Meteo archive, same places and heights. The archive can lag by a few days, so yesterday may be blank. Still a model estimate, not a person on the ground.</p>
      ${weatherRows("archive")}
    </section>

    <section class="section" id="snow">
      <h2>Snow places you can reach</h2>
      <p class="sub">Road kilometres are measured. Drive hours are realistic (router time plus a hill buffer and 30 minutes for food and fuel). Petrol is a terrain-aware estimate for a round trip. Sissu and Chitkul are marked as already visited.</p>
      <div class="grid mobile-only">${snow.map(cardHTML).join("")}</div>
      ${tableHTML(snow)}
    </section>

    <section class="section" id="rivers">
      <h2>Offbeat riverside villages — a one-day drive</h2>
      <p class="sub">These are river valleys you can reach in a day’s realistic driving (under about 9 hours one way). They are not snow bowls. Come for the water and a quiet night, then drive home the next day if you want.</p>
      <div class="grid">${rivers.map(cardHTML).join("")}</div>
    </section>

    <section class="section">${budgetFormHTML(snow[0].id)}</section>

    <section class="section" id="tips">
      <h2>Short tips, so you do not get stuck</h2>
      <div class="tips">${DATA.tips.map((t) => `<article class="tip"><h3>${esc(t.title)}</h3><p>${esc(t.body)}</p></article>`).join("")}</div>
      <p class="note">Road data was precomputed on ${esc(DATA.generated_at)} (${esc(DATA.timezone)}). ${esc(DATA.osrm_note)}</p>
    </section>
  `;
  bindBudget();
  if (section === "rivers" || section === "budget" || section === "tips") {
    const el = section === "budget" ? $("#budget") : $("#" + section);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function photoFigs(photos) {
  if (!photos || !photos.length) {
    return `<p class="note">No verified Wikimedia Commons photo is listed for this place yet.</p>`;
  }
  return `<div class="gallery">${photos.map((p) => `
    <figure class="fig">
      <a href="${esc(p.page)}" target="_blank" rel="noopener noreferrer">
        <img src="${esc(p.thumb || p.file)}" alt="${esc(p.title)}" loading="lazy">
      </a>
      <figcaption>
        <em>${esc(p.title)}</em><br>
        ${esc(p.author)}, ${esc(p.license)}.
        <a href="${esc(p.page)}" target="_blank" rel="noopener noreferrer">Wikimedia Commons</a>
      </figcaption>
    </figure>`).join("")}</div>`;
}

function renderSpot(id) {
  const s = DATA.spots.find((x) => x.id === id);
  renderNav("home");
  if (!s) {
    app.innerHTML = `<p class="error">That place is not in the planner. <a href="#/">Back to the list</a>.</p>`;
    return;
  }
  const pet = s.petrol_round_trip;
  const wxBits = s.forecast_points.map((p) => {
    const f = WX.forecast[p.id];
    if (!f || !f.daily) return "";
    const cells = f.daily.time.map((d, i) => {
      const cm = f.daily.snowfall_sum[i];
      return `<td><div class="cell ${snowClass(cm)}">${esc(shortDay(d))}<br>${snowLabel(cm)}</div></td>`;
    }).join("");
    return `<h3 style="margin:12px 0 6px">${esc(p.name)} · ${p.elevation_m.toLocaleString("en-IN")} m</h3>
      <div class="snow-wrap"><table class="snow-table"><tbody><tr>${cells}</tr></tbody></table></div>`;
  }).join("");

  app.innerHTML = `
    <p><a class="back" href="#/">← All places</a></p>
    <section class="detail-hero">
      ${s.visited ? `<span class="badge">Already visited</span>` : ""}
      <h1>${esc(s.name)}</h1>
      <p class="kicker">${esc(s.region)} · ${s.elevation_m.toLocaleString("en-IN")} m
        ${s.extra && s.extra.el ? ` · ${esc(s.extra.label)} ${s.extra.el.toLocaleString("en-IN")} m` : ""}
        ${s.visited_note ? `<br>${esc(s.visited_note)}` : ""}</p>
      <div class="bigstats">
        <div class="stat"><b>${fmtKm(s.one_way_km)}</b><span>one way from Shaheen Bagh</span></div>
        <div class="stat"><b>${fmtH(s.realistic_hours)}</b><span>realistic drive</span></div>
        <div class="stat"><b>${fmtH(s.osrm_hours)}</b><span>router time (optimistic)</span></div>
        <div class="stat"><b>${rupee(pet.ex.inr)}</b><span>round-trip petrol, mid</span></div>
        <div class="stat"><b>${rupee(pet.lo.inr)}–${rupee(pet.hi.inr)}</b><span>petrol range</span></div>
        <div class="stat"><b>${s.plan_days} days</b><span>suggested trip length</span></div>
      </div>
    </section>

    <section class="section">
      <h2>Route from Shaheen Bagh</h2>
      <div id="map" role="img" aria-label="Map of the driving route"></div>
      <p class="note">${esc(s.corridor)} ${esc(s.time_note)}. ${esc(DATA.osrm_note)}</p>
      ${s.legs && s.legs.length ? `<table class="legs">
        <thead><tr><th>Leg</th><th>Km</th><th>Rough time</th></tr></thead>
        <tbody>
          ${s.legs.map((leg) => {
            const share = leg.km / s.one_way_km;
            const hrs = s.realistic_hours * share;
            return `<tr><td>${esc(leg.from)} → ${esc(leg.to)}</td><td>${fmtKm(leg.km)}</td><td>${fmtH(hrs)} <span class="region">(split from the total, rough)</span></td></tr>`;
          }).join("")}
          <tr><td><strong>Total one way</strong></td><td><strong>${fmtKm(s.one_way_km)}</strong></td><td><strong>${fmtH(s.realistic_hours)}</strong></td></tr>
        </tbody>
      </table>` : ""}
      ${s.side_trips && s.side_trips.length ? `<p class="note" style="margin-top:12px"><strong>Side trips, measured:</strong> ${s.side_trips.map((t) => `${esc(t.from)} → ${esc(t.to)} ${fmtKm(t.km)} (router ${fmtH(t.osrm_h)}). ${esc(t.note)}`).join(" ")}</p>` : ""}
      <p class="note">Terrain on the way out: plain ${fmtKm(s.terrain.plain)}, uphill ${fmtKm(s.terrain.up)}, downhill ${fmtKm(s.terrain.down)}, hill cruise ${fmtKm(s.terrain.crawl)}. Route height ${s.route_min_m}–${s.route_max_m} m.</p>
    </section>

    <section class="section">
      <h2>Day-by-day plan</h2>
      <p class="sub">Photo-stop time is already written into these days. The realistic drive hours above do not add every viewpoint — if you stop often, the day gets longer.</p>
      <div class="plan">${s.plan.map((d) => `<article class="day">
        <div class="num">Day ${d.day}</div>
        <div><h3>${esc(d.title)}</h3><p>${esc(d.body)}</p></div>
      </article>`).join("")}</div>
    </section>

    <section class="section">
      <h2>Viewpoints, walks and photo spots</h2>
      <div class="spots-list">${s.photo_spots.map((p) => `<article class="spot-item"><h3>${esc(p.name)}</h3><p>${esc(p.what)}</p></article>`).join("")}</div>
      <h3 style="font-family:Fraunces,Georgia,serif;margin:22px 0 8px">Photos</h3>
      <p class="note">Wikimedia Commons only, with the author and licence on each picture. Click a photo to open the file page.</p>
      ${photoFigs(s.photos)}
    </section>

    <section class="section">
      <h2>Cheap food stops</h2>
      <ul class="food">${s.food_stops.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>
      <p class="note">${esc(s.food_disclaimer)}</p>
    </section>

    <section class="section">
      <h2>A cheap bed</h2>
      <div class="callout">
        <p><strong>Look in ${esc(s.stay_where)}</strong></p>
        <p>${esc(s.stay_disclaimer)}</p>
        <p>Search on <a href="https://www.booking.com" target="_blank" rel="noopener noreferrer">Booking.com</a>
        or <a href="https://www.airbnb.com" target="_blank" rel="noopener noreferrer">Airbnb</a> for “${esc(s.stay_search)}”, and filter for a bed-only room or a dorm if you want the cheapest stay.</p>
      </div>
    </section>

    <section class="section">
      <h2>Road safety for a 2WD SUV</h2>
      <p>${esc(s.safety)}</p>
      <p class="note">${esc(s.snow_months)}</p>
    </section>

    <section class="section">
      <h2>Live snow and weather</h2>
      <p class="stamp">${WX.fetchedAt ? esc("Fetched " + istStamp(WX.fetchedAt) + ". Open-Meteo model estimate.") : "Fetching…"}</p>
      ${wxBits || `<p class="note">${esc(WX.error || "No forecast yet.")}</p>`}
    </section>

    <section class="section">${budgetFormHTML(s.id, { days: s.plan_days, toll: s.toll_rt_estimate })}</section>
  `;
  bindBudget();
  requestAnimationFrame(() => drawMap(s));
}

function drawMap(s) {
  const el = $("#map");
  if (!el || typeof L === "undefined") return;
  if (mapRef) { mapRef.remove(); mapRef = null; }
  const map = L.map(el, { scrollWheelZoom: false });
  mapRef = map;
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a>"
  }).addTo(map);
  const home = DATA.home;
  const latlngs = (s.geometry || []).map((p) => [p[0], p[1]]);
  const line = L.polyline(latlngs, { color: "#c0562a", weight: 4, opacity: 0.9 }).addTo(map);
  L.circleMarker([home.lat, home.lon], { radius: 8, color: "#14364b", fillColor: "#215e82", fillOpacity: 1 })
    .addTo(map).bindPopup("Shaheen Bagh, Delhi");
  L.circleMarker([s.lat, s.lon], { radius: 8, color: "#9a3f1c", fillColor: "#c0562a", fillOpacity: 1 })
    .addTo(map).bindPopup(s.name);
  if (s.extra && s.extra.lat) {
    L.circleMarker([s.extra.lat, s.extra.lon], { radius: 6, color: "#1b4a38", fillColor: "#2a6a52", fillOpacity: 1 })
      .addTo(map).bindPopup(s.extra.label);
  }
  if (latlngs.length) map.fitBounds(line.getBounds(), { padding: [24, 24] });
  else map.setView([s.lat, s.lon], 8);
  setTimeout(() => map.invalidateSize(), 200);
}

function render() {
  if (!DATA) return;
  const r = routeFromHash();
  if (r.page === "spot") renderSpot(r.id);
  else renderHome(r.section);
}

async function init() {
  try {
    const res = await fetch("data/spots.json");
    if (!res.ok) throw new Error("Could not load places data");
    DATA = await res.json();
    render();
    await fetchOpenMeteo();
    render();
  } catch (e) {
    app.innerHTML = `<p class="error">The planner data did not load (${esc(e.message)}). Check the site files and refresh.</p>`;
  }
}

window.addEventListener("hashchange", render);
init();
