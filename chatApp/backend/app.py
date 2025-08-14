import os
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from datetime import datetime
from werkzeug.utils import secure_filename
# NEW: Import our database helper functions
import database as db

# --- Initial Setup ---
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'averysecretkey!'
app.config['UPLOAD_FOLDER'] = 'uploads'
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# --- User Management ---
active_users = {}

def get_username_by_sid(sid):
    for username, session_id in active_users.items():
        if session_id == sid: return username
    return None

# --- SocketIO Event Handlers ---

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    username = get_username_by_sid(request.sid)
    if username and username in active_users:
        active_users.pop(username)
        print(f"User {username} has left")
        emit('update_user_list', list(active_users.keys()), broadcast=True)

@socketio.on('user_joined')
def handle_user_joined(username):
    active_users[username] = request.sid
    emit('update_user_list', list(active_users.keys()), broadcast=True)
    # NEW: Send chat history for the public room to the new user
    history = db.get_chat_history('public')
    emit('chat_history', {'room': 'public', 'history': history}, room=request.sid)

@socketio.on('message')
def handle_public_message(data):
    data['timestamp'] = datetime.now().isoformat()
    # NEW: Save public message to the database
    db.add_message('public', data['user'], text=data['text'], timestamp=data['timestamp'])
    emit('message', data, broadcast=True, include_self=False)

@socketio.on('start_private_chat')
def handle_start_private_chat(target_username):
    sender_username = get_username_by_sid(request.sid)
    target_sid = active_users.get(target_username)
    if target_sid and sender_username:
        room_name = '-'.join(sorted((sender_username, target_username)))
        join_room(room_name, sid=request.sid)
        join_room(room_name, sid=target_sid)
        
        # NEW: Send chat history for the private room
        history = db.get_chat_history(room_name)
        emit('chat_history', {'room': room_name, 'history': history}, room=request.sid)
        emit('chat_history', {'room': room_name, 'history': history}, room=target_sid)

        emit('private_chat_started', {'room': room_name}, room=request.sid)
        emit('private_chat_started', {'room': room_name}, room=target_sid)


@socketio.on('private_message')
def handle_private_message(data):
    room_name = data['room']
    message_data = data['message']
    message_data['timestamp'] = datetime.now().isoformat()
    # NEW: Save private message to the database
    db.add_message(room_name, message_data['user'], text=message_data['text'], timestamp=message_data['timestamp'])
    emit('private_message', {'room': room_name, 'message': message_data}, room=room_name, include_self=False)

@socketio.on('ai_message')
def handle_ai_message(prompt):
    # AI messages are not saved to history for now
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content(prompt)
        ai_response_data = {'user': 'AI Assistant', 'text': response.text, 'sender': 'them', 'timestamp': datetime.now().isoformat()}
        emit('ai_response', ai_response_data, room=request.sid)
    except Exception as e:
        print(f"Error generating AI response: {e}")
        error_message = {'user': 'AI Assistant', 'text': 'Sorry, I could not process your request.', 'sender': 'them', 'timestamp': datetime.now().isoformat()}
        emit('ai_response', error_message, room=request.sid)

# --- File Handling ---

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return 'No file part', 400
    file = request.files['file']
    if file.filename == '': return 'No selected file', 400
    
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        file_url = f"http://localhost:5000/uploads/{filename}"
        file_type = file.mimetype
        sender = request.form.get('sender')
        room = request.form.get('room')
        timestamp = datetime.now().isoformat()

        # NEW: Save file message to the database
        db.add_message(room, sender, file_url=file_url, file_type=file_type, filename=filename, timestamp=timestamp)

        file_message_data = {'user': sender, 'file_url': file_url, 'filename': filename, 'file_type': file_type, 'timestamp': timestamp}

        if room == 'public':
            socketio.emit('file_shared', file_message_data, broadcast=True, include_self=False)
        else:
            socketio.emit('file_shared', {'room': room, 'message': file_message_data}, room=room, include_self=False)

        return 'File uploaded successfully', 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
# backend/app.py

@socketio.on('clear_chat')
def handle_clear_chat(room_name):
    """Handles a request to clear chat history for a room."""
    # Call the database function to delete the messages
    db.clear_chat_history(room_name)
    # Notify all clients in that room that the chat has been cleared
    emit('chat_cleared', {'room': room_name}, room=room_name, broadcast=True)
    
# --- Main Execution ---
if __name__ == '__main__':
    # NEW: Initialize the database when the server starts
    db.init_db()
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    socketio.run(app, debug=True, port=5000)
