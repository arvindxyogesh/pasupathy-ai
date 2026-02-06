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
from llm_model import (
    initialize_llm_model, 
    get_retriever_context, 
    add_user_contributions_to_vectorstore, 
    rebuild_vectorstore_with_contributions,
    _detect_query_context,
    get_context_filtered_docs
)
from user_knowledge import UserKnowledgeManager

# Initialize user knowledge manager
user_knowledge_manager = None

# Initialize LLM model in background thread
llm_chain = None
model_status = {"status": "initializing", "message": "Loading model and embeddings..."}

def init_model_background():
    global llm_chain, model_status, user_knowledge_manager
    try:
        print("🚀 Starting LLM model initialization in background...")
        model_status = {"status": "initializing", "message": "Loading documents and building embeddings..."}
        
        # Initialize user knowledge manager
        user_knowledge_manager = UserKnowledgeManager(mongo.db)
        print("✅ User knowledge manager initialized")
        
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

def generate_creative_title(user_message, bot_response, query_context=None):
    """Generate a creative, contextual title for the chat session using LLM"""
    try:
        if not llm_chain or model_status["status"] != "ready":
            # Fallback to simple title
            return user_message[:40] + ("..." if len(user_message) > 40 else "")
        
        gemini_model = llm_chain.get("gemini_model")
        if not gemini_model:
            return user_message[:40] + ("..." if len(user_message) > 40 else "")
        
        # Create prompt for title generation
        context_hint = f" (about {query_context.replace('_', ' ')})" if query_context else ""
        
        title_prompt = f"""Generate a short, creative title (3-5 words max) for this conversation{context_hint}.

User Question: {user_message[:200]}
Assistant Response: {bot_response[:200]}

Requirements:
- Maximum 5 words
- Descriptive and contextual
- Professional and clear
- No quotes or punctuation
- Capture the main topic/theme

Examples:
- "Computer Vision Projects"
- "Education Background"
- "Machine Learning Skills"
- "Robotics Experience"

Title:"""

        response = gemini_model.generate_content(title_prompt)
        title = response.text.strip()
        
        # Clean up the title
        title = title.replace('"', '').replace("'", '').strip()
        
        # Ensure it's not too long
        if len(title) > 50:
            title = title[:47] + "..."
        
        logging.info(f"💡 Generated creative title: '{title}'")
        return title
        
    except Exception as e:
        logging.error(f"Error generating title: {str(e)}")
        # Fallback to simple title
        return user_message[:40] + ("..." if len(user_message) > 40 else "")

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
                    # Use Gemini client
                    gemini_model = llm_chain["gemini_model"]
                    retriever = llm_chain["retriever"]
                    
                    # Detect if this is a follow-up question
                    follow_up_indicators = ['he', 'his', 'him', 'that', 'those', 'them', 'this', 'these', 'it', 'also', 'more', 'tell me more', 'what about', 'and']
                    is_follow_up = any(word in user_message.lower().split()[:5] for word in follow_up_indicators)
                    
                    # Detect query context for focused retrieval
                    conversation_text = [msg['content'] for msg in session.messages[-3:]]
                    query_context = _detect_query_context(user_message, conversation_text)
                    
                    # Build conversation context if this seems like a follow-up
                    conv_context = ""
                    if is_follow_up and len(session.messages) > 1:
                        recent_messages = session.messages[-4:]  # Last 2 Q&A pairs
                        conv_context = "\n\nRecent Conversation (for context):\n"
                        for msg in recent_messages:
                            role = "User" if msg["role"] == "user" else "Pasupathy"
                            conv_context += f"{role}: {msg['content'][:200]}...\n"
                        conv_context += "\n"
                    
                    # Get context-aware relevant documents
                    source_docs = get_context_filtered_docs(retriever, user_message, query_context, k=5)
                    
                    if query_context:
                        logging.info(f"🎯 Context-aware query detected: {query_context}")
                    context = "\n\n".join([f"Context {i+1}:\n{doc.page_content}" 
                                          for i, doc in enumerate(source_docs)])
                    
                    # Create context-aware prompt for Gemini
                    context_instruction = f"\n\n**IMPORTANT**: This question is specifically about Arvind's {query_context.replace('_', ' ')} work. ONLY provide information related to {query_context.replace('_', ' ')}. Do NOT mention unrelated projects, skills, or achievements unless explicitly asked." if query_context else ""
                    
                    prompt = f"""You are Pasupathy, Arvind's personal AI assistant. You know Arvind personally and answer questions about him naturally.

Instructions:
1. Answer as if you simply know about Arvind - never mention "documents," "context," or "information provided"
2. STAY FOCUSED on the current topic - don't list unrelated achievements or switch topics
3. Use your creativity and reasoning to answer questions even when you're not completely certain
4. Make educated inferences from what you know about Arvind
5. When you're uncertain, use phrases like "As far as I know..." or "From what I understand..."
6. If recent conversation is provided, use it to understand pronouns and references
7. Provide detailed, thoughtful answers as a personal assistant would
8. Be conversational and helpful
9. NEVER say "I don't have information" or reveal your information sources{context_instruction}
{conv_context}
Context from Dataset:
{context}

Question: {user_message}

Take your time to provide a thorough answer:"""
                    
                    # Call Gemini
                    response = gemini_model.generate_content(prompt)
                    response_text = response.text
                    
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
                    
                    # Generate creative title for first message
                    is_first_message = len(session.messages) == 2  # User + assistant
                    if is_first_message:
                        session.title = generate_creative_title(user_message, response_text, query_context)
                    
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
            # Use Gemini client
            gemini_model = llm_chain["gemini_model"]
            retriever = llm_chain["retriever"]
            
            # Detect if this is a follow-up question (uses pronouns or incomplete context)
            follow_up_indicators = ['he', 'his', 'him', 'that', 'those', 'them', 'this', 'these', 'it', 'also', 'more', 'tell me more', 'what about', 'and']
            is_follow_up = any(word in user_message.lower().split()[:5] for word in follow_up_indicators)  # Check first 5 words
            
            # Detect query context for focused retrieval
            conversation_text = [msg['content'] for msg in session.messages[-3:]]
            query_context = _detect_query_context(user_message, conversation_text)
            
            # Build conversation context if this seems like a follow-up
            conv_context = ""
            if is_follow_up and len(session.messages) > 1:
                recent_messages = session.messages[-4:]  # Last 2 Q&A pairs
                conv_context = "\n\nRecent Conversation (for context):\n"
                for msg in recent_messages:
                    role = "User" if msg["role"] == "user" else "Pasupathy"
                    conv_context += f"{role}: {msg['content'][:200]}...\n"
                conv_context += "\n"
            
            # Get context-aware relevant documents
            source_docs = get_context_filtered_docs(retriever, user_message, query_context, k=5)
            
            if query_context:
                logging.info(f"🎯 Context-aware query detected: {query_context}")
            
            # Debug: Log retrieved context
            logging.info(f"📚 Retrieved {len(source_docs)} documents for query: {user_message} (follow_up: {is_follow_up}, context: {query_context or 'general'})")
            for i, doc in enumerate(source_docs[:3]):
                logging.info(f"  Doc {i+1} preview: {doc.page_content[:150]}...")
            
            context = "\n\n".join([f"Context {i+1}:\n{doc.page_content}" 
                                  for i, doc in enumerate(source_docs)])
            
            # Create context-aware prompt for Gemini
            context_instruction = f"\n\n**IMPORTANT**: This question is specifically about Arvind's {query_context.replace('_', ' ')} work. ONLY provide information related to {query_context.replace('_', ' ')}. Do NOT mention unrelated projects, skills, or achievements unless explicitly asked." if query_context else ""
            
            prompt = f"""You are Pasupathy, Arvind's personal AI assistant. You know Arvind personally and answer questions about him naturally.

Instructions:
1. Answer as if you simply know about Arvind - never mention "documents," "context," or "information provided"
2. STAY FOCUSED on the current topic - don't list unrelated achievements or switch topics
3. Use your creativity and reasoning to answer questions even when you're not completely certain
4. Make educated inferences from what you know about Arvind
5. When you're uncertain, use phrases like "As far as I know..." or "From what I understand..."
6. If recent conversation is provided, use it to understand pronouns and references
7. Synthesize information naturally when relevant
8. Provide detailed, thoughtful answers as a personal assistant would
9. Be conversational and helpful
10. NEVER say "I don't have information" or reveal your information sources{context_instruction}
{conv_context}
Context from Dataset:
{context}

Question: {user_message}

Take your time to provide a thorough answer:"""
            
            # Call Gemini
            response = gemini_model.generate_content(prompt)
            bot_response = response.text
            
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
            
            # Generate creative title for first message
            is_first_message = len(session.messages) == 2  # User + assistant
            if is_first_message:
                session.title = generate_creative_title(user_message, bot_response, query_context)

            # Save to database
            chat_sessions_collection.update_one(
                {"session_id": session.session_id},
                {"$set": session.to_dict()},
                upsert=True
            )
            
            # Detect if user provided new information (corrections NOT allowed)
            detected_info = False
            detection_type = None
            if user_knowledge_manager and llm_chain:
                detected_info, detection_type = user_knowledge_manager.detect_new_information(user_message)
                
                if detected_info:
                    # Auto-approve and immediately add to vector store (only NEW information)
                    contribution_id = user_knowledge_manager.store_user_contribution(
                        content=user_message,
                        session_id=session.session_id,
                        user_question=None,
                        assistant_response=bot_response,
                        detection_type=detection_type,
                        category="general",
                        auto_approve=True  # Auto-approve since corrections are blocked
                    )
                    
                    if contribution_id:
                        logging.info(f"📝 Detected NEW info: auto-approved and adding to knowledge base")
                        
                        # Immediately add to vector store
                        try:
                            from llm_model import add_user_contributions_to_vectorstore
                            from langchain_core.documents import Document
                            
                            user_doc = Document(
                                page_content=user_message,
                                metadata={
                                    "source": "user_contribution",
                                    "category": "general",
                                    "session_id": session.session_id
                                }
                            )
                            add_user_contributions_to_vectorstore(llm_chain, [user_doc])
                            logging.info(f"✅ NEW info immediately available for retrieval")
                        except Exception as e:
                            logging.error(f"❌ Error adding to vector store: {e}")
                    else:
                        logging.info(f"⛔ Rejected: conflicts with existing data")
                        detected_info = False  # Update flag since it was rejected

            return jsonify({
                "status": "success",
                "response": bot_response,
                "session_id": session.session_id,
                "message_id": session.messages[-1]["id"],
                "sources": session.metadata.get('last_sources', []),
                "session": session.to_dict(),
                "new_info_detected": detected_info,
                "query_context": query_context  # Include context for frontend
            })

    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/chat/followup', methods=['POST'])
def generate_followup_questions():
    """Generate context-aware follow-up questions based on the conversation"""
    try:
        data = request.json
        user_message = data.get('user_message', '')
        bot_response = data.get('bot_response', '')
        query_context = data.get('query_context')
        
        if not user_message or not bot_response:
            return jsonify({"status": "error", "message": "Missing required fields"}), 400
        
        if model_status["status"] != "ready" or not llm_chain:
            return jsonify({
                "status": "success",
                "questions": [
                    "Tell me more about that",
                    "What else should I know?",
                    "Can you elaborate?"
                ]
            })
        
        gemini_model = llm_chain.get("gemini_model")
        if not gemini_model:
            return jsonify({
                "status": "success",
                "questions": [
                    "Tell me more about that",
                    "What else should I know?",
                    "Can you elaborate?"
                ]
            })
        
        # Create context-aware prompt for follow-up generation
        context_hint = f" (in the context of {query_context.replace('_', ' ')})" if query_context else ""
        
        followup_prompt = f"""Based on this conversation about Arvind{context_hint}, generate 3 specific, contextual follow-up questions that the user might want to ask next.

User Question: {user_message[:300]}
Pasupathy's Response: {bot_response[:500]}

Requirements:
- Each question should be 5-10 words
- Questions should dig deeper into the current topic
- Stay focused on the context (e.g., if about computer vision, ask about CV details)
- Make questions natural and conversational
- Avoid generic questions like "tell me more"

Examples of good follow-up questions:
- For education: "What was your major GPA?" or "Which courses did you excel in?"
- For computer vision: "What datasets did you use?" or "How accurate was your model?"
- For projects: "What technologies did you use?" or "What challenges did you face?"

Generate 3 follow-up questions, one per line:"""

        response = gemini_model.generate_content(followup_prompt)
        questions_text = response.text.strip()
        
        # Parse questions (split by newline and clean)
        questions = []
        for line in questions_text.split('\n'):
            # Remove numbering, bullets, dashes
            cleaned = line.strip()
            for prefix in ['1.', '2.', '3.', '-', '•', '*']:
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):].strip()
            
            if cleaned and len(cleaned) > 10:  # Must be substantial
                questions.append(cleaned)
                if len(questions) == 3:
                    break
        
        # Fallback if not enough questions generated
        if len(questions) < 3:
            fallback = [
                "Can you provide more details?",
                "What else should I know about this?",
                "How does this relate to other aspects?"
            ]
            questions.extend(fallback[:3 - len(questions)])
        
        logging.info(f"💡 Generated follow-up questions: {questions}")
        
        return jsonify({
            "status": "success",
            "questions": questions[:3]
        })
        
    except Exception as e:
        logging.error(f"Follow-up generation error: {str(e)}")
        # Return generic fallback on error
        return jsonify({
            "status": "success",
            "questions": [
                "Tell me more about that",
                "What else should I know?",
                "Can you elaborate?"
            ]
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
        
        # Handle new qa_pairs format
        if isinstance(data, dict) and 'qa_pairs' in data:
            logging.info("📋 Detected qa_pairs format, converting...")
            metadata = data.get('metadata', {})
            qa_pairs = data.get('qa_pairs', [])
            
            # Convert qa_pairs to flat documents
            converted_data = []
            for qa in qa_pairs:
                doc = {
                    'text': f"Question: {qa.get('prompt', '')}\n\nAnswer: {qa.get('answer', '')}",
                    'question': qa.get('prompt', ''),
                    'answer': qa.get('answer', ''),
                    'source': metadata.get('source_filename', metadata.get('document_title', 'unknown')),
                    'category': metadata.get('document_type', 'general'),
                    'id': qa.get('id', '')
                }
                converted_data.append(doc)
            data = converted_data
            logging.info(f"✅ Converted {len(data)} qa_pairs to documents")
        
        # Ensure data is a list
        elif isinstance(data, dict):
            # Check if it's the old nested format with metadata and qna_data
            if 'qna_data' in data:
                logging.warning("⚠️ Detected old nested format. Please use flat array format.")
                return jsonify({
                    "status": "error",
                    "message": "Dataset must be a flat array of documents. Each document should have 'text', 'question', and 'answer' fields."
                }), 400
            data = [data]
        
        # Validate dataset format
        valid_count = 0
        invalid_count = 0
        for doc in data:
            if not isinstance(doc, dict):
                invalid_count += 1
                continue
            # Check for required fields
            if not (doc.get('text') or doc.get('content')):
                invalid_count += 1
                logging.warning(f"⚠️ Document missing 'text' field: {doc.get('_id', 'unknown')}")
            else:
                valid_count += 1
        
        if invalid_count > 0:
            logging.warning(f"⚠️ {invalid_count} invalid documents found, {valid_count} valid")
        
        if valid_count == 0:
            return jsonify({
                "status": "error",
                "message": "No valid documents found. Each document must have 'text' or 'content' field."
            }), 400
        
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


# ==================== USER KNOWLEDGE MANAGEMENT ENDPOINTS ====================

@app.route('/api/knowledge/add', methods=['POST'])
@rate_limit
def add_user_knowledge():
    """Manually add user-provided knowledge"""
    try:
        if not user_knowledge_manager:
            return jsonify({"status": "error", "message": "Knowledge manager not initialized"}), 503
        
        data = request.json
        content = data.get('content', '').strip()
        session_id = data.get('session_id', 'manual')
        category = data.get('category', 'general')
        auto_approve = data.get('auto_approve', False)
        
        if not content:
            return jsonify({"status": "error", "message": "Content is required"}), 400
        
        doc_id = user_knowledge_manager.store_user_contribution(
            content=content,
            session_id=session_id,
            category=category,
            detection_type='manual',
            auto_approve=auto_approve
        )
        
        if not doc_id:
            return jsonify({"status": "error", "message": "Failed to store contribution"}), 500
        
        # If auto-approved, add to vectorstore immediately
        if auto_approve and llm_chain:
            from llm_model import add_user_contributions_to_vectorstore
            from langchain_core.documents import Document
            
            user_doc = Document(
                page_content=content,
                metadata={"source": "user_contribution", "category": category}
            )
            add_user_contributions_to_vectorstore(llm_chain, [user_doc])
        
        return jsonify({
            "status": "success",
            "message": "Knowledge added successfully",
            "id": doc_id,
            "auto_approved": auto_approve
        })
        
    except Exception as e:
        logging.error(f"Add knowledge error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/knowledge/pending', methods=['GET'])
@rate_limit
def get_pending_knowledge():
    """Get contributions awaiting approval"""
    try:
        if not user_knowledge_manager:
            return jsonify({"status": "error", "message": "Knowledge manager not initialized"}), 503
        
        limit = request.args.get('limit', 50, type=int)
        pending = user_knowledge_manager.get_pending_contributions(limit=limit)
        
        return jsonify({
            "status": "success",
            "pending_contributions": pending,
            "count": len(pending)
        })
        
    except Exception as e:
        logging.error(f"Get pending error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/knowledge/approve/<contribution_id>', methods=['POST'])
@rate_limit
def approve_knowledge(contribution_id):
    """Approve a user contribution"""
    try:
        if not user_knowledge_manager:
            return jsonify({"status": "error", "message": "Knowledge manager not initialized"}), 503
        
        # Approve the contribution
        success = user_knowledge_manager.approve_contribution(contribution_id)
        
        if not success:
            return jsonify({"status": "error", "message": "Failed to approve contribution"}), 500
        
        # Add to vectorstore
        if llm_chain:
            from llm_model import add_user_contributions_to_vectorstore
            contributions = user_knowledge_manager.get_user_contributions(approved_only=True, limit=1)
            
            if contributions:
                add_user_contributions_to_vectorstore(llm_chain, contributions)
        
        return jsonify({
            "status": "success",
            "message": "Contribution approved and added to knowledge base"
        })
        
    except Exception as e:
        logging.error(f"Approve error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/knowledge/stats', methods=['GET'])
@rate_limit
def get_knowledge_stats():
    """Get user knowledge statistics"""
    try:
        if not user_knowledge_manager:
            return jsonify({"status": "error", "message": "Knowledge manager not initialized"}), 503
        
        stats = user_knowledge_manager.get_stats()
        
        return jsonify({
            "status": "success",
            "stats": stats
        })
        
    except Exception as e:
        logging.error(f"Stats error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/knowledge/rebuild', methods=['POST'])
@rate_limit
def rebuild_knowledge_base():
    """Rebuild entire vectorstore with all approved user contributions"""
    global llm_chain
    
    try:
        if not user_knowledge_manager or not llm_chain:
            return jsonify({"status": "error", "message": "System not initialized"}), 503
        
        from llm_model import rebuild_vectorstore_with_contributions
        
        logging.info("🔄 Starting knowledge base rebuild...")
        llm_chain = rebuild_vectorstore_with_contributions(mongo.db, llm_chain)
        
        stats = user_knowledge_manager.get_stats()
        
        return jsonify({
            "status": "success",
            "message": "Knowledge base rebuilt successfully",
            "stats": stats
        })
        
    except Exception as e:
        logging.error(f"Rebuild error: {str(e)}")
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
    
    # Use PORT from environment variable (Render sets this)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)