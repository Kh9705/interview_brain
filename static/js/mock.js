// ── Mock Interview Logic ────────────────────────────────────────────────────

const Mock = (() => {
  let interviewId = null;
  let questions = [];
  let currentIndex = 0;
  let company = '';
  let role = '';
  let results = [];

  // Speech
  let recognition = null;
  let isListening = false;
  let synth = window.speechSynthesis;

  // ── Init ─────────────────────────────────────────────────────────────────

  async function init() {
    if (!API.requireAuth()) return;

    // Load user's companies to populate dropdown
    try {
      const profile = await API.getProfile();
      const companies = profile.user.companies || [];
      const select = document.getElementById('mock-company');
      select.innerHTML = companies.map(c =>
        `<option value="${c}">${c}</option>`
      ).join('');
      if (companies.length === 0) {
        select.innerHTML = '<option value="">No companies — add some first</option>';
      }
      role = profile.user.role || 'Software Engineer';
    } catch (err) {
      Toast.error('Failed to load profile');
    }
  }

  // ── Start Interview ──────────────────────────────────────────────────────

  async function startInterview() {
    company = document.getElementById('mock-company').value;
    const numQuestions = parseInt(document.getElementById('mock-num-questions').value);

    if (!company) {
      Toast.error('Please select a company');
      return;
    }

    // Show loading
    document.getElementById('setup-phase').classList.add('hidden');
    document.getElementById('loading-phase').classList.remove('hidden');

    try {
      const res = await API.startMockInterview(company, numQuestions);
      interviewId = res.interview_id;
      questions = res.questions || [];
      role = res.role || role;
      currentIndex = 0;
      results = [];

      if (questions.length === 0) {
        Toast.error('No questions generated. Please try again.');
        document.getElementById('loading-phase').classList.add('hidden');
        document.getElementById('setup-phase').classList.remove('hidden');
        return;
      }

      // Start camera
      await startCamera();

      // Show interview phase
      document.getElementById('loading-phase').classList.add('hidden');
      document.getElementById('interview-phase').classList.remove('hidden');
      document.getElementById('company-label').textContent = `${company} — ${role}`;

      // Show first question
      showQuestion(0);

    } catch (err) {
      Toast.error('Failed to start interview: ' + err.message);
      document.getElementById('loading-phase').classList.add('hidden');
      document.getElementById('setup-phase').classList.remove('hidden');
    }
  }

  // ── Camera ───────────────────────────────────────────────────────────────

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false
      });
      const video = document.getElementById('camera-video');
      video.srcObject = stream;
    } catch (err) {
      console.warn('Camera not available:', err.message);
      Toast.info('Camera not available — you can still type answers');
    }
  }

  function stopCamera() {
    const video = document.getElementById('camera-video');
    if (video && video.srcObject) {
      video.srcObject.getTracks().forEach(t => t.stop());
      video.srcObject = null;
    }
  }

  // ── Show Question ────────────────────────────────────────────────────────

  function parseMarkdown(md) {
    if (!md) return '';
    let html = md.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/\n/g, '<br>');
    return html;
  }

  function showQuestion(index) {
    currentIndex = index;
    const total = questions.length;

    document.getElementById('question-counter').textContent = `Question ${index + 1} / ${total}`;
    document.getElementById('progress-fill').style.width = `${((index) / total) * 100}%`;
    document.getElementById('question-text').innerHTML = parseMarkdown(questions[index]);
    document.getElementById('answer-textarea').value = '';
    document.getElementById('feedback-card').classList.add('hidden');
    document.getElementById('submit-answer-btn').disabled = false;
    document.getElementById('submit-answer-btn').textContent = 'Submit Answer';

    // Speak the question
    speakQuestion(questions[index]);
  }

  // ── Speech Synthesis (AI reads question) ─────────────────────────────────

  function speakQuestion(text) {
    if (!synth) return;
    synth.cancel();

    // Strip markdown formatting before speaking
    const cleanText = text.replace(/[*#`_~>-]/g, '').trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 0.9;
    utterance.pitch = 1.0;

    // Show speaking indicator
    const indicator = document.getElementById('ai-speaking');
    indicator.classList.remove('hidden');

    utterance.onend = () => {
      indicator.classList.add('hidden');
    };
    utterance.onerror = () => {
      indicator.classList.add('hidden');
    };

    synth.speak(utterance);
  }

  // ── Speech Recognition (user speaks answer) ──────────────────────────────

  function toggleMic() {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }

  function startListening() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      Toast.info('Speech recognition not supported in this browser. Please type your answer.');
      return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    const textarea = document.getElementById('answer-textarea');
    let finalTranscript = textarea.value;

    recognition.onresult = (event) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interim += transcript;
        }
      }
      textarea.value = finalTranscript + interim;
    };

    recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
      if (event.error !== 'no-speech') {
        Toast.info('Voice recognition error. Please type your answer.');
      }
      stopListening();
    };

    recognition.onend = () => {
      if (isListening) {
        // Restart if still in listening mode
        try { recognition.start(); } catch (e) { stopListening(); }
      }
    };

    recognition.start();
    isListening = true;

    document.getElementById('mic-btn').textContent = 'Stop Voice';
    document.getElementById('mic-btn').style.borderColor = 'var(--red)';
    document.getElementById('recording-indicator').classList.remove('hidden');
    document.getElementById('rec-badge').classList.remove('hidden');
  }

  function stopListening() {
    if (recognition) {
      isListening = false;
      try { recognition.stop(); } catch (e) {}
      recognition = null;
    }
    document.getElementById('mic-btn').textContent = 'Start Voice';
    document.getElementById('mic-btn').style.borderColor = '';
    document.getElementById('recording-indicator').classList.add('hidden');
    document.getElementById('rec-badge').classList.add('hidden');
  }

  // ── Submit Answer ────────────────────────────────────────────────────────

  async function submitAnswer() {
    const answer = document.getElementById('answer-textarea').value.trim();
    if (!answer) {
      Toast.error('Please provide an answer first');
      return;
    }

    // Stop any voice recording
    stopListening();
    synth.cancel();

    const btn = document.getElementById('submit-answer-btn');
    btn.disabled = true;
    btn.textContent = 'Evaluating...';

    try {
      const res = await API.evaluateAnswer(
        interviewId,
        currentIndex + 1,
        questions[currentIndex],
        answer
      );

      results.push({
        question: questions[currentIndex],
        answer: answer,
        score: res.score,
        feedback: res.feedback,
      });

      // Show feedback
      const scoreEl = document.getElementById('feedback-score');
      scoreEl.textContent = res.score.toFixed(1);
      scoreEl.className = `q-score ${res.score >= 6 ? 'good' : 'bad'}`;

      document.getElementById('feedback-text').textContent = res.feedback;
      document.getElementById('feedback-card').classList.remove('hidden');

      // Update button text for last question
      const nextBtn = document.getElementById('next-question-btn');
      if (currentIndex >= questions.length - 1) {
        nextBtn.textContent = 'View Results';
      } else {
        nextBtn.textContent = 'Next Question';
      }

      // Update progress
      document.getElementById('progress-fill').style.width =
        `${((currentIndex + 1) / questions.length) * 100}%`;

    } catch (err) {
      Toast.error('Evaluation failed: ' + err.message);
      btn.disabled = false;
      btn.textContent = 'Submit Answer';
    }
  }

  // ── Next Question / Finish ───────────────────────────────────────────────

  function nextQuestion() {
    if (currentIndex >= questions.length - 1) {
      // Finish — go to results
      finishInterview();
    } else {
      showQuestion(currentIndex + 1);
    }
  }

  function finishInterview() {
    stopCamera();
    stopListening();
    synth.cancel();

    // Store results in sessionStorage for results page
    const data = {
      interviewId,
      company,
      role,
      results,
      overallScore: results.reduce((sum, r) => sum + r.score, 0) / results.length,
    };
    sessionStorage.setItem('ib_mock_results', JSON.stringify(data));
    window.location.href = '/static/results.html';
  }

  // ── Init on load ─────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', init);

  return { startInterview, toggleMic, submitAnswer, nextQuestion };
})();
