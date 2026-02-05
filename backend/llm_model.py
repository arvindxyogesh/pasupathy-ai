import os
import json
import threading
import numpy as np
from flask_pymongo import PyMongo
from sentence_transformers import SentenceTransformer
import faiss
# LangChain and Gemini imports
from langchain_community.vectorstores import FAISS as LCFAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import google.generativeai as genai
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from config import (
    CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL, 
    SEARCH_K, GOOGLE_API_KEY, GEMINI_MODEL, TEMPERATURE
)
import logging
from typing import List, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

def _detect_context_tags(text):
    """Auto-detect context tags from text content for filtering"""
    text_lower = text.lower()
    
    context_keywords = {
        'computer_vision': ['computer vision', 'cv', 'object detection', 'yolo', 'image processing', 'opencv', 'cnn', 'rcnn', 'segmentation', 'face detection', 'tracking'],
        'machine_learning': ['machine learning', 'ml', 'deep learning', 'neural network', 'tensorflow', 'pytorch', 'model training', 'classification', 'regression'],
        'robotics': ['robot', 'robotics', 'autonomous', 'navigation', 'ros', 'arduino', 'sensor', 'actuator'],
        'education': ['education', 'degree', 'university', 'college', 'gpa', 'course', 'academic', 'studied', 'graduated'],
        'experience': ['experience', 'intern', 'work', 'job', 'company', 'role', 'position', 'worked at', 'employed'],
        'projects': ['project', 'developed', 'built', 'created', 'implemented', 'designed', 'application'],
        'skills': ['skill', 'proficient', 'programming', 'language', 'framework', 'tool', 'python', 'javascript', 'react'],
        'research': ['research', 'paper', 'publication', 'study', 'analysis', 'experiment'],
        'achievements': ['award', 'achievement', 'recognition', 'certificate', 'win', 'winner', 'competition'],
        'nlp': ['nlp', 'natural language', 'text processing', 'sentiment', 'chatbot', 'language model'],
        'web_development': ['web', 'website', 'frontend', 'backend', 'api', 'react', 'flask', 'django'],
        'data_science': ['data science', 'data analysis', 'visualization', 'pandas', 'numpy', 'analytics']
    }
    
    detected_tags = []
    for tag, keywords in context_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            detected_tags.append(tag)
    
    return detected_tags if detected_tags else ['general']

def _detect_query_context(query, conversation_history=None):
    """Detect the contextual domain of a query"""
    query_lower = query.lower()
    
    context_patterns = {
        'computer_vision': ['computer vision', 'cv', 'object detection', 'yolo', 'image', 'vision', 'detect', 'tracking', 'opencv'],
        'machine_learning': ['machine learning', 'ml', 'deep learning', 'model', 'training', 'neural', 'ai'],
        'robotics': ['robot', 'robotics', 'autonomous', 'navigation', 'ros', 'sensor'],
        'education': ['education', 'degree', 'university', 'study', 'academic', 'gpa', 'college', 'school'],
        'experience': ['experience', 'work', 'intern', 'job', 'company', 'worked'],
        'projects': ['project', 'built', 'developed', 'created', 'application'],
        'skills': ['skill', 'programming', 'language', 'framework', 'proficient', 'know'],
        'research': ['research', 'paper', 'publication', 'study'],
        'achievements': ['award', 'achievement', 'win', 'certificate', 'competition'],
        'nlp': ['nlp', 'natural language', 'text', 'chatbot', 'language model'],
        'web_development': ['web', 'website', 'frontend', 'backend', 'api', 'development'],
        'data_science': ['data', 'analysis', 'analytics', 'visualization']
    }
    
    # Check conversation history for context continuity
    if conversation_history:
        recent_text = ' '.join(conversation_history[-3:]).lower()
        for context, keywords in context_patterns.items():
            if any(keyword in recent_text for keyword in keywords):
                # Check if current query is a follow-up (doesn't specify new context)
                follow_up_indicators = ['more', 'also', 'what about that', 'tell me more', 'and', 'his', 'that', 'those']
                if any(indicator in query_lower for indicator in follow_up_indicators):
                    return context
    
    # Check current query
    for context, keywords in context_patterns.items():
        if any(keyword in query_lower for keyword in keywords):
            return context
    
    return None

def get_context_filtered_docs(retriever, query, context_filter=None, k=5):
    """Retrieve documents with optional context filtering"""
    try:
        # Get more candidates for filtering
        all_docs = retriever.get_relevant_documents(query)
        
        if not context_filter or not all_docs:
            return all_docs[:k]
        
        # Filter by context tags
        filtered_docs = []
        for doc in all_docs:
            metadata = doc.metadata
            context_tags = metadata.get('context_tags', [])
            
            # Match if context is in tags or in other metadata
            if (context_filter in context_tags or 
                context_filter in str(metadata.get('category', '')).lower() or
                context_filter in str(metadata.get('subcategory', '')).lower()):
                filtered_docs.append(doc)
                if len(filtered_docs) >= k:
                    break
        
        # If not enough context-specific docs, add high-relevance docs
        if len(filtered_docs) < k:
            for doc in all_docs:
                if doc not in filtered_docs:
                    filtered_docs.append(doc)
                    if len(filtered_docs) >= k:
                        break
        
        logging.info(f"🎯 Context filter '{context_filter}': {len(filtered_docs)} docs selected from {len(all_docs)} candidates")
        return filtered_docs
        
    except Exception as e:
        logging.error(f"Error in context filtering: {str(e)}")
        return retriever.get_relevant_documents(query)[:k]

def initialize_llm_model(db):
    """Initialize the AGENTIC RAG system with FAISS vector store and ReAct agent"""
    try:
        logging.info("🔄 Loading documents from MongoDB...")
        
        # Load documents from MongoDB dataset collection
        dataset_collection = db.dataset
        documents = list(dataset_collection.find())
        
        if not documents:
            logging.warning("⚠️ No documents found in dataset. RAG will return empty responses.")
            logging.warning("Upload data using POST /api/dataset/upload")
        
        # Convert MongoDB documents to LangChain Document objects
        text_docs = []
        for doc in documents:
            # Extract text content - handle different formats
            # Priority: text > prompt+answer > content > description
            if doc.get('text'):
                content = doc.get('text')
            elif doc.get('prompt') and doc.get('answer'):
                # Handle prompt/answer format
                content = f"Question: {doc.get('prompt')}\n\nAnswer: {doc.get('answer')}"
            elif doc.get('question') and doc.get('answer'):
                # Handle question/answer format
                content = f"Question: {doc.get('question')}\n\nAnswer: {doc.get('answer')}"
            else:
                content = doc.get('content') or doc.get('description') or str(doc)
            
            # Add comprehensive metadata with context tags for filtering
            metadata = {
                'source': doc.get('source', 'unknown'),
                'category': doc.get('category', 'general'),
                'subcategory': doc.get('subcategory', ''),
                'difficulty': doc.get('difficulty', ''),
                'question': doc.get('question') or doc.get('prompt', ''),
                'answer': doc.get('answer', ''),
                '_id': str(doc.get('_id', ''))
            }
            
            # Auto-detect context tags from content for better filtering
            metadata['context_tags'] = _detect_context_tags(content)
            
            # Remove empty metadata fields
            metadata = {k: v for k, v in metadata.items() if v}
            
            text_docs.append(Document(page_content=content, metadata=metadata))
        
        logging.info(f"📚 Loaded {len(text_docs)} documents")
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_documents(text_docs)
        logging.info(f"✂️ Split into {len(chunks)} chunks")
        
        # Create embeddings
        logging.info(f"🧠 Creating embeddings with {EMBEDDING_MODEL}...")
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL
        )
        
        # Check if FAISS index already exists
        faiss_index_path = "/app/faiss_index"
        if os.path.exists(faiss_index_path):
            logging.info("📂 Found existing FAISS index, loading from disk...")
            try:
                vectorstore = LCFAISS.load_local(
                    faiss_index_path, 
                    embeddings,
                    allow_dangerous_deserialization=True
                )
                logging.info("✅ FAISS index loaded successfully from disk!")
            except Exception as e:
                logging.warning(f"⚠️ Failed to load FAISS index: {str(e)}. Rebuilding...")
                vectorstore = None
        else:
            vectorstore = None
        
        # Build FAISS vector store if not loaded
        if vectorstore is None:
            logging.info("🗄️ Building FAISS vector store...")
            if chunks:
                vectorstore = LCFAISS.from_documents(chunks, embeddings)
                # Save to disk for future use
                logging.info("💾 Saving FAISS index to disk...")
                vectorstore.save_local(faiss_index_path)
                logging.info("✅ FAISS index saved successfully!")
            else:
                # Create empty vectorstore if no documents
                vectorstore = LCFAISS.from_texts(["No data available"], embeddings)
                logging.warning("⚠️ Created empty vector store")
        
        # Initialize Google Gemini client
        logging.info(f"🤖 Initializing Gemini ({GEMINI_MODEL})...")
        genai.configure(api_key=GOOGLE_API_KEY)
        gemini_model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Create retriever with MMR (Maximum Marginal Relevance) for diversity
        retriever = vectorstore.as_retriever(
            search_type="mmr",  # Use MMR instead of pure similarity
            search_kwargs={
                "k": SEARCH_K,
                "fetch_k": SEARCH_K * 3,  # Fetch more candidates
                "lambda_mult": 0.7  # Balance between relevance and diversity
            }
        )
        
        # ============= SIMPLE RAG WITHOUT AGENT (due to proxy issues) =============
        # We'll use direct OpenAI calls instead of LangChain's ChatOpenAI wrapper
        
        logging.info("✅ RAG system initialized successfully with Gemini!")
        
        return {
            "gemini_model": gemini_model,
            "retriever": retriever,
            "vectorstore": vectorstore,
            "model_name": GEMINI_MODEL,
            "is_agentic": False
        }
        
    except Exception as e:
        logging.error(f"❌ Error initializing LLM model: {str(e)}")
        raise

def get_retriever_context(qa_chain, query, k=3):
    """Get relevant context from vector store without generating answer"""
    try:
        retriever = qa_chain.get('retriever')
        if not retriever:
            return "", []
        docs = retriever.get_relevant_documents(query)[:k]
        context = "\n\n".join([doc.page_content for doc in docs])
        sources = [doc.metadata.get('source', 'unknown') for doc in docs]
        return context, sources
    except Exception as e:
        logging.error(f"Error retrieving context: {str(e)}")
        return "", []


def add_user_contributions_to_vectorstore(qa_chain, user_documents: List[Document]):
    """
    Add user-contributed documents to the existing FAISS vectorstore
    
    Args:
        qa_chain: The QA chain dict with vectorstore
        user_documents: List of LangChain Document objects from user contributions
    
    Returns:
        bool: Success status
    """
    try:
        if not user_documents:
            logging.info("No user contributions to add")
            return True
        
        vectorstore = qa_chain.get('vectorstore')
        if not vectorstore:
            logging.error("No vectorstore found in qa_chain")
            return False
        
        logging.info(f"➕ Adding {len(user_documents)} user contributions to vectorstore...")
        
        # Add documents to existing vectorstore
        vectorstore.add_documents(user_documents)
        
        # Save updated index to disk
        faiss_index_path = "/app/faiss_index"
        vectorstore.save_local(faiss_index_path)
        logging.info("✅ User contributions added and index saved!")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error adding user contributions: {e}")
        return False


def rebuild_vectorstore_with_contributions(db, qa_chain):
    """
    Rebuild entire vectorstore including original data + user contributions
    Use this for periodic full refreshes
    
    Args:
        db: MongoDB database connection
        qa_chain: Current QA chain to update
    
    Returns:
        Updated qa_chain dict
    """
    try:
        logging.info("🔄 Rebuilding vectorstore with user contributions...")
        
        # Load original documents from dataset
        dataset_collection = db.dataset
        documents = list(dataset_collection.find())
        
        text_docs = []
        for doc in documents:
            if doc.get('text'):
                content = doc.get('text')
            elif doc.get('prompt') and doc.get('answer'):
                content = f"Question: {doc.get('prompt')}\n\nAnswer: {doc.get('answer')}"
            elif doc.get('question') and doc.get('answer'):
                content = f"Question: {doc.get('question')}\n\nAnswer: {doc.get('answer')}"
            elif doc.get('content'):
                content = doc.get('content')
            else:
                continue
            
            metadata = {
                "source": doc.get('source', 'dataset'),
                "category": doc.get('category', 'general')
            }
            text_docs.append(Document(page_content=content, metadata=metadata))
        
        # Add user contributions
        user_knowledge_collection = db.user_knowledge
        user_docs = list(user_knowledge_collection.find({"approved": True}))
        
        for doc in user_docs:
            content = doc["content"]
            if doc.get("user_question"):
                content = f"Question: {doc['user_question']}\n\nAnswer: {content}"
            
            metadata = {
                "source": "user_contribution",
                "category": doc.get("category", "general"),
                "created_at": doc.get("created_at")
            }
            text_docs.append(Document(page_content=content, metadata=metadata))
        
        logging.info(f"📚 Total documents: {len(text_docs)} (including {len(user_docs)} user contributions)")
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_documents(text_docs)
        
        # Create embeddings
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        
        # Build new vectorstore
        vectorstore = LCFAISS.from_documents(chunks, embeddings)
        
        # Save to disk
        faiss_index_path = "/app/faiss_index"
        vectorstore.save_local(faiss_index_path)
        
        # Update retriever
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": SEARCH_K,
                "fetch_k": SEARCH_K * 3,
                "lambda_mult": 0.7
            }
        )
        
        # Update qa_chain
        qa_chain['vectorstore'] = vectorstore
        qa_chain['retriever'] = retriever
        
        logging.info("✅ Vectorstore rebuilt successfully with user contributions!")
        return qa_chain
        
    except Exception as e:
        logging.error(f"❌ Error rebuilding vectorstore: {e}")
        return qa_chain

