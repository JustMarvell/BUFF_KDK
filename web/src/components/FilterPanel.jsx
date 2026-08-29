const FACILITY_OPTIONS = ["wifi", "ac", "parkir", "kamar_mandi_dalam", "laundry"];

export default function FilterPanel({ faculties, filters, onChange }) {
  const set = (patch) => onChange({ ...filters, ...patch });

  const toggleFacility = (f) => {
    const current = filters.facility || [];
    const next = current.includes(f) ? current.filter((x) => x !== f) : [...current, f];
    set({ facility: next });
  };

  return (
    <div className="filter-panel">
      <div>
        <label htmlFor="faculty-select">Your faculty</label>
        <select
          id="faculty-select"
          value={filters.faculty_id || ""}
          onChange={(e) => set({ faculty_id: e.target.value || undefined })}
        >
          <option value="">All areas (no recommendation)</option>
          {faculties.map((f) => (
            <option key={f.id} value={f.id}>
              {f.name}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-row">
        <div>
          <label htmlFor="min-price">Min price (Rp)</label>
          <input
            id="min-price"
            type="number"
            min="0"
            placeholder="0"
            value={filters.min_price || ""}
            onChange={(e) => set({ min_price: e.target.value || undefined })}
          />
        </div>
        <div>
          <label htmlFor="max-price">Max price (Rp)</label>
          <input
            id="max-price"
            type="number"
            min="0"
            placeholder="No limit"
            value={filters.max_price || ""}
            onChange={(e) => set({ max_price: e.target.value || undefined })}
          />
        </div>
      </div>

      <div>
        <label htmlFor="room-type">Room type</label>
        <select
          id="room-type"
          value={filters.room_type || ""}
          onChange={(e) => set({ room_type: e.target.value || undefined })}
        >
          <option value="">Any</option>
          <option value="putra">Putra (male)</option>
          <option value="putri">Putri (female)</option>
          <option value="campur">Campur (mixed)</option>
        </select>
      </div>

      <div>
        <label>Facilities</label>
        <div className="filter-row" style={{ flexWrap: "wrap", gap: "6px" }}>
          {FACILITY_OPTIONS.map((f) => {
            const active = (filters.facility || []).includes(f);
            return (
              <button
                key={f}
                type="button"
                onClick={() => toggleFacility(f)}
                className="badge"
                style={{
                  border: active ? "1px solid #2f5d50" : "1px solid var(--color-border)",
                  background: active ? "#e2ece7" : "var(--color-bg)",
                  fontWeight: active ? 700 : 500,
                }}
              >
                {f.replace(/_/g, " ")}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
