# Snow Trip Planner

A public, mobile-friendly trip planner for snow and riverside drives **from Shaheen Bagh, Delhi**, in a petrol Mahindra XUV700.

Open the site, check this week’s snow, pick a place, and see the route, a day-by-day plan, photos, food-stop towns and a budget you can split between friends.

## What is measured, and what is an estimate

- **Road kilometres and the route line** come from the public [OSRM](https://router.project-osrm.org) driving router, precomputed.
- **Realistic hours** take the (optimistic) OSRM time and add a hill buffer plus 30 minutes for food and fuel. Photo stops in the day plan are extra.
- **Round-trip petrol** is a terrain-aware estimate for this XUV700 (highway about 12–14 km/l, hill cruise about 9 km/l, uphill about 8–9 km/l), at about ₹102 per litre in Delhi. A low–high range is shown.
- **Tolls, meals and beds** are planning figures you can edit. No live hotel or restaurant price is listed.
- **Snow** is fetched live in the browser from the [Open-Meteo](https://open-meteo.com/) model, using each place’s real elevation. It is a model estimate, not a person in the village.
- **Photos** are from Wikimedia Commons only, with the author and licence on each picture.

If a bed or a dhaba is not named here, that is on purpose — names and prices change. Search Booking.com or Airbnb yourself.

## Run locally

Any static server from the `public` folder:

```bash
cd public && python3 -m http.server 8080
```

Then open http://localhost:8080

## Deploy

This is a static site. On Render, set the publish path to `public` and the build command to `true`.
