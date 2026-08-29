from rest_framework import serializers
from .models import Faculty, BoardingHouse, RoadSegment


class FacultySerializer(serializers.ModelSerializer):
    lng = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()

    class Meta:
        model = Faculty
        fields = ["id", "name", "address", "lng", "lat"]

    def get_lng(self, obj):
        return obj.geom.x

    def get_lat(self, obj):
        return obj.geom.y


class BoardingHouseSerializer(serializers.ModelSerializer):
    lng = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()
    # Present only when the queryset was annotated with `.annotate(distance=...)`
    distance_m = serializers.SerializerMethodField()

    class Meta:
        model = BoardingHouse
        fields = [
            "id", "name", "description", "address", "price_min", "price_max",
            "room_type", "facilities", "photos", "contact", "owner_name",
            "lng", "lat", "distance_m",
        ]

    def get_lng(self, obj):
        return obj.geom.x

    def get_lat(self, obj):
        return obj.geom.y

    def get_distance_m(self, obj):
        distance = getattr(obj, "distance", None)
        return round(distance.m, 1) if distance is not None else None


class BoardingHouseCreateSerializer(serializers.ModelSerializer):
    """Accepts plain lng/lat floats from clients and builds the PointField."""

    lng = serializers.FloatField(write_only=True)
    lat = serializers.FloatField(write_only=True)

    class Meta:
        model = BoardingHouse
        fields = [
            "name", "description", "address", "price_min", "price_max",
            "room_type", "facilities", "photos", "contact", "owner_name",
            "lng", "lat",
        ]

    def create(self, validated_data):
        from django.contrib.gis.geos import Point

        lng = validated_data.pop("lng")
        lat = validated_data.pop("lat")
        validated_data["geom"] = Point(lng, lat, srid=4326)
        return BoardingHouse.objects.create(**validated_data)


class RoadSegmentGeoJSONSerializer(serializers.ModelSerializer):
    """Serializes a queryset into a GeoJSON-shaped feature, ready to drop
    straight into Leaflet's L.geoJSON() on the frontend."""

    class Meta:
        model = RoadSegment
        fields = ["id", "name", "condition", "notes"]

    def to_representation(self, instance):
        import json

        props = super().to_representation(instance)
        return {
            "type": "Feature",
            "geometry": json.loads(instance.geom.geojson),
            "properties": props,
        }


class RoadSegmentCreateSerializer(serializers.ModelSerializer):
    """Accepts a list of [lng, lat] points from clients and builds the LineStringField."""

    points = serializers.ListField(child=serializers.ListField(child=serializers.FloatField()), write_only=True)

    class Meta:
        model = RoadSegment
        fields = ["name", "condition", "notes", "reported_by", "points"]

    def create(self, validated_data):
        from django.contrib.gis.geos import LineString

        points = validated_data.pop("points")
        if len(points) < 2:
            raise serializers.ValidationError("points must contain at least 2 [lng, lat] pairs")
        validated_data["geom"] = LineString([(p[0], p[1]) for p in points], srid=4326)
        return RoadSegment.objects.create(**validated_data)
