from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from flask_pymongo import PyMongo
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
import datetime as dt
import uuid
import logging
import json
import os
from functools import wraps
from collections import defaultdict
import time
from config import SECRET_KEY, MONGO_URI

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["MONGO_URI"] = MONGO_URI
CORS(app)

# Rate limiting
request_counts = defaultdict(lambda: {"count": 0, "reset_time": time.time()})
RATE_LIMIT = 20  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        current_time = time.time()
        
        if current_time - request_counts[client_ip]["reset_time"] > RATE_LIMIT_WINDOW:
            request_counts[client_ip] = {"count": 0, "reset_time": current_time}
        
        if request_counts[client_ip]["count"] >= RATE_LIMIT:
            return jsonify({"status": "error", "message": "Rate limit exceeded"}), 429
        
        request_counts[client_ip]["count"] += 1
        return f(*args, **kwargs)
    return decorated_function

# MongoDB connection
mongo = PyMongo(app)

# Import after mongo is initialized
from llm_model import initialize_llm_model

# Initialize LLM model in background thread
llm_chain = None
model_status = {"status": "initializing", "message": "Loading model and embeddings..."}

def init_model_background():
    global llm_chain, model_status
    try:
        print("🚀 Starting LLM model initialization in background...")
        model_status = {"status": "initializing", "message": "Loading documents and building embeddings..."}
        llm_chain = initialize_llm_model(mongo.db)
        model_status = {"status": "ready", "message": "Model initialized successfully"}
        print("✅ Model initialized successfully!")
    except Exception as e:
        model_status = {"status": "error", "message": str(e)}
        print(f"❌ Model initialization failed: {str(e)}")

# Start initialization in background thread
import threading
init_thread = threading.Thread(target=init_model_background, daemon=True)
init_thread.start()
print("✅ API server starting... Model initializing in background...")

# Collections
chat_sessions_collection = mongo.db.chat_sessions
dataset_collection = mongo.db.dataset

class ChatSession:
    def __init__(self, session_id=None):
        self.session_id = session_id or str(uuid.uuid4())
        self.messages = []
        self.created_at = datetime.now()
        self.title = "New Chat"
        self.updated_at = datetime.now()
        self.metadata = {"model": "gemini-2.5-flash", "total_tokens": 0}

    def add_message(self, role, content, message_id=None):
        message = {
            "id": message_id or str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "edited": False
        }
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message

    def edit_message(self, message_id, new_content):
        for msg in self.messages:
            if msg["id"] == message_id:
                msg["content"] = new_content
                msg["edited"] = True
                msg["edited_at"] = datetime.now().isoformat()
                self.updated_at = datetime.now()
                return True
        return False

    def delete_message(self, message_id):
        self.messages = [m for m in self.messages if m["id"] != message_id]
        self.updated_at = datetime.now()

    def get_context(self, max_messages=10):
        """Get recent conversation context for better responses"""
        return self.messages[-max_messages:]

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "created_at": self.created_at.isoformat(),
            "title": self.title,
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }

def get_chat_session(session_id=None):
    if session_id:
        session_data = chat_sessions_collection.find_one({'session_id': session_id})
        if session_data:
            session = ChatSession(session_id)
            session.messages = session_data.get('messages', [])
            session.title = session_data.get('title', 'New Chat')
            session.created_at = datetime.datetime.fromisoformat(session_data.get('created_at'))
            return session
    
    new_session = ChatSession()
    chat_sessions_collection.insert_one(new_session.to_dict())
    return new_session

def save_chat_session(session):
    chat_sessions_collection.update_one(
        {'session_id': session.session_id},
        {'$set': session.to_dict()},
        upsert=True
    )

# API Routes
@app.route('/')
def landing():
    return jsonify({"message": "LLM API Server is running!"})

@app.route('/api/health')
def health_check():
    """Check if the model and database are initialized"""
    try:
        # Test MongoDB connection
        mongo.db.command('ping')
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    return jsonify({
        'status': 'ready' if model_status["status"] == "ready" and db_status == "connected" else model_status["status"],
        'database': db_status,
        'model_status': model_status["status"],
        'model_message': model_status["message"],
        'initialized': llm_chain is not None,
        'dataset_count': dataset_collection.count_documents({})
    })

@app.route('/api/chat', methods=['POST'])
@rate_limit
def chat():
    try:
        # Check if model is ready
        if not llm_chain:
            return jsonify({
                "status": "error", 
                "message": f"Model is not ready yet. Status: {model_status['status']} - {model_status['message']}"
            }), 503
        
        data = request.json
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        stream = data.get('stream', False)
        
        if not user_message:
            return jsonify({"status": "error", "message": "Message cannot be empty"}), 400

        # Get or create session
        if session_id:
            session_data = chat_sessions_collection.find_one({"session_id": session_id})
            if session_data:
                session = ChatSession(session_id)
                session.messages = session_data.get("messages", [])
                session.title = session_data.get("title", "New Chat")
                # Ensure created_at is a datetime object
                created_at = session_data.get("created_at", datetime.now())
                if isinstance(created_at, str):
                    session.created_at = dt.datetime.fromisoformat(created_at)
                else:
                    session.created_at = created_at
                session.metadata = session_data.get("metadata", {})
            else:
                session = ChatSession()
        else:
            session = ChatSession()

        # Set title from first message
        if not session.messages:
            session.title = user_message[:50] + ("..." if len(user_message) > 50 else "")

        # Add user message
        user_msg = session.add_message("user", user_message)

        # Get conversation history context (for multi-turn conversations)
        conversation_context = session.get_context(max_messages=6)  # Last 3 exchanges
        conversation_history = "\n".join([
            f"{m['role'].capitalize()}: {m['content']}" 
            for m in conversation_context[:-1]  # Exclude current message
        ]) if len(conversation_context) > 1 else ""

        # Build query with conversation context
        if conversation_history:
            full_query = f"Previous conversation:\n{conversation_history}\n\nCurrent question: {user_message}"
        else:
            full_query = user_message

        if stream:
            def generate():
                try:
                    # Use RAG chain to get response
                    response_text = llm_chain["chain"].invoke(full_query)
                    # Get source documents separately
                    source_docs = llm_chain["retriever"].get_relevant_documents(full_query)
                    
                    # Stream the response word by word for better UX
                    words = response_text.split()
                    for i, word in enumerate(words):
                        chunk = word + (" " if i < len(words) - 1 else "")
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                    
                    # Save complete response with metadata
                    session.add_message("assistant", response_text)
                    session.metadata['last_sources'] = [
                        doc.metadata.get('source', 'unknown') 
                        for doc in source_docs[:3]
                    ]
                    
                    chat_sessions_collection.update_one(
                        {"session_id": session.session_id},
                        {"$set": session.to_dict()},
                        upsert=True
                    )
                    yield f"data: {json.dumps({'done': True, 'session_id': session.session_id})}\n\n"
                except Exception as e:
                    logging.error(f"Stream error: {str(e)}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"

            return Response(stream_with_context(generate()), mimetype='text/event-stream')
        else:
            # Use RAG chain with retrieval
            bot_response = llm_chain["chain"].invoke(full_query)
            # Get source documents separately
            source_docs = llm_chain["retriever"].get_relevant_documents(full_query)
            
            # Add assistant message
            session.add_message("assistant", bot_response)
            
            # Store sources in metadata
            session.metadata['last_sources'] = [
                {
                    'source': doc.metadata.get('source', 'unknown'),
                    'category': doc.metadata.get('category', 'general')
                }
                for doc in source_docs[:3]
            ]

            # Save to database
            chat_sessions_collection.update_one(
                {"session_id": session.session_id},
                {"$set": session.to_dict()},
                upsert=True
            )

            return jsonify({
                "status": "success",
                "response": bot_response,
                "session_id": session.session_id,
                "message_id": session.messages[-1]["id"],
                "sources": session.metadata.get('last_sources', []),
                "session": session.to_dict()
            })

    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/chat/regenerate', methods=['POST'])
@rate_limit
def regenerate_response():
    """Regenerate the last assistant response"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({"status": "error", "message": "Session ID required"}), 400

        session_data = chat_sessions_collection.find_one({"session_id": session_id})
        if not session_data:
            return jsonify({"status": "error", "message": "Session not found"}), 404

        session = ChatSession(session_id)
        session.messages = session_data.get("messages", [])
        session.title = session_data.get("title", "New Chat")
        session.metadata = session_data.get("metadata", {})

        # Remove last assistant message if exists
        if session.messages and session.messages[-1]["role"] == "assistant":
            session.messages.pop()

        # Get last user message
        if not session.messages or session.messages[-1]["role"] != "user":
            return jsonify({"status": "error", "message": "No user message to regenerate from"}), 400

        user_message = session.messages[-1]["content"]
        
        # Get conversation context
        conversation_context = session.get_context(max_messages=6)
        conversation_history = "\n".join([
            f"{m['role'].capitalize()}: {m['content']}" 
            for m in conversation_context[:-1]
        ]) if len(conversation_context) > 1 else ""
        
        full_query = f"Previous conversation:\n{conversation_history}\n\nCurrent question: {user_message}" if conversation_history else user_message

        # Use RAG chain
        bot_response = llm_chain["chain"].invoke(full_query)
        source_docs = llm_chain["retriever"].get_relevant_documents(full_query)
        
        session.add_message("assistant", bot_response)
        session.metadata['last_sources'] = [
            doc.metadata.get('source', 'unknown') 
            for doc in source_docs[:3]
        ]
        
        chat_sessions_collection.update_one(
            {"session_id": session.session_id},
            {"$set": session.to_dict()},
            upsert=True
        )

        return jsonify({
            "status": "success",
            "response": bot_response,
            "sources": session.metadata.get('last_sources', []),
            "session": session.to_dict()
        })

    except Exception as e:
        logging.error(f"Regenerate error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/chat/edit', methods=['PUT'])
def edit_message():
    """Edit a message in a session"""
    try:
        data = request.json
        session_id = data.get('session_id')
        message_id = data.get('message_id')
        new_content = data.get('content')

        if not all([session_id, message_id, new_content]):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        session_data = chat_sessions_collection.find_one({"session_id": session_id})
        if not session_data:
            return jsonify({"status": "error", "message": "Session not found"}), 404

        session = ChatSession(session_id)
        session.messages = session_data["messages"]
        
        if session.edit_message(message_id, new_content):
            chat_sessions_collection.update_one(
                {"session_id": session.session_id},
                {"$set": session.to_dict()}
            )
            return jsonify({"status": "success", "session": session.to_dict()})
        
        return jsonify({"status": "error", "message": "Message not found"}), 404

    except Exception as e:
        logging.error(f"Edit error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/chat/sessions', methods=['GET'])
def get_sessions():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        skip = (page - 1) * limit

        sessions = list(chat_sessions_collection.find()
                       .sort("updated_at", DESCENDING)
                       .skip(skip)
                       .limit(limit))
        
        total = chat_sessions_collection.count_documents({})
        
        for session in sessions:
            session['_id'] = str(session['_id'])
        
        return jsonify({
            "status": "success",
            "sessions": sessions,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        })
    except Exception as e:
        logging.error(f"Get sessions error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/chat/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    try:
        session = chat_sessions_collection.find_one({"session_id": session_id})
        if session:
            session['_id'] = str(session['_id'])
            return jsonify({"status": "success", "session": session})
        return jsonify({"status": "error", "message": "Session not found"}), 404
    except Exception as e:
        logging.error(f"Get session error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/chat/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    try:
        result = chat_sessions_collection.delete_one({"session_id": session_id})
        if result.deleted_count > 0:
            return jsonify({"status": "success", "message": "Session deleted"})
        return jsonify({"status": "error", "message": "Session not found"}), 404
    except Exception as e:
        logging.error(f"Delete session error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/chat/sessions/<session_id>/rename', methods=['PUT'])
def rename_session(session_id):
    try:
        data = request.json
        new_title = data.get('title', '').strip()
        
        if not new_title:
            return jsonify({"status": "error", "message": "Title cannot be empty"}), 400

        result = chat_sessions_collection.update_one(
            {"session_id": session_id},
            {"$set": {"title": new_title, "updated_at": datetime.now().isoformat()}}
        )
        
        if result.modified_count > 0:
            return jsonify({"status": "success", "message": "Session renamed"})
        return jsonify({"status": "error", "message": "Session not found"}), 404
    except Exception as e:
        logging.error(f"Rename session error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/chat/search', methods=['GET'])
def search_sessions():
    """Search through chat sessions"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({"status": "error", "message": "Search query required"}), 400

        # Search in titles and message content
        sessions = list(chat_sessions_collection.find({
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"messages.content": {"$regex": query, "$options": "i"}}
            ]
        }).sort("updated_at", DESCENDING).limit(50))

        for session in sessions:
            session['_id'] = str(session['_id'])

        return jsonify({
            "status": "success",
            "sessions": sessions,
            "count": len(sessions)
        })
    except Exception as e:
        logging.error(f"Search error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/chat/export/<session_id>', methods=['GET'])
def export_session(session_id):
    """Export a chat session as JSON or Markdown"""
    try:
        format_type = request.args.get('format', 'json')
        session = chat_sessions_collection.find_one({"session_id": session_id})
        
        if not session:
            return jsonify({"status": "error", "message": "Session not found"}), 404

        if format_type == 'markdown':
            md_content = f"# {session['title']}\n\n"
            md_content += f"Created: {session['created_at']}\n\n"
            
            for msg in session['messages']:
                role = "**User**" if msg['role'] == 'user' else "**Pasupathy**"
                md_content += f"{role}: {msg['content']}\n\n---\n\n"
            
            return Response(md_content, mimetype='text/markdown', 
                          headers={"Content-Disposition": f"attachment; filename=chat_{session_id}.md"})
        else:
            session['_id'] = str(session['_id'])
            return jsonify({"status": "success", "session": session})

    except Exception as e:
        logging.error(f"Export error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/dataset/upload', methods=['POST'])
def upload_dataset():
    """Upload JSON dataset to MongoDB"""
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400
        
        if not file.filename.endswith('.json'):
            return jsonify({"status": "error", "message": "Only JSON files are supported"}), 400
        
        # Parse JSON
        data = json.load(file)
        
        # Ensure data is a list
        if isinstance(data, dict):
            data = [data]
        
        # Insert into MongoDB
        result = dataset_collection.insert_many(data)
        count = len(result.inserted_ids)
        
        logging.info(f"📤 Uploaded {count} documents to dataset")
        
        # Reinitialize RAG system with new data
        global llm_chain
        logging.info("🔄 Reinitializing RAG system with new data...")
        llm_chain = initialize_llm_model(mongo.db)
        
        return jsonify({
            "status": "success",
            "message": f"Uploaded {count} documents",
            "count": count
        })
        
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/dataset/stats', methods=['GET'])
def dataset_stats():
    """Get dataset statistics"""
    try:
        count = dataset_collection.count_documents({})
        sample = list(dataset_collection.find().limit(3))
        
        for doc in sample:
            doc['_id'] = str(doc['_id'])
        
        return jsonify({
            "status": "success",
            "total_documents": count,
            "sample": sample
        })
    except Exception as e:
        logging.error(f"Stats error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Create indexes for better performance
    try:
        chat_sessions_collection.create_index([("session_id", ASCENDING)], unique=True)
        chat_sessions_collection.create_index([("updated_at", DESCENDING)])
        chat_sessions_collection.create_index([("title", "text"), ("messages.content", "text")])
        logging.info("Database indexes created successfully")
    except Exception as e:
        logging.warning(f"Index creation warning: {str(e)}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)