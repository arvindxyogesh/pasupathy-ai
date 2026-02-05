# Pasupathy Enhanced - Quick Reference Guide

## 🚀 Getting Started

Run the deployment script to activate all features:
```bash
./deploy_enhanced.sh
```

Or manually:
```bash
docker-compose down
docker-compose up --build -d
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+Enter` or `Ctrl+Enter` | Send message |
| `Cmd+N` or `Ctrl+N` | New chat |
| `Cmd+K` or `Ctrl+K` | Focus search |
| `Cmd+/` or `Ctrl+/` | Open settings |
| `Shift+Enter` | New line in input |
| `Escape` | Clear input / Close modals |

---

## 💬 Message Actions

Hover over any message to see actions:

- **👍 👎** Thumbs up/down - Rate responses
- **📋** Copy - Copy message to clipboard
- **✏️** Edit - Modify and regenerate
- **📌** Pin - Pin important messages
- **⬇️ ⬆️** Fold/Expand - Collapse long messages
- **🗑️** Delete - Remove message

---

## 🗂️ Conversation Management

### Sidebar Search
- Type in search box or press `Cmd+K`
- Filters by title and content

### Filters
- **All** - Show all conversations
- **⭐ Favorites** - Show only starred chats
- **📦 Archive** - Show/hide archived chats

### Right-Click Menu
- **✏️ Rename** - Change conversation title
- **📦 Archive** - Hide from main list
- **📁 Move to folder** - Organize by category
- **🏷️ Add tag** - Add custom tags
- **🗑️ Delete** - Remove conversation

### Quick Actions
- **⭐ Star** - Click star icon to favorite
- **⋮ More** - Click for context menu

---

## ⚙️ Settings Panel

Press `Cmd+/` or click ⚙️ in sidebar

### Appearance
- **Theme**: Dark / Light / Auto
- **Font Size**: Small / Medium / Large / XL
- **Show Timestamps**: Toggle message times

### AI Behavior
- **Temperature**: 0.0 (Precise) → 1.0 (Creative)
- **Response Style**: Concise / Balanced / Detailed / Technical / Casual
- **Response Length**: Short / Medium / Long
- **Max Tokens**: 256 - 4096
- **Search Depth (K)**: 5 - 50 (RAG retrieval count)
- **Enable Learning**: Toggle user knowledge capture

### Custom Instructions
Add persistent instructions for every conversation:
- "Always be concise"
- "Use bullet points"
- "Explain like I'm a beginner"

---

## 📤 Export & Share

### Export Formats (Header buttons)
- **JSON** - Full conversation data
- **MD** - Markdown formatted
- **PDF** - Printable document
- **TXT** - Plain text

### Share
- **🔗 Share** - Generate public link (30 days)
- **📋 Copy All** - Copy entire transcript
- **🖨️ Print** - Print-optimized view

---

## 🎯 Pro Tips

### Organize Your Chats
1. Star important conversations (⭐)
2. Create folders: Work, Personal, Research
3. Add tags: #urgent, #reference, #draft
4. Archive old chats to declutter

### Customize AI Responses
1. Open Settings (`Cmd+/`)
2. Set Custom Instructions for your needs
3. Adjust Temperature for creativity level
4. Choose Response Style (Technical/Casual)

### Efficient Messaging
1. Use follow-up suggestions (below AI responses)
2. Pin important answers for reference
3. Edit messages to regenerate better responses
4. Save drafts automatically (restored per session)

### Search Like a Pro
1. Press `Cmd+K` anytime
2. Search by keyword or phrase
3. Filter by favorites/archives
4. Navigate with arrow keys

---

## 🔧 Technical Details

### Token Counter
- Click 📄 in header to toggle
- Shows: ↑ Input tokens, ↓ Output tokens
- Tracks cumulative usage per session

### Stop Generation
- Red "Stop Generating" button appears during streaming
- Immediately cancels AI response
- Safe cancellation with AbortController

### Draft Auto-Save
- Input is automatically saved per session
- Restored when you return to a chat
- Cleared when message is sent

### Pin Messages
- Pinned messages appear in special section at top
- Survives page refresh (localStorage)
- Max flexibility - pin as many as needed

---

## 🐛 Troubleshooting

### Settings Not Saving
- Check if localStorage is enabled in browser
- Try: Chrome DevTools → Application → Local Storage

### Theme Not Changing
- Clear browser cache
- Refresh page (Cmd+R)
- Check Settings → Theme selection

### Search Not Working
- Ensure you're typing in search box (not input)
- Press `Cmd+K` to focus search
- Try shorter keywords

### Export Failed
- PDF export requires backend setup (see docs)
- JSON/MD/TXT should work out of box
- Check browser console for errors

---

## 📊 Feature Checklist

Use this to explore all features:

### Message Actions
- [ ] Edit a message and regenerate
- [ ] Delete a message
- [ ] Pin an important response
- [ ] React with thumbs up/down
- [ ] Fold a long message
- [ ] Copy a message

### Conversation Management
- [ ] Search conversations (`Cmd+K`)
- [ ] Rename a chat
- [ ] Create a folder
- [ ] Add a tag
- [ ] Archive a conversation
- [ ] Star a favorite
- [ ] Bulk delete archived

### Settings & Customization
- [ ] Toggle dark/light theme
- [ ] Adjust font size
- [ ] Change temperature
- [ ] Set custom instructions
- [ ] Configure response style
- [ ] Adjust search depth
- [ ] Toggle timestamps

### Export & Share
- [ ] Export as JSON
- [ ] Export as Markdown
- [ ] Export as TXT
- [ ] Share conversation link
- [ ] Copy entire conversation
- [ ] Print conversation

### Keyboard Shortcuts
- [ ] Send with `Cmd+Enter`
- [ ] New chat with `Cmd+N`
- [ ] Search with `Cmd+K`
- [ ] Settings with `Cmd+/`
- [ ] New line with `Shift+Enter`
- [ ] Clear with `Escape`

---

## 📚 Further Reading

- **Full Feature List**: [ENHANCED_FEATURES.md](ENHANCED_FEATURES.md)
- **Backend Endpoints**: [backend/ENHANCED_ENDPOINTS.py](backend/ENHANCED_ENDPOINTS.py)
- **Original Instructions**: [.github/copilot-instructions.md](.github/copilot-instructions.md)

---

## 🎉 Have Fun!

You now have **46 text-based features** making Pasupathy comparable to ChatGPT!

**Questions?** Check logs:
```bash
docker logs llm_backend --tail 50
docker logs llm_frontend --tail 50
```

**Reset Everything:**
```bash
docker-compose down
docker volume prune  # Removes MongoDB data
./deploy_enhanced.sh
```

---

**Made with ❤️ for Arvind**
