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
            
            # Add comprehensive metadata for better retrieval and context
            metadata = {
                'source': doc.get('source', 'unknown'),
                'category': doc.get('category', 'general'),
                'subcategory': doc.get('subcategory', ''),
                'difficulty': doc.get('difficulty', ''),
                'question': doc.get('question') or doc.get('prompt', ''),
                'answer': doc.get('answer', ''),
                '_id': str(doc.get('_id', ''))
            }
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
