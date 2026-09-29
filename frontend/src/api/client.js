// HTTP client providing typed API requests to the OpsPilot FastAPI backend
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Centralized request dispatcher handling auth token injection and error unwrapping
async function request(path, options) {
  const token = localStorage.getItem("opspilot_token");
  const headers = new Headers(options?.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    let errorMessage = `Request failed (${response.status})`;
    if (typeof body.detail === "string") {
      errorMessage = body.detail;
    } else if (Array.isArray(body.detail) && body.detail.length > 0) {
      errorMessage = body.detail.map((err) => err.msg || JSON.stringify(err)).join(", ");
    } else if (body.detail && typeof body.detail === "object") {
      errorMessage = body.detail.message || body.detail.msg || JSON.stringify(body.detail);
    } else if (body.message) {
      errorMessage = body.message;
    }
    throw new Error(errorMessage);
  }
  if (response.status === 204) return null;
  return response.json();
}

// Register a new user account
export function register(credentials) {
  return request("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  });
}

// Authenticate user and receive JWT bearer token
export function login(credentials) {
  return request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  });
}

// Retrieve backend health status
export function getHealth() {
  return request("/health");
}

// Retrieve all monitored microservices
export function getServices() {
  return request("/services");
}

// Register a new microservice in the catalog (Admin only)
export function createService(service) {
  return request("/services", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(service),
  });
}

export function updateService(serviceName, data) {
  return request(`/services/${encodeURIComponent(serviceName)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function updateServiceStatus(serviceName, status) {
  return request(`/services/${encodeURIComponent(serviceName)}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
}

// Query paginated incident records with optional status/severity filtering
export function getIncidents(filters = {}) {
  const pageSize = filters.page_size || "5";
  const params = new URLSearchParams({ page: filters.page || "1", page_size: String(pageSize) });
  Object.entries(filters).forEach(([key, value]) => {
    if (value && key !== "page" && key !== "page_size") params.set(key, value);
  });
  return request(`/incidents?${params}`);
}

// File a new incident report against a service
export function createIncident(incident) {
  return request("/incidents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(incident),
  });
}

export function updateIncident(incidentId, data) {
  return request(`/incidents/${incidentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

// Request AI root cause analysis for an incident
export function analyzeIncident(incidentId) {
  return request(`/incidents/${incidentId}/analyze`, {
    method: "POST",
  });
}