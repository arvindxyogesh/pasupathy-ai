# Pasupathy - Personal AI Assistant

![Pasupathy Logo](https://img.shields.io/badge/AI-Pasupathy-8b5cf6?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)
![React](https://img.shields.io/badge/React-18.2-61dafb?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ed?style=flat-square)

**Pasupathy** is a sophisticated personal AI assistant powered by Retrieval-Augmented Generation (RAG) technology. Built with cutting-edge LLM capabilities and a futuristic ChatGPT-style interface, Pasupathy provides intelligent, context-aware responses based on curated personal knowledge.

## ✨ Features

- 🤖 **Advanced RAG System** - Uses FAISS vector store with semantic search for accurate context retrieval
- 💬 **Real-time Streaming** - ChatGPT-like streaming responses for smooth UX
- 🎨 **Futuristic UI** - Modern black & purple theme with glassmorphism effects
- 🔄 **Session Management** - Persistent chat history with MongoDB
- ⚡ **Fast Performance** - FAISS index persistence (loads in 5s vs 60min rebuild)
- 🐳 **Dockerized** - Complete containerized setup for easy deployment
- 🔒 **Secure** - Environment-based API key management

## 🏗️ Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   React UI      │─────▶│  Flask Backend   │─────▶│   MongoDB       │
│  (Port 3000)    │◀─────│   (Port 5000)    │◀─────│  (Port 27017)   │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   FAISS + LLM    │
                         │  Google Gemini   │
                         └──────────────────┘
```

**Tech Stack:**
- **Backend**: Flask 2.3.3, LangChain, Google Gemini 2.5 Flash
- **Frontend**: React 18.2, Real-time streaming with SSE
- **Vector DB**: FAISS with HuggingFace embeddings (all-MiniLM-L6-v2)
- **Database**: MongoDB 7.0
- **Infrastructure**: Docker Compose with persistent volumes

## 🚀 Quick Start (Recommended)

1. **Set up environment variables:**

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose installed
- Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/pasupathy-ai.git
   cd pasupathy-ai
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API key:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

3. **Start the application**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - Health check: http://localhost:5000/api/health

### First-Time Setup

On first run, the system will:
- Build FAISS embeddings from your dataset (~60 minutes for 97K documents)
- Save the index to disk for future fast loading (5 seconds)
- Initialize the Gemini model

Subsequent starts will load from disk in ~5 seconds!

## 📊 Dataset Format

Place your personal knowledge in `data/arvind_personal_llm_dataset_mongo.json`:

```json
[
  {
    "text": "Your knowledge content here",
    "category": "personal",
    "source": "bio"
  }
]
```

Or upload via API:
```bash
curl -X POST http://localhost:5000/api/dataset/upload \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_dataset.json"
```

## 🎨 UI Features

### Modern Design
- **Black & Purple Theme** - Futuristic ChatGPT-inspired interface
- **Glassmorphism** - Translucent elements with backdrop blur
- **Smooth Animations** - Fade-in messages, hover effects
- **Responsive Layout** - Works on desktop and mobile

### Chat Features
- ✅ Real-time streaming responses
- ✅ Code syntax highlighting
- ✅ Markdown rendering
- ✅ Copy message content
- ✅ Session persistence
- ✅ Delete conversations
- ✅ New chat creation

## 🔧 Configuration

### Backend Configuration (`backend/config.py`)

```python
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
TEMPERATURE = 0.0  # Deterministic responses
SEARCH_K = 3  # Number of documents to retrieve
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
```

### Docker Volumes

- `mongodb_data` - Persistent chat sessions
- `backend_cache` - HuggingFace model cache
- `faiss_index` - Pre-built vector embeddings

## 📡 API Endpoints

### Chat
- `POST /api/chat` - Send message (streaming or standard)
- `GET /api/chat/sessions` - List all chat sessions
- `GET /api/chat/sessions/:id` - Get specific session
- `DELETE /api/chat/sessions/:id` - Delete session

### Dataset
- `POST /api/dataset/upload` - Upload knowledge base
- `GET /api/dataset/stats` - Get dataset statistics

### System
- `GET /api/health` - Health check

## 🛠️ Development Workflow

### Daily Development
```bash
# Start all services
docker-compose up

# Stop all services
docker-compose down

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild after dependency changes
docker-compose up --build
```

### Clean Rebuild
```bash
# Stop and remove all containers, networks, volumes
docker-compose down -v

# Remove all images
docker-compose down --rmi all

# Rebuild from scratch
docker-compose up --build
```

## 📁 Project Structure

```
pasupathy-ai/
├── backend/
│   ├── app.py              # Flask API endpoints
│   ├── config.py           # Configuration management
│   ├── llm_model.py        # RAG system & LLM integration

## 📁 Project Structure

```
pasupathy-ai/
├── backend/
│   ├── app.py              # Flask API endpoints
│   ├── config.py           # Configuration management
│   ├── llm_model.py        # RAG system & LLM integration
│   ├── llm_rerank_llm.py   # Answer reranking
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend container config
├── frontend/
│   ├── src/
│   │   ├── App.js          # Main app component
│   │   ├── components/     # React components
│   │   ├── services/       # API integration
│   │   └── styles/         # CSS styles
│   ├── package.json        # Node dependencies
│   └── Dockerfile          # Frontend container config
├── data/
│   └── arvind_personal_llm_dataset_mongo.json  # Knowledge base
├── .env                    # Environment variables (KEEP SECRET!)
├── .env.example           # Template for environment setup
├── docker-compose.yml     # Multi-container orchestration
└── README.md              # This file
```

## 🐛 Troubleshooting

### "Model not initialized"
**Cause**: MongoDB not running or dataset empty  
**Solution**:
```bash
docker ps  # Check containers
curl http://localhost:5000/api/dataset/stats  # Verify dataset
docker logs llm_backend -f  # Check backend logs
```

### CORS errors in frontend
**Cause**: API_BASE_URL misconfigured  
**Solution**: Check `frontend/src/services/api.js` - should point to `http://localhost:5000/api`

### `GOOGLE_API_KEY not found`
**Cause**: Environment variable not set in container  
**Solution**:
```bash
# Check .env file exists
cat .env

# Restart containers to load .env
docker-compose down
docker-compose up -d
```

### API Rate Limits
**Cause**: Free tier limit (15 requests/minute)  
**Solution**:
- Wait a few minutes
- Upgrade API plan
- Get new API key

### Port already in use
**Solution**:
```bash
docker-compose down
docker system prune -f
docker-compose up --build
```

### FAISS not loading from disk
**Solution**:
```bash
# Check if index exists
docker exec llm_backend ls -lh /app/faiss_index/

# Rebuild if corrupted
docker-compose down -v
docker-compose up --build
```

### Container restart doesn't pick up new .env
**Cause**: Restart doesn't reload environment variables  
**Solution**:
```bash
docker-compose down
docker-compose up -d  # Full recreation needed
```

## 📈 Performance

- **Embedding build**: ~60 minutes (one-time, for 97K documents)
- **FAISS load time**: ~5 seconds (cached, from disk)
- **Query response**: ~2-5 seconds
- **Memory usage**: ~2GB RAM (backend)
- **Storage**: ~500MB (FAISS index)

## 🔐 Security Notes

- ⚠️ **Never commit `.env` file to version control**
- ⚠️ Rotate API keys regularly
- ⚠️ Use production WSGI server (Gunicorn) for deployment
- ⚠️ Enable HTTPS in production
- ⚠️ Implement authentication for public deployment

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [LangChain](https://langchain.com) - RAG framework
- [Google Gemini](https://ai.google.dev) - LLM provider
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search
- [React](https://react.dev) - UI framework
- [Flask](https://flask.palletsprojects.com/) - Backend framework

## 📞 Support

Having issues? Check:
- Backend logs: `docker logs llm_backend`
- Frontend logs: Browser DevTools → Console
- Health endpoint: http://localhost:5000/api/health
- [Issues page](https://github.com/yourusername/pasupathy-ai/issues)

---

**Made with ❤️ for intelligent personal AI assistance**


Response includes:
- API status
- Database connection status
- LLM model initialization status

## 🛠️ Development

### Adding New Features

1. **Backend endpoint**: Add to `backend/app.py` and update config if needed
2. **Frontend**: Create component in `frontend/src/components/`
3. **API integration**: Update `frontend/src/services/api.js`
4. **Styling**: Add CSS to `frontend/src/styles/`

### Testing Locally

```bash
# Terminal 1: Backend
cd backend && python app.py

# Terminal 2: Frontend
cd frontend && npm start

# Terminal 3: Test API
curl http://localhost:5000/api/health
```

## 🚢 Production Deployment

1. Set strong `SECRET_KEY` in environment
2. Use production MONGO_URI (managed MongoDB service)
3. Configure frontend `REACT_APP_API_URL` for production domain
4. Add HTTPS/SSL certificates
5. Implement rate limiting and authentication
6. Use managed database backups
7. Monitor logs and errors

## 📖 Related Documentation

- [Project Architecture Details](./.github/copilot-instructions.md)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [LangChain Docs](https://python.langchain.com/)
- [Google Gemini API](https://ai.google.dev/)
- [React Documentation](https://react.dev/)

## 📧 Support

For issues or questions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review logs: `docker logs llm_backend` or `docker logs llm_frontend`
3. Verify environment setup: `docker-compose config`

## 📄 License

This project is personal and proprietary. All rights reserved.

---

**Built with ❤️ by Arvind | Powered by Google Gemini & LangChain**
