from django import forms
from django.conf import settings

# Real coordinates for Universitas Negeri Manado (UNIMA), Tondano campus.
UNIMA_LAT = 1.26667
UNIMA_LNG = 124.88306
DEFAULT_ZOOM = 16


class BaseGoogleMapsGeometryWidget(forms.Textarea):
    """
    Renders a Google Maps-based editor for a GeoDjango geometry field,
    replacing Django's default admin widget. Same underlying approach as
    before: JS writes a GeoJSON string into a hidden <textarea>, which
    GeoDjango's GeometryField.to_python() parses natively via GEOSGeometry().

    Subclasses set `mode`:
      - "point": exactly one marker, click-to-place or drag to move.
      - "road":  a marker (single-point issue) OR one or more polylines
                 (a road path; drawing the polyline tool more than once
                 adds a branch, serialized as a MultiLineString).
    """

    mode = "point"
    template_name = "listings/widgets/gmaps_geom_widget.html"

    class Media:
        js = (
            f"https://maps.googleapis.com/maps/api/js?key={settings.GOOGLE_MAPS_API_KEY}&libraries=places",
        )

    def __init__(self, attrs=None, default_lat=UNIMA_LAT, default_lng=UNIMA_LNG, default_zoom=DEFAULT_ZOOM):
        widget_attrs = {"class": "gmaps-geom-widget-textarea", "style": "display:none;"}
        if attrs:
            widget_attrs.update(attrs)
        super().__init__(widget_attrs)
        self.default_lat = default_lat
        self.default_lng = default_lng
        self.default_zoom = default_zoom

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if value not in (None, ""):
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


class GoogleMapsPointWidget(BaseGoogleMapsGeometryWidget):
    mode = "point"


class GoogleMapsRoadWidget(BaseGoogleMapsGeometryWidget):
    mode = "road"
    
class GoogleMapsSingleLineWidget(BaseGoogleMapsGeometryWidget):
    mode = "single_line"