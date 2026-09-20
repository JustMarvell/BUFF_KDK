from django.contrib.gis.db import models


class Faculty(models.Model):
    """A campus faculty/building. Boarding houses are recommended
    relative to whichever faculty the student selects."""

    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300, blank=True)
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
        ("fair", "Fair"),
        ("poor", "Poor"),
    ]

    name = models.CharField(max_length=200, blank=True)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES)
    notes = models.TextField(blank=True)
    reported_by = models.CharField(max_length=150, blank=True)
    geom = models.GeometryField(geography=True, srid=4326)
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

class RoadNode(models.Model):
    """A point in the routable road network - an intersection, a dead
    end, or any point where the walkable/drivable path changes shape.
    This is the vertex set of the graph Dijkstra searches over."""

    name = models.CharField(max_length=200, blank=True, help_text="Optional label, e.g. an intersection name")
    geom = models.PointField(geography=True, srid=4326)
    # Set only for nodes auto-imported from OpenStreetMap (via osmnx) -
    # lets re-running the import be idempotent instead of duplicating
    # nodes. Manually-drawn nodes leave this blank.
    osm_id = models.BigIntegerField(null=True, blank=True, unique=True, db_index=True)


class RoadEdge(models.Model):
    """A drivable/walkable stretch of road connecting two RoadNodes -
    the edge set of the graph. Treated as bidirectional (two-way)."""

    from_node = models.ForeignKey(RoadNode, on_delete=models.CASCADE, related_name="edges_from")
    to_node = models.ForeignKey(RoadNode, on_delete=models.CASCADE, related_name="edges_to")
    # The actual shape of the road (can have bends, doesn't have to be a
    # straight line between the two nodes) - used both for accurate
    # distance and for drawing the real route on the map afterward.
    geom = models.LineStringField(geography=True, srid=4326)

    def save(self, *args, **kwargs):
        # Force the line's endpoints to exactly match the chosen nodes,
        # regardless of how precisely it was drawn - this is what
        # guarantees the graph is actually connected at every junction.
        from django.contrib.gis.geos import LineString

        coords = list(self.geom.coords)
        coords[0] = (self.from_node.geom.x, self.from_node.geom.y)
        coords[-1] = (self.to_node.geom.x, self.to_node.geom.y)
        self.geom = LineString(coords, srid=4326)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Edge #{self.pk}: {self.from_node} \u2194 {self.to_node}"