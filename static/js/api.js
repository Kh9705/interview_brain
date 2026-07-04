// ── Interview Brain API Client ──────────────────────────────────────────────

const API = (() => {
  const TOKEN_KEY = 'ib_token';
  const USER_KEY  = 'ib_user';

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
  }

  function removeToken() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  function getUser() {
    try { return JSON.parse(localStorage.getItem(USER_KEY)); }
    catch { return null; }
  }

  function setUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  function isLoggedIn() {
    return !!getToken();
  }

  function requireAuth() {
    if (!isLoggedIn()) {
      window.location.href = '/static/login.html';
      return false;
    }
    return true;
  }

  function logout() {
    removeToken();
    window.location.href = '/static/login.html';
  }

  /**
   * Core fetch wrapper with JWT auth and error handling.
   * @param {string} endpoint  – e.g. '/api/login'
   * @param {string} method    – GET | POST | PUT | DELETE
   * @param {object|null} body – JSON body (auto-stringified)
   * @returns {Promise<object>}
   */
  async function call(endpoint, method = 'GET', body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const token = getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const opts = { method, headers };
    if (body && method !== 'GET') {
      opts.body = JSON.stringify(body);
    }

    const res = await fetch(endpoint, opts);

    // Handle auth failures
    if (res.status === 401) {
      removeToken();
      window.location.href = '/static/login.html';
      throw new Error('Session expired. Please log in again.');
    }

    // Parse JSON response
    let data;
    const contentType = res.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      data = await res.json();
    } else {
      data = await res.text();
    }

    if (!res.ok) {
      const msg = (typeof data === 'object' && data.detail) ? data.detail : `Request failed (${res.status})`;
      throw new Error(msg);
    }

    return data;
  }

  // ── Convenience methods ─────────────────────────────────────────────────

  async function register(payload) {
    const data = await call('/api/register', 'POST', payload);
    setToken(data.access_token);
    setUser({ id: data.user_id, name: data.name, email: data.email });
    return data;
  }

  async function login(email, password) {
    const data = await call('/api/login', 'POST', { email, password });
    setToken(data.access_token);
    setUser({ id: data.user_id, name: data.name, email: data.email });
    return data;
  }

  async function ingest(payload) {
    return call('/api/ingest', 'POST', payload);
  }

  async function ask(question) {
    return call('/api/ask', 'POST', { question });
  }

  async function getProfile() {
    return call('/api/profile');
  }

  async function getFeedback() {
    return call('/api/feedback');
  }

  async function createFeedback(payload) {
    return call('/api/feedback', 'POST', payload);
  }

  async function startMockInterview(company, numQuestions) {
    return call('/api/mock-interview/start', 'POST', { company, num_questions: numQuestions });
  }

  async function evaluateAnswer(interviewId, questionNumber, question, answer) {
    return call('/api/mock-interview/evaluate', 'POST', {
      interview_id: interviewId,
      question_number: questionNumber,
      question,
      answer,
    });
  }

  async function getMockHistory() {
    return call('/api/mock-interview/history');
  }

  async function compare(company1, company2) {
    return call('/api/compare', 'POST', { company1, company2 });
  }

  async function generateRoadmap(company, days) {
    return call('/api/roadmap', 'POST', { company, days });
  }

  async function getRoadmaps() {
    return call('/api/roadmap');
  }

  async function updateRoadmap(id, content) {
    return call(`/api/roadmap/${id}`, 'PUT', { content });
  }

  async function getGraph() {
    return call('/api/visualize');
  }

  async function deleteCompany(name) {
    return call(`/api/company/${encodeURIComponent(name)}`, 'DELETE');
  }

  return {
    getToken, setToken, removeToken,
    getUser, setUser, isLoggedIn, requireAuth, logout,
    call,
    register, login, ingest, ask,
    getProfile, getFeedback, createFeedback,
    startMockInterview, evaluateAnswer, getMockHistory,
    compare, generateRoadmap, getRoadmaps, updateRoadmap, getGraph, deleteCompany,
  };
})();

// ── Toast notifications ─────────────────────────────────────────────────────

const Toast = (() => {
  function _ensureContainer() {
    let c = document.getElementById('toast-container');
    if (!c) {
      c = document.createElement('div');
      c.id = 'toast-container';
      c.className = 'toast-container';
      document.body.appendChild(c);
    }
    return c;
  }

  function show(message, type = 'info', duration = 4000) {
    const container = _ensureContainer();
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.textContent = message;
    container.appendChild(el);
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(-10px)';
      setTimeout(() => el.remove(), 300);
    }, duration);
  }

  return {
    success: (msg) => show(msg, 'success'),
    error:   (msg) => show(msg, 'error'),
    info:    (msg) => show(msg, 'info'),
  };
})();
