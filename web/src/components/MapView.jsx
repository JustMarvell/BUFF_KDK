import { useEffect, useMemo } from "react";
import { APIProvider, Map, AdvancedMarker, Pin, Polyline, Polygon, useMap } from "@vis.gl/react-google-maps";

const CONDITION_COLOR = { good: "#3c8f5c", fair: "#d9a441", poor: "#c1483e" };
const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

function FitBounds({ points }) {
  const map = useMap();
  useEffect(() => {
    if (!map || !points || !points.length) return;
    const bounds = new window.google.maps.LatLngBounds();
    points.forEach(([lat, lng]) => bounds.extend({ lat, lng }));
    map.fitBounds(bounds, 60);
  }, [map, points]);
  return null;
}

function RoadSegmentLayer({ roadSegments }) {
  if (!roadSegments) return null;
  return roadSegments.features.map((feature) => {
    const { id, name, condition, notes } = feature.properties;
    const color = CONDITION_COLOR[condition] || "#888888";
    const geom = feature.geometry;

    if (geom.type === "Point") {
      const [lng, lat] = geom.coordinates;
      return (
        <AdvancedMarker
          key={`road-${id}`}
          position={{ lat, lng }}
          title={`${name || "Reported spot"} - ${condition}${notes ? `: ${notes}` : ""}`}
        >
          <Pin background={color} borderColor="#fff" glyphColor="#fff" scale={0.8} />
        </AdvancedMarker>
      );
    }
    if (geom.type === "LineString") {
      const path = geom.coordinates.map(([lng, lat]) => ({ lat, lng }));
      return <Polyline key={`road-${id}`} path={path} strokeColor={color} strokeWeight={5} strokeOpacity={0.8} />;
    }
    if (geom.type === "MultiLineString") {
      return geom.coordinates.map((line, i) => {
        const path = line.map(([lng, lat]) => ({ lat, lng }));
        return <Polyline key={`road-${id}-${i}`} path={path} strokeColor={color} strokeWeight={5} strokeOpacity={0.8} />;
      });
    }
    return null;
  });
}

function lerpColor(colorA, colorB, t) {
  const a = parseInt(colorA.slice(1), 16);
  const b = parseInt(colorB.slice(1), 16);
  const ar = (a >> 16) & 0xff, ag = (a >> 8) & 0xff, ab = a & 0xff;
  const br = (b >> 16) & 0xff, bg = (b >> 8) & 0xff, bb = b & 0xff;
  const r = Math.round(ar + (br - ar) * t);
  const g = Math.round(ag + (bg - ag) * t);
  const bl = Math.round(ab + (bb - ab) * t);
  return `rgb(${r},${g},${bl})`;
}

function densityColor(normalized, metric) {
  // road_condition: pale yellow -> red (severity). boarding_houses: pale blue -> deep blue (density).
  return metric === "road_condition"
    ? lerpColor("#fff3b0", "#c1483e", normalized)
    : lerpColor("#dbe9ff", "#1b4f8c", normalized);
}

function HeatmapLayer({ heatmap }) {
  if (!heatmap) return null;
  return heatmap.features.map((f, i) => {
    const ring = f.geometry.coordinates[0].map(([lng, lat]) => ({ lat, lng }));
    return (
      <Polygon
        key={`heat-${i}`}
        paths={ring}
        strokeWeight={0}
        fillColor={densityColor(f.properties.normalized, heatmap.metric)}
        fillOpacity={0.55}
      />
    );
  });
}

export default function MapView({
  center = { lat: 1.26667, lng: 124.88306 }, // Universitas Negeri Manado (UNIMA), Tondano
  zoom = 15,
  boardingHouses = [],
  faculties = [],
  roadSegments,
  routeGeometry,
  heatmap,
  onSelectBoardingHouse,
  fitToMarkers = false,
}) {
  const fitPoints = useMemo(() => {
    if (!fitToMarkers) return null;
    return [
      ...boardingHouses.map((b) => [b.lat, b.lng]),
      ...faculties.map((f) => [f.lat, f.lng]),
    ];
  }, [fitToMarkers, boardingHouses, faculties]);

  const routePath = routeGeometry
    ? routeGeometry.coordinates.map(([lng, lat]) => ({ lat, lng }))
    : null;

  if (!GOOGLE_MAPS_API_KEY) {
    return <div style={{ padding: 16 }}>Missing VITE_GOOGLE_MAPS_API_KEY - check web/.env.</div>;
  }

  return (
    <APIProvider apiKey={GOOGLE_MAPS_API_KEY}>
      <Map
        defaultCenter={center}
        defaultZoom={zoom}
        mapId="DEMO_MAP_ID"
        className="map-container"
        gestureHandling="greedy"
      >
        <RoadSegmentLayer roadSegments={roadSegments} />
        <HeatmapLayer heatmap={heatmap} />

        {routePath && (
          <Polyline path={routePath} strokeColor="#2f5d50" strokeWeight={5} strokeOpacity={0.9} />
        )}

        {faculties.map((f) => (
          <AdvancedMarker key={`fac-${f.id}`} position={{ lat: f.lat, lng: f.lng }} title={f.name}>
            <Pin background="#2f5d50" borderColor="#fff" glyphColor="#fff" />
          </AdvancedMarker>
        ))}

        {boardingHouses.map((b) => (
          <AdvancedMarker
            key={`bh-${b.id}`}
            position={{ lat: b.lat, lng: b.lng }}
            title={`${b.name} - Rp ${b.price_min?.toLocaleString("id-ID")}-${b.price_max?.toLocaleString("id-ID")}`}
            onClick={() => onSelectBoardingHouse && onSelectBoardingHouse(b.id)}
          />
        ))}

        {fitToMarkers && fitPoints && fitPoints.length > 0 && <FitBounds points={fitPoints} />}
      </Map>
    </APIProvider>
  );
}