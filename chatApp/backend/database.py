import sqlite3

DATABASE_NAME = 'chat_history.db'

def init_db():
    """Initializes the database and creates the messages table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    # Create a table to store all messages
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT NOT NULL,
            sender TEXT NOT NULL,
            text TEXT,
            file_url TEXT,
            file_type TEXT,
            filename TEXT,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def add_message(room, sender, text=None, file_url=None, file_type=None, filename=None, timestamp=None):
    """Adds a new message to the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (room, sender, text, file_url, file_type, filename, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (room, sender, text, file_url, file_type, filename, timestamp))
    conn.commit()
    conn.close()
def clear_chat_history(room):
    """Deletes all messages for a specific room from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM messages WHERE room = ?', (room,))
    conn.commit()
    conn.close()
    print(f"Chat history for room '{room}' has been cleared.")
    
def get_chat_history(room, limit=50):
    """Retrieves the last N messages for a specific room."""
    conn = sqlite3.connect(DATABASE_NAME)
    # This allows us to get results as dictionaries instead of tuples
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM messages
        WHERE room = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (room, limit))
    
    # Fetch all rows and convert them to a list of dictionaries
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Reverse the list to have the oldest message first
    return history[::-1]