# HCP CRM — AI-First Log Interaction Module

An AI-powered CRM screen for pharmaceutical sales reps to log interactions with Healthcare Professionals (HCPs), built with React + Redux, FastAPI, LangGraph, and Groq LLM.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Redux Toolkit, Vite, Google Inter font |
| Backend | Python 3.11+, FastAPI |
| AI Agent | LangGraph (ReAct agent) |
| LLM | Groq API — `gemma2-9b-it` |
| Database | SQLite (via SQLAlchemy, zero-install) |

---

## Features

- **Dual-mode input**: Log interactions via structured form OR natural language AI chat
- **5 LangGraph AI tools** orchestrated by a ReAct agent
- **AI sentiment analysis** of HCP responses
- **AI-suggested follow-up actions**
- **Edit existing interactions** (form + AI)
- **HCP profile search** with interaction history

---

## LangGraph Agent & Tools

The LangGraph agent uses a ReAct (Reason + Act) pattern to choose and execute tools based on the sales rep's natural language input.

### Tool 1 — `log_interaction`
Saves a new HCP interaction to the PostgreSQL database. When triggered via the chat interface, the LLM first extracts structured fields (HCP name, topics, sentiment, outcomes, follow-up actions) from the natural language input, then persists them. Supports both form-submitted structured data and AI-extracted data from conversational input.

### Tool 2 — `edit_interaction`
Modifies an existing interaction record. Accepts the interaction ID and only the fields that need updating (partial updates supported). Used when a rep says "Update interaction 5, change sentiment to Positive."

### Tool 3 — `search_hcp_profile`
Queries the HCP table by name, speciality, or hospital using SQL ILIKE search. Returns HCP details plus the 3 most recent interactions. Helps reps quickly recall context before a meeting.

### Tool 4 — `suggest_followup`
Generates context-aware follow-up action recommendations for the rep based on the HCP's speciality, interaction history count, and the content of the last interaction summary. Checks for keywords (e.g., "sample", "conference") to tailor suggestions.

### Tool 5 — `analyze_sentiment`
Rule-based + LLM-assisted sentiment analysis that scans interaction notes for positive/negative signals (e.g., "interested", "skeptical", "side effects") and returns Positive / Neutral / Negative with confidence percentage and detected signal list.

---

## Project Structure

```
hcp-crm/
├── backend/
│   ├── main.py          # FastAPI app + all routes
│   ├── agent.py         # LangGraph ReAct agent
│   ├── tools.py         # All 5 LangGraph tools
│   ├── database.py      # SQLAlchemy models + DB init
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── store/
    │   │   └── index.js         # Redux store + async thunks
    │   └── pages/
    │       └── LogInteractionScreen.jsx   # Main UI screen
    ├── index.html
    ├── vite.config.js
    └── package.json
```

---

## Setup & Run

### Prerequisites
- Python 3.10+
- Node.js 18+
- No database installation needed (SQLite is built into Python)
- Groq API key from https://console.groq.com

### Backend

```bash
cd backend
cp .env.example .env
# Edit .env: add your DATABASE_URL and GROQ_API_KEY

pip install -r requirements.txt
uvicorn main:app --reload
# Runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Runs at http://localhost:5173
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/hcps` | List all HCPs (with optional search) |
| GET | `/api/interactions` | List interactions |
| POST | `/api/interactions` | Create interaction (form) |
| PUT | `/api/interactions/:id` | Update interaction |
| DELETE | `/api/interactions/:id` | Delete interaction |
| POST | `/api/agent/chat` | Send message to LangGraph AI agent |
| POST | `/api/tools/log` | Direct tool: log interaction |
| POST | `/api/tools/analyze-sentiment` | Direct tool: sentiment analysis |
| GET | `/api/tools/suggest-followup/:id` | Direct tool: follow-up suggestions |
| GET | `/api/tools/search-hcp` | Direct tool: search HCP |

---

## Environment Variables

```env
# No database URL needed — SQLite file is created automatically
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=your_secret_key
```

---

## Author

Sreelakshmi Chowdam  
GitHub: https://github.com/sreelakshmi1593
