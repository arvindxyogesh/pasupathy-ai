#!/bin/bash

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Pasupathy RAG System Diagnostic Tool                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Docker Services
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Checking Docker Services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker-compose ps
echo ""

# Test 2: Backend Health
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Backend Health Check..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
HEALTH=$(curl -s http://localhost:5000/api/health)
echo "$HEALTH" | jq '.'

MODEL_STATUS=$(echo "$HEALTH" | jq -r '.model_status // "unknown"')
DB_STATUS=$(echo "$HEALTH" | jq -r '.db_status // "unknown"')

if [ "$MODEL_STATUS" = "ready" ]; then
    echo -e "${GREEN}✅ Model Status: READY${NC}"
else
    echo -e "${RED}❌ Model Status: NOT READY${NC}"
fi

if [ "$DB_STATUS" = "connected" ]; then
    echo -e "${GREEN}✅ Database Status: CONNECTED${NC}"
else
    echo -e "${RED}❌ Database Status: DISCONNECTED${NC}"
fi
echo ""

# Test 3: Dataset Stats
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Dataset Statistics..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
STATS=$(curl -s http://localhost:5000/api/dataset/stats)
echo "$STATS" | jq '.'

DOC_COUNT=$(echo "$STATS" | jq -r '.data.document_count // 0')
echo -e "Document Count: ${YELLOW}$DOC_COUNT${NC}"

if [ "$DOC_COUNT" -eq 0 ]; then
    echo -e "${RED}⚠️  WARNING: No documents in dataset!${NC}"
    echo -e "${YELLOW}💡 You need to upload a dataset for RAG to work.${NC}"
fi
echo ""

# Test 4: MongoDB Direct Check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  MongoDB Document Count (Direct)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
MONGO_COUNT=$(docker exec llm_mongodb mongosh llm_chat --quiet --eval "db.dataset.countDocuments()")
echo "MongoDB dataset collection count: $MONGO_COUNT"
echo ""

# Test 5: Test Chat Endpoint
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  Testing Chat Endpoint with Sample Query..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
CHAT_RESPONSE=$(curl -s -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Who is Arvind?"}')

echo "$CHAT_RESPONSE" | jq '.'

CHAT_STATUS=$(echo "$CHAT_RESPONSE" | jq -r '.status')
CHAT_MESSAGE=$(echo "$CHAT_RESPONSE" | jq -r '.data.message // .message')

if [ "$CHAT_STATUS" = "success" ]; then
    echo -e "${GREEN}✅ Chat Response: SUCCESS${NC}"
    echo -e "Response: ${GREEN}$CHAT_MESSAGE${NC}"
else
    echo -e "${RED}❌ Chat Response: ERROR${NC}"
    echo -e "Error: ${RED}$CHAT_MESSAGE${NC}"
fi
echo ""

# Test 6: Backend Logs (last 30 lines)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  Backend Logs (Last 30 Lines)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker logs llm_backend --tail 30
echo ""

# Final Diagnosis
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  DIAGNOSIS & RECOMMENDATIONS                               ║"
echo "╚════════════════════════════════════════════════════════════╝"

if [ "$MODEL_STATUS" != "ready" ] || [ "$DOC_COUNT" -eq 0 ]; then
    echo -e "${RED}❌ RAG SYSTEM IS NOT WORKING${NC}"
    echo ""
    echo "Reasons:"
    [ "$MODEL_STATUS" != "ready" ] && echo "  • Model is not initialized"
    [ "$DOC_COUNT" -eq 0 ] && echo "  • Dataset is empty (0 documents)"
    echo ""
    echo -e "${YELLOW}SOLUTION:${NC}"
    echo "  1. Upload a dataset:"
    echo "     cat > /tmp/arvind_dataset.json << 'EOF'"
    echo '     [{"text": "Arvind is a software engineer specializing in AI and machine learning."}]'
    echo "     EOF"
    echo ""
    echo "     curl -X POST http://localhost:5000/api/dataset/upload \\"
    echo "       -F 'file=@/tmp/arvind_dataset.json'"
    echo ""
    echo "  2. Restart the backend:"
    echo "     docker-compose restart backend"
    echo ""
    echo "  3. Wait 10 seconds and re-run this test:"
    echo "     ./test_rag.sh"
else
    echo -e "${GREEN}✅ RAG SYSTEM IS WORKING CORRECTLY${NC}"
    echo ""
    echo "All checks passed:"
    echo "  • Backend is healthy"
    echo "  • Database is connected"
    echo "  • Model is initialized"
    echo "  • Dataset has $DOC_COUNT documents"
    echo "  • Chat endpoint is responding"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
