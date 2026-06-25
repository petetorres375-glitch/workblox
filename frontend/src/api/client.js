const BASE_URL = import.meta.env.VITE_API_URL || "";

async function handleResponse(res) {
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return res.json();
}

export function post(path, body) {
  return fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then(handleResponse);
}

export function postForm(path, formData) {
  return fetch(`${BASE_URL}${path}`, {
    method: "POST",
    body: formData,
  }).then(handleResponse);
}
