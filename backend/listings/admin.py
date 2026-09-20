from django.contrib import admin
from django.contrib.gis.db import models as gis_models

from .models import BoardingHouse, Faculty, RoadSegment, RouteCache, RoadNode, RoadEdge
from .widgets import GoogleMapsPointWidget, GoogleMapsRoadWidget, GoogleMapsSingleLineWidget


class LeafletPointAdminMixin:
    """Renders PointField(s) with our campus-centered Leaflet widget
    instead of Django's default (world-centered, OpenLayers-based) one."""

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, gis_models.PointField):
            kwargs["widget"] = GoogleMapsPointWidget()
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(Faculty)
class FacultyAdmin(LeafletPointAdminMixin, admin.ModelAdmin):
    list_display = ("name", "address")
    search_fields = ("name", "address")


@admin.register(BoardingHouse)
class BoardingHouseAdmin(LeafletPointAdminMixin, admin.ModelAdmin):
    list_display = ("name", "room_type", "price_min", "price_max", "updated_at")
    list_filter = ("room_type",)
    search_fields = ("name", "address", "owner_name")


@admin.register(RoadSegment)
class RoadSegmentAdmin(admin.ModelAdmin):
    list_display = ("name", "condition", "reported_by", "updated_at")
    list_filter = ("condition",)
    search_fields = ("name", "notes")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, gis_models.GeometryField):
            kwargs["widget"] = GoogleMapsRoadWidget()
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(RouteCache)
class RouteCacheAdmin(admin.ModelAdmin):
    list_display = ("boarding_house", "faculty", "profile", "distance_m", "duration_s", "computed_at")
    list_filter = ("profile",)
    
@admin.register(RoadNode)
class RoadNodeAdmin(LeafletPointAdminMixin, admin.ModelAdmin):
    list_display = ("name", "id")
    search_fields = ("name",)


@admin.register(RoadEdge)
class RoadEdgeAdmin(admin.ModelAdmin):
    list_display = ("id", "from_node", "to_node")
    change_form_template = "admin/listings/roadedge/change_form.html"

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, gis_models.LineStringField):
            kwargs["widget"] = GoogleMapsSingleLineWidget()
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def _with_node_coords(self, extra_context):
        import json
        extra_context = extra_context or {}
        extra_context["road_nodes_json"] = json.dumps(
            [{"id": n.id, "lat": n.geom.y, "lng": n.geom.x} for n in RoadNode.objects.all()]
        )
        return extra_context

    def add_view(self, request, form_url="", extra_context=None):
        return super().add_view(request, form_url, self._with_node_coords(extra_context))

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return super().change_view(request, object_id, form_url, self._with_node_coords(extra_context))
