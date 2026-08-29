from django.contrib import admin
from django.contrib.gis.db import models as gis_models

from .models import BoardingHouse, Faculty, RoadSegment, RouteCache
from .widgets import LeafletPointWidget, LeafletRoadWidget


class LeafletPointAdminMixin:
    """Renders PointField(s) with our campus-centered Leaflet widget
    instead of Django's default (world-centered, OpenLayers-based) one."""

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, gis_models.PointField):
            kwargs["widget"] = LeafletPointWidget()
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
            kwargs["widget"] = LeafletRoadWidget()
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(RouteCache)
class RouteCacheAdmin(admin.ModelAdmin):
    list_display = ("boarding_house", "faculty", "profile", "distance_m", "duration_s", "computed_at")
    list_filter = ("profile",)
