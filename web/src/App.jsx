import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home.jsx";
import BoardingHouseDetail from "./pages/BoardingHouseDetail.jsx";

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark">KostFinder</span>
          <span className="brand-tag">boarding houses near campus</span>
        </div>
      </header>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/boarding-houses/:id" element={<BoardingHouseDetail />} />
      </Routes>
    </div>
  );
}
