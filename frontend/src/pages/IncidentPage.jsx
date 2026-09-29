import { useState } from "react";
import { analyzeIncident, updateIncident } from "../api/client";

export default function IncidentPage({ incident, onBack, onUpdate }) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisError, setAnalysisError] = useState("");

  const [status, setStatus] = useState(incident.status);
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState("");
  const [updateSuccess, setUpdateSuccess] = useState("");

  // isResolved reflects the current select value (not just the DB state)
  const isResolved = status === "resolved";

  async function handleAnalyze() {
    if (isResolved) return;
    setIsAnalyzing(true);
    setAnalysisResult(null);
    setAnalysisError("");
    try {
      const result = await analyzeIncident(incident.id);
      setAnalysisResult(result);
    } catch (error) {
      setAnalysisError(error.message || "Failed to analyze incident with AI.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleUpdateStatus(e) {
    e.preventDefault();
    setUpdateError("");
    setUpdateSuccess("");
    setIsUpdating(true);
    try {
      await updateIncident(incident.id, { status });
      setUpdateSuccess("Incident updated successfully.");
      if (onUpdate) onUpdate();
    } catch (err) {
      setUpdateError(err.message || "Failed to update incident.");
    } finally {
      setIsUpdating(false);
    }
  }

  return (
    <div className="dashboard-layout">
      {/* Page header: back link left-aligned, title block below */}
      <div className="incident-page-header">
        <button className="back-link" onClick={onBack}>
          &larr; Back to Dashboard
        </button>
        <div className="incident-page-title">
          <h2>
            {incident.incident_number
              ? `${incident.incident_number} — ${incident.title}`
              : incident.title}
          </h2>
          <p>
            {incident.service} &middot; Opened{" "}
            {new Date(incident.created_at).toLocaleString(undefined, {
              month: "short",
              day: "numeric",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        </div>
      </div>

      <div className="content-grid" style={{ gridTemplateColumns: "1fr", gap: "2rem" }}>
        {/* Incident Info */}
        <section className="card">
          <div className="card-header">
            <h3>Incident Information</h3>
            <span className={"severity-pill " + incident.severity}>{incident.severity}</span>
          </div>
          <div style={{ marginTop: "1rem", lineHeight: "1.6" }}>
            <p><strong>Incident Number:</strong> {incident.incident_number || "—"}</p>
            <p><strong>Service:</strong> {incident.service}</p>
            <p><strong>Description:</strong> {incident.description}</p>
            <p><strong>Current Status:</strong> {incident.status}</p>
            <p><strong>Created At:</strong> {new Date(incident.created_at).toLocaleString()}</p>
          </div>
        </section>

        {/* Update Incident */}
        <section className="card">
          <div className="card-header">
            <h3>Update Incident Status</h3>
          </div>
          <form style={{ marginTop: "1rem" }} onSubmit={handleUpdateStatus}>
            {updateError && <div className="form-error">{updateError}</div>}
            {updateSuccess && <div className="form-success">{updateSuccess}</div>}
            <label style={{ display: "block", marginBottom: "0.5rem" }}>
              Status
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                style={{ width: "100%", marginTop: "0.5rem", padding: "0.5rem" }}
              >
                <option value="open">Open</option>
                <option value="investigating">Investigating</option>
                <option value="resolved">Resolved</option>
              </select>
            </label>
            <button
              type="submit"
              className="primary-button"
              disabled={isUpdating}
              style={{ marginTop: "1rem" }}
            >
              {isUpdating ? "Updating..." : "Update Incident"}
            </button>
          </form>
        </section>

        {/* AI Analysis */}
        <section className="card">
          <div
            className="card-header"
            style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
          >
            <h3>AI Root Cause Analysis</h3>

            {isResolved ? (
              <div className="incident-resolved-badge">
                Resolved — AI analysis disabled
              </div>
            ) : (
              <button
                className="ai-analyze-btn"
                onClick={handleAnalyze}
                disabled={isAnalyzing}
              >
                {isAnalyzing ? "Analyzing…" : "✨ Analyze with AI"}
              </button>
            )}
          </div>

          <div style={{ marginTop: "1rem" }}>
            {isResolved && !analysisResult && !analysisError && (
              <p className="incident-resolved-notice">
                This incident is marked as <strong>Resolved</strong>. AI analysis is only
                available for open or investigating incidents.
              </p>
            )}

            {isAnalyzing && (
              <div className="ai-loading-state" style={{ padding: "1rem" }}>
                <div className="ai-spinner"></div>
                <h4 style={{ marginTop: "1rem" }}>Analyzing incident with Google Gemini…</h4>
              </div>
            )}

            {analysisError && !isAnalyzing && (
              <div className="ai-error-state form-error">{analysisError}</div>
            )}

            {analysisResult && !isAnalyzing && (
              <div className="ai-analysis-details">
                <div className="ai-section summary-section">
                  <h4>Incident Summary</h4>
                  <p>{analysisResult.summary}</p>
                </div>

                <div className="ai-section">
                  <h4>Possible Root Cause</h4>
                  <p>{analysisResult.possible_root_cause}</p>
                </div>

                <div className="ai-section">
                  <h4>Recommended Checks</h4>
                  <ul className="ai-checks-list">
                    {analysisResult.recommended_checks?.map((check, idx) => (
                      <li key={idx}>{check}</li>
                    ))}
                  </ul>
                </div>

                <div className="ai-section">
                  <h4>Suggested Resolution</h4>
                  <p>{analysisResult.suggested_resolution}</p>
                </div>

                <div className="ai-disclaimer" style={{ marginTop: "1rem" }}>
                  <span>
                    <em>
                      AI-generated recommendation for advisory purposes. Verify findings
                      prior to making production infrastructure changes.
                    </em>
                  </span>
                </div>
              </div>
            )}

            {!isAnalyzing && !analysisError && !analysisResult && !isResolved && (
              <p style={{ color: "#64748b" }}>
                Click &ldquo;Analyze with AI&rdquo; to generate an advisory root-cause investigation.
              </p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
