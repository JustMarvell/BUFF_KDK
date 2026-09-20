import networkx as nx
from django.contrib.gis.db.models.functions import Distance, Length
from django.contrib.gis.measure import D

from ..models import RoadEdge, RoadNode, RoadSegment

SPEED_MPS = {
    "driving": 30 * 1000 / 3600,
    "walking": 5 * 1000 / 3600,
    "cycling": 15 * 1000 / 3600,
}

# How much to multiply an edge's real distance by, for pathfinding
# purposes only, when a condition report is nearby. Tunable - these
# values just need to be "enough to matter" without ever fully
# blocking a road (no infinite weight), so a poor road stays usable
# when it's genuinely the only connection.
CONDITION_PENALTY = {
    "poor": 4.0,
    "fair": 1.8,
}
# How close a condition report needs to be to an edge to be considered
# "on this stretch of road" - same distance used for the final route
# overlay, for consistency.
CONDITION_CHECK_BUFFER_M = 25


class RouteNotFound(Exception):
    pass


def _edge_condition_penalty(edge_geom):
    """Checks whether any fair/poor RoadSegment report lies within
    CONDITION_CHECK_BUFFER_M of this edge, and returns the weight
    multiplier to apply. Does not affect the edge's real distance -
    only how attractive Dijkstra finds it relative to alternatives."""
    conditions = set(
        RoadSegment.objects.filter(
            condition__in=["poor", "fair"],
            geom__dwithin=(edge_geom, D(m=CONDITION_CHECK_BUFFER_M)),
        ).values_list("condition", flat=True)
    )
    if "poor" in conditions:
        return CONDITION_PENALTY["poor"]
    if "fair" in conditions:
        return CONDITION_PENALTY["fair"]
    return 1.0


def build_graph():
    """
    Builds an undirected graph from RoadNode/RoadEdge data. Each edge
    carries two separate numbers:
      - length_m: real-world distance (metres), via PostGIS Length() -
        this is what gets reported to the user as the route's distance.
      - weight: length_m multiplied by a condition penalty if a nearby
        RoadSegment reports fair/poor - this is what Dijkstra actually
        minimizes, so the algorithm can prefer a longer-but-better road.
    """
    graph = nx.Graph()

    for node in RoadNode.objects.all():
        graph.add_node(node.id, point=node.geom)

    edges = RoadEdge.objects.select_related("from_node", "to_node").annotate(length_m=Length("geom"))
    for edge in edges:
        length_m = edge.length_m.m
        penalty = _edge_condition_penalty(edge.geom)
        graph.add_edge(
            edge.from_node_id,
            edge.to_node_id,
            length_m=length_m,
            weight=length_m * penalty,
            condition_penalty=penalty,
            geom=edge.geom,
            from_node_id=edge.from_node_id,
            to_node_id=edge.to_node_id,
        )
    return graph


def nearest_node(point, max_distance_m=1000):
    """Finds the RoadNode nearest to an arbitrary point (e.g. a boarding
    house or faculty), within a sanity-check radius."""
    return (
        RoadNode.objects.filter(geom__dwithin=(point, D(m=max_distance_m)))
        .annotate(distance=Distance("geom", point))
        .order_by("distance")
        .first()
    )


def shortest_path(origin_point, destination_point):
    """
    Computes the route between two arbitrary points: snaps each to its
    nearest RoadNode, then runs Dijkstra's algorithm (via NetworkX) over
    the condition-weighted graph. The path Dijkstra picks is optimized
    for the penalized `weight`, but the distance reported back is the
    real, unpenalized `length_m` sum along that same path - the penalty
    only ever influences *which* path is chosen, never the number shown
    to the user.
    """
    graph = build_graph()
    if graph.number_of_nodes() == 0:
        raise RouteNotFound("Road network is empty - add RoadNode/RoadEdge data first.")

    origin_node = nearest_node(origin_point)
    destination_node = nearest_node(destination_point)
    if origin_node is None or destination_node is None:
        raise RouteNotFound("Could not find a nearby road network node for one of the endpoints.")

    try:
        node_path = nx.dijkstra_path(graph, origin_node.id, destination_node.id, weight="weight")
    except nx.NetworkXNoPath:
        raise RouteNotFound("No connected path exists between these two points in the road network yet.")

    coordinates = [(origin_point.x, origin_point.y), (origin_node.geom.x, origin_node.geom.y)]
    network_distance_m = 0.0

    for i in range(len(node_path) - 1):
        a, b = node_path[i], node_path[i + 1]
        edge_data = graph.get_edge_data(a, b)
        network_distance_m += edge_data["length_m"]

        coords = list(edge_data["geom"].coords)
        if edge_data["from_node_id"] != a:
            coords = list(reversed(coords))
        coordinates.extend(coords[1:])  # skip first point - already the previous segment's end

    coordinates.append((destination_point.x, destination_point.y))

    origin_connector_m = origin_node.distance.m
    destination_connector_m = destination_node.distance.m
    total_distance_m = origin_connector_m + network_distance_m + destination_connector_m

    return {"distance_m": total_distance_m, "coordinates": coordinates}