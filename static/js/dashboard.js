// ── Dashboard Logic ─────────────────────────────────────────────────────────

const Dashboard = (() => {
  let profile = null;
  let companies = [];

  // ── Init ─────────────────────────────────────────────────────────────────

  async function init() {
    if (!API.requireAuth()) return;

    try {
      profile = await API.getProfile();
      renderSidebar(profile);
      populateModals(profile.user.companies);
    } catch (err) {
      Toast.error('Failed to load profile: ' + err.message);
    }

    // Chat input: send on Enter
    const input = document.getElementById('chat-input');
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  // ── Render Sidebar ───────────────────────────────────────────────────────

  function renderSidebar(data) {
    const user = data.user;
    companies = user.companies || [];

    // Avatar
    const avatar = document.getElementById('user-avatar');
    avatar.textContent = (user.name || '?')[0].toUpperCase();

    // Name & role
    document.getElementById('user-name').textContent = user.name;
    document.getElementById('user-role').textContent = user.role || 'Job Seeker';

    // Companies — render as chips
    const companyList = document.getElementById('company-list');
    if (companies.length === 0) {
      companyList.innerHTML = '<span class="text-muted" style="font-size:0.85rem;">No companies added</span>';
    } else {
      companyList.innerHTML = companies.map(c => `
        <div class="company-chip">
          <span>${escapeHtml(c)}</span>
          <span class="chip-x" onclick="Dashboard.removeCompany('${escapeHtml(c)}')" title="Remove">✕</span>
        </div>
      `).join('');
    }

    // Weak areas
    const weakList = document.getElementById('weak-areas-list');
    const areas = user.weak_areas || [];
    weakList.innerHTML = areas.length
      ? areas.map(a => `<span class="tag">${escapeHtml(a)}</span>`).join('')
      : '<span class="text-muted" style="font-size:0.85rem;">None specified</span>';

    // Recent interviews
    const recentEl = document.getElementById('recent-interviews');
    const history = data.mock_interview_history || [];
    if (history.length === 0) {
      recentEl.innerHTML = '<span class="text-muted">No interviews yet</span>';
    } else {
      recentEl.innerHTML = history.slice(0, 3).map(h => {
        const scoreColor = h.overall_score >= 7
          ? 'var(--accent)'
          : h.overall_score >= 5
            ? 'var(--orange)'
            : 'var(--red)';
        return `
          <div class="score-mini">
            <div>
              <span class="score-mini-company">${escapeHtml(h.company)}</span>
              <div class="score-mini-date" style="font-size: 0.7rem; color: var(--text-muted);">${new Date(h.created_at).toLocaleDateString()}</div>
            </div>
            <span class="score-mini-value" style="color: ${scoreColor}; font-weight: 600;">
              ${h.overall_score.toFixed(1)}/10
            </span>
          </div>
        `;
      }).join('');
    }
  }

  // ── Populate Modals ──────────────────────────────────────────────────────

  function populateModals(companyList) {
    const selects = ['compare-c1', 'compare-c2'];
    selects.forEach(id => {
      const sel = document.getElementById(id);
      if (!sel) return;
      sel.innerHTML = companyList.map(c =>
        `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`
      ).join('');
    });
  }

  // ── Quick Ask ────────────────────────────────────────────────────────────

  function quickAsk(text) {
    const input = document.getElementById('chat-input');
    input.value = text;
    sendMessage();
  }

  // ── Chat ──────────────────────────────────────────────────────────────────

  async function sendMessage() {
    const input = document.getElementById('chat-input');
    const question = input.value.trim();
    if (!question) return;

    addMessage(question, 'user');
    input.value = '';

    // Show loading
    const loadingId = addLoading();

    try {
      const res = await API.ask(question);
      removeLoading(loadingId);
      addMessage(res.answer, 'ai');
    } catch (err) {
      removeLoading(loadingId);
      addMessage('Error: ' + err.message, 'ai');
    }
  }

  function addMessage(text, type) {
    const container = document.getElementById('chat-messages');
    const el = document.createElement('div');
    el.className = `message message-${type}`;
    // Convert newlines and basic markdown
    el.innerHTML = formatMessage(text);
    container.appendChild(el);
    container.scrollTop = container.scrollHeight;
    return el;
  }

  function addLoading() {
    const container = document.getElementById('chat-messages');
    const el = document.createElement('div');
    const id = 'loading-' + Date.now();
    el.id = id;
    el.className = 'message message-ai message-loading';
    el.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
    container.appendChild(el);
    container.scrollTop = container.scrollHeight;
    return id;
  }

  function removeLoading(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function formatMessage(text) {
    if (!text) return '';
    // Escape HTML first
    let html = escapeHtml(text);
    // Bold: **text**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Code blocks: ```code```
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    // Inline code: `code`
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Newlines
    html = html.replace(/\n/g, '<br>');
    return html;
  }

  // ── Compare ──────────────────────────────────────────────────────────────

  function showCompareModal() {
    document.getElementById('compare-modal').classList.add('active');
  }

  async function doCompare() {
    const c1 = document.getElementById('compare-c1').value;
    const c2 = document.getElementById('compare-c2').value;
    if (c1 === c2) {
      Toast.error('Please select two different companies');
      return;
    }
    closeModals();
    addMessage(`Compare ${c1} vs ${c2}`, 'user');
    const loadingId = addLoading();

    try {
      const res = await API.compare(c1, c2);
      removeLoading(loadingId);
      const msg = `**${c1} vs ${c2}**\n\n**${c1} Requirements:**\n${res.company1_requirements}\n\n**${c2} Requirements:**\n${res.company2_requirements}\n\n**Comparison:**\n${res.comparison}`;
      addMessage(msg, 'ai');
    } catch (err) {
      removeLoading(loadingId);
      addMessage('Error: ' + err.message, 'ai');
    }
  }


  // ── Remove Company ───────────────────────────────────────────────────────

  async function removeCompany(name) {
    if (!confirm(`Remove ${name} from your targets? This will also forget its data from Cognee.`)) return;

    try {
      await API.deleteCompany(name);
      Toast.success(`${name} removed`);
      // Refresh profile
      profile = await API.getProfile();
      renderSidebar(profile);
      populateModals(profile.user.companies);
    } catch (err) {
      Toast.error(err.message);
    }
  }

  // ── Modals ───────────────────────────────────────────────────────────────

  function closeModals() {
    document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
  }

  // Close modal on overlay click
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
      closeModals();
    }
  });

  // ── Utils ────────────────────────────────────────────────────────────────

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // ── Init on load ─────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', init);

  return {
    sendMessage, quickAsk, showCompareModal, doCompare,
    removeCompany, closeModals,
  };
})();
