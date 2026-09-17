import { useEffect, useState } from "react";
import { createIncident, getIncidents } from "../api/client";

const emptyIncident = {
  service: "",
  severity: "medium",
  title: "",
  description: "",
};

function formatTime(value) {
  return new Intl.DateTimeFormat("en", {
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

function IncidentsTable({ services, onSummaryChange, onError }) {
  const [filters, setFilters] = useState({
    service: "",
    severity: "",
    status: "",
  });
  const [incidents, setIncidents] = useState({
    items: [],
    total: 0,
    page: 1,
    page_size: 5,
  });
  const [form, setForm] = useState(emptyIncident);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function loadIncidents(nextFilters = filters) {
    setLoading(true);
    return getIncidents(nextFilters)
      .then((response) => {
        setIncidents(response);
        onSummaryChange(
          response.total,
          response.items.filter((incident) => incident.status !== "resolved")
            .length,
        );
      })
      .catch((error) => onError(error.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    let active = true;
    getIncidents({})
      .then((response) => {
        if (!active) return;
        setIncidents(response);
        onSummaryChange(
          response.total,
          response.items.filter((incident) => incident.status !== "resolved")
            .length,
        );
      })
      .catch((error) => {
        if (active) onError(error.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [onError, onSummaryChange]);

  function updateFilter(event) {
    const nextFilters = { ...filters, [event.target.name]: event.target.value };
    setFilters(nextFilters);
    loadIncidents(nextFilters);
  }

  async function submitIncident(event) {
    event.preventDefault();
    setIsSubmitting(true);
    onError("");
    try {
      await createIncident(form);
      setForm(emptyIncident);
      await loadIncidents();
    } catch (error) {
      onError(error.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="dashboard-lower">
      <section className="panel incidents-panel">
        <div className="panel-heading incident-heading">
          <div>
            <p className="eyebrow">Response queue</p>
            <h3>Recent incidents</h3>
          </div>
          <span className="count-label">{incidents.total} matching</span>
        </div>
        <div className="filters" aria-label="Incident filters">
          <select
            name="service"
            value={filters.service}
            onChange={updateFilter}
          >
            <option value="">All services</option>
            {services.map((service) => (
              <option key={service.name} value={service.name}>
                {service.name}
              </option>
            ))}
          </select>
          <select
            name="severity"
            value={filters.severity}
            onChange={updateFilter}
          >
            <option value="">All severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select name="status" value={filters.status} onChange={updateFilter}>
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
        <div className="incident-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Incident</th>
                <th>Service</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {incidents.items.map((incident) => (
                <tr key={incident.id}>
                  <td>
                    <strong>{incident.title}</strong>
                    <span>{incident.description}</span>
                  </td>
                  <td>{incident.service}</td>
                  <td>
                    <span className={`severity ${incident.severity}`}>
                      {incident.severity}
                    </span>
                  </td>
                  <td>
                    <span className={`incident-status ${incident.status}`}>
                      {incident.status}
                    </span>
                  </td>
                  <td>{formatTime(incident.created_at)}</td>
                </tr>
              ))}
              {!loading && incidents.items.length === 0 && (
                <tr>
                  <td className="empty-state" colSpan="5">
                    No incidents match the current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel create-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">Incident intake</p>
            <h3>Report an incident</h3>
          </div>
        </div>
        <form onSubmit={submitIncident}>
          <label>
            Service
            <select
              required
              value={form.service}
              onChange={(event) =>
                setForm({ ...form, service: event.target.value })
              }
            >
              <option value="">Select a service</option>
              {services.map((service) => (
                <option key={service.name} value={service.name}>
                  {service.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Severity
            <select
              value={form.severity}
              onChange={(event) =>
                setForm({ ...form, severity: event.target.value })
              }
            >
              <option>low</option>
              <option>medium</option>
              <option>high</option>
              <option>critical</option>
            </select>
          </label>
          <label>
            Title
            <input
              required
              value={form.title}
              placeholder="What changed?"
              onChange={(event) =>
                setForm({ ...form, title: event.target.value })
              }
            />
          </label>
          <label>
            Description
            <textarea
              required
              rows="3"
              value={form.description}
              placeholder="Add useful context for the responder"
              onChange={(event) =>
                setForm({ ...form, description: event.target.value })
              }
            />
          </label>
          <button
            className="primary-button"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? "Creating..." : "Create incident"}{" "}
            <span aria-hidden="true">→</span>
          </button>
        </form>
      </section>
    </section>
  );
}

export default IncidentsTable;
