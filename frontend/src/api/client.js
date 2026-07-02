/**
 * API client — thin wrapper around fetch.
 * All requests go to the FastAPI backend.
 */

const BASE = import.meta.env.VITE_API_URL || '';

async function request(method, path, body, isFormData = false) {
  const opts = { method, headers: {} };
  if (body) {
    if (isFormData) {
      opts.body = body; // FormData — let browser set Content-Type
    } else {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
  }
  const res = await fetch(`${BASE}${path}`, opts);
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) {
    const msg = data?.detail || `HTTP ${res.status}`;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return data;
}

export const api = {
  // Goblins
  listGoblins: () => request('GET', '/goblins'),
  getGoblin: (id) => request('GET', `/goblins/${id}`),

  // Health
  health: () => request('GET', '/health'),

  // Cases
  createCase: (type, goblinId) =>
    request('POST', '/cases', { type, assignedGoblinId: goblinId ?? undefined }),
  listCases: () => request('GET', '/cases'),
  getCase: (id) => request('GET', `/cases/${id}`),
  deleteCase: (id) => request('DELETE', `/cases/${id}`),

  uploadEvidence: (caseId, files) => {
    const fd = new FormData();
    for (const f of files) fd.append('files', f);
    return request('POST', `/cases/${caseId}/evidence`, fd, true);
  },

  extract: (caseId) => request('POST', `/cases/${caseId}/extract`),

  saveReview: (caseId, data) => request('PUT', `/cases/${caseId}/review`, data),

  generate: (caseId) => request('POST', `/cases/${caseId}/generate`),

  archive: (caseId) => request('POST', `/cases/${caseId}/archive`),

  downloadUrl: (caseId, filename) =>
    `${BASE}/cases/${caseId}/download/${filename}`,

  // Ledgergut standalone endpoints
  ledgergutExtract: (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return request('POST', '/ledgergut/extract', fd, true);
  },

  ledgergutGenerate: (data) =>
    request('POST', '/ledgergut/generate-reimbursement', data),

  ledgergutDownloadUrl: (filename) =>
    `${BASE}/ledgergut/download/${filename}`,
};
