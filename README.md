# KostFinder — Campus Boarding House GIS

A GIS-based system that helps university students find boarding houses
("kost") near campus, recommends the best-suited option based on the
student's faculty, and shows real road conditions on the route there.

## Why this counts as a GIS project

- **Spatial data model**: boarding houses, faculties, and road segments
  are stored as real geometries (`PointField`, `LineStringField`) via
  **GeoDjango**, backed by PostgreSQL + PostGIS — not plain lat/lng
  floats in a spreadsheet.
- **Proximity analysis**: GeoDjango's `Distance()` function and
  `dwithin` lookups power "nearest boarding houses to my faculty."
- **Network analysis**: actual road-network routing via OSRM, not
  straight-line distance.
- **Spatial overlay**: road-condition segments are intersected with the
  computed route (`dwithin` buffer) to flag problem sections.
- **Multi-criteria suitability scoring**: distance + price + road
  condition combined into one ranked recommendation — a simple spatial
  decision-support system (SDSS).

## Stack (100% free/open tools)

| Layer | Tool |
|---|---|
| Database | PostgreSQL + PostGIS |
| Backend API | Python + Django + GeoDjango + Django REST Framework |
| Admin / data entry | Django admin (built-in, with map widgets for spatial fields) |
| Web frontend | React + Vite + Leaflet.js |
| Map tiles | OpenStreetMap |
| Routing | OSRM (public demo server, or self-hosted) |
| Android | WebView wrapper or native osmdroid client (see note at the bottom) |

## Project layout

```
kostfinder/
├── backend/                  Django + GeoDjango + DRF API
│   ├── config/                Project settings, URLs
│   ├── listings/               The app: models, views, serializers, admin
│   │   └── management/commands/seed_data.py   Sample data loader
│   ├── requirements.txt
│   └── .env.example
├── web/                      React + Leaflet web app (the "web app" requirement)
├── docker-compose.yml         One-command local PostGIS database
└── README.md                  (this file)
```

## Quickstart

### 1. Start the database

```bash
docker compose up -d
```

This starts PostGIS on `localhost:5432` (db: `kostfinder`, user:
`kostfinder_user`, password: `changeme` — change these in
`docker-compose.yml` and `backend/.env` for anything beyond local dev).

Don't have Docker? Install PostgreSQL + the PostGIS extension locally
instead, create a `kostfinder` database, and run
`CREATE EXTENSION postgis;` once connected to it.

### 2. Set up and run the backend

GeoDjango needs the GDAL/GEOS/PROJ system libraries (not just Python
packages) to talk to PostGIS geometry types. Install them first:

```bash
# Ubuntu/Debian
sudo apt-get install gdal-bin libgdal-dev libgeos-dev libproj-dev

# macOS (Homebrew)
brew install gdal geos proj
```

Then set up the Django project:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env          # adjust if you changed DB credentials

python manage.py migrate      # creates tables (migrations are already generated)
python manage.py seed_data    # inserts sample faculties/boarding houses/roads
python manage.py createsuperuser   # so you can log into /admin/
python manage.py runserver    # starts API on http://localhost:8000
```

Sanity checks:
- http://localhost:8000/api/health/ → `{"status": "ok"}`
- http://localhost:8000/admin/ → log in and browse/edit boarding houses,
  faculties, and road segments through Django's built-in admin, complete
  with an interactive map widget for editing each geometry field.

### 3. Run the web app

```bash
cd web
npm install
npm run dev
```

Open http://localhost:5173. In development, point the frontend at the
Django API by setting `VITE_API_BASE=http://localhost:8000/api` (or add
a proxy in `vite.config.js` similar to before — see note below).

> **Note:** the web app was originally scaffolded against the old
> Node/Express API. The Django API is designed to return the *same JSON
> shapes* (same field names: `lng`, `lat`, `distance_m`,
> `suitability_score`, etc.) so the frontend should work with minimal
> changes — mainly swapping the request base URL and, since Django URLs
> use trailing slashes by default (e.g. `/api/faculties/` instead of
> `/api/faculties`), double-check `web/src/lib/api.js` and
> `vite.config.js`'s proxy target if you see 404s.

## Managing data through Django admin

This is the main advantage of Django over the previous Express setup:
instead of writing a custom admin UI, `/admin/` already lets you:

- Add/edit boarding houses with an interactive map for setting their
  location (drop a pin instead of typing lat/lng).
- Add/edit road segments and their condition rating (good/fair/poor) —
  useful for crowdsourcing or manually walking your campus once and
  recording conditions.
- Add/edit faculties.

Just run `python manage.py createsuperuser` once and log in.

## Replacing the sample data with your real campus

Edit `backend/listings/management/commands/seed_data.py`:

1. Replace `FACULTIES` with your actual faculty building coordinates
   (from Google Maps: right-click a building → click the coordinates to
   copy; note GeoJSON/PostGIS convention is **longitude first**).
2. Replace `BOARDING_HOUSES` with real listings around your campus.
3. Replace `ROAD_SEGMENTS` with a handful of roads you've personally
   checked — even 10-20 walked/driven segments is enough to demonstrate
   the concept convincingly for a class project.

Then run `python manage.py seed_data --flush` to wipe and reload, or
just add more entries through the Django admin instead.

## API overview

| Endpoint | Purpose |
|---|---|
| `GET /api/faculties/` | List all faculties |
| `GET /api/boarding-houses/` | List/filter boarding houses (price, room type, facilities) |
| `GET /api/boarding-houses/recommended/?faculty_id=` | **Ranked recommendations** by suitability score |
| `GET /api/boarding-houses/:id/` | Single boarding house detail |
| `POST /api/boarding-houses/` | Add a new listing |
| `GET /api/road-segments/` | Road condition data as GeoJSON |
| `POST /api/road-segments/` | Submit/crowdsource a road condition rating |
| `GET /api/route/?boarding_house_id=&faculty_id=&profile=` | Route geometry + road condition overlay |

## Android app options

You asked for both a standalone Android app and web access. Two realistic
paths, in order of effort:

1. **WebView wrapper (fastest, fully valid)**: a minimal Android app
   with a single `WebView` pointed at your deployed web app URL, plus
   basic offline/error handling. Satisfies "standalone app" for grading
   purposes while reusing 100% of the web frontend.
2. **Native Android client**: Kotlin app using `osmdroid` (Leaflet's
   Android equivalent) for the map, calling the same Django API. More
   work, but demonstrates native mobile GIS development if your rubric
   specifically wants that.

Ask when you're ready to scaffold either of these — the backend API is
already shaped to serve both the web and a native client identically.

## Next steps / suggested build order

1. Swap in your real campus data (see above).
2. Try the Django admin — add a boarding house through it and see the
   map widget in action.
3. Update `web/src/lib/api.js` / `vite.config.js` to point at the
   Django API (trailing slashes, port 8000).
4. Deploy: backend to something like Render/Railway (both support
   Python + PostGIS), web app to Vercel/Netlify, database to a managed
   free-tier Postgres with PostGIS (e.g. Supabase).
5. Then start the Android client.
6. Write up the proposal/report using this working prototype as evidence.
