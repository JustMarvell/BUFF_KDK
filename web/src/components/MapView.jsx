import { MapContainer, TileLayer, Marker, Popup, GeoJSON, Polyline, useMap } from "react-leaflet";
import L from "leaflet";
import { useEffect } from "react";

// Leaflet's default marker icons reference image files that don't resolve
// correctly under bundlers like Vite - rebuild them from the CDN instead.
const houseIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

const facultyIcon = new L.DivIcon({
  className: "faculty-marker",
  html: `<div style="background:#2f5d50;border:2px solid white;width:16px;height:16px;border-radius:4px;box-shadow:0 1px 4px rgba(0,0,0,.4)"></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

const CONDITION_COLOR = { good: "#3c8f5c", fair: "#d9a441", poor: "#c1483e" };

function FitBounds({ points }) {
  const map = useMap();
  useEffect(() => {
    if (!points || !points.length) return;
    const bounds = L.latLngBounds(points.map(([lat, lng]) => [lat, lng]));
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 16 });
  }, [points, map]); // eslint-disable-line react-hooks/exhaustive-deps
  return null;
}

export default function MapView({
  center = [1.4748, 124.8421],
  zoom = 15,
  boardingHouses = [],
  faculties = [],
  roadSegments,
  routeGeometry,
  selectedId,
  onSelectBoardingHouse,
  fitToMarkers = false,
}) {
  const roadStyle = (feature) => ({
    color: CONDITION_COLOR[feature.properties.condition] || "#888",
    weight: 5,
    opacity: 0.75,
  });

  const routeLatLngs = routeGeometry
    ? routeGeometry.coordinates.map(([lng, lat]) => [lat, lng])
    : null;

  const fitPoints = fitToMarkers
    ? [...boardingHouses.map((b) => [b.lat, b.lng]), ...faculties.map((f) => [f.lat, f.lng])]
    : null;

  return (
    <MapContainer center={center} zoom={zoom} className="map-container" scrollWheelZoom>
      <TileLayer
        // Free OpenStreetMap tiles - no API key required.
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {roadSegments && (
        <GeoJSON
          key={JSON.stringify(roadSegments.features.map((f) => f.properties.id))}
          data={roadSegments}
          style={roadStyle}
          onEachFeature={(feature, layer) => {
            const { name, condition, notes } = feature.properties;
            layer.bindPopup(
              `<strong>${name || "Road segment"}</strong><br/>Condition: ${condition}${
                notes ? `<br/><em>${notes}</em>` : ""
              }`
            );
          }}
        />
      )}

      {routeLatLngs && <Polyline positions={routeLatLngs} pathOptions={{ color: "#2f5d50", weight: 5, opacity: 0.9 }} />}

      {faculties.map((f) => (
        <Marker key={`fac-${f.id}`} position={[f.lat, f.lng]} icon={facultyIcon}>
          <Popup>
            <div className="popup-title">{f.name}</div>
            {f.address && <div>{f.address}</div>}
          </Popup>
        </Marker>
      ))}

      {boardingHouses.map((b) => (
        <Marker
          key={`bh-${b.id}`}
          position={[b.lat, b.lng]}
          icon={houseIcon}
          eventHandlers={{ click: () => onSelectBoardingHouse && onSelectBoardingHouse(b.id) }}
        >
          <Popup>
            <div className="popup-title">{b.name}</div>
            <div>Rp {b.price_min?.toLocaleString("id-ID")} – {b.price_max?.toLocaleString("id-ID")} /mo</div>
            {b.distance_m != null && <div>{(b.distance_m / 1000).toFixed(2)} km from selected faculty</div>}
            <div className="popup-actions">
              <a className="btn" href={`/boarding-houses/${b.id}`}>
                Details
              </a>
            </div>
          </Popup>
        </Marker>
      ))}

      {fitToMarkers && fitPoints && fitPoints.length > 0 && <FitBounds points={fitPoints} />}
    </MapContainer>
  );
}
