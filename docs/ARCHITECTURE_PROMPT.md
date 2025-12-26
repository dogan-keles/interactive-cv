# interactive-cv — Architecture Prompt

## Architecture Diagram

See `docs/architecture-diagram.jpeg`.

This diagram visually represents the mandatory system architecture.
The diagram is a reference and must be followed strictly.

## SYSTEM ROLE


You are implementing a **GitHub repository project**, not a commercial product, not a startup MVP, and not a UI demo.

Repository name: **interactive-cv**

This repository must demonstrate:
- clean backend architecture
- agent-based AI system design
- correct use of LLMs with guardrails
- strong separation of concerns

Avoid marketing language, buzzwords, or unnecessary abstractions.

---

## 1. Project Purpose

This project implements an **agent-based, interactive CV system**.

Users interact via a chat interface and can:
- ask questions about the candidate’s skills, experience, and interests
- explore selected GitHub projects
- request and download CV documents

All responses must be grounded in stored data.
Hallucination is strictly forbidden.

---

## 2. Reference Architecture (MANDATORY)

The system must follow this architecture strictly:

### Frontend
- React-based chat interface
- Communicates only with the Backend API
- Frontend implementation is OUT OF SCOPE

### Backend API
- Python
- FastAPI
- Async endpoints
- Acts as the entry point for chat requests

---

## 3. Core AI Layer

### AI Orchestrator (Central Component)

Responsibilities:
- Receives user messages from the API layer
- Performs **intent detection**
- Performs **implicit role detection** (HR / technical / general)
- Decides which agent(s) should handle the request
- Aggregates agent responses into a final answer

Restrictions:
- Must NOT access databases directly
- Must NOT generate content without agent input

---

## 4. Agents (STRICT ROLES)

### Profile Agent
- Answers questions about:
  - skills
  - experience
  - tech stack
  - interests
- Reads from:
  - Knowledge Base (PostgreSQL)
  - Vector Database (semantic search)

---

### GitHub Agent
- Selects relevant GitHub projects
- Explains projects briefly and technically
- Filters projects based on user intent
- Must NOT dump all repositories blindly

---

### CV / Document Agent
- Handles CV-related requests
- Generates or retrieves CV documents
- Returns secure download links
- Reads from File Storage only

---

### Guardrail Agent
- Ensures:
  - privacy
  - safety
  - professional tone
- Prevents:
  - sensitive data leakage
  - speculation
  - non-grounded answers

Guardrail checks must be applied before returning a final response.

---

## 5. Knowledge & Storage Layer

### Knowledge Base
- PostgreSQL
- Stores structured data:
  - profile
  - experience
  - skills
  - project metadata

---

### Vector Database
- Used for semantic search
- Query-first, then generate
- No direct answer generation without retrieval

---

### File Storage
- Stores CVs and related documents
- Accessed only via the CV / Document Agent

---

## 6. LLM Usage Rules (CRITICAL)

- LLM access is allowed ONLY inside agents
- LLM must NEVER:
  - invent information
  - assume missing data
- If required data is missing:
  - respond with uncertainty
  - explain limitations clearly

LLM provider must be abstracted (no vendor lock-in).

---

## 7. Tool-Based Agent Design

Agents must interact via explicit tools with structured inputs/outputs.

Example tools:
- `search_profile(query)`
- `semantic_search(query)`
- `fetch_github_projects(topic)`
- `generate_cv(version)`
- `get_file_link(file_id)`

Agents must NOT access databases directly.

---

## 8. API Design

Minimum required endpoints:
- `POST /chat`
- `GET /download/{file_id}`

Requirements:
- Pydantic models
- Clear request/response schemas
- Proper error handling
- No authentication logic

---

## 9. Code Quality Expectations

- Clean folder structure
- Separation of concerns
- Agent logic isolated from API layer
- Configuration via environment variables
- Minimal but meaningful comments

This repository should look like a serious engineer’s AI system design portfolio.

---

## 10. Explicit Non-Goals

DO NOT:
- implement frontend
- add authentication
- add analytics dashboards
- over-optimize prematurely
- introduce unnecessary abstractions

---

## 11. Expected Outputs

The implementation should include:
- backend folder structure
- agent implementations
- orchestrator logic
- database schema
- tool interfaces
- README explaining:
  - architecture
  - data flow
  - local setup
  - how to add profile data

---

## END OF ARCHITECTURE PROMPT