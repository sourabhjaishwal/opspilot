import { useEffect, useState, useCallback } from "react";
import { createIncident, getIncidents } from "../api/client";

const emptyIncident = {
  service_id: "",
  severity: "medium",
  title: "",
  description: "",
};

const initialFilters = {
  service: "",
  severity: "",
  status: "",
  page: 1,
};

function formatDate(isoString) {
  return new Date(isoString).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function stateLabel(status) {
  if (status === "resolved") return "Resolved";
  if (status === "investigating") return "Investigating";
  return "Open";
}

export default function IncidentsTable({ services, onSummaryChange, onError, onSelectIncident }) {
  const [incidents, setIncidents] = useState({ items: [], total: 0 });
  const [filters, setFilters] = useState(initialFilters);
  const [form, setForm] = useState(emptyIncident);
  const [loading, setLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState("");
  const [formSuccess, setFormSuccess] = useState("");

  const loadIncidents = useCallback(
    async (queryFilters = filters) => {
      setLoading(true);
      try {
        const response = await getIncidents(queryFilters);
        setIncidents(response);
        if (onSummaryChange) {
          getIncidents({ page: 1, page_size: 100 })
            .then((allData) => {
              const openCount = allData.items.filter(
                (incident) => incident.status !== "resolved",
              ).length;
              onSummaryChange(allData.total, openCount);
            })
            .catch(() => {
              const openCount = response.items.filter(
                (incident) => incident.status !== "resolved",
              ).length;
              onSummaryChange(response.total, openCount);
            });
        }
        return response;
      } catch (error) {
        if (onError) onError(error.message);
      } finally {
        setLoading(false);
      }
    },
    [filters, onError, onSummaryChange],
  );

  useEffect(() => {
    let isMounted = true;
    getIncidents({ page: 1, page_size: 5 })
      .then((response) => {
        if (!isMounted) return;
        setIncidents(response);
        if (onSummaryChange) {
          getIncidents({ page: 1, page_size: 100 })
            .then((allData) => {
              if (!isMounted) return;
              const openCount = allData.items.filter(
                (incident) => incident.status !== "resolved",
              ).length;
              onSummaryChange(allData.total, openCount);
            })
            .catch(() => {
              const openCount = response.items.filter(
                (incident) => incident.status !== "resolved",
              ).length;
              onSummaryChange(response.total, openCount);
            });
        }
      })
      .catch((error) => {
        if (isMounted && onError) onError(error.message);
      });

    return () => {
      isMounted = false;
    };
  }, [onError, onSummaryChange]);

  function handleFilterChange(key, value) {
    const nextFilters = { ...filters, [key]: value, page: 1 };
    setFilters(nextFilters);
    loadIncidents(nextFilters);
  }

  function handlePageChange(newPage) {
    const nextFilters = { ...filters, page: newPage };
    setFilters(nextFilters);
    loadIncidents(nextFilters);
  }

  async function submitIncident(event) {
    event.preventDefault();
    setFormError("");
    setFormSuccess("");

    if (!form.service_id) {
      setFormError("Please select an affected service.");
      return;
    }

    setIsSubmitting(true);
    try {
      await createIncident({
        ...form,
        service_id: Number(form.service_id),
      });

      setForm(emptyIncident);
      setFilters(initialFilters);
      setFormSuccess("Incident logged successfully.");

      await loadIncidents(initialFilters);
    } catch (error) {
      const message =
        !error?.message || error.message.toLowerCase().includes("failed to fetch")
          ? "Failed to create incident"
          : error.message;
      setFormError(message);
      if (onError) onError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  const totalPages = Math.ceil(incidents.total / 5);

  return (
    <div className="incident-layout">
      {/* Incidents table card */}
      <section className="card">
        <div className="card-header">
          <div>
            <h2>Recent Incidents ({incidents.total})</h2>
            <p>Showing {incidents.items.length} of {incidents.total} total recorded incidents</p>
          </div>
        </div>

        {/* Filters */}
        <div className="filters-row">
          <select
            value={filters.service}
            onChange={(e) => handleFilterChange("service", e.target.value)}
            aria-label="Filter by service"
          >
            <option value="">All Services</option>
            {services.map((svc) => (
              <option key={svc.id} value={svc.name}>
                {svc.name}
              </option>
            ))}
          </select>
          <select
            value={filters.severity}
            onChange={(e) => handleFilterChange("severity", e.target.value)}
            aria-label="Filter by severity"
          >
            <option value="">All Severities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
          <select
            value={filters.status}
            onChange={(e) => handleFilterChange("status", e.target.value)}
            aria-label="Filter by status"
          >
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>

        {/* Table */}
        <div className="table-wrapper">
          {loading ? (
            <p className="loading-state">Loading incidents...</p>
          ) : incidents.items.length === 0 ? (
            <p className="empty-state">No incidents match the selected filters.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Incident Number</th>
                  <th>Created On</th>
                  <th>Severity Level</th>
                  <th>Incident Title</th>
                  <th>Current State</th>
                </tr>
              </thead>
              <tbody>
                {incidents.items.map((incident) => (
                  <tr
                    key={incident.id}
                    className="incident-table-row"
                    onClick={() => onSelectIncident(incident)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") onSelectIncident(incident);
                    }}
                    aria-label={`View details for incident ${incident.incident_number || incident.id}: ${incident.title}`}
                  >
                    <td>
                      <span className="incident-number-cell">
                        {incident.incident_number || `#${incident.id}`}
                      </span>
                    </td>
                    <td className="timestamp-cell">{formatDate(incident.created_at)}</td>
                    <td>
                      <span className={"severity-pill " + incident.severity}>
                        {incident.severity}
                      </span>
                    </td>
                    <td>
                      <strong>{incident.title}</strong>
                      <p className="incident-description">{incident.service}</p>
                    </td>
                    <td>
                      <span className={"status-pill " + incident.status}>
                        {stateLabel(incident.status)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="pagination-row">
            <button
              disabled={filters.page <= 1}
              onClick={() => handlePageChange(filters.page - 1)}
              className="ghost-button"
              style={{ padding: "0.2rem 0.5rem" }}
            >
              &lt;
            </button>
            {[...Array(totalPages)].map((_, idx) => {
              const p = idx + 1;
              return (
                <button
                  key={p}
                  onClick={() => handlePageChange(p)}
                  className={p === filters.page ? "primary-button" : "ghost-button"}
                  style={{ padding: "0.2rem 0.5rem", minWidth: "30px" }}
                >
                  {p}
                </button>
              );
            })}
            <button
              disabled={filters.page >= totalPages}
              onClick={() => handlePageChange(filters.page + 1)}
              className="ghost-button"
              style={{ padding: "0.2rem 0.5rem" }}
            >
              &gt;
            </button>
          </div>
        )}
      </section>

      {/* Report Incident form */}
      <section className="card form-card">
        <div className="card-header">
          <h3>Report Incident</h3>
        </div>
        <form onSubmit={submitIncident}>
          {formError && (
            <div className="form-error" role="alert">
              {formError}
            </div>
          )}
          {formSuccess && (
            <div className="form-success" role="alert">
              {formSuccess}
            </div>
          )}
          <label>
            Affected Service
            <select
              required
              value={form.service_id}
              onChange={(e) => setForm({ ...form, service_id: e.target.value })}
            >
              <option value="" disabled>Select a service...</option>
              {services.map((svc) => (
                <option key={svc.id} value={svc.id}>
                  {svc.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Severity Level
            <select
              value={form.severity}
              onChange={(e) => setForm({ ...form, severity: e.target.value })}
            >
              <option value="low">Low - Minimal impact</option>
              <option value="medium">Medium - Partial degradation</option>
              <option value="high">High - Significant disruption</option>
              <option value="critical">Critical - Complete outage</option>
            </select>
          </label>
          <label>
            Title
            <input
              required
              placeholder="e.g. Database connection timeouts"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </label>
          <label>
            Detailed Description
            <textarea
              required
              rows={4}
              placeholder="Describe symptoms, logs, or metrics observed..."
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </label>
          <button type="submit" className="primary-button" disabled={isSubmitting}>
            {isSubmitting ? "Submitting..." : "Submit Incident Report"}
          </button>
        </form>
      </section>
    </div>
  );
}
