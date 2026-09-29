import { useState } from "react";
import { createService, updateService } from "../api/client";

const emptyServiceForm = {
  name: "",
  description: "",
  status: "healthy",
};

export default function ServicesList({ services, isAdmin, onRegistered, onError }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isEdit, setIsEdit] = useState(false);
  const [form, setForm] = useState(emptyServiceForm);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [modalError, setModalError] = useState("");
  const [originalName, setOriginalName] = useState("");

  function openModal(service = null) {
    if (service) {
      setForm({
        name: service.name,
        description: service.description || "",
        status: service.status,
      });
      setOriginalName(service.name);
      setIsEdit(true);
    } else {
      setForm(emptyServiceForm);
      setOriginalName("");
      setIsEdit(false);
    }
    setModalError("");
    setIsOpen(true);
  }

  function closeModal() {
    setModalError("");
    setIsOpen(false);
  }

  async function submitService(event) {
    event.preventDefault();
    setIsSubmitting(true);
    setModalError("");
    try {
      if (isEdit) {
        await updateService(originalName, form);
      } else {
        await createService(form);
      }
      setForm(emptyServiceForm);
      setIsOpen(false);
      await onRegistered();
    } catch (error) {
      const msg =
        error.message || `Failed to ${isEdit ? "update" : "register"} service.`;
      setModalError(msg);
      if (onError) onError(msg);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="card services-card">
      <div className="card-header">
        <div>
          <h2>Registered Services</h2>
          <p>Microservices monitored by OpsPilot</p>
        </div>
        {isAdmin && (
          <button
            type="button"
            className="primary-button"
            onClick={() => openModal()}
          >
            Register Service
          </button>
        )}
      </div>

      <div className="services-grid">
        {services.length === 0 ? (
          <p className="empty-state">No services registered yet.</p>
        ) : (
          services.map((service) => (
            <article key={service.id || service.name} className="service-card">
              <div className="service-headline">
                <div
                  style={{
                    display: "flex",
                    gap: "0.5rem",
                    alignItems: "center",
                    flexWrap: "wrap",
                    minWidth: 0,
                  }}
                >
                  <h3>{service.name}</h3>
                  <span className={`status-pill ${service.status}`}>
                    {service.status}
                  </span>
                </div>
                {isAdmin && (
                  <button
                    type="button"
                    className="ghost-button"
                    onClick={() => openModal(service)}
                    title={`Edit ${service.name}`}
                    style={{
                      padding: "0.25rem 0.65rem",
                      fontSize: "0.75rem",
                      flexShrink: 0,
                    }}
                  >
                    Edit
                  </button>
                )}
              </div>
              <p className="service-description">
                {service.description || "No description provided."}
              </p>
            </article>
          ))
        )}
      </div>


      {isOpen && (
        <div
          className="modal-backdrop"
          onClick={closeModal}
          role="presentation"
        >
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-title"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h3 id="modal-title">
                {isEdit ? "Update Microservice" : "Register Microservice"}
              </h3>
              <button
                type="button"
                className="close-button"
                onClick={closeModal}
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            <form onSubmit={submitService}>
              {modalError && (
                <div className="form-error" role="alert">
                  {modalError}
                </div>
              )}

              <label>
                Service Name
                <input
                  required
                  placeholder="e.g. payment-service"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </label>

              <label>
                Description
                <textarea
                  placeholder="Brief description of service domain and dependencies"
                  value={form.description}
                  rows={3}
                  onChange={(e) =>
                    setForm({ ...form, description: e.target.value })
                  }
                />
              </label>

              <label>
                Health Status
                <select
                  value={form.status}
                  onChange={(e) =>
                    setForm({ ...form, status: e.target.value })
                  }
                >
                  <option value="healthy">healthy</option>
                  <option value="degraded">degraded</option>
                  <option value="down">down</option>
                </select>
              </label>

              <div className="modal-actions">
                <button
                  type="button"
                  className="ghost-button"
                  onClick={closeModal}
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="primary-button"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Saving..." : "Save Service"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}

