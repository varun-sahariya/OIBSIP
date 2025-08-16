import os
from app import app, socketio  # import socketio from your app.py

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Replit provides PORT
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
