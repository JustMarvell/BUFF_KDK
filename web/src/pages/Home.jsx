import { useEffect, useState, useCallback } from "react";
import { api } from "../lib/api.js";
import MapView from "../components/MapView.jsx";
import FilterPanel from "../components/FilterPanel.jsx";
import BoardingHouseCard from "../components/BoardingHouseCard.jsx";

export default function Home() {
  const [faculties, setFaculties] = useState([]);
  const [roadSegments, setRoadSegments] = useState(null);
  const [filters, setFilters] = useState({});
  const [boardingHouses, setBoardingHouses] = useState([]);
  const [hoveredId, setHoveredId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getFaculties().then(setFaculties).catch((e) => setError(e.message));
    api.getRoadSegments().then(setRoadSegments).catch(() => {});
  }, []);

  const loadResults = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (filters.faculty_id) {
        // Faculty selected: show the ranked, distance+road+price-aware
        // recommendation list, our core differentiating feature.
        const rows = await api.getRecommended(filters.faculty_id, 20);
        setBoardingHouses(rows);
      } else {
        const rows = await api.getBoardingHouses(filters);
        setBoardingHouses(rows);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadResults();
  }, [loadResults]);

  return (
    <div className="app-body">
      <aside className="sidebar">
        <FilterPanel faculties={faculties} filters={filters} onChange={setFilters} />

        {error && <div style={{ color: "var(--color-poor)", marginBottom: 10 }}>{error}</div>}

        <div className="result-count">
          {loading ? "Loading…" : `${boardingHouses.length} boarding house${boardingHouses.length === 1 ? "" : "s"}`}
          {filters.faculty_id ? " · ranked by suitability" : ""}
        </div>

        {!loading && boardingHouses.length === 0 && (
          <div className="empty-state">No boarding houses match these filters yet.</div>
        )}

        {boardingHouses.map((bh) => (
          <BoardingHouseCard key={bh.id} bh={bh} active={hoveredId === bh.id} onHover={setHoveredId} />
        ))}
      </aside>

      <MapView
        boardingHouses={boardingHouses}
        faculties={faculties}
        roadSegments={roadSegments}
        fitToMarkers
        onSelectBoardingHouse={setHoveredId}
      />
    </div>
  );
}
