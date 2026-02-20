# 🤖 Interactive CV Assistant

Multi-agent AI system for interactive CV queries with RAG and multi-language support.

## ✨ Features

- 🎯 **Multi-agent architecture** — Profile, GitHub, CV, and Guardrail agents working together
- 🧠 **GPT-4o-mini powered** — Fast, accurate responses via OpenAI API
- 🔍 **RAG pipeline** — TF-IDF embeddings with pgvector for context-aware answers
- 🌍 **Multi-language** — Turkish, English, Kurdish, German, Spanish, French, and more
- 🛡️ **Guardrail agent** — Prevents hallucinations and off-topic responses
- 🔄 **Auto-sync** — Vector embeddings updated automatically
- ⚡ **Serverless deployment** — Koyeb (backend) + Vercel (frontend)

## 🏗️ Architecture

```
                    Frontend                          Backend API
  User ──► React Chat Interface ──────► Python / FastAPI
                                              │
                                              ▼
                                ┌──────────────────────────┐
                                │     AI Orchestrator       │
                                │  Intent & Role Detection  │◄──── Guardrail Agent
                                └─────┬────────┬────────┬──┘      (Privacy & Safety)
                                      │        │        │
                                      ▼        ▼        ▼
                                ┌─────────┐ ┌────────┐ ┌──────────────┐
                                │ Profile │ │ GitHub │ │ CV/Document  │
                                │  Agent  │ │ Agent  │ │    Agent     │
                                │ Skills  │ │Project │ │ Generate &   │
                                │  & Exp  │ │Fetch & │ │  Serve CV    │
                                └────┬────┘ │Explain │ └──────┬───────┘
                                     │      └───┬────┘        │
                                     │          │             │
                                     ▼          ▼             ▼
                                        LLM Provider
                                    (OpenAI GPT-4o-mini)
                                     │          │             │
                                     ▼          ▼             ▼
                              ┌────────────┐ ┌──────────┐ ┌────────────┐
                              │ Knowledge  │ │  Vector  │ │   File     │
                              │    Base    │ │ Database │ │  Storage   │
                              │(PostgreSQL)│ │(Semantic │ │ (CV & Docs)│
                              │            │ │ Search)  │ │            │
                              └────────────┘ └──────────┘ └────────────┘
```

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | Python, FastAPI, SQLAlchemy, OpenAI GPT-4o-mini |
| **Frontend** | React, Vite, Tailwind CSS |
| **Database** | PostgreSQL (Neon DB), pgvector |
| **AI/RAG** | TF-IDF embeddings, pgvector similarity search |
| **Deployment** | Koyeb (backend), Vercel (frontend) |
| **CI/CD** | GitHub → Auto-deploy |

## 🚀 Live Demo

🌐 **Website:** [dogankeles.com](https://dogankeles.com)

## 📦 Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL with pgvector extension

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=your_postgresql_connection_string
GITHUB_TOKEN=your_github_token
ENVIRONMENT=development
```

Run the server:

```bash
uvicorn backend.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```


## 🤝 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send a query to the AI assistant |
| `GET` | `/health` | Health check with DB status |
| `GET` | `/api/profile/{id}` | Get profile data |
| `POST` | `/admin/ingest-vectors` | Trigger vector embedding ingestion |

### Example Request

```bash
curl -X POST https://your-api-url/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What skills does Doğan have?", "profile_id": 1}'
```

## 👤 Author

**Doğan Keleş** — [LinkedIn](https://linkedin.com/in/dogan-keles) · [GitHub](https://github.com/dogan-keles) · [Website](https://dogankeles.com)