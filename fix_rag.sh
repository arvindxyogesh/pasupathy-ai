#!/bin/bash

echo "🔧 Fixing Pasupathy RAG System..."
echo ""

# Create sample dataset
echo "1️⃣  Creating sample dataset..."
cat > /tmp/arvind_dataset.json << 'EOF'
[
  {
    "text": "Arvind is a highly skilled software engineer specializing in artificial intelligence and machine learning."
  },
  {
    "text": "Arvind has expertise in building intelligent chatbots, RAG systems, and working with large language models (LLMs)."
  },
  {
    "text": "Arvind graduated with a degree in Computer Science and has a passion for cutting-edge AI technologies."
  },
  {
    "text": "In his free time, Arvind enjoys reading AI research papers, contributing to open-source projects, and experimenting with new LLM frameworks."
  },
  {
    "text": "Arvind has built several projects including Pasupathy, his personalized AI assistant powered by RAG and Gemini."
  },
  {
    "text": "Arvind is proficient in Python, JavaScript, React, Flask, LangChain, and working with vector databases like FAISS."
  },
  {
    "text": "Arvind believes in building AI systems that are ethical, transparent, and beneficial to society."
  }
]
EOF

echo "✅ Sample dataset created at /tmp/arvind_dataset.json"
echo ""

# Upload dataset
echo "2️⃣  Uploading dataset to backend..."
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:5000/api/dataset/upload \
  -F "file=@/tmp/arvind_dataset.json")

echo "$UPLOAD_RESPONSE" | jq '.'

UPLOAD_STATUS=$(echo "$UPLOAD_RESPONSE" | jq -r '.status')

if [ "$UPLOAD_STATUS" = "success" ]; then
    echo "✅ Dataset uploaded successfully!"
else
    echo "❌ Failed to upload dataset. Check if backend is running."
    exit 1
fi
echo ""

# Restart backend
echo "3️⃣  Restarting backend to initialize RAG model..."
docker-compose restart backend

echo "⏳ Waiting 15 seconds for backend to initialize..."
sleep 15
echo ""

# Verify
echo "4️⃣  Verifying RAG system..."
HEALTH=$(curl -s http://localhost:5000/api/health)
MODEL_STATUS=$(echo "$HEALTH" | jq -r '.model_status')

if [ "$MODEL_STATUS" = "ready" ]; then
    echo "✅ RAG system is now READY!"
    echo ""
    echo "Testing with a sample query..."
    curl -s -X POST http://localhost:5000/api/chat \
      -H "Content-Type: application/json" \
      -d '{"message": "Who is Arvind?"}' | jq '.data.message'
else
    echo "❌ Model still not ready. Check logs:"
    echo "   docker logs llm_backend"
fi

echo ""
echo "🎉 Fix complete! Run ./test_rag.sh to verify."
