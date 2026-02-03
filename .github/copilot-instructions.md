# Pasupathy - Arvind's AI Assistant

## Project Overview
**Pasupathy** is a personalized **Retrieval-Augmented Generation (RAG) AI assistant** designed to answer questions about Arvind using his curated personal data. The system features a modern, advanced UI/UX powered by Flask backend with LangChain/Gemini integration and a React frontend.

### Purpose
Pasupathy serves as Arvind's intelligent AI companion that:
- Answers questions about Arvind's background, interests, and expertise
- Provides context-aware responses using personal knowledge stored in MongoDB
- Delivers instant, intelligent answers through advanced RAG technology
- Maintains conversation history for seamless multi-turn interactions

### Architecture
```
Frontend (React - Advanced UI/UX) → Backend API (Flask - Pasupathy) ← MongoDB + FAISS Vector Store
                                           ↓
                                  Google Gemini LLM
```

## Key Technologies & Stack
- **Backend**: Flask 2.3.3, PyMongo, LangChain, Google Generative AI (Gemini)
- **Frontend**: React 18.2.0, Axios, Lucide React, Advanced CSS (animations, gradients, responsive design)
- **Database**: MongoDB 7.0 (for chat sessions + Arvind's personal knowledge base)
- **ML**: HuggingFace Embeddings (all-MiniLM-L6-v2), FAISS vector store
- **Infrastructure**: Docker Compose (3 services: MongoDB, Flask backend, React frontend)
- **Branding**: Modern gradient UI with Pasupathy logo and animations

## Critical Architecture Patterns

### 1. RAG System Flow (`backend/llm_model.py`)
The LLM model initialization follows this sequence:
1. **Load documents** from MongoDB `dataset` collection
2. **Create embeddings** using HuggingFace sentence-transformers (all-MiniLM-L6-v2)
3. **Build FAISS vector store** with k=3 retrieval (configured in `config.py` as `SEARCH_K`)
4. **Initialize Gemini** with google_api_key from environment (`GOOGLE_API_KEY` required)
5. **Create RAG chain** using LangChain's retriever + LLM pipeline

**Critical**: If no documents exist in MongoDB, model still initializes as "ready" but returns empty responses. Always check dataset upload endpoints.

### 2. Chat Session Management (`backend/app.py`)
- **ChatSession class**: In-memory representation with `session_id`, `messages`, `title`, `created_at`
- **Persistence**: Sessions saved to MongoDB `chat_sessions` collection on every message
- **Title generation**: First user message (truncated to 50 chars) becomes session title
- **Message structure**: Each message has `id`, `role` (user/assistant), `content`, `timestamp`

### 3. Frontend-Backend Communication
- **Base URL**: `http://localhost:5000/api` (hardcoded in `frontend/src/services/api.js`)
- **Health check**: `/api/health` endpoint verifies MongoDB + model status
- **Key endpoints**:
  - `POST /api/chat` - Send message (returns session + response)
  - `GET /api/chat/sessions` - List all sessions
  - `POST /api/dataset/upload` - Upload JSON dataset file
  - `GET /api/dataset/stats` - Get document count

### 4. Configuration Management
**Config sources** (in order of precedence):
1. Environment variables (`.env` file via `python-dotenv`)
2. Default values in `backend/config.py`
3. Docker Compose env section (sets `MONGO_URI`, `GOOGLE_API_KEY`, `SECRET_KEY`)

**Essential environment variables**:
```
GOOGLE_API_KEY=xxx        # Required for Gemini
MONGO_URI=mongodb://mongodb:27017/llm_chat  # Container networking
SECRET_KEY=your-secret    # Flask app secret
```

## Development Workflows

### Local Development (without Docker)
```bash
# Backend setup
cd backend
python -m venv ../pasupathy
source ../pasupathy/bin/activate
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install

# Run services individually
python app.py              # Backend at http://localhost:5000
npm start                  # Frontend at http://localhost:3000
```

### Docker Compose (recommended)
```bash
docker-compose up --build
# Services auto-connect via llm-network bridge
# Frontend → http://localhost:3000
# Backend → http://localhost:5000
# MongoDB → localhost:27017
```

### Health Check Pattern
Both backend and frontend implement health checks:
- **Backend**: `GET /api/health` returns `{status, db_status, model_status}`
- **Frontend**: Calls health check on app mount, stores status in React state for error boundaries

## Project-Specific Conventions

### API Response Format
All endpoints return JSON with consistent structure:
```javascript
{
  "status": "success|error",
  "data": {...},
  "message": "optional error message",
  "session_id": "uuid" // for chat endpoints
}
```

### Collection Structure (MongoDB)
- **chat_sessions**: `{session_id, messages[], created_at, title, updated_at}`
- **dataset**: `{_id, text|content|*, ...}` (custom fields preserved)

### Embedding Model Hardcoded
The embedding model is **hardcoded** in two places:
- `backend/llm_model.py`: `HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")`
- `backend/config.py`: `EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"`

Keep these synchronized if changing the embedding strategy.

### Temperature & Model Selection
- **Temperature**: Fixed at 0.0 (deterministic responses, no creativity)
- **LLM**: Primary model is "gemini-pro", fallbacks in `config.py` → `GEMINI_MODELS` list

## Integration Points & Data Flows

### Dataset Upload Flow
1. Frontend (`ChatInterface` or `Landing`) sends file via `POST /api/dataset/upload`
2. Backend parses JSON, inserts into MongoDB `dataset` collection
3. **Does NOT auto-reinitialize embeddings** - model needs manual restart or new initialization call
4. Frontend calls `getDatasetStats()` to verify upload

### Chat Message Flow
1. User sends message from `ChatInterface.js` → `sendMessage(message, sessionId)`
2. Backend receives at `POST /api/chat`:
   - If no session_id: create new ChatSession
   - Append user message to session
   - Pass message + retriever context to Gemini
   - Get response, append assistant message
   - Save session to MongoDB
3. Frontend updates local state and re-renders

## Common Gotchas & Debugging

| Issue | Root Cause | Solution |
|-------|-----------|----------|
| "Model not initialized" | MongoDB not running or dataset empty | Check `docker-compose ps`, verify dataset upload |
| CORS errors in frontend | API_BASE_URL hardcoded to localhost:5000 | In Docker, frontend container can access backend via service name |
| Empty responses | No documents in dataset collection | Upload dataset via `/api/dataset/upload` |
| GOOGLE_API_KEY errors | Env var not set in container | Add to docker-compose `environment` section |
| Slow first request | FAISS + embedding model loading | Expected on cold start (~5-10s) |

## Files to Reference When Implementing Features

| Component | Primary File | Related |
|-----------|-------------|---------|
| Chat logic | `backend/app.py` (lines 54-130) | `backend/llm_model.py` |
| Session persistence | `backend/app.py` (ChatSession class) | MongoDB `chat_sessions` collection |
| UI Layout | `frontend/src/App.js` | `Sidebar`, `ChatInterface`, `Landing` components |
| API contracts | `frontend/src/services/api.js` | Every endpoint call goes through here |
| Config centralization | `backend/config.py` | Environment variable defaults |

## Quick Commands for Common Tasks

```bash
# Check backend health
curl http://localhost:5000/api/health

# View MongoDB data
docker exec llm_mongodb mongosh --eval "db.chat_sessions.find().pretty()"

# Rebuild containers after dependency changes
docker-compose up --build

# Check backend logs
docker logs llm_backend -f

# Access Flask shell (for manual session/data inspection)
docker exec llm_backend python -c "from app import *; ..."
```

## Troubleshooting Docker Issues

### `docker-compose: command not found`
**Solution**: Docker Compose isn't in PATH. Use full path:
```bash
/opt/homebrew/bin/docker-compose up
```
Or add to your shell profile (~/.zshrc):
```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
```

### `Cannot connect to the Docker daemon`
**Solution**: Docker Desktop isn't running or socket is disconnected:
1. Open Docker Desktop from Applications
2. Wait 30 seconds for daemon to fully initialize
3. Verify: `docker ps` should return container list
4. If still failing, restart Docker Desktop: **Preferences → Troubleshoot → Restart**

### Port Already Allocated (e.g., `port 27017 is already allocated`)
**Solution**: Stop conflicting containers and prune:
```bash
docker-compose down
docker system prune -f
```

### GOOGLE_API_KEY Not Set Warning
**Solution**: Required for Gemini to work. Set environment variable before running:
```bash
export GOOGLE_API_KEY="your-api-key"
docker-compose up
```
Or create `.env` file in project root:
```
GOOGLE_API_KEY=your-api-key
```
