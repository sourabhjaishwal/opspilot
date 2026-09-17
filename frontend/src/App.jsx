import { useCallback, useEffect, useState } from "react";
import { getServices } from "./api/client";
import HealthStatus from "./components/HealthStatus";
import ServicesList from "./components/ServicesList";
import IncidentsTable from "./components/IncidentsTable";
import "./App.css";

function App() {
  const [health, setHealth] = useState("checking");
  const [services, setServices] = useState([]);
  const [servicesLoading, setServicesLoading] = useState(true);
  const [summary, setSummary] = useState({ total: 0, open: 0 });
  const [error, setError] = useState("");
  const [refreshToken, setRefreshToken] = useState(0);

  function loadServices() {
    setServicesLoading(true);
    return getServices()
      .then((response) => setServices(response))
      .catch((requestError) => setError(requestError.message))
      .finally(() => setServicesLoading(false));
  }

  useEffect(() => {
    let active = true;
    getServices()
      .then((response) => {
        if (active) setServices(response);
      })
      .catch((requestError) => {
        if (active) setError(requestError.message);
      })
      .finally(() => {
        if (active) setServicesLoading(false);
      });
    return () => {
      active = false;
    };
  }, [refreshToken]);

  function refreshDashboard() {
    setError("");
    setRefreshToken((value) => value + 1);
  }

  const handleSummaryChange = useCallback((total, open) => {
    setSummary({ total, open });
  }, []);

  const healthyServices = services.filter(
    (service) => service.status === "healthy",
  ).length;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark">OP</div>
          <div>
            <p className="eyebrow">Operations control plane</p>
            <h1>OpsPilot</h1>
          </div>
        </div>
        <HealthStatus key={refreshToken} onStatusChange={setHealth} />
      </header>

      <main>
        <section className="intro-row">
          <div>
            <p className="eyebrow accent-text">Live service intelligence</p>
            <h2>Keep the signal clear.</h2>
            <p className="intro-copy">
              A quiet, focused view of the systems your team is responsible for.
            </p>
          </div>
          <button
            className="refresh-button"
            type="button"
            onClick={refreshDashboard}
            title="Refresh dashboard"
          >
            <span aria-hidden="true">↻</span> Refresh data
          </button>
        </section>

        {error && (
          <div className="error-banner" role="alert">
            {error}
          </div>
        )}

        <section className="metric-strip" aria-label="Platform summary">
          <div className="metric-card">
            <span>Services online</span>
            <strong>
              {healthyServices}
              <small> / {services.length}</small>
            </strong>
            <em>registered services</em>
          </div>
          <div className="metric-card">
            <span>Visible incidents</span>
            <strong>{summary.total}</strong>
            <em>{summary.open} requiring attention</em>
          </div>
          <div className="metric-card">
            <span>System status</span>
            <strong className="status-value">
              {health === "healthy"
                ? "Nominal"
                : health === "checking"
                  ? "Checking"
                  : "Offline"}
            </strong>
            <em>last checked just now</em>
          </div>
        </section>

        <div className="content-grid">
          <ServicesList
            services={services}
            loading={servicesLoading}
            onRegistered={loadServices}
            onError={setError}
          />
        </div>
        <IncidentsTable
          key={refreshToken}
          services={services}
          onSummaryChange={handleSummaryChange}
          onError={setError}
        />
      </main>
      <footer>
        <span>OpsPilot / service health</span>
        <span>API v0.1.0</span>
      </footer>
    </div>
  );
}

export default App;
