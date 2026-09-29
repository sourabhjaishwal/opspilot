// Main operational dashboard page aggregating telemetry, services, and incident management
import { useEffect, useState, useCallback } from "react";
import { getServices } from "../api/client";
import { useAuth } from "../context/useAuth";
import MetricStrip from "../components/MetricStrip";
import ServicesList from "../components/ServicesList";
import IncidentsTable from "../components/IncidentsTable";
import IncidentPage from "./IncidentPage";

export default function DashboardPage() {
  const { user } = useAuth();
  const [services, setServices] = useState([]);
  const [summary, setSummary] = useState({ totalIncidents: 0, openIncidents: 0 });
  const [error, setError] = useState("");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedIncident, setSelectedIncident] = useState(null);

  // Fetch all registered services
  const loadServices = useCallback(async () => {
    try {
      const data = await getServices();
      setServices(data);
      return data;
    } catch (err) {
      setError(err.message || "Failed to load services");
      return [];
    }
  }, []);

  // Initial load
  useEffect(() => {
    let isMounted = true;
    getServices()
      .then((data) => {
        if (isMounted) setServices(data);
      })
      .catch((err) => {
        if (isMounted) setError(err.message || "Failed to load services");
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Handle manual dashboard refresh
  async function handleRefresh() {
    setIsRefreshing(true);
    setError(""); // Clear previous errors on refresh
    try {
      await loadServices();
      setRefreshKey((prev) => prev + 1); // Trigger child component reload
    } catch (err) {
      setError(err.message || "Failed to refresh data");
    } finally {
      setIsRefreshing(false);
    }
  }

  const handleSummaryChange = useCallback((total, open) => {
    setSummary({ totalIncidents: total, openIncidents: open });
  }, []);

  if (selectedIncident) {
    return (
      <IncidentPage
        incident={selectedIncident}
        onBack={() => {
          setSelectedIncident(null);
          handleRefresh();
        }}
        onUpdate={() => {
          // Additional update logic if needed
        }}
      />
    );
  }

  return (
    <div className="dashboard-layout">
      {/* Dashboard intro header */}
      <div className="intro-row">
        <div>
          <h2>Operational Dashboard</h2>
          <p>
            Track real-time microservice status, active incidents, and response
            telemetry.
          </p>
        </div>
        <button
          type="button"
          className="ghost-button refresh-button"
          onClick={handleRefresh}
          disabled={isRefreshing}
        >
          {isRefreshing ? "Refreshing..." : "Refresh data"}
        </button>
      </div>

      {/* Dashboard error alert banner */}
      {error && (
        <div className="error-banner" role="alert">
          <span>{error}</span>
          <button
            type="button"
            className="ghost-button small-button"
            onClick={() => setError("")}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Metric telemetry strip */}
      <MetricStrip
        servicesCount={services.length}
        openIncidentsCount={summary.openIncidents}
        totalIncidentsCount={summary.totalIncidents}
      />

      {/* Primary content grid */}
      <div className="content-grid">
        <ServicesList
          services={services}
          isAdmin={user?.role === 'admin'}
          onRegistered={loadServices}
          onError={setError}
        />
        <IncidentsTable
          key={refreshKey}
          services={services}
          onSummaryChange={handleSummaryChange}
          onError={setError}
          onSelectIncident={setSelectedIncident}
        />
      </div>
    </div>
  );
}
