# 🧠 Interview Brain

**Interview Brain** is an intelligent, personalized interview preparation platform built for the **Cognee AI Hackathon**. 

It moves beyond generic LLM advice by leveraging **Cognee's Graph RAG** capabilities to build a persistent memory of a candidate's strengths, target companies, and weak areas. As you interact with the platform, it builds a personalized knowledge graph that dynamically influences your mock interviews and study roadmaps.

![Skill Map](https://img.shields.io/badge/Knowledge_Graph-Powered_by_Cognee-1a1a2e?style=for-the-badge)

---

## 🚀 Key Features

* **AI Mock Interviews with Voice Synthesis:** Practice real technical and behavioral questions tailored to your target companies. The AI evaluates your answer in real-time using Cognee `recall` to check your weaknesses. It even speaks to you using text-to-speech for a realistic interview feel!
* **Dynamic Study Roadmaps:** Generates structured, day-by-day study roadmaps. Includes a **✨ AI Edit** feature—simply tell the AI how you want to adjust your plan (e.g., "Add more system design"), and it intelligently rewrites the roadmap.
* **Skill Map Visualization:** See exactly how the AI understands your profile! We use Cognee's native visualization engine to display a live Knowledge Graph of your target companies, roles, and skills.
* **Compare Readiness:** Instantly compare the interview requirements of two different companies to see how your current skill profile stacks up.
* **Persistent Memory:** Everything you do is remembered. Your profile is continuously updated using Cognee's memory endpoints to ensure the AI's advice gets better over time.

---

## 🛠️ How We Built It (Cognee Integration)

This project strictly adheres to the hackathon requirements by deeply integrating the **Cognee Cloud API** into the backend architecture (FastAPI). 

Here are the primary endpoints utilized across the 4 Core Memory Lifecycle operations:

1. **`POST /api/v1/remember`**: When a user registers or updates their target companies/weak areas, we format this data and send it to the `remember` endpoint. This builds a dedicated dataset for the user and maps relationships between their identity, target companies, and skills in the Knowledge Graph.
2. **`POST /api/v1/recall`**: Used extensively throughout the app. Whether evaluating a mock interview answer, generating a custom 30-day roadmap, or performing an AI edit on an existing roadmap, we query the user's specific dataset to ensure the LLM's response is grounded in their historical data.
3. **`POST /api/v1/improve`**: Featured natively on the Skill Map! Users can click the **🧠 Enhance Graph (Memify)** button to run post-ingestion enrichment on their dataset and adapt weights.
4. **`POST /api/v1/forget`**: Implemented perfectly! When a user decides they no longer want to interview at a specific company (by deleting it from their dashboard), we surgically prune and delete that company's memory dataset using `forget()`.
5. **`GET /api/v1/visualize` & `GET /api/v1/datasets`**: We fetch the user's dataset and render the live HTML visualization graph directly in the browser on the "Skill Map" page.

### Tech Stack
* **Frontend:** Vanilla HTML/CSS/JS (Lightweight, beautiful dark-mode UI)
* **Backend:** Python, FastAPI, SQLite (Local tracking)
* **AI Engine:** Cognee Cloud API

---

## 💻 Running it Locally

### Prerequisites
* Python 3.10+
* A Cognee API Key & Tenant ID

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Kh9705/interview_brain.git
   cd interview_brain
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   COGNEE_API_KEY=your_api_key_here
   COGNEE_BASE_URL=https://tenant-XXXX.aws.cognee.ai
   COGNEE_TENANT_ID=your_tenant_id_here
   ```

4. **Run the server:**
   ```bash
   python main.py
   ```

5. **Open the app:**
   Navigate to `http://localhost:8000` in your web browser.

---

## 🏆 Hackathon Notes
This project was designed specifically for the Cognee hackathon to demonstrate how Graph RAG can solve the problem of "generic AI advice" in the EdTech/Career space. By using a knowledge graph to track a user's progress, target companies, and weaknesses, **Interview Brain** creates a highly personalized, adaptive learning experience.

*Note: AI tools were used to assist in writing parts of the code for this submission.*
