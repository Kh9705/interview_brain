// ── Roadmap Page Logic ──────────────────────────────────────────────────────

const RoadmapApp = (() => {
  let profile = null;
  let roadmaps = [];
  let currentRoadmap = null;

  async function init() {
    if (!API.requireAuth()) return;

    try {
      profile = await API.getProfile();
      populateCompanyDropdown(profile.user.companies);
      await loadRoadmaps();
    } catch (err) {
      Toast.error('Failed to load profile or roadmaps: ' + err.message);
    }
    
    setupEventListeners();
  }

  function populateCompanyDropdown(companies) {
    const sel = document.getElementById('new-company');
    if (!companies || companies.length === 0) {
      sel.innerHTML = '<option value="">No targets set</option>';
      return;
    }
    sel.innerHTML = companies.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join('');
  }

  async function loadRoadmaps() {
    try {
      const res = await API.getRoadmaps();
      roadmaps = res.roadmaps || [];
      renderSidebarList();
    } catch (err) {
      Toast.error('Failed to load roadmaps: ' + err.message);
    }
  }

  function renderSidebarList() {
    const listEl = document.getElementById('roadmap-list');
    if (roadmaps.length === 0) {
      listEl.innerHTML = '<div style="padding: 8px; font-size: 0.85rem; color: var(--text-muted);">No roadmaps yet. Generate one!</div>';
      return;
    }
    
    listEl.innerHTML = roadmaps.map(rm => `
      <div class="roadmap-item ${currentRoadmap && currentRoadmap.id === rm.id ? 'active' : ''}" data-id="${rm.id}">
        <div class="roadmap-item-title">${escapeHtml(rm.company)}</div>
        <div class="roadmap-item-date">${new Date(rm.created_at).toLocaleDateString()}</div>
      </div>
    `).join('');
    
    // Add click listeners
    document.querySelectorAll('.roadmap-item').forEach(el => {
      el.addEventListener('click', () => {
        const id = el.getAttribute('data-id');
        selectRoadmap(id);
      });
    });
  }

  function selectRoadmap(id) {
    currentRoadmap = roadmaps.find(r => r.id === id);
    renderSidebarList(); // Update active state
    
    document.getElementById('empty-state').classList.add('hidden');
    document.getElementById('loading-state').classList.add('hidden');
    document.getElementById('content-state').classList.remove('hidden');
    
    // Switch to view mode
    document.getElementById('roadmap-rendered').classList.remove('hidden');
    document.getElementById('roadmap-editor').classList.add('hidden');
    document.getElementById('btn-edit').classList.remove('hidden');
    document.getElementById('btn-save').classList.add('hidden');
    
    document.getElementById('view-title').textContent = currentRoadmap.company;
    renderMarkdownView();
  }

  function renderMarkdownView() {
    const container = document.getElementById('roadmap-rendered');
    let html = currentRoadmap.content || '';
    
    // Basic escape
    html = html.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    
    // Parse checkboxes anywhere
    let cbIndex = 0;
    html = html.replace(/- \[( |x|X)\] ([^\n<|]+)/g, (match, state, text) => {
      const isChecked = state.trim().toLowerCase() === 'x';
      const checkedAttr = isChecked ? 'checked' : '';
      const idx = cbIndex++;
      return `<div style="display:flex; align-items:flex-start; gap:8px; margin-bottom:4px;"><input type="checkbox" class="roadmap-cb" data-index="${idx}" ${checkedAttr} style="margin-top:4px;"> <span>${text}</span></div>`;
    });
    
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');
    html = html.replace(/^- (?!<)(.*)$/gm, '<li>$1</li>'); // Standard bullets
    html = html.replace(/\n/g, '<br>');
    
    container.innerHTML = html;
  }

  function setupEventListeners() {
    // Generate new roadmap
    document.getElementById('btn-generate').addEventListener('click', async () => {
      const company = document.getElementById('new-company').value;
      const days = parseInt(document.getElementById('new-days').value);
      if (!company) {
        Toast.error('Please select a company');
        return;
      }
      
      document.getElementById('empty-state').classList.add('hidden');
      document.getElementById('content-state').classList.add('hidden');
      document.getElementById('loading-state').classList.remove('hidden');
      
      try {
        const res = await API.generateRoadmap(company, days);
        roadmaps.unshift(res.roadmap); // Add to front
        selectRoadmap(res.roadmap.id);
        Toast.success('Roadmap generated!');
      } catch (err) {
        document.getElementById('loading-state').classList.add('hidden');
        document.getElementById('empty-state').classList.remove('hidden');
        Toast.error('Generation failed: ' + err.message);
      }
    });

    // Edit button
    document.getElementById('btn-edit').addEventListener('click', () => {
      document.getElementById('roadmap-rendered').classList.add('hidden');
      const editor = document.getElementById('roadmap-editor');
      editor.classList.remove('hidden');
      editor.value = currentRoadmap.content;
      
      document.getElementById('btn-edit').classList.add('hidden');
      document.getElementById('btn-save').classList.remove('hidden');
    });

    // Save button (manual edits)
    document.getElementById('btn-save').addEventListener('click', async () => {
      const newContent = document.getElementById('roadmap-editor').value;
      await saveRoadmap(newContent);
      
      // Switch back to view
      document.getElementById('roadmap-rendered').classList.remove('hidden');
      document.getElementById('roadmap-editor').classList.add('hidden');
      document.getElementById('btn-edit').classList.remove('hidden');
      document.getElementById('btn-save').classList.add('hidden');
      renderMarkdownView();
    });

    // Checkbox clicks (auto-save)
    document.getElementById('roadmap-rendered').addEventListener('change', async (e) => {
      if (e.target.classList.contains('roadmap-cb')) {
        const idx = parseInt(e.target.getAttribute('data-index'), 10);
        const isChecked = e.target.checked;
        
        let matchCount = 0;
        const newContent = currentRoadmap.content.replace(/- \[( |x|X)\] /g, (match) => {
          if (matchCount === idx) {
            matchCount++;
            return isChecked ? '- [x] ' : '- [ ] ';
          }
          matchCount++;
          return match;
        });
        
        await saveRoadmap(newContent);
      }
    });
  }

  async function saveRoadmap(newContent) {
    if (!currentRoadmap) return;
    try {
      const res = await API.updateRoadmap(currentRoadmap.id, newContent);
      // Update local state
      currentRoadmap.content = res.content;
      const idx = roadmaps.findIndex(r => r.id === currentRoadmap.id);
      if (idx !== -1) roadmaps[idx] = currentRoadmap;
      Toast.success('Progress saved');
    } catch (err) {
      Toast.error('Failed to save: ' + err.message);
    }
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  document.addEventListener('DOMContentLoaded', init);

})();
