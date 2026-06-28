export const BASE_URL = import.meta.env.VITE_API_URL || "";

function authHeaders() {
  const token = localStorage.getItem("wb_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleResponse(res, path) {
  if (res.status === 401 && !path.startsWith("/api/auth/")) {
    localStorage.removeItem("wb_token");
    localStorage.removeItem("wb_name");
    window.location.reload();
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return res.json();
}

export function post(path, body) {
  return fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  }).then((res) => handleResponse(res, path));
}

export function postForm(path, formData) {
  return fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  }).then((res) => handleResponse(res, path));
}
