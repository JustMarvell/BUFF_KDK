from django.contrib.gis.db import models


class Faculty(models.Model):
    """A campus faculty/building. Boarding houses are recommended
    relative to whichever faculty the student selects."""

    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300, blank=True)
    # geography=True stores this as a PostGIS geography(Point,4326),
    # so distance calculations return real metres, not degrees.
    geom = models.PointField(geography=True, srid=4326)

    class Meta:
        verbose_name_plural = "Faculties"
        ordering = ["name"]

    def __str__(self):
        return self.name


class BoardingHouse(models.Model):
    ROOM_TYPE_CHOICES = [
        ("putra", "Putra (male)"),
        ("putri", "Putri (female)"),
        ("campur", "Campur (mixed)"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=300, blank=True)
    price_min = models.PositiveIntegerField(help_text="Monthly price, lower bound")
    price_max = models.PositiveIntegerField(help_text="Monthly price, upper bound")
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, blank=True)
    # Stored as JSON lists so we don't need a separate Facility model for
    # a project of this scope; still queryable with JSONField lookups.
    facilities = models.JSONField(default=list, blank=True, help_text='e.g. ["wifi", "ac", "parkir"]')
    photos = models.JSONField(default=list, blank=True, help_text="List of image URLs")
    contact = models.CharField(max_length=100, blank=True)
    owner_name = models.CharField(max_length=150, blank=True)
    geom = models.PointField(geography=True, srid=4326)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class RoadSegment(models.Model):
    CONDITION_CHOICES = [
        ("good", "Good"),
        ("fair", "Fair"),
        ("poor", "Poor"),
    ]

    name = models.CharField(max_length=200, blank=True)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default="good")
    notes = models.TextField(blank=True)
    reported_by = models.CharField(max_length=150, blank=True)
    geom = models.LineStringField(geography=True, srid=4326)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name or f"Road segment #{self.pk}"


class RouteCache(models.Model):
    """Cached OSRM route between one boarding house and one faculty, so
    repeated requests for the same pair don't hit OSRM every time."""

    boarding_house = models.ForeignKey(BoardingHouse, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    profile = models.CharField(max_length=20, default="driving")
    distance_m = models.FloatField()
    duration_s = models.FloatField()
    geom = models.LineStringField(geography=True, srid=4326)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("boarding_house", "faculty", "profile")
