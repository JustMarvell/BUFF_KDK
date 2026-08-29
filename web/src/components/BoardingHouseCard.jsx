import { useNavigate } from "react-router-dom";

const CONDITION_LABEL = { good: "Good road", fair: "Fair road", poor: "Poor road" };

export default function BoardingHouseCard({ bh, active, onHover }) {
  const navigate = useNavigate();

  return (
    <div
      className={`bh-card${active ? " active" : ""}`}
      onMouseEnter={() => onHover && onHover(bh.id)}
      onClick={() => navigate(`/boarding-houses/${bh.id}`)}
    >
      <div className="bh-card-top">
        <div className="bh-card-name">{bh.name}</div>
        <div className="bh-card-price">
          Rp {bh.price_min?.toLocaleString("id-ID")}–{bh.price_max?.toLocaleString("id-ID")}
        </div>
      </div>

      <div className="bh-card-meta">
        {bh.room_type && <span className="badge">{bh.room_type}</span>}
        {bh.distance_m != null && <span className="badge">{(bh.distance_m / 1000).toFixed(2)} km</span>}
        {bh.road_condition && (
          <span className="badge">
            <span className={`badge-dot ${bh.road_condition}`} />
            {CONDITION_LABEL[bh.road_condition]}
          </span>
        )}
        {bh.suitability_score != null && (
          <span className="suitability-score">Match {Math.round(bh.suitability_score * 100)}%</span>
        )}
      </div>
    </div>
  );
}
