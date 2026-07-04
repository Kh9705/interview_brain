# 🧠 Interview Brain

> AI-powered interview preparation platform that **actually remembers you** — powered by [Cognee](https://cognee.ai) knowledge graphs.

Built for the [Hangover Hackathon](https://www.wemakedevs.org/hackathons/cognee) by Cognee × WeMakeDevs.

---

## ✨ Features

| Feature | Description |
|---|---|
| **🎤 Mock Interviews** | Real-time AI interviews with camera feed, speech synthesis (AI speaks questions), and speech recognition (voice answers) |
| **💬 Smart Q&A** | Ask anything about your target companies, prep strategy, or weak areas — AI answers using your personalized knowledge graph |
| **⚖️ Company Compare** | Side-by-side comparison of interview requirements between two companies |
| **🗺️ Prep Roadmap** | Day-by-day study plan tailored to a specific company and your weak areas |
| **🔮 Knowledge Graph** | Interactive D3.js visualization of your knowledge — skills, companies, topics, relationships |
| **📊 Performance Tracking** | Track mock interview scores over time, identify patterns in weak areas |

## 🧬 Cognee Integration (All 5 Lifecycle APIs)

This project uses **all 5 core Cognee memory lifecycle APIs** for deep integration:

| Cognee API | Endpoint | How We Use It |
|---|---|---|
| **remember()** | `POST /api/v1/remember` | Ingest user profiles + company interview data into knowledge graph |
| **recall()** | `POST /api/v1/recall` | Query graph for advice, generate interview questions, evaluate answers, compare companies, build roadmaps |
| **improve()** | `POST /api/v1/improve` | Enrich graph with mock interview feedback + performance data |
| **forget()** | `POST /api/v1/forget` | Remove company data when user drops a target company |
| **visualize** | `GET /api/v1/datasets/{id}/graph` | Render interactive knowledge graph with D3.js |

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Cognee Cloud API key (use promo code `COGNEE-35` for free credits)

### Setup

```bash
# Clone & enter project
cd interview-brain

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your COGNEE_API_KEY and JWT_SECRET

# Run
python main.py
```

Visit `http://localhost:8000` → Landing page.

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `COGNEE_API_KEY` | ✅ | Cognee Cloud API key |
| `COGNEE_API_URL` | ❌ | Cognee API base URL (default: `https://api.cognee.ai`) |
| `JWT_SECRET_KEY` | ✅ | Secret for JWT token signing |
| `DATABASE_URL` | ❌ | SQLite path (default: `interview_brain.db`) |

## 🏗️ Architecture

```
User Browser (HTML/JS/CSS)
    ↓ REST API calls
FastAPI Backend (Python)
    ├── SQLite (users, feedback, mock_interviews)
    ├── JWT Auth (register, login, protected routes)
    └── Cognee Cloud API (via httpx)
            ├── remember() → ingest profile + company data
            ├── recall()   → query for advice, questions, comparisons
            ├── improve()  → enrich with feedback
            ├── forget()   → drop company data
            └── get_graph  → knowledge graph visualization
```

## 📁 Project Structure

```
interview-brain/
├── main.py              # FastAPI app entry point
├── config.py            # Environment configuration
├── database.py          # SQLite setup (aiosqlite)
├── models.py            # Pydantic schemas
├── auth.py              # JWT authentication
├── cognee_client.py     # Cognee Cloud API wrapper
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
├── routes/
│   ├── ingest.py        # POST /api/ingest (remember)
│   ├── ask.py           # POST /api/ask (recall)
│   ├── feedback.py      # POST/GET /api/feedback (remember)
│   ├── profile.py       # GET /api/profile
│   ├── mock_interview.py # Mock interview flow (recall + remember)
│   ├── compare.py       # POST /api/compare (recall)
│   ├── roadmap.py       # POST /api/roadmap (recall)
│   ├── visualize.py     # GET /api/visualize (get_graph)
│   └── company.py       # DELETE /api/company/{name} (forget)
└── static/
    ├── css/style.css     # Design system (dark mode, glassmorphism)
    ├── js/
    │   ├── api.js        # API client with JWT auth
    │   ├── auth.js       # Login/register logic
    │   ├── dashboard.js  # Dashboard + chat logic
    │   ├── mock.js       # Mock interview (camera, voice, scoring)
    │   └── graph.js      # D3.js knowledge graph
    ├── index.html        # Landing page
    ├── login.html        # Login
    ├── register.html     # Multi-step registration
    ├── dashboard.html    # Main dashboard + AI chat
    ├── mock.html         # Mock interview screen
    ├── results.html      # Interview results
    └── graph.html        # Knowledge graph visualization
```

## 🎯 User Flow

1. **Register** → Multi-step form: name, role, target companies, weak areas
2. **Ingest** → Profile + company data sent to Cognee via `remember()`
3. **Dashboard** → Chat with AI, compare companies, generate roadmaps
4. **Mock Interview** → Camera on, AI speaks questions, user answers via voice/text
5. **Results** → Score breakdown, feedback, memory updated via `improve()`
6. **Knowledge Graph** → Explore your data visually
7. **Iterate** → Each interaction enriches your Cognee knowledge graph

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLite (aiosqlite), httpx
- **Auth**: JWT (python-jose), bcrypt (passlib)
- **AI Memory**: Cognee Cloud REST API
- **Frontend**: Vanilla HTML/CSS/JS
- **Visualization**: D3.js v7
- **Voice**: Web Speech API (SpeechRecognition + SpeechSynthesis)
- **Camera**: getUserMedia API

## 📜 License

MIT — Built with ❤️ for the Hangover Hackathon.
