import { useState } from "react";
import { createService } from "../api/client";

function formatTime(value) {
  if (!value) return "Not checked";
  return new Intl.DateTimeFormat("en", {
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

function ServicesList({ services, loading, onRegistered, onError, isAdmin }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form, setForm] = useState({
    name: "",
    description: "",
    status: "healthy",
  });

  async function submitService(event) {
    event.preventDefault();
    setIsSubmitting(true);
    onError("");
    try {
      await createService(form);
      setForm({ name: "", description: "", status: "healthy" });
      setIsOpen(false);
      await onRegistered();
    } catch (error) {
      onError(error.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="panel services-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Service registry</p>
          <h3>Services</h3>
        </div>
        <div className="panel-actions">
          <span className="count-label">{services.length} total</span>
          {isAdmin && (
            <button
              className="secondary-button"
              type="button"
              onClick={() => setIsOpen(true)}
            >
              + Register Service
            </button>
          )}
        </div>
      </div>
      <div className="service-list">
        {loading && <p className="muted">Loading service registry...</p>}
        {!loading &&
          services.map((service) => (
            <article className="service-row" key={service.name}>
              <div className="service-icon">
                {service.name.slice(0, 2).toUpperCase()}
              </div>
              <div className="service-copy">
                <strong>{service.name}</strong>
                <span>{service.description || "No description provided"}</span>
              </div>
              <div className={`pill ${service.status}`}>
                <span className="status-dot" />
                {service.status}
              </div>
              <time>{formatTime(service.last_checked_at)}</time>
            </article>
          ))}
        {!loading && services.length === 0 && (
          <p className="muted">No services registered yet.</p>
        )}
      </div>
      {isOpen && (
        <div
          className="modal-backdrop"
          role="presentation"
          onMouseDown={(event) =>
            event.target === event.currentTarget && setIsOpen(false)
          }
        >
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="register-service-title"
          >
            <div className="modal-header">
              <div>
                <p className="eyebrow">Service registry</p>
                <h3 id="register-service-title">Register service</h3>
              </div>
              <button
                className="close-button"
                type="button"
                aria-label="Close modal"
                onClick={() => setIsOpen(false)}
              >
                ×
              </button>
            </div>
            <form onSubmit={submitService}>
              <label>
                Name
                <input
                  required
                  maxLength="100"
                  value={form.name}
                  placeholder="payment-service"
                  onChange={(event) =>
                    setForm({ ...form, name: event.target.value })
                  }
                />
              </label>
              <label>
                Description
                <textarea
                  maxLength="1000"
                  rows="3"
                  value={form.description}
                  placeholder="What does this service do?"
                  onChange={(event) =>
                    setForm({ ...form, description: event.target.value })
                  }
                />
              </label>
              <label>
                Initial status
                <select
                  value={form.status}
                  onChange={(event) =>
                    setForm({ ...form, status: event.target.value })
                  }
                >
                  <option value="healthy">Healthy</option>
                  <option value="degraded">Degraded</option>
                  <option value="down">Down</option>
                </select>
              </label>
              <div className="modal-actions">
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() => setIsOpen(false)}
                >
                  Cancel
                </button>
                <button
                  className="primary-button"
                  disabled={isSubmitting}
                  type="submit"
                >
                  {isSubmitting ? "Registering..." : "Register service"}{" "}
                  <span aria-hidden="true">→</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}

export default ServicesList;
