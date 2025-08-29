#
# ===============================================================
# FINAL HYBRID VERSION: app.py
# Supports both server-side .env keys and client-side user keys
# ===============================================================
#

import eventlet
eventlet.monkey_patch()

import os
import json
import logging
import queue
import time
import re
from dotenv import load_dotenv
from functools import partial
import assemblyai as aai
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from assemblyai.streaming.v3 import (
    StreamingClient,
    StreamingEvents,
    StreamingParameters,
    StreamingClientOptions,
)
import google.generativeai as genai
import asyncio
import websockets
from typing import Dict, Any
from tavily import TavilyClient
import requests

# =========================================
# Setup
# =========================================
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Load Default API Keys from .env file ---
# These will be used if the user doesn't provide their own
DEFAULT_API_KEYS = {
    "assemblyai": os.getenv("ASSEMBLYAI_API_KEY"),
    "gemini": os.getenv("GEMINI_API_KEY"),
    "murf": os.getenv("MURF_API_KEY"),
    "tavily": os.getenv("TAVILY_API_KEY"),
    "gnews": os.getenv("GNEWS_API_KEY"),
}
HAS_DEFAULT_KEYS = all([DEFAULT_API_KEYS["assemblyai"], DEFAULT_API_KEYS["gemini"], DEFAULT_API_KEYS["murf"]])

# --- Flask App and SocketIO Initialization ---
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "a_super_secret_key")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

clients = {}
PERSONAS = {
    "default": {"prompt": "You are a helpful, professional AI assistant."},
    "pirate": {"prompt": "You are a salty pirate captain named Redbeard."},
    "scientist": {"prompt": "You are a brilliant but slightly eccentric scientist named Dr. Eureka."},
    "wizard": {"prompt": "You are an ancient and wise wizard named Arcanum."},
    "robot": {"prompt": "You are a friendly but logical robot assistant named ALEX-7."},
    "chef": {"prompt": "You are a passionate master chef named Chef Antoine."},
    "detective": {"prompt": "You are a sharp-eyed detective named Inspector Sharp."}
}

# (All tool functions like get_weather, get_time, etc. remain the same as the last version)
# ... [Tool functions are omitted here for brevity, but should be included in your file] ...
def get_weather(location: str) -> Dict[str, Any]:
    """Get the current weather for a specific location."""
    logging.info(f"--- 🔧 TOOL CALLED: get_weather(location={location}) ---")
    if "agra" in location.lower(): return {"location": "Agra", "temperature": 34, "unit": "celsius", "description": "Hot and sunny"}
    elif "delhi" in location.lower(): return {"location": "Delhi", "temperature": 36, "unit": "celsius", "description": "Very hot and humid"}
    else: return {"location": location, "temperature": "unknown", "description": "Weather data not available"}

def get_time() -> str:
    """Get the current time."""
    logging.info("--- 🔧 TOOL CALLED: get_time() ---")
    return f"The current time is {time.strftime('%I:%M %p', time.localtime())}."

def perform_search(query: str, tavily_api_key: str) -> str:
    """Performs a web search using the Tavily API."""
    if not tavily_api_key: return "Tavily API key not provided for this session."
    try:
        tavily_client = TavilyClient(api_key=tavily_api_key)
        response = tavily_client.search(query=query, search_depth="basic", max_results=3)
        return "Search results:\n" + "\n".join([f"- {res['content']}" for res in response['results']])
    except Exception as e: return f"An error occurred during search: {e}"

def get_latest_news(topic: str, gnews_api_key: str) -> str:
    """Fetches the latest news headlines on a specific topic."""
    if not gnews_api_key: return "GNews API key not provided for this session."
    url = f"https://gnews.io/api/v4/top-headlines?q={topic}&lang=en&country=in&max=3&apikey={gnews_api_key}"
    try:
        data = requests.get(url).json()
        if data.get("articles"): return f"Headlines for '{topic}':\n" + "\n".join([f"- {a['title']}" for a in data["articles"]])
        return f"No recent headlines found for '{topic}'."
    except Exception as e: return f"Error fetching news: {e}"

def add_todo(item: str) -> str:
    sid = request.sid
    if sid in clients:
        clients[sid]["todo_list"].append(item)
        return f"Added '{item}' to your to-do list."
    return "Error: Could not find your session."

def view_todos() -> str:
    sid = request.sid
    if sid in clients:
        if not clients[sid]["todo_list"]: return "Your to-do list is empty."
        return "Your to-do list:\n" + "\n".join(f"- {item}" for item in clients[sid]["todo_list"])
    return "Error: Could not find your session."


# =========================================
# Main Logic & Tasks
# =========================================
async def process_llm_and_murf(prompt: str, client_sid: str):
    client_data = clients.get(client_sid, {})
    api_keys = client_data.get("api_keys", {})
    if not all(k in api_keys for k in ["murf", "gemini"]):
        socketio.emit("llm_error", {"error": "Murf or Gemini API key not configured for this session."}, room=client_sid)
        return

    genai.configure(api_key=api_keys["gemini"])
    MURF_WS_URL = f"wss://api.murf.ai/v1/speech/stream-input?api-key={api_keys['murf']}&sample_rate=44100&channel_type=MONO&format=WAV"
    
    # ... (Rest of process_llm_and_murf is the same, using partial for tool keys)
    try:
        async with websockets.connect(MURF_WS_URL) as ws:
            context_id = f"{client_sid}-{int(time.time())}"
            await ws.send(json.dumps({"context_id": context_id, "voice_config": { "voiceId": "en-US-amara", "style": "Conversational", "rate": -5 }}))

            async def receive_audio(websocket):
                async for message in websocket:
                    data = json.loads(message)
                    if data.get("context_id") == context_id and data.get("audio"): socketio.emit('audio_chunk', data['audio'], room=client_sid)
                    if data.get("final"): break

            receiver_task = asyncio.create_task(receive_audio(ws))
            
            persona_prompt = PERSONAS.get(client_data.get('persona', 'default'), PERSONAS['default'])["prompt"]
            tools = [ get_weather, get_time, add_todo, view_todos,
                partial(perform_search, tavily_api_key=api_keys.get("tavily")),
                partial(get_latest_news, gnews_api_key=api_keys.get("gnews"))
            ]
            model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=persona_prompt, tools=tools)
            chat = model.start_chat(enable_automatic_function_calling=True)
            response = await chat.send_message_async(prompt)
            
            for sentence in filter(None, [s.strip() for s in re.split(r'(?<=[.?!])\s+', response.text)]):
                text_to_send = sentence + " "
                socketio.emit("llm_chunk", {"text": text_to_send}, room=client_sid)
                await ws.send(json.dumps({"context_id": context_id, "text": text_to_send}))
            
            await ws.send(json.dumps({"context_id": context_id, "end": True}))
            await asyncio.wait_for(receiver_task, timeout=20.0)
            socketio.emit("llm_complete", room=client_sid)
    except Exception as e:
        logging.error(f"Error in LLM/Murf process: {e}", exc_info=True)
        socketio.emit("llm_error", {"error": str(e)}, room=client_sid)


def transcribe_task(sid: str):
    if sid not in clients: return
    audio_queue = clients[sid]["audio_queue"]
    def read_from_queue(q):
        while True:
            data = q.get()
            if data is None: break
            yield data
    try:
        clients[sid]["client"].stream(read_from_queue(audio_queue))
    except Exception as e:
        logging.error(f"Error in transcribe_task for {sid}: {e}")

# =========================================
# SocketIO Event Handlers
# =========================================
def initialize_client_services(sid):
    """Helper to initialize AssemblyAI client for a session."""
    if sid not in clients: return
    
    # Clean up old client if it exists (e.g., on re-configuration)
    if clients[sid].get("client"):
        try: clients[sid]["client"].disconnect()
        except Exception: pass

    api_keys = clients[sid].get("api_keys", {})
    ASSEMBLYAI_API_KEY = api_keys.get("assemblyai")

    if not ASSEMBLYAI_API_KEY:
        socketio.emit("config_error", {"message": "AssemblyAI API key not configured for this session."}, room=sid)
        return

    try:
        def on_turn(self, event):
            if event.end_of_turn and event.transcript.strip():
                logging.info(f"🔚 End of turn for {sid}: '{event.transcript}'")
                socketio.emit("turn_ended", {"final_transcript": event.transcript}, room=sid)
                socketio.start_background_task(process_llm_and_murf, event.transcript, sid)
        
        client = StreamingClient(StreamingClientOptions(api_key=ASSEMBLYAI_API_KEY))
        client.on(StreamingEvents.Turn, on_turn)
        # Add other handlers like on_error, on_open if needed
        
        clients[sid]["client"] = client
        socketio.start_background_task(transcribe_task, sid)
        logging.info(f"AssemblyAI services initialized for SID {sid}")
    except Exception as e:
        logging.error(f"Failed to initialize AssemblyAI for {sid}: {e}")
        socketio.emit("config_error", {"message": f"Invalid AssemblyAI API key or configuration issue."}, room=sid)

@socketio.on("connect")
def handle_connect():
    sid = request.sid
    logging.info(f"Client connected: {sid}")
    clients[sid] = {
        "client": None, "audio_queue": queue.Queue(),
        "persona": "default", "todo_list": [], "api_keys": {}
    }
    # If server has default keys, use them automatically
    if HAS_DEFAULT_KEYS:
        logging.info(f"Applying default server keys for SID {sid}")
        clients[sid]["api_keys"] = DEFAULT_API_KEYS
        initialize_client_services(sid)

@socketio.on("configure_keys")
def handle_configure_keys(keys):
    sid = request.sid
    if sid in clients:
        logging.info(f"Received user-provided API keys for SID {sid}")
        clients[sid]["api_keys"] = keys
        initialize_client_services(sid) # Re-initialize with new keys

@socketio.on("persona_change")
def handle_persona_change(data):
    sid = request.sid
    if sid in clients: clients[sid]['persona'] = data.get('persona', 'default')

@socketio.on("stream")
def handle_stream(data):
    sid = request.sid
    if sid in clients and clients[sid].get("audio_queue"):
        clients[sid]["audio_queue"].put(data)

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    logging.info(f"Client disconnected: {sid}")
    if sid in clients:
        if clients[sid].get("audio_queue"): clients[sid]["audio_queue"].put(None)
        if clients[sid].get("client"):
            try: clients[sid]["client"].disconnect()
            except Exception: pass
        del clients[sid]

# =========================================
# Flask Routes
# =========================================
@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)