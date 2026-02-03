#!/bin/bash

echo "🚀 Starting Pasupathy AI Assistant..."
echo ""

# Navigate to project directory
cd /Users/arvindxyogesh/Documents/pasupathy-ai

# Stop existing containers
echo "1️⃣  Stopping existing containers..."
docker-compose down

# Start services
echo "2️⃣  Building and starting services..."
docker-compose up --build -d

# Wait for services
echo "⏳ Waiting 20 seconds for services to initialize..."
sleep 20

# Check health
echo "3️⃣  Checking backend health..."
HEALTH=$(curl -s http://localhost:5000/api/health)
echo "$HEALTH" | jq '.'

MODEL_STATUS=$(echo "$HEALTH" | jq -r '.model_status // "unknown"')

if [ "$MODEL_STATUS" != "ready" ]; then
    echo "⚠️  Model not ready. Uploading sample dataset..."
    
    # Create and upload dataset
    cat > /tmp/arvind_dataset.json << 'EOF'
[
  {"text": "Arvind is a software engineer specializing in AI and machine learning."},
  {"text": "Arvind has built Pasupathy, a RAG-powered AI assistant using Google Gemini."},
  {"text": "Arvind is proficient in Python, React, Flask, LangChain, and FAISS."}
]
EOF
    
    curl -s -X POST http://localhost:5000/api/dataset/upload -F "file=@/tmp/arvind_dataset.json"
    
    echo "♻️  Restarting backend..."
    docker-compose restart backend
    sleep 15
fi

# Final check
echo "4️⃣  Final verification..."
curl -s http://localhost:5000/api/health | jq '.'

echo ""
echo "✅ Pasupathy is ready!"
echo ""
echo "📱 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:5000/api/health"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f"
