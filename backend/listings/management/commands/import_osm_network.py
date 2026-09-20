from django.contrib.gis.geos import LineString, Point
from django.core.management.base import BaseCommand

from listings.models import RoadEdge, RoadNode

# Same UNIMA coordinates used elsewhere in the project.
UNIMA_LAT = 1.26667
UNIMA_LNG = 124.88306


class Command(BaseCommand):
    help = "Import a real road network from OpenStreetMap (via osmnx) into RoadNode/RoadEdge."

    def add_arguments(self, parser):
        parser.add_argument("--lat", type=float, default=UNIMA_LAT, help="Center latitude")
        parser.add_argument("--lng", type=float, default=UNIMA_LNG, help="Center longitude")
        parser.add_argument(
            "--radius", type=int, default=3000,
            help="Radius in metres around the center point to import (default: 3000)",
        )
        parser.add_argument(
            "--network-type", default="all",
            choices=["all", "drive", "walk", "bike"],
            help="Which OSM road/path types to include (default: all)",
        )

    def handle(self, *args, **options):
        try:
            import osmnx as ox
        except ImportError:
            self.stderr.write(self.style.ERROR("osmnx is not installed - run: pip install osmnx"))
            return

        lat, lng, radius, network_type = (
            options["lat"], options["lng"], options["radius"], options["network_type"],
        )

        self.stdout.write(f"Downloading OSM {network_type} network within {radius}m of ({lat}, {lng})...")
        graph = ox.graph.graph_from_point((lat, lng), dist=radius, network_type=network_type)
        nodes_gdf, edges_gdf = ox.convert.graph_to_gdfs(graph)
        self.stdout.write(f"Downloaded {len(nodes_gdf)} nodes and {len(edges_gdf)} edge records from OSM.")

        self.stdout.write("Importing nodes...")
        node_lookup = {}  # osm_id -> RoadNode instance
        for osm_id, row in nodes_gdf.iterrows():
            node, _ = RoadNode.objects.update_or_create(
                osm_id=osm_id,
                defaults={"geom": Point(row.geometry.x, row.geometry.y, srid=4326)},
            )
            node_lookup[osm_id] = node

        self.stdout.write("Importing edges...")
        # edges_gdf is indexed by (u, v, key) - u/v are OSM node ids at
        # each end, key distinguishes parallel edges between the same
        # two nodes (rare, but the OSM data model allows it).
        created = 0
        skipped = 0
        seen_pairs = set()
        for (u, v, _key), row in edges_gdf.iterrows():
            # Treat as undirected: skip if we've already imported the
            # reverse direction of this same pair (avoids duplicate
            # parallel edges, since our graph is undirected anyway).
            pair = tuple(sorted((u, v)))
            if pair in seen_pairs:
                skipped += 1
                continue
            seen_pairs.add(pair)

            from_node = node_lookup.get(u)
            to_node = node_lookup.get(v)
            if not from_node or not to_node or from_node.id == to_node.id:
                skipped += 1
                continue

            geom = row.geometry
            coords = list(geom.coords) if geom is not None else [
                (from_node.geom.x, from_node.geom.y), (to_node.geom.x, to_node.geom.y),
            ]
            if len(coords) < 2:
                skipped += 1
                continue

            RoadEdge.objects.create(
                from_node=from_node,
                to_node=to_node,
                geom=LineString(coords, srid=4326),
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Import complete: {len(node_lookup)} nodes, {created} edges created, {skipped} edge records skipped."
        ))