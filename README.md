# Pasupathy - Personal AI Assistant

![Pasupathy Logo](https://img.shields.io/badge/AI-Pasupathy-8b5cf6?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)
![React](https://img.shields.io/badge/React-18.2-61dafb?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ed?style=flat-square)

**Pasupathy** is a sophisticated personal AI assistant powered by Retrieval-Augmented Generation (RAG) technology. Built using cutting-edge LLM capabilities and a futuristic ChatGPT-style interface, it provides intelligent, context-aware responses based on curated personal knowledge.

This project demonstrates expertise in full-stack AI development, cloud infrastructure, and modern web technologies.

## Key Features

- **Advanced RAG System** - Implemented FAISS vector store with semantic search for accurate context retrieval
- **Real-time Streaming** - ChatGPT-like streaming responses providing smooth user experience
- **Futuristic UI** - Modern black and purple theme with glassmorphism effects
- **Browser-Only Privacy** - All chat sessions stored locally in browser localStorage, ensuring complete privacy
- **Fast Performance** - FAISS index persistence loads in 5 seconds versus 60 minute rebuild
- **Production-Ready Deployment** - Complete AWS infrastructure with Docker containerization
- **HTTPS Security** - CloudFront CDN configuration for secure HTTPS access on both frontend and backend

## Architecture Overview

Modern cloud-native design patterns:

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   React UI      │─────▶│  Flask Backend   │─────▶│  MongoDB Atlas  │
│  AWS S3 +       │◀─────│  AWS Elastic     │◀─────│  Cloud Database │
│  CloudFront     │      │  Beanstalk       │      │                 │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   FAISS + LLM    │
                         │  Google Gemini   │
                         └──────────────────┘
```

**Technology Stack:**
- **Backend**: Flask 2.3.3, LangChain, Google Gemini 2.5 Flash
- **Frontend**: React 18.2 with real-time streaming via Server-Sent Events
- **Vector Database**: FAISS with HuggingFace embeddings (all-MiniLM-L6-v2)
- **Database**: MongoDB Atlas (cloud-managed)
- **Infrastructure**: Docker containers on AWS Elastic Beanstalk
- **CDN**: AWS CloudFront for HTTPS delivery
- **Storage**: AWS S3 for static website hosting

## Quick Start for Local Development

### Prerequisites

- Docker and Docker Compose installed
- Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/arvindxyogesh/pasupathy-ai.git
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
- Build FAISS embeddings from the personal knowledge dataset (approximately 60 minutes for 97K documents)
- Save the index to disk for future fast loading (5 seconds)
- Initialize the Gemini model

Subsequent starts will load from disk in approximately 5 seconds.

## Dataset Format

Personal knowledge is stored in `data/arvind_personal_llm_dataset_mongo.json`:

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

## User Interface Features

### Modern Design
- **Black and Purple Theme** - Futuristic ChatGPT-inspired interface
- **Glassmorphism Effects** - Translucent elements with backdrop blur
- **Smooth Animations** - Fade-in messages and hover effects
- **Responsive Layout** - Works seamlessly on desktop and mobile devices

### Chat Features
- Real-time streaming responses
- Code syntax highlighting
- Markdown rendering
- Copy message content
- Browser-only session persistence (complete privacy)
- Delete conversations
- New chat creation

## Configuration

### Backend Configuration

Backend settings in `backend/config.py`:

```python
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
TEMPERATURE = 0.0  # Deterministic responses for consistency
SEARCH_K = 3  # Number of documents to retrieve from vector store
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
```

### Docker Volumes

- `mongodb_data` - Persistent storage for dataset
- `backend_cache` - HuggingFace model cache
- `faiss_index` - Pre-built vector embeddings index

## API Endpoints

### Chat Endpoints
- `POST /api/chat` - Send message and receive AI response (streaming or standard)
- `GET /api/chat/sessions` - List all chat sessions
- `GET /api/chat/sessions/:id` - Get specific session details
- `DELETE /api/chat/sessions/:id` - Delete a session

### Dataset Management
- `POST /api/dataset/upload` - Upload knowledge base
- `GET /api/dataset/stats` - Get dataset statistics

### System Health
- `GET /api/health` - Health check endpoint (database, model status)

## Development Workflow

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

## Project Structure

```
pasupathy-ai/
├── backend/
│   ├── app.py              # Flask API endpoints
│   ├── config.py           # Configuration management
│   ├── llm_model.py        # RAG system & LLM integration

## 📁 Project Structure

Arvind organized the codebase as follows:

```
pasupathy-ai/
├── backend/
│   ├── app.py              # Flask API endpoints by Arvind
│   ├── config.py           # Configuration management
│   ├── llm_model.py        # RAG system and LLM integration
│   ├── user_knowledge.py   # User contribution handling
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Backend container configuration
├── frontend/
│   ├── src/
│   │   ├── App.js          # Main React application component
│   │   ├── components/     # React UI components
│   │   ├── services/       # API integration layer
│   │   └── styles/         # Custom CSS styles
│   ├── package.json        # Node.js dependencies
│   └── Dockerfile          # Frontend container configuration
├── data/
│   └── arvind_personal_llm_dataset_mongo.json  # Arvind's knowledge base (251 docs)
├── .env                    # Environment variables (NEVER commit to git)
├── .env.example            # Template for environment setup
├── docker-compose.yml      # Multi-container orchestration
└── README.md               # This documentation file
```

## Troubleshooting Guide

### "Model not initialized" Error
**Cause**: MongoDB not running or dataset empty  
**Solution**:
```bash
docker ps  # Check container status
curl http://localhost:5000/api/dataset/stats  # Verify Arvind's dataset is loaded
docker logs llm_backend -f  # Check backend logs for errors
```

### CORS Errors in Frontend
**Cause**: API_BASE_URL misconfigured  
**Solution**: Check `frontend/src/services/api.js` - should point to `http://localhost:5000/api` for local development

### "GOOGLE_API_KEY not found" Error
**Cause**: Environment variable not set in container  
**Solution**:
```bash
# Verify .env file exists and contains your API key
cat .env

# Restart containers to load environment variables
docker-compose down
docker-compose up -d
```

### API Rate Limits
**Cause**: Free tier Google API limit (15 requests per minute)  
**Solution**:
- Wait a few minutes before retrying
- Upgrade your API plan if needed
- Generate a new API key from Google AI Studio

### Port Already in Use
**Solution**:
```bash
docker-compose down
docker system prune -f
docker-compose up --build
```

### FAISS Not Loading from Disk
**Solution**:
```bash
# Check if index exists
docker exec llm_backend ls -lh /app/faiss_index/

# Rebuild if corrupted
docker-compose down -v
docker-compose up --build
```

### Container Restart Doesn't Pick Up New .env
**Cause**: Restart doesn't reload environment variables  
**Solution**:
```bash
docker-compose down  # Full stop required
docker-compose up -d  # Start fresh with new environment
```

## Performance Metrics

Optimized system performance:

- **Initial embedding build**: Approximately 60 minutes (one-time, for 97K documents)
- **FAISS load time**: Approximately 5 seconds (cached from disk)
- **Query response time**: 2-5 seconds average
- **Memory usage**: Approximately 2GB RAM (backend container)
- **Storage requirements**: Approximately 500MB (FAISS index)

## Security Best Practices

Implemented security measures:

- **Never commit `.env` file to version control** - Contains sensitive API keys
- **Rotate API keys regularly** - Best practice for credential management
- **Production WSGI server** - Uses Gunicorn instead of Flask development server
- **HTTPS enabled** - CloudFront CDN provides SSL/TLS encryption
- **Browser-only storage** - Chat sessions never leave the user's browser
- **No authentication logging** - Privacy-focused design

## AWS Production Deployment

Deployed using modern AWS infrastructure:

**Current Production Setup:**
- **Frontend**: AWS S3 Static Website + CloudFront CDN (HTTPS)
  - URL: https://d2wb2ysunmtcp0.cloudfront.net
- **Backend**: AWS Elastic Beanstalk (Docker platform) + CloudFront CDN (HTTPS)
  - URL: https://d2bsiqcy48fx87.cloudfront.net
- **Database**: MongoDB Atlas (cloud-managed)
- **Region**: us-west-2 (Oregon)
- **Instance**: t3.micro (AWS Free Tier eligible)

**Deployment Features:**
- Complete HTTPS encryption on both frontend and backend
- CloudFront CDN for global content delivery
- Docker containerization for consistent environments
- Automated CI/CD pipeline with Elastic Beanstalk
- Environment variable management via AWS console
- Zero-downtime deployments

## Contributing

This is a personal project. If you'd like to contribute or have suggestions:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with clear documentation
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request with detailed description

## License

This project is personal and proprietary. All rights reserved.

## Technical Acknowledgments

Leveraging the following open-source technologies:

- [LangChain](https://langchain.com) - RAG framework for building AI applications
- [Google Gemini](https://ai.google.dev) - Large language model provider
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search by Meta AI
- [React](https://react.dev) - Frontend UI framework
- [Flask](https://flask.palletsprojects.com/) - Python web framework
- [MongoDB](https://www.mongodb.com/) - NoSQL database
- [HuggingFace](https://huggingface.co/) - Transformer models and embeddings

## Support and Contact

For issues or questions about the Pasupathy AI Assistant:

**Debugging Steps:**
1. Check the [Troubleshooting Guide](#troubleshooting-guide) section above
2. Review backend logs: `docker logs llm_backend`
3. Review frontend logs: Browser DevTools → Console tab
4. Test health endpoint: http://localhost:5000/api/health
5. Visit [Issues page](https://github.com/arvindxyogesh/pasupathy-ai/issues)

**Health Endpoint Response Includes:**
- API operational status
- Database connection status
- LLM model initialization status
- Dataset document count

## Development and Testing

### Adding New Features

Designed for easy extensibility:

1. **Backend endpoint**: Add to `backend/app.py` and update `config.py` if needed
2. **Frontend component**: Create in `frontend/src/components/`
3. **API integration**: Update `frontend/src/services/api.js`
4. **Styling**: Add CSS to `frontend/src/styles/`

### Testing Locally Without Docker

```bash
# Terminal 1: Start backend
cd backend && python app.py

# Terminal 2: Start frontend
cd frontend && npm start

# Terminal 3: Test API endpoints
curl http://localhost:5000/api/health
```

## Related Documentation

For deeper technical insights:

- [Project Architecture Details](./.github/copilot-instructions.md) - Comprehensive system design
- [Flask Documentation](https://flask.palletsprojects.com/) - Python web framework
- [LangChain Documentation](https://python.langchain.com/) - RAG framework
- [Google Gemini API](https://ai.google.dev/) - LLM integration
- [React Documentation](https://react.dev/) - Frontend framework
- [AWS Elastic Beanstalk](https://aws.amazon.com/elasticbeanstalk/) - Deployment platform
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) - Cloud database

---

**Pasupathy - Personal AI Assistant**  
**Powered by Google Gemini AI, LangChain RAG, and AWS Cloud Infrastructure**  
**Repository**: https://github.com/arvindxyogesh/pasupathy-ai
