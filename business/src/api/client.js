export const BASE_URL = import.meta.env.VITE_API_URL || "";

export function get(path) {
  const token = localStorage.getItem("wbb_token");
  return fetch(`${BASE_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  }).then((res) => handleResponse(res, path));
}

function authHeaders() {
  const token = localStorage.getItem("wbb_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleResponse(res, path) {
  if (res.status === 401 && !path.startsWith("/api/auth/")) {
    localStorage.removeItem("wbb_token");
    localStorage.removeItem("wbb_name");
    localStorage.removeItem("wbb_email");
    localStorage.removeItem("wbb_plan");
    window.location.reload();
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return res.json();
}

function networkGuard(err) {
  if (err instanceof TypeError && err.message === "Failed to fetch") {
    throw new Error("Unable to reach the server. Check your connection and try again.");
  }
  throw err;
}

export function post(path, body) {
  return fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  }).then((res) => handleResponse(res, path)).catch(networkGuard);
}

export async function postBlob(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return res.blob();
}

export function postForm(path, formData) {
  return fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  }).then((res) => handleResponse(res, path)).catch(networkGuard);
}
