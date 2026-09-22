import math

from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.geos import Polygon
from django.db.models.functions import Cast

from ..models import BoardingHouse, RoadSegment

METERS_PER_DEGREE_LAT = 111320
CONDITION_WEIGHT = {"poor": 2, "fair": 1}


def _meters_to_degrees(meters, at_latitude):
    lat_deg = meters / METERS_PER_DEGREE_LAT
    lng_deg = meters / (METERS_PER_DEGREE_LAT * math.cos(math.radians(at_latitude)))
    return lat_deg, lng_deg


def _data_extent(padding_m=300):
    """Bounding box around existing boarding house data, with padding -
    the grid adapts to wherever your data actually is, rather than a
    hardcoded area. Computed in Python rather than via Django's Extent
    aggregate, since PostGIS's ST_Extent has no geography overload -
    only geometry - and our geom fields are geography-typed for
    accurate real-world distance calculations elsewhere."""
    points = list(BoardingHouse.objects.values_list("geom", flat=True))
    if not points:
        return None
    lngs = [p.x for p in points]
    lats = [p.y for p in points]
    min_lng, max_lng = min(lngs), max(lngs)
    min_lat, max_lat = min(lats), max(lats)
    center_lat = (min_lat + max_lat) / 2
    pad_lat, pad_lng = _meters_to_degrees(padding_m, center_lat)
    return (min_lng - pad_lng, min_lat - pad_lat, max_lng + pad_lng, max_lat + pad_lat)


def _build_grid(bbox, cell_size_m):
    min_lng, min_lat, max_lng, max_lat = bbox
    center_lat = (min_lat + max_lat) / 2
    cell_lat_deg, cell_lng_deg = _meters_to_degrees(cell_size_m, center_lat)

    cells = []
    lat = min_lat
    while lat < max_lat:
        lng = min_lng
        while lng < max_lng:
            cells.append((lng, lat, lng + cell_lng_deg, lat + cell_lat_deg))
            lng += cell_lng_deg
        lat += cell_lat_deg
    return cells


def boarding_house_density(cell_size_m=200):
    bbox = _data_extent()
    if not bbox:
        return []
    results = []
    for (min_lng, min_lat, max_lng, max_lat) in _build_grid(bbox, cell_size_m):
        cell = Polygon.from_bbox((min_lng, min_lat, max_lng, max_lat))
        cell.srid = 4326
        # PostGIS's ST_Within has no geography overload, so we cast the
        # geography column to geometry just for this lookup - verified
        # against a real PostGIS instance that this produces correct results.
        count = (
            BoardingHouse.objects.annotate(geom_geometry=Cast("geom", GeometryField()))
            .filter(geom_geometry__within=cell)
            .count()
        )
        if count > 0:
            results.append({"bbox": (min_lng, min_lat, max_lng, max_lat), "value": count})
    return results


def road_condition_density(cell_size_m=200):
    bbox = _data_extent()
    if not bbox:
        return []
    results = []
    for (min_lng, min_lat, max_lng, max_lat) in _build_grid(bbox, cell_size_m):
        cell = Polygon.from_bbox((min_lng, min_lat, max_lng, max_lat))
        cell.srid = 4326
        segments = RoadSegment.objects.filter(geom__intersects=cell)
        weight = sum(CONDITION_WEIGHT.get(s.condition, 0) for s in segments)
        if weight > 0:
            results.append({"bbox": (min_lng, min_lat, max_lng, max_lat), "value": weight})
    return results