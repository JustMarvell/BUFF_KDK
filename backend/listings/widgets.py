from django import forms

# Real coordinates for Universitas Negeri Manado (UNIMA), Tondano campus.
# Used as the default map center so admins don't start out looking at
# the middle of the Atlantic Ocean.
UNIMA_LAT = 1.26667
UNIMA_LNG = 124.88306
DEFAULT_ZOOM = 16


class BaseLeafletGeometryWidget(forms.Textarea):
    """
    Renders a Leaflet map (same library as the public web app) for
    editing a GeoDjango geometry field, instead of Django's default
    admin widget (which uses an old bundled OpenLayers build and
    always opens centered on the whole world map).

    The underlying form value is a GeoJSON string written into a
    hidden <textarea> by JS - GeoDjango's GeometryField.to_python()
    accepts GeoJSON strings natively via GEOSGeometry(), so no custom
    field/form-cleaning code is needed on the Python side.

    Subclasses set `mode`:
      - "point": exactly one marker, click-to-place or drag to move.
      - "road":  a marker (single-point issue, e.g. a pothole) OR one
                 or more polylines (a road path; drawing the line tool
                 more than once adds a branch, serialized as a
                 MultiLineString).
    """

    mode = "point"
    template_name = "listings/widgets/leaflet_geom_widget.html"

    class Media:
        css = {
            "all": (
                "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
                "https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css",
            )
        }
        js = (
            "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
            "https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js",
        )

    def __init__(self, attrs=None, default_lat=UNIMA_LAT, default_lng=UNIMA_LNG, default_zoom=DEFAULT_ZOOM):
        widget_attrs = {"class": "leaflet-geom-widget-textarea", "style": "display:none;"}
        if attrs:
            widget_attrs.update(attrs)
        super().__init__(widget_attrs)
        self.default_lat = default_lat
        self.default_lng = default_lng
        self.default_zoom = default_zoom

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if value not in (None, ""):
            # `value` is a GEOSGeometry instance when redisplaying a
            # saved object or after a validation error; a plain string
            # (already GeoJSON) is possible too in edge cases.
            geojson_value = value.geojson if hasattr(value, "geojson") else value
        else:
            geojson_value = ""
        context.update(
            {
                "widget_map_id": f"map_{name}".replace("-", "_"),
                "field_name": name,
                "geojson_value": geojson_value,
                "default_lat": self.default_lat,
                "default_lng": self.default_lng,
                "default_zoom": self.default_zoom,
                "mode": self.mode,
            }
        )
        return context


class LeafletPointWidget(BaseLeafletGeometryWidget):
    mode = "point"


class LeafletRoadWidget(BaseLeafletGeometryWidget):
    mode = "road"
