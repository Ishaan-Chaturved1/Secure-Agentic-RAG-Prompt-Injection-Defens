const API_BASE = import.meta.env.VITE_API_URL || (
  window.location.hostname === 'localhost' ? 'http://localhost:8000' : ''
);

const TOKEN_KEY = 'secure_rag_token';
const USER_KEY = 'secure_rag_user';

export function getStoredToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {}
}

export function getStoredUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setStoredUser(user) {
  try {
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
    else localStorage.removeItem(USER_KEY);
  } catch {}
}

export function clearStoredAuth() {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  } catch {}
}

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = { ...options.headers };

  // Set Content-Type only if not FormData
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  // Attach Authorization token if available
  const token = getStoredToken();
  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || JSON.stringify(errJson);
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail || `HTTP error ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Check health
  async checkHealth() {
    return request('/health');
  },

  // --- Auth endpoints ---
  async register({ username, email, password }) {
    const res = await request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    });
    if (res.token) {
      setStoredToken(res.token);
      setStoredUser(res.user);
    }
    return res;
  },

  async login({ username_or_email, password }) {
    const res = await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username_or_email, password }),
    });
    if (res.token) {
      setStoredToken(res.token);
      setStoredUser(res.user);
    }
    return res;
  },

  async getMe() {
    return request('/auth/me');
  },

  async logout() {
    try {
      await request('/auth/logout', { method: 'POST' });
    } finally {
      clearStoredAuth();
    }
  },

  // --- Workspaces endpoints ---
  async getWorkspaces() {
    return request('/workspaces');
  },

  async createWorkspace(name) {
    return request('/workspaces', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  },

  // --- Documents endpoints ---
  async getDocuments(workspace_id = null) {
    const query = workspace_id ? `?workspace_id=${encodeURIComponent(workspace_id)}` : '';
    return request(`/documents${query}`);
  },

  async uploadDocument(file, workspace_id = null) {
    const formData = new FormData();
    formData.append('file', file);
    if (workspace_id) {
      formData.append('workspace_id', workspace_id);
    }
    return request('/documents/upload', {
      method: 'POST',
      body: formData,
    });
  },

  async deleteDocument(document_id) {
    return request(`/documents/${document_id}`, {
      method: 'DELETE',
    });
  },

  // --- Tenant-Scoped User Query ---
  async queryUserRAG({ query, workspace_id = null, mode = 'hardened' }) {
    return request('/user/query', {
      method: 'POST',
      body: JSON.stringify({ query, workspace_id, mode }),
    });
  },

  // Query agent (baseline or hardened, for demo playground)
  async queryAgent({ query, mode = 'hardened', injected_documents = null, attack_id = null, workspace_id = null }) {
    return request('/query', {
      method: 'POST',
      body: JSON.stringify({ query, mode, injected_documents, attack_id, workspace_id }),
    });
  },

  // Get list of all 50 attacks
  async getAttacks() {
    return request('/red-team/attacks');
  },

  // Execute a single red-team attack case with poisoned document payload
  async executeAttack(attack_id, mode = 'hardened') {
    return request(`/red-team/attack/${attack_id}?mode=${mode}`, {
      method: 'POST',
    });
  },

  // Run a single attack side-by-side (Baseline vs Hardened)
  async runSingleAttack(attack_id) {
    return request('/red-team/run-single', {
      method: 'POST',
      body: JSON.stringify({ attack_id }),
    });
  },

  // Run full red-team suite
  async runRedTeamSuite(modes = ['baseline', 'hardened']) {
    return request('/red-team/run', {
      method: 'POST',
      body: JSON.stringify({ modes }),
    });
  },

  // Get latest benchmark results
  async getResults() {
    return request('/red-team/results');
  },

  // Get 6 security layers documentation
  async getSecurityLayers() {
    return request('/security/layers');
  },

  // Get real-time audit event logs
  async getAuditEvents(limit = 50) {
    return request(`/audit/events?limit=${limit}`);
  },
};
