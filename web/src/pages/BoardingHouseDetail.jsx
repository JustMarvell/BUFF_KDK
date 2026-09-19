import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../lib/api.js";
import MapView from "../components/MapView.jsx";

function formatDuration(seconds) {
  const mins = Math.round(seconds / 60);
  if (mins < 60) return `${mins} min`;
  return `${Math.floor(mins / 60)}h ${mins % 60}m`;
}

export default function BoardingHouseDetail() {
  const { id } = useParams();
  const [bh, setBh] = useState(null);
  const [faculties, setFaculties] = useState([]);
  const [facultyId, setFacultyId] = useState("");
  const [profile, setProfile] = useState("driving");
  const [route, setRoute] = useState(null);
  const [routeLoading, setRouteLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getBoardingHouse(id).then(setBh).catch((e) => setError(e.message));
    api.getFaculties().then(setFaculties).catch(() => {});
  }, [id]);

  const fetchRoute = async (facId, prof) => {
    if (!facId) return;
    setRouteLoading(true);
    setError(null);
    try {
      const r = await api.getRoute(id, facId, prof);
      setRoute(r);
    } catch (e) {
      setError(e.message);
      setRoute(null);
    } finally {
      setRouteLoading(false);
    }
  };

  useEffect(() => {
    if (facultyId) fetchRoute(facultyId, profile);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [facultyId, profile]);

  if (!bh) {
    return <div className="detail-page">{error ? <p>{error}</p> : <p>Loading…</p>}</div>;
  }

  const selectedFaculty = faculties.find((f) => String(f.id) === String(facultyId));

  return (
    <div className="detail-page">
      <Link to="/" className="btn secondary" style={{ display: "inline-block", marginBottom: 16 }}>
        ← Back to map
      </Link>

      <div className="detail-header">
        <div>
          <h1>{bh.name}</h1>
          <p style={{ color: "var(--color-ink-soft)", margin: "4px 0" }}>{bh.address}</p>
        </div>
        <div className="bh-card-price" style={{ fontSize: 18 }}>
          Rp {bh.price_min?.toLocaleString("id-ID")}–{bh.price_max?.toLocaleString("id-ID")}/mo
        </div>
      </div>

      {bh.description && <p>{bh.description}</p>}

      <div className="bh-card-meta" style={{ marginBottom: 8 }}>
        {bh.room_type && <span className="badge">{bh.room_type}</span>}
        {(bh.facilities || []).map((f) => (
          <span className="badge" key={f}>
            {f.replace(/_/g, " ")}
          </span>
        ))}
      </div>

      {bh.contact && (
        <p>
          <strong>Contact:</strong> {bh.contact}
        </p>
      )}

      <div className="detail-facility-select">
        <label htmlFor="facility-pick" style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase" }}>
          Get route &amp; road condition to your faculty
        </label>
        <div className="filter-row" style={{ marginTop: 8 }}>
          <select id="facility-pick" value={facultyId} onChange={(e) => setFacultyId(e.target.value)}>
            <option value="">Select your faculty…</option>
            {faculties.map((f) => (
              <option key={f.id} value={f.id}>
                {f.name}
              </option>
            ))}
          </select>
          <select value={profile} onChange={(e) => setProfile(e.target.value)}>
            <option value="driving">Driving</option>
            <option value="walking">Walking</option>
            <option value="cycling">Cycling</option>
          </select>
        </div>

        {routeLoading && <p>Calculating route…</p>}
        {error && <p style={{ color: "var(--color-poor)" }}>{error}</p>}

        {route && !routeLoading && (
          <div className="route-summary">
            <div>
              <strong>{(route.distance_m / 1000).toFixed(2)} km</strong> · {formatDuration(route.duration_s)} by {profile}
            </div>
            <div style={{ marginTop: 6 }}>
              Road condition along this route:{" "}
              <span className={`condition-pill ${route.overall_condition}`}>{route.overall_condition}</span>
            </div>
            {route.condition_breakdown && (
              <div style={{ marginTop: 6, fontSize: 12, color: "var(--color-ink-soft)" }}>
                {route.condition_breakdown.poor > 0 &&
                  `${route.condition_breakdown.poor} poor segment(s) reported along the way. `}
                {route.condition_breakdown.fair > 0 && `${route.condition_breakdown.fair} fair segment(s). `}
                {route.road_condition_overlay.length === 0 && "No community road reports along this route yet."}
              </div>
            )}
          </div>
        )}
      </div>

      <div style={{ height: 420, borderRadius: "var(--radius)", overflow: "hidden", border: "1px solid var(--color-border)" }}>
        <MapView
          center={{ lat: bh.lat, lng: bh.lng }}
          zoom={15}
          boardingHouses={[bh]}
          faculties={selectedFaculty ? [selectedFaculty] : []}
          routeGeometry={route ? route.geometry : null}
          roadSegments={route ? { type: "FeatureCollection", features: route.road_condition_overlay.map((s) => ({ type: "Feature", geometry: s.geometry, properties: s })) } : null}
          fitToMarkers={!route}
        />
      </div>
    </div>
  );
}
