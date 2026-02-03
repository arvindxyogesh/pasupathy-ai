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
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from config import (
    CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL, 
    SEARCH_K, GOOGLE_API_KEY, GEMINI_MODELS, TEMPERATURE
)
import logging
from typing import List, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document

logger = logging.getLogger(__name__)

def initialize_llm_model(db):
    """Initialize the RAG system with FAISS vector store"""
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
            # Extract text content from various possible fields
            content = doc.get('text') or doc.get('content') or doc.get('description') or str(doc)
            # Add metadata
            metadata = {
                'source': doc.get('source', 'unknown'),
                'category': doc.get('category', 'general'),
                '_id': str(doc.get('_id', ''))
            }
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
                vectorstore = LCFAISS.load_local(faiss_index_path, embeddings)
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
        
        # Initialize Gemini LLM
        logging.info(f"🤖 Initializing Gemini ({GEMINI_MODELS[0]})...")
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODELS[0],
            google_api_key=GOOGLE_API_KEY,
            temperature=TEMPERATURE
        )
        
        # Create retriever
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": SEARCH_K}
        )
        
        # Create custom prompt template for Pasupathy
        prompt_template = ChatPromptTemplate.from_template(
            """You are Pasupathy, Arvind's personal AI assistant. Use the following context about Arvind to answer the question accurately and personally.

Context from Arvind's knowledge base:
{context}

Question: {question}

Instructions:
- Answer as if you are speaking on behalf of Arvind
- Use first-person pronouns when referring to Arvind ("I", "my", "me")
- If the context doesn't contain relevant information, say "I don't have that information in my knowledge base"
- Be conversational but informative
- Keep responses concise and relevant

Answer:"""
        )
        
        # Create RAG chain using LCEL
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt_template
            | llm
            | StrOutputParser()
        )
        
        logging.info("✅ RAG system initialized successfully!")
        return {"chain": rag_chain, "retriever": retriever}
        
    except Exception as e:
        logging.error(f"❌ Error initializing LLM model: {str(e)}")
        raise

def get_retriever_context(qa_chain, query, k=3):
    """Get relevant context from vector store without generating answer"""
    try:
        retriever = qa_chain.retriever
        docs = retriever.get_relevant_documents(query)[:k]
        context = "\n\n".join([doc.page_content for doc in docs])
        sources = [doc.metadata.get('source', 'unknown') for doc in docs]
        return context, sources
    except Exception as e:
        logging.error(f"Error retrieving context: {str(e)}")
        return "", []