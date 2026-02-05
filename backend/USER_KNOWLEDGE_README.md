# User Knowledge Learning System

## Overview
Pasupathy now includes a reinforcement learning system that captures and learns from NEW information provided by users. **Corrections to existing data are NOT allowed** - only additions.

## How It Works

### 1. Automatic Detection
The system automatically detects when users provide new information using patterns like:
- "FYI, Arvind also likes..."
- "By the way, he recently started..."
- "You should know that..."
- "Another thing about Arvind..."

### 2. Conflict Prevention
The system prevents modifications to existing core data:
- ❌ **NOT ALLOWED**: "Actually, his father's name is..." (father already in database)
- ❌ **NOT ALLOWED**: "No, he was born in..." (birthplace already in database)
- ✅ **ALLOWED**: "Arvind also likes playing chess" (new interest)
- ✅ **ALLOWED**: "He recently joined a robotics club" (new activity)

### 3. Protected Entities
These core facts cannot be modified:
- Father's name
- Mother's name
- Brother's name
- Birthdate and birthplace
- University names
- Other biographical data already in the database

### 4. Approval Workflow
1. User provides new information in chat
2. System detects and stores it as "pending"
3. Admin reviews pending contributions
4. Approved contributions are added to knowledge base
5. Future queries will include this new information

## API Endpoints

### Add New Information Manually
```bash
POST /api/knowledge/add
{
  "content": "Arvind recently started learning Spanish",
  "category": "hobbies",
  "auto_approve": false
}
```

### View Pending Contributions
```bash
GET /api/knowledge/pending?limit=50
```

### Approve a Contribution
```bash
POST /api/knowledge/approve/<contribution_id>
```

### Get Statistics
```bash
GET /api/knowledge/stats
```

### Rebuild Knowledge Base (after approvals)
```bash
POST /api/knowledge/rebuild
```

## Example Usage

### Conversation Example 1 (Allowed)
**User**: "FYI, Arvind also enjoys playing basketball"
**System**: ✅ Detected NEW info, stored for review
**Result**: Stored in pending contributions

### Conversation Example 2 (Blocked)
**User**: "Actually, his father's name is Kumar"
**System**: ⛔ Blocked - cannot modify existing father information
**Result**: Not stored, existing data protected

### Conversation Example 3 (Allowed)
**User**: "He recently joined the Ann Arbor hiking club"
**System**: ✅ Detected NEW info, stored for review
**Result**: Stored in pending contributions

## MongoDB Collections

### user_knowledge
Stores all user contributions:
- `content`: The new information
- `session_id`: Chat session where it was provided
- `detection_type`: How it was detected ('new_info', 'manual')
- `category`: Category of information
- `approved`: Boolean flag for approval status
- `used_count`: How many times retrieved in responses
- `created_at`: Timestamp
- `source`: Always "user_contribution"

## Best Practices

1. **Review Regularly**: Check pending contributions daily
2. **Verify Accuracy**: Ensure new info is correct before approving
3. **Rebuild After Batch Approvals**: Use rebuild endpoint after approving multiple items
4. **Monitor Stats**: Check statistics to see most-used contributions

## Technical Details

### Detection Patterns
```python
# Allowed new info patterns
- "remember", "note", "keep in mind"
- "you should know", "for future reference"
- "also", "additionally", "by the way"
- "fun fact", "interesting fact"

# Blocked correction patterns
- "actually", "no", "not", "wrong"
- "let me correct", "the real", "the actual"
```

### Conflict Checking
The system checks new content against fixed entities:
- Extracts entity types (father, mother, birthdate, etc.)
- Compares against known values
- Rejects if trying to redefine existing entities

## Future Enhancements
- [ ] Semantic similarity checking for duplicates
- [ ] Auto-categorization of contributions
- [ ] Confidence scoring for auto-approval
- [ ] User feedback loop for quality improvement
