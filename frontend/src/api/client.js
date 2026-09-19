const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  if (response.status === 204) return null;
  return response.json();
}

export function register(credentials) {
  return request("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  });
}

export function login(credentials) {
  return request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  });
}

export function logout() {
  return request("/auth/logout", { method: "POST" });
}

export function getHealth() {
  return request("/health");
}

export function getServices() {
  return request("/services");
}

export function createService(service) {
  return request("/services", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(service),
  });
}

export function getIncidents(filters = {}) {
  const params = new URLSearchParams({ page: "1", page_size: "5" });
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  return request(`/incidents?${params}`);
}

export function createIncident(incident) {
  return request("/incidents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(incident),
  });
}
