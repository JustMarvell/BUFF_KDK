import json

import requests
from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import LineString
from django.contrib.gis.measure import D
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import BoardingHouse, Faculty, RoadSegment, RouteCache
from .serializers import (
    BoardingHouseCreateSerializer,
    BoardingHouseSerializer,
    FacultySerializer,
    RoadSegmentCreateSerializer,
    RoadSegmentGeoJSONSerializer,
)

ROAD_CONDITION_SCORE = {"good": 1.0, "fair": 0.6, "poor": 0.2}


class FacultyListView(APIView):
    def get(self, request):
        faculties = Faculty.objects.all()
        return Response(FacultySerializer(faculties, many=True).data)


class FacultyDetailView(APIView):
    def get(self, request, pk):
        try:
            faculty = Faculty.objects.get(pk=pk)
        except Faculty.DoesNotExist:
            return Response({"error": "Faculty not found"}, status=404)
        return Response(FacultySerializer(faculty).data)


class BoardingHouseListView(APIView):
    """
    GET /api/boarding-houses/
    Filters: faculty_id, min_price, max_price, room_type, facility (repeatable), limit
    If faculty_id is given, results are annotated with distance_m and
    ordered nearest-first, using GeoDjango's Distance() on a geography
    field (so the result is true metres, not degrees).
    """

    def get(self, request):
        qs = BoardingHouse.objects.all()

        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")
        room_type = request.query_params.get("room_type")
        facilities = request.query_params.getlist("facility")
        faculty_id = request.query_params.get("faculty_id")
        limit = int(request.query_params.get("limit", 50))

        if min_price:
            qs = qs.filter(price_max__gte=int(min_price))
        if max_price:
            qs = qs.filter(price_min__lte=int(max_price))
        if room_type:
            qs = qs.filter(room_type=room_type)
        for f in facilities:
            qs = qs.filter(facilities__contains=[f])

        if faculty_id:
            try:
                faculty = Faculty.objects.get(pk=faculty_id)
            except Faculty.DoesNotExist:
                return Response({"error": "Faculty not found"}, status=404)
            qs = qs.annotate(distance=Distance("geom", faculty.geom)).order_by("distance")
        else:
            qs = qs.order_by("name")

        return Response(BoardingHouseSerializer(qs[:limit], many=True).data)

    def post(self, request):
        serializer = BoardingHouseCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        bh = serializer.save()
        return Response({"id": bh.id}, status=status.HTTP_201_CREATED)


class BoardingHouseDetailView(APIView):
    def get(self, request, pk):
        try:
            bh = BoardingHouse.objects.get(pk=pk)
        except BoardingHouse.DoesNotExist:
            return Response({"error": "Boarding house not found"}, status=404)
        return Response(BoardingHouseSerializer(bh).data)


class BoardingHouseRecommendedView(APIView):
    """
    GET /api/boarding-houses/recommended/?faculty_id=1&limit=10

    The core differentiating GIS feature: ranks boarding houses for a
    given faculty by a weighted suitability score combining:
      - proximity to the faculty (via GeoDjango Distance on a geography field)
      - nearby road condition (nearest road_segment within 300m, via a
        correlated subquery using OuterRef/Subquery)
      - price (cheaper = better, normalized within this result set)

    Road condition here is a simple proxy - "what's the road like right
    outside this place" - rather than the full route condition (see
    RouteView for the actual routed-path overlay, which is more precise).

    Note on implementation: the nearest-road-segment lookup is done with
    one small query per boarding house rather than a single correlated
    subquery. GeoDjango's Distance() function does not reliably resolve
    an OuterRef() as its geometry argument (it needs a concrete output
    field), so a straightforward per-row lookup is both simpler and more
    robust here - and for a single-campus dataset (tens of boarding
    houses, not thousands), the extra queries are negligible.
    """

    def get(self, request):
        faculty_id = request.query_params.get("faculty_id")
        limit = int(request.query_params.get("limit", 10))
        if not faculty_id:
            return Response({"error": "faculty_id query param is required"}, status=400)

        try:
            faculty = Faculty.objects.get(pk=faculty_id)
        except Faculty.DoesNotExist:
            return Response({"error": "Faculty not found"}, status=404)

        rows = list(BoardingHouse.objects.annotate(distance=Distance("geom", faculty.geom)))
        if not rows:
            return Response([])

        def nearest_road_condition(bh):
            nearest = (
                RoadSegment.objects.filter(geom__dwithin=(bh.geom, D(m=300)))
                .annotate(d=Distance("geom", bh.geom))
                .order_by("d")
                .first()
            )
            return nearest.condition if nearest else "good"

        avg_prices = [(r.price_min + r.price_max) / 2 for r in rows]
        max_avg_price = max(avg_prices) or 1

        results = []
        for r, avg_price in zip(rows, avg_prices):
            distance_m = r.distance.m
            road_condition = nearest_road_condition(r)
            distance_score = max(0, 1 - (distance_m / 2000.0))
            price_score = 1 - (avg_price / max_avg_price)
            road_score = ROAD_CONDITION_SCORE.get(road_condition, 1.0)
            suitability = round(distance_score * 0.5 + price_score * 0.25 + road_score * 0.25, 4)

            results.append(
                {
                    "id": r.id,
                    "name": r.name,
                    "address": r.address,
                    "price_min": r.price_min,
                    "price_max": r.price_max,
                    "room_type": r.room_type,
                    "facilities": r.facilities,
                    "photos": r.photos,
                    "contact": r.contact,
                    "lng": r.geom.x,
                    "lat": r.geom.y,
                    "distance_m": round(distance_m, 1),
                    "road_condition": road_condition,
                    "suitability_score": suitability,
                }
            )

        results.sort(key=lambda x: x["suitability_score"], reverse=True)
        return Response(results[:limit])


class RoadSegmentListView(APIView):
    def get(self, request):
        segments = RoadSegment.objects.all()
        features = RoadSegmentGeoJSONSerializer(segments, many=True).data
        return Response({"type": "FeatureCollection", "features": features})

    def post(self, request):
        serializer = RoadSegmentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        segment = serializer.save()
        return Response({"id": segment.id}, status=status.HTTP_201_CREATED)


class RouteView(APIView):
    """
    GET /api/route/?boarding_house_id=1&faculty_id=2&profile=walking

    Calls OSRM for the actual road-network route, then finds
    road_segments within 25m of that route (ST_DWithin via GeoDjango's
    dwithin lookup) to overlay condition data - the "road condition as
    a deciding factor" feature.
    """

    def get(self, request):
        boarding_house_id = request.query_params.get("boarding_house_id")
        faculty_id = request.query_params.get("faculty_id")
        profile = request.query_params.get("profile", "driving")

        if not boarding_house_id or not faculty_id:
            return Response({"error": "boarding_house_id and faculty_id are required"}, status=400)

        try:
            bh = BoardingHouse.objects.get(pk=boarding_house_id)
        except BoardingHouse.DoesNotExist:
            return Response({"error": "Boarding house not found"}, status=404)
        try:
            faculty = Faculty.objects.get(pk=faculty_id)
        except Faculty.DoesNotExist:
            return Response({"error": "Faculty not found"}, status=404)

        coords = f"{bh.geom.x},{bh.geom.y};{faculty.geom.x},{faculty.geom.y}"
        url = f"{settings.OSRM_BASE_URL}/route/v1/{profile}/{coords}?overview=full&geometries=geojson"

        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            return Response({"error": "Failed to reach routing service", "details": str(e)}, status=502)

        if data.get("code") != "Ok" or not data.get("routes"):
            return Response({"error": f"OSRM could not find a route: {data.get('code', 'unknown error')}"}, status=502)

        route = data["routes"][0]
        geometry = route["geometry"]  # GeoJSON LineString dict
        route_line = LineString([(c[0], c[1]) for c in geometry["coordinates"]], srid=4326)

        nearby_segments = RoadSegment.objects.filter(geom__dwithin=(route_line, D(m=25)))

        counts = {"fair": 0, "poor": 0}
        overlay = []
        for seg in nearby_segments:
            counts[seg.condition] += 1
            overlay.append(
                {
                    "id": seg.id,
                    "name": seg.name,
                    "condition": seg.condition,
                    "notes": seg.notes,
                    "geometry": json.loads(seg.geom.geojson),
                }
            )

        if counts["poor"] > 0:
            overall = "poor"
        elif counts["fair"] > 0:
            overall = "fair"
        else:
            overall = "good"

        # Best-effort cache upsert
        RouteCache.objects.update_or_create(
            boarding_house=bh,
            faculty=faculty,
            profile=profile,
            defaults={
                "distance_m": route["distance"],
                "duration_s": route["duration"],
                "geom": route_line,
            },
        )

        return Response(
            {
                "distance_m": route["distance"],
                "duration_s": route["duration"],
                "geometry": geometry,
                "road_condition_overlay": overlay,
                "overall_condition": overall,
                "condition_breakdown": counts,
            }
        )
