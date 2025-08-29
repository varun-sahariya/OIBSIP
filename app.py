# ===============================================================
# FINAL WORKING VERSION: app.py
# - Definitive fix for the 'AttributeError: PartialTranscript'.
# - Uses a single, correct event handler as per AssemblyAI documentation.
# ===============================================================

import os
import json
import logging
import queue
import time
import re
from functools import partial
import asyncio
import websockets
from typing import Dict, Any

from dotenv import load_dotenv
import assemblyai as aai
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from assemblyai.streaming.v3 import (
    StreamingClient,
    StreamingEvents,
    StreamingClientOptions,
    Transcript, # We need to import the Transcript object for type checking
)
import google.generativeai as genai
from tavily import TavilyClient
import requests

# =========================================
# Setup
# =========================================
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "a_super_secret_key")

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='gevent',
    logger=False,
    engineio_logger=False
)

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

# =========================================
# Tool Functions (Unchanged)
# =========================================
def get_weather(location: str) -> Dict[str, Any]:
    logging.info(f"--- 🔧 TOOL CALLED: get_weather(location={location}) ---")
    if "agra" in location.lower(): return {"location": "Agra", "temperature": 34, "unit": "celsius", "description": "Hot and sunny"}
    elif "delhi" in location.lower(): return {"location": "Delhi", "temperature": 36, "unit": "celsius", "description": "Very hot and humid"}
    else: return {"location": location, "temperature": "unknown", "description": "Weather data not available"}
def get_time() -> str:
    logging.info("--- 🔧 TOOL CALLED: get_time() ---")
    return f"The current time is {time.strftime('%I:%M %p', time.localtime())}."
def perform_search(query: str, tavily_api_key: str) -> str:
    if not tavily_api_key: return "Tavily API key not provided."
    try:
        client = TavilyClient(api_key=tavily_api_key)
        response = client.search(query=query, search_depth="basic", max_results=3)
        return "Search results:\n" + "\n".join([f"- {res['content']}" for res in response['results']])
    except Exception as e: return f"Search error: {e}"
def get_latest_news(topic: str, gnews_api_key: str) -> str:
    if not gnews_api_key: return "GNews API key not provided."
    url = f"https://gnews.io/api/v4/top-headlines?q={topic}&lang=en&country=in&max=3&apikey={gnews_api_key}"
    try:
        data = requests.get(url).json()
        if data.get("articles"): return f"Headlines for '{topic}':\n" + "\n".join([f"- {a['title']}" for a in data["articles"]])
        return f"No headlines for '{topic}'."
    except Exception as e: return f"News error: {e}"
def add_todo(item: str) -> str:
    sid = getattr(request, 'sid', None)
    if sid and sid in clients:
        clients[sid]["todo_list"].append(item); return f"Added '{item}' to your to-do list."
    return "Error: Could not find session."
def view_todos() -> str:
    sid = getattr(request, 'sid', None)
    if sid and sid in clients:
        if not clients[sid]["todo_list"]: return "To-do list is empty."
        return "To-do list:\n" + "\n".join(f"- {item}" for item in clients[sid]["todo_list"])
    return "Error: Could not find session."

# =========================================
# Main Logic & Tasks (Unchanged)
# =========================================
async def process_llm_and_murf(prompt: str, client_sid: str):
    client_data = clients.get(client_sid, {})
    api_keys = client_data.get("api_keys", {})
    if not all(k in api_keys and api_keys[k] for k in ["murf", "gemini"]):
        socketio.emit("llm_error", {"error": "Murf or Gemini API key not set."}, room=client_sid)
        return
    try:
        genai.configure(api_key=api_keys["gemini"])
        MURF_WS_URL = f"wss://api.murf.ai/v1/speech/stream-input?api-key={api_keys['murf']}&sample_rate=44100&channel_type=MONO&format=WAV"
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
        logging.error(f"LLM/Murf Error for {client_sid}: {e}", exc_info=True)
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
        logging.error(f"Transcribe Task Error for {sid}: {e}", exc_info=True)

# =========================================
# SocketIO Event Handlers
# =========================================
def initialize_client_services(sid):
    """Initializes AssemblyAI services for a client AFTER they provide keys."""
    if sid not in clients: return
    if clients[sid].get("client"):
        try: clients[sid]["client"].disconnect()
        except Exception: pass
    api_keys = clients[sid].get("api_keys", {})
    ASSEMBLYAI_API_KEY = api_keys.get("assemblyai")
    if not ASSEMBLYAI_API_KEY:
        socketio.emit("config_error", {"message": "AssemblyAI API key not provided."}, room=sid)
        return

    try:
        # ===== THIS IS THE DEFINITIVE FIX =====
        def on_transcript(event: Transcript):
            # Check the message type to differentiate partial vs. final
            if event.message_type == "PartialTranscript" and event.text:
                socketio.emit("turn_detected", {"transcript": event.text}, room=sid)
            elif event.message_type == "FinalTranscript" and event.text:
                logging.info(f"🔚 Final transcript for {sid}: '{event.text}'")
                socketio.emit("turn_ended", {"final_transcript": event.text}, room=sid)
                socketio.start_background_task(process_llm_and_murf, event.text, sid)
        
        def on_error(error: Exception):
            logging.error(f"AssemblyAI Stream Error for {sid}: {error}", exc_info=True)

        client = StreamingClient(StreamingClientOptions(api_key=ASSEMBLYAI_API_KEY))
        
        # Subscribe to the single, correct event
        client.on(StreamingEvents.Transcript, on_transcript)
        client.on(StreamingEvents.Error, on_error)
        
        clients[sid]["client"] = client
        socketio.start_background_task(transcribe_task, sid)
        logging.info(f"AssemblyAI services initialized successfully for SID {sid}")

    except Exception as e:
        logging.error(f"Failed to initialize AssemblyAI for {sid}: {e}", exc_info=True)
        socketio.emit("config_error", {"message": "Invalid AssemblyAI API key or config issue."}, room=sid)

@socketio.on("connect")
def handle_connect():
    sid = request.sid
    logging.info(f"Client connected: {sid}")
    clients[sid] = {
        "client": None, "audio_queue": queue.Queue(),
        "persona": "default", "todo_list": [], "api_keys": {}
    }

@socketio.on("configure_keys")
def handle_configure_keys(keys):
    sid = request.sid
    if sid in clients:
        logging.info(f"Received user keys for SID {sid}")
        clients[sid]["api_keys"] = keys
        initialize_client_services(sid)

@socketio.on("persona_change")
def handle_persona_change(data):
    sid = request.sid
    if sid in clients: clients[sid]['persona'] = data.get('persona', 'default')

@socketio.on("stream")
def handle_stream(data):
    sid = request.sid
    if sid in clients and "audio_queue" in clients[sid]:
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
# Flask Routes (Unchanged)
# =========================================
@app.route("/")
def index():
    return render_template("index.html")

# =========================================
# Application Entry Point (Unchanged)
# =========================================
if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))