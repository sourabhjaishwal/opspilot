// Metric strip component rendering key platform telemetry counters
export default function MetricStrip({
  servicesCount,
  openIncidentsCount,
  totalIncidentsCount,
}) {
  return (
    <section className="metric-strip">
      <article className="metric-card">
        <span className="metric-label">Services online</span>
        <strong className="metric-value">{servicesCount}</strong>
        <span className="metric-hint">Active microservices registered</span>
      </article>
      <article className="metric-card">
        <span className="metric-label">Total incidents</span>
        <strong className="metric-value">{totalIncidentsCount}</strong>
        <span className="metric-hint">total tracked across systems</span>
      </article>
      <article className="metric-card">
        <span className="metric-label">System status</span>
        <strong className="metric-value">
          {openIncidentsCount === 0 ? "Normal" : "Degraded"}
        </strong>
        <span className="metric-hint">Based on currently open incidents</span>
      </article>
    </section>
  );
}
