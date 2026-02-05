#!/bin/bash

# Pasupathy Enhanced Features Deployment Script
# This script activates all 46 new text-based features

echo "🚀 Pasupathy Enhanced Features Deployment"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.yml not found${NC}"
    echo "Please run this script from the pasupathy-ai directory"
    exit 1
fi

echo -e "${YELLOW}📋 This will deploy all enhanced features:${NC}"
echo "  ✅ Stop generation button"
echo "  ✅ Dark/Light theme toggle"
echo "  ✅ Keyboard shortcuts (Cmd+Enter, Cmd+N, Cmd+K, etc.)"
echo "  ✅ Edit, delete, pin, react to messages"
echo "  ✅ Search conversations"
echo "  ✅ Folders, tags, archives, favorites"
echo "  ✅ Follow-up questions"
echo "  ✅ Settings panel (temperature, style, etc.)"
echo "  ✅ Token counter"
echo "  ✅ Multiple export formats"
echo "  ✅ Share conversations"
echo "  ✅ Draft auto-save"
echo "  ... and 34 more features!"
echo ""

read -p "Do you want to continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

echo ""
echo -e "${GREEN}Step 1/5: Backing up original files...${NC}"
mkdir -p backups
cp frontend/src/App.js backups/App_Original.js 2>/dev/null || true
cp frontend/src/components/ChatInterface.js backups/ChatInterface_Original.js 2>/dev/null || true
cp frontend/src/components/Sidebar.js backups/Sidebar_Original.js 2>/dev/null || true
cp frontend/src/styles/App.css backups/App_Original.css 2>/dev/null || true
cp frontend/src/styles/ChatInterface.css backups/ChatInterface_Original.css 2>/dev/null || true
cp frontend/src/styles/Sidebar.css backups/Sidebar_Original.css 2>/dev/null || true
echo -e "${GREEN}✓ Backups created in ./backups/${NC}"

echo ""
echo -e "${GREEN}Step 2/5: Replacing with enhanced versions...${NC}"

# Replace App.js
if [ -f "frontend/src/App_Enhanced.js" ]; then
    mv frontend/src/App_Enhanced.js frontend/src/App.js
    echo "✓ Updated App.js"
fi

# Replace ChatInterface.js
if [ -f "frontend/src/components/ChatInterface_Enhanced.js" ]; then
    mv frontend/src/components/ChatInterface_Enhanced.js frontend/src/components/ChatInterface.js
    echo "✓ Updated ChatInterface.js"
fi

# Replace Sidebar.js
if [ -f "frontend/src/components/Sidebar_Enhanced.js" ]; then
    mv frontend/src/components/Sidebar_Enhanced.js frontend/src/components/Sidebar.js
    echo "✓ Updated Sidebar.js"
fi

# Replace CSS files
if [ -f "frontend/src/styles/App_Enhanced.css" ]; then
    mv frontend/src/styles/App_Enhanced.css frontend/src/styles/App.css
    echo "✓ Updated App.css"
fi

if [ -f "frontend/src/styles/ChatInterface_Enhanced.css" ]; then
    mv frontend/src/styles/ChatInterface_Enhanced.css frontend/src/styles/ChatInterface.css
    echo "✓ Updated ChatInterface.css"
fi

if [ -f "frontend/src/styles/Sidebar_Enhanced.css" ]; then
    mv frontend/src/styles/Sidebar_Enhanced.css frontend/src/styles/Sidebar.css
    echo "✓ Updated Sidebar.css"
fi

echo -e "${GREEN}✓ All files updated${NC}"

echo ""
echo -e "${GREEN}Step 3/5: Stopping existing containers...${NC}"
docker-compose down
echo -e "${GREEN}✓ Containers stopped${NC}"

echo ""
echo -e "${GREEN}Step 4/5: Building new containers with enhanced features...${NC}"
docker-compose build --no-cache
echo -e "${GREEN}✓ Build complete${NC}"

echo ""
echo -e "${GREEN}Step 5/5: Starting enhanced Pasupathy...${NC}"
docker-compose up -d
echo -e "${GREEN}✓ Containers started${NC}"

echo ""
echo -e "${YELLOW}⏳ Waiting for services to initialize (15 seconds)...${NC}"
sleep 15

echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo ""
echo -e "${YELLOW}🎉 All 46 Enhanced Features Are Now Active!${NC}"
echo ""
echo "Access Pasupathy at: ${GREEN}http://localhost:3000${NC}"
echo ""
echo "📚 Features documentation: ENHANCED_FEATURES.md"
echo ""
echo "🔑 Quick Keyboard Shortcuts:"
echo "  • Cmd+Enter: Send message"
echo "  • Cmd+N: New chat"
echo "  • Cmd+K: Search conversations"
echo "  • Cmd+/: Open settings"
echo ""
echo "🎨 Try the new Settings panel (Cmd+/) to customize:"
echo "  • Theme (Dark/Light)"
echo "  • Font size"
echo "  • Temperature (creativity)"
echo "  • Response style"
echo "  • Custom instructions"
echo ""
echo "💡 Tips:"
echo "  • Right-click conversations for more options"
echo "  • Pin important messages"
echo "  • Use folders and tags to organize chats"
echo "  • Export conversations in multiple formats"
echo ""
echo "📊 Check status:"
echo "  docker logs llm_backend --tail 50"
echo "  docker logs llm_frontend --tail 50"
echo ""
echo -e "${GREEN}Happy chatting! 🚀${NC}"
