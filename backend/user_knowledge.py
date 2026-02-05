"""
User Knowledge Management System
Captures and stores user-provided NEW information only (NO CORRECTIONS ALLOWED)
"""
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class UserKnowledgeManager:
    """Manages user-contributed NEW knowledge (blocks corrections to existing data)"""
    
    # Patterns for NEW information provision only
    INFO_PROVISION_PATTERNS = [
        r'^(remember|note|keep in mind|fyi|btw)',
        r'(you should know|for future reference)',
        r'^(here\'?s? some info|some information)',
        r'(let me tell you|i want to tell you)',
        r'^(also|additionally|by the way|another thing)',
        r'(fun fact|interesting fact|did you know)',
    ]
    
    def __init__(self, db):
        """Initialize with MongoDB database connection"""
        self.db = db
        self.user_knowledge_collection = db.user_knowledge
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create indexes for user knowledge collection"""
        try:
            self.user_knowledge_collection.create_index([("created_at", -1)])
            self.user_knowledge_collection.create_index([("category", 1)])
            self.user_knowledge_collection.create_index([("approved", 1)])
        except Exception as e:
            logger.warning(f"Could not create indexes: {e}")
    
    def detect_new_information(self, user_message: str, context: List[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Detect if user is providing NEW information (corrections NOT allowed)
        
        Returns:
            Tuple[bool, Optional[str]]: (is_new_info, detection_type)
        """
        message_lower = user_message.lower().strip()
        
        # Block correction attempts
        correction_blocklist = [
            r'^(no|nope|not|wrong|incorrect|actually|correction)',
            r'(not true|that\'?s? wrong|that\'?s? incorrect)',
            r'(let me correct|to correct|fix that)',
            r'(the real|the actual|in reality)',
        ]
        
        for pattern in correction_blocklist:
            if re.search(pattern, message_lower, re.IGNORECASE):
                logger.info(f"⛔ Blocked correction attempt: {user_message[:50]}...")
                return False, None
        
        # Check for explicit NEW information provision
        for pattern in self.INFO_PROVISION_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True, 'new_info'
        
        # Check if message contains factual statements about new things
        new_info_patterns = [
            r'(arvind|he|his)\s+(also|recently|now|currently)',
            r'(new|latest|recent|another)\s+(project|skill|interest|hobby|friend)',
            r'(started|began|joined|learned)',
        ]
        
        for pattern in new_info_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                if not message_lower.strip().endswith('?'):
                    return True, 'new_info'
        
        return False, None
    
    def check_for_conflicts(self, content: str) -> Tuple[bool, Optional[str]]:
        """
        Check if the new information conflicts with existing database entries
        
        Returns:
            Tuple[bool, str]: (has_conflict, conflict_description)
        """
        try:
            content_lower = content.lower()
            
            # Check for known fixed entities that shouldn't be modified
            fixed_entities = {
                'father': ['suresh babu', 'suresh babu annamalai'],
                'mother': ['veeralakshmi', 'veeralakshmi suresh babu'],
                'brother': ['subash', 'subash niranjan'],
                'birthdate': ['april 1', '2003', 'april 1st 2003'],
                'birthplace': ['karaikudi'],
                'university': ['mit', 'madras institute of technology', 'university of michigan'],
            }
            
            # Check if content tries to redefine fixed entities
            for entity_type, known_values in fixed_entities.items():
                patterns = [
                    rf'{entity_type}\s+(is|was|:)\s+(\w+)',
                    rf'(his|arvind\'?s)\s+{entity_type}\s+(is|was)\s+(\w+)',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, content_lower, re.IGNORECASE)
                    if match:
                        provided_value = match.group(0).lower()
                        matches_known = any(val in provided_value for val in known_values)
                        
                        if not matches_known:
                            return True, f"Cannot modify existing {entity_type} information"
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error checking conflicts: {e}")
            return False, None
    
    def store_user_contribution(
        self,
        content: str,
        session_id: str,
        user_question: Optional[str] = None,
        assistant_response: Optional[str] = None,
        detection_type: str = 'manual',
        category: str = 'general',
        auto_approve: bool = False
    ) -> Optional[str]:
        """Store user-contributed NEW knowledge"""
        try:
            # Check for conflicts with existing database
            has_conflict, conflict_msg = self.check_for_conflicts(content)
            if has_conflict:
                logger.warning(f"⛔ Rejected contribution - {conflict_msg}: {content[:50]}...")
                return None
            
            doc = {
                "content": content,
                "session_id": session_id,
                "user_question": user_question,
                "assistant_response": assistant_response,
                "detection_type": detection_type,
                "category": category,
                "approved": auto_approve,
                "created_at": datetime.utcnow(),
                "used_count": 0,
                "source": "user_contribution"
            }
            
            result = self.user_knowledge_collection.insert_one(doc)
            logger.info(f"✅ Stored NEW info contribution: {content[:100]}...")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"❌ Error storing user contribution: {e}")
            return None
    
    def get_user_contributions(
        self,
        approved_only: bool = True,
        limit: int = None,
        category: str = None
    ) -> List[Document]:
        """Retrieve user contributions as LangChain Documents"""
        try:
            query = {}
            if approved_only:
                query["approved"] = True
            if category:
                query["category"] = category
            
            cursor = self.user_knowledge_collection.find(query).sort("created_at", -1)
            
            if limit:
                cursor = cursor.limit(limit)
            
            documents = []
            for doc in cursor:
                self.user_knowledge_collection.update_one(
                    {"_id": doc["_id"]},
                    {"$inc": {"used_count": 1}}
                )
                
                metadata = {
                    "source": "user_contribution",
                    "category": doc.get("category", "general"),
                    "created_at": doc.get("created_at"),
                    "detection_type": doc.get("detection_type", "manual"),
                    "used_count": doc.get("used_count", 0)
                }
                
                content = doc["content"]
                if doc.get("user_question"):
                    content = f"Question: {doc['user_question']}\n\nAnswer: {content}"
                
                documents.append(Document(page_content=content, metadata=metadata))
            
            logger.info(f"📚 Retrieved {len(documents)} user contributions")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Error retrieving user contributions: {e}")
            return []
    
    def approve_contribution(self, contribution_id: str) -> bool:
        """Approve a user contribution for use in RAG"""
        try:
            from bson import ObjectId
            result = self.user_knowledge_collection.update_one(
                {"_id": ObjectId(contribution_id)},
                {"$set": {"approved": True}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Error approving contribution: {e}")
            return False
    
    def get_pending_contributions(self, limit: int = 50) -> List[Dict]:
        """Get contributions awaiting approval"""
        try:
            cursor = self.user_knowledge_collection.find(
                {"approved": False}
            ).sort("created_at", -1).limit(limit)
            
            return [
                {
                    "id": str(doc["_id"]),
                    "content": doc["content"],
                    "user_question": doc.get("user_question"),
                    "detection_type": doc.get("detection_type"),
                    "created_at": doc.get("created_at"),
                    "session_id": doc.get("session_id")
                }
                for doc in cursor
            ]
        except Exception as e:
            logger.error(f"❌ Error fetching pending contributions: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get statistics about user contributions"""
        try:
            total = self.user_knowledge_collection.count_documents({})
            approved = self.user_knowledge_collection.count_documents({"approved": True})
            pending = self.user_knowledge_collection.count_documents({"approved": False})
            
            most_used = list(self.user_knowledge_collection.find(
                {"approved": True}
            ).sort("used_count", -1).limit(5))
            
            return {
                "total_contributions": total,
                "approved": approved,
                "pending_approval": pending,
                "most_used": [
                    {
                        "content": doc["content"][:100],
                        "used_count": doc.get("used_count", 0)
                    }
                    for doc in most_used
                ]
            }
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {}
