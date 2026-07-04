// ── Auth Page Logic ─────────────────────────────────────────────────────────
// Handles login form, multi-step register form, and auth redirects.

document.addEventListener('DOMContentLoaded', () => {
  // If already logged in, redirect to dashboard
  if (API.isLoggedIn()) {
    window.location.href = '/static/dashboard.html';
    return;
  }

  // ── Login Form ──────────────────────────────────────────────────────────
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = loginForm.querySelector('button[type="submit"]');
      const email = document.getElementById('login-email').value.trim();
      const password = document.getElementById('login-password').value;

      if (!email || !password) {
        Toast.error('Please fill in all fields');
        return;
      }

      btn.disabled = true;
      btn.textContent = 'Signing in...';

      try {
        await API.login(email, password);
        Toast.success('Welcome back!');
        setTimeout(() => window.location.href = '/static/dashboard.html', 500);
      } catch (err) {
        Toast.error(err.message);
        btn.disabled = false;
        btn.textContent = 'Sign In';
      }
    });
  }

  // ── Multi-Step Register Form ────────────────────────────────────────────
  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    let currentStep = 1;
    const totalSteps = 4;

    const steps = document.querySelectorAll('.step');
    const dots  = document.querySelectorAll('.step-dot');

    function showStep(n) {
      steps.forEach((s, i) => {
        s.classList.toggle('active', i + 1 === n);
      });
      dots.forEach((d, i) => {
        d.classList.remove('active', 'done');
        if (i + 1 === n)  d.classList.add('active');
        if (i + 1 < n)   d.classList.add('done');
      });
      currentStep = n;
    }

    // Next / Back buttons
    document.querySelectorAll('[data-next]').forEach(btn => {
      btn.addEventListener('click', () => {
        // Validate current step before proceeding
        if (currentStep === 1) {
          const name = document.getElementById('reg-name').value.trim();
          const email = document.getElementById('reg-email').value.trim();
          const password = document.getElementById('reg-password').value;
          if (!name || !email || !password) {
            Toast.error('Please fill in all fields');
            return;
          }
          if (password.length < 6) {
            Toast.error('Password must be at least 6 characters');
            return;
          }
        }
        if (currentStep < totalSteps) showStep(currentStep + 1);
      });
    });

    document.querySelectorAll('[data-back]').forEach(btn => {
      btn.addEventListener('click', () => {
        if (currentStep > 1) showStep(currentStep - 1);
      });
    });

    // Prevent accidental Enter submission
    registerForm.addEventListener('keydown', (e) => {
      // Allow enter to be handled by custom-company input without submitting form
      if (e.key === 'Enter' && e.target.id !== 'custom-company' && e.target.tagName !== 'BUTTON') {
        e.preventDefault();
      }
    });

    // Custom companies array
    const customCompaniesList = [];
    const customCompanyInput = document.getElementById('custom-company');
    const customCompanyTags = document.getElementById('custom-company-tags');

    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }

    function renderCustomCompanies() {
      if (!customCompanyTags) return;
      customCompanyTags.innerHTML = customCompaniesList.map(c => 
        `<span class="tag">${escapeHtml(c)} <span class="remove-tag" data-company="${escapeHtml(c)}" style="cursor:pointer; margin-left:4px; opacity:0.7;">&times;</span></span>`
      ).join('');
      
      customCompanyTags.querySelectorAll('.remove-tag').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const c = e.target.getAttribute('data-company');
          const idx = customCompaniesList.indexOf(c);
          if (idx > -1) {
            customCompaniesList.splice(idx, 1);
            renderCustomCompanies();
          }
        });
      });
    }

    if (customCompanyInput) {
      customCompanyInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const val = customCompanyInput.value.trim();
          if (val && !customCompaniesList.includes(val)) {
            customCompaniesList.push(val);
            renderCustomCompanies();
          }
          customCompanyInput.value = '';
        }
      });
    }

    // Toggle check items on click
    document.querySelectorAll('.check-item').forEach(item => {
      item.addEventListener('click', (e) => {
        // If the user clicked the input directly, just update the class
        if (e.target.tagName.toLowerCase() === 'input') {
          item.classList.toggle('active', e.target.checked);
          return;
        }
        
        e.preventDefault(); // Prevent native label click
        const input = item.querySelector('input');
        if (input) {
          if (input.type === 'checkbox') {
            input.checked = !input.checked;
          } else if (input.type === 'radio') {
            input.checked = true;
            // Deselect siblings
            const name = input.name;
            document.querySelectorAll(`.check-item input[name="${name}"]`).forEach(other => {
              other.closest('.check-item').classList.toggle('active', other.checked);
            });
          }
          item.classList.toggle('active', input.checked);
        }
      });
    });

    // Submit handler
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = registerForm.querySelector('button[type="submit"]');
      btn.disabled = true;
      btn.textContent = 'Creating your account...';

      // Cycle loading text since it takes time
      const loadingTexts = [
        'Creating your account...',
        'Building your skill map...',
        'Analyzing companies...',
        'Ingesting target roles...',
        'Finalizing setup...'
      ];
      let textIdx = 0;
      const loadingInterval = setInterval(() => {
        textIdx = (textIdx + 1) % loadingTexts.length;
        if (btn.disabled) {
          btn.textContent = loadingTexts[textIdx];
        }
      }, 3000);

      // Gather data
      const name = document.getElementById('reg-name').value.trim();
      const email = document.getElementById('reg-email').value.trim();
      const password = document.getElementById('reg-password').value;

      // Roles (multi-select checkboxes)
      const roles = [];
      document.querySelectorAll('input[name="role"]:checked').forEach(cb => {
        roles.push(cb.value);
      });
      const role = roles.join(', ');

      // Companies (checkboxes)
      const companies = [];
      document.querySelectorAll('input[name="company"]:checked').forEach(cb => {
        companies.push(cb.value);
      });
      // Custom companies
      if (typeof customCompaniesList !== 'undefined') {
        companies.push(...customCompaniesList);
      }
      const customCompanyInputVal = document.getElementById('custom-company');
      if (customCompanyInputVal && customCompanyInputVal.value.trim()) {
        const val = customCompanyInputVal.value.trim();
        if (!companies.includes(val)) companies.push(val);
      }

      // Weak areas (checkboxes)
      const weakAreas = [];
      document.querySelectorAll('input[name="weak_area"]:checked').forEach(cb => {
        weakAreas.push(cb.value);
      });

      if (!name || !email || !password) {
        clearInterval(loadingInterval);
        Toast.error('Please complete step 1');
        btn.disabled = false;
        btn.textContent = 'Create Account';
        showStep(1);
        return;
      }

      try {
        // 1. Register
        await API.register({ name, email, password, role, companies, weak_areas: weakAreas });

        // 2. Ingest profile into Cognee
        try {
          await API.ingest({ name, role, companies, weak_areas: weakAreas });
        } catch (ingestErr) {
          console.warn('Ingest warning (non-blocking):', ingestErr.message);
        }

        clearInterval(loadingInterval);
        btn.textContent = 'Setup Complete!';
        Toast.success('Your personalized map is ready!');
        setTimeout(() => window.location.href = '/static/dashboard.html', 800);
      } catch (err) {
        clearInterval(loadingInterval);
        Toast.error(err.message);
        btn.disabled = false;
        btn.textContent = 'Create Account';
      }
    });

    // Init first step
    showStep(1);
  }
});
