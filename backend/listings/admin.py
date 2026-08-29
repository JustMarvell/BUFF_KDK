from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import Faculty, BoardingHouse, RoadSegment, RouteCache


@admin.register(Faculty)
class FacultyAdmin(GISModelAdmin):
    list_display = ("name", "address")
    search_fields = ("name", "address")
    # GISModelAdmin renders an interactive Leaflet-based map widget for
    # the `geom` field automatically - no custom admin template needed.


@admin.register(BoardingHouse)
class BoardingHouseAdmin(GISModelAdmin):
    list_display = ("name", "room_type", "price_min", "price_max", "updated_at")
    list_filter = ("room_type",)
    search_fields = ("name", "address", "owner_name")


@admin.register(RoadSegment)
class RoadSegmentAdmin(GISModelAdmin):
    list_display = ("name", "condition", "reported_by", "updated_at")
    list_filter = ("condition",)
    search_fields = ("name", "notes")


@admin.register(RouteCache)
class RouteCacheAdmin(admin.ModelAdmin):
    list_display = ("boarding_house", "faculty", "profile", "distance_m", "duration_s", "computed_at")
    list_filter = ("profile",)
