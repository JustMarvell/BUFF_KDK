FROM python:3.12-slim

# GDAL/GEOS/PROJ for GeoDjango, libpq/build tools for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev libgeos-dev libproj-dev \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Bakes static files (admin CSS/JS) into the image at build time -
# doesn't need a live database connection, so it's safe to run here.
RUN python manage.py collectstatic --noinput

# Render sets $PORT itself; we just need to listen on whatever it gives us.
CMD gunicorn config.wsgi:application --bind 0.0.0.0:$PORT