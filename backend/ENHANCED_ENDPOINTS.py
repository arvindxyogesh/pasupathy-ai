# Backend API Endpoints for Enhanced Features

## New endpoints to add to app.py:

# 1. Rename session
@app.route('/api/chat/sessions/<session_id>/rename', methods=['PUT'])
@rate_limit
def rename_session(session_id):
    """Rename a chat session"""
    try:
        data = request.get_json()
        new_title = data.get('title', '').strip()
        
        if not new_title:
            return jsonify({"status": "error", "message": "Title cannot be empty"}), 400
        
        result = chat_sessions_collection.update_one(
            {'session_id': session_id},
            {'$set': {
                'title': new_title,
                'updated_at': datetime.now().isoformat()
            }}
        )
        
        if result.modified_count > 0:
            return jsonify({"status": "success", "message": "Session renamed successfully"})
        else:
            return jsonify({"status": "error", "message": "Session not found"}), 404
            
    except Exception as e:
        logging.error(f"Error renaming session: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


# 2. Edit message in session
@app.route('/api/chat/sessions/<session_id>/messages/<message_id>/edit', methods=['PUT'])
@rate_limit
def edit_message(session_id, message_id):
    """Edit a specific message in a session"""
    try:
        data = request.get_json()
        new_content = data.get('content', '').strip()
        
        if not new_content:
            return jsonify({"status": "error", "message": "Content cannot be empty"}), 400
        
        session_data = chat_sessions_collection.find_one({'session_id': session_id})
        if not session_data:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        
        messages = session_data.get('messages', [])
        message_found = False
        
        for msg in messages:
            if msg['id'] == message_id:
                msg['content'] = new_content
                msg['edited'] = True
                msg['edited_at'] = datetime.now().isoformat()
                message_found = True
                break
        
        if not message_found:
            return jsonify({"status": "error", "message": "Message not found"}), 404
        
        chat_sessions_collection.update_one(
            {'session_id': session_id},
            {'$set': {
                'messages': messages,
                'updated_at': datetime.now().isoformat()
            }}
        )
        
        return jsonify({"status": "success", "message": "Message edited successfully", "messages": messages})
        
    except Exception as e:
        logging.error(f"Error editing message: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


# 3. Delete message from session
@app.route('/api/chat/sessions/<session_id>/messages/<message_id>', methods=['DELETE'])
@rate_limit
def delete_message(session_id, message_id):
    """Delete a specific message from a session"""
    try:
        session_data = chat_sessions_collection.find_one({'session_id': session_id})
        if not session_data:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        
        messages = session_data.get('messages', [])
        original_length = len(messages)
        messages = [m for m in messages if m['id'] != message_id]
        
        if len(messages) == original_length:
            return jsonify({"status": "error", "message": "Message not found"}), 404
        
        chat_sessions_collection.update_one(
            {'session_id': session_id},
            {'$set': {
                'messages': messages,
                'updated_at': datetime.now().isoformat()
            }}
        )
        
        return jsonify({"status": "success", "message": "Message deleted successfully"})
        
    except Exception as e:
        logging.error(f"Error deleting message: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


# 4. Search sessions
@app.route('/api/chat/sessions/search', methods=['GET'])
@rate_limit
def search_sessions():
    """Search sessions by title or message content"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({"status": "error", "message": "Search query required"}), 400
        
        # Search in titles and message content
        sessions = chat_sessions_collection.find({
            '$or': [
                {'title': {'$regex': query, '$options': 'i'}},
                {'messages.content': {'$regex': query, '$options': 'i'}}
            ]
        }).sort('updated_at', DESCENDING).limit(50)
        
        results = []
        for session in sessions:
            results.append({
                'session_id': session['session_id'],
                'title': session.get('title', 'New Chat'),
                'created_at': session.get('created_at'),
                'updated_at': session.get('updated_at'),
                'message_count': len(session.get('messages', []))
            })
        
        return jsonify({"status": "success", "results": results, "count": len(results)})
        
    except Exception as e:
        logging.error(f"Error searching sessions: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


# 5. Share session (generate public link)
@app.route('/api/chat/sessions/<session_id>/share', methods=['POST'])
@rate_limit
def share_session(session_id):
    """Generate a shareable link for a session"""
    try:
        session_data = chat_sessions_collection.find_one({'session_id': session_id})
        if not session_data:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        
        # Generate share token
        share_token = str(uuid.uuid4())
        share_url = f"/shared/{share_token}"
        
        # Store share mapping
        mongo.db.shared_sessions.update_one(
            {'session_id': session_id},
            {
                '$set': {
                    'share_token': share_token,
                    'shared_at': datetime.now().isoformat(),
                    'expires_at': (datetime.now() + dt.timedelta(days=30)).isoformat()
                }
            },
            upsert=True
        )
        
        return jsonify({
            "status": "success",
            "share_url": share_url,
            "share_token": share_token,
            "expires_at": (datetime.now() + dt.timedelta(days=30)).isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error sharing session: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


# 6. Export session to different formats
@app.route('/api/chat/sessions/<session_id>/export/<format>', methods=['GET'])
@rate_limit
def export_session_format(session_id, format):
    """Export session to PDF, TXT, or DOCX"""
    try:
        session_data = chat_sessions_collection.find_one({'session_id': session_id})
        if not session_data:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        
        messages = session_data.get('messages', [])
        title = session_data.get('title', 'New Chat')
        
        if format == 'txt':
            content = f"{title}\n{'='*50}\n\n"
            for msg in messages:
                role = "You" if msg['role'] == 'user' else "Pasupathy"
                content += f"{role}: {msg['content']}\n\n"
            
            return Response(
                content,
                mimetype='text/plain',
                headers={'Content-Disposition': f'attachment; filename="{title}.txt"'}
            )
        
        elif format == 'markdown':
            content = f"# {title}\n\n"
            for msg in messages:
                role = "You" if msg['role'] == 'user' else "Pasupathy"
                content += f"## {role}\n\n{msg['content']}\n\n---\n\n"
            
            return Response(
                content,
                mimetype='text/markdown',
                headers={'Content-Disposition': f'attachment; filename="{title}.md"'}
            )
        
        elif format == 'pdf':
            # For PDF, you'd need a library like reportlab or weasyprint
            return jsonify({"status": "error", "message": "PDF export requires additional setup"}), 501
        
        else:
            return jsonify({"status": "error", "message": "Unsupported format"}), 400
            
    except Exception as e:
        logging.error(f"Error exporting session: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


# 7. Get session statistics
@app.route('/api/chat/sessions/<session_id>/stats', methods=['GET'])
@rate_limit
def get_session_stats(session_id):
    """Get statistics for a session"""
    try:
        session_data = chat_sessions_collection.find_one({'session_id': session_id})
        if not session_data:
            return jsonify({"status": "error", "message": "Session not found"}), 404
        
        messages = session_data.get('messages', [])
        
        # Calculate stats
        total_messages = len(messages)
        user_messages = len([m for m in messages if m['role'] == 'user'])
        assistant_messages = len([m for m in messages if m['role'] == 'assistant'])
        
        # Estimate tokens (rough approximation)
        total_tokens = sum(len(m['content'].split()) for m in messages) * 1.3  # avg tokens per word
        
        # Calculate average response time if available
        timestamps = [datetime.fromisoformat(m['timestamp']) for m in messages]
        if len(timestamps) > 1:
            duration = (timestamps[-1] - timestamps[0]).total_seconds()
            avg_response_time = duration / assistant_messages if assistant_messages > 0 else 0
        else:
            avg_response_time = 0
        
        return jsonify({
            "status": "success",
            "stats": {
                "total_messages": total_messages,
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "estimated_tokens": int(total_tokens),
                "duration_seconds": duration if len(timestamps) > 1 else 0,
                "avg_response_time_seconds": avg_response_time,
                "created_at": session_data.get('created_at'),
                "updated_at": session_data.get('updated_at')
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting session stats: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


# 8. Update chat endpoint to accept settings
# Modify the existing chat endpoint to accept temperature, max_tokens, etc.
# The enhanced ChatInterface will send these as parameters

