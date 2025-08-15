import os
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import assemblyai as aai
import google.generativeai as genai
# This is your real Murf client import
from murf.client import Murf 

# ===================================================
# --- CONFIGURATION ---
# ===================================================
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MURF_VOICE_ID = "en-US-natalie"
GEMINI_MODEL = 'gemini-1.5-flash-latest'
FALLBACK_ERROR_MESSAGE = "I'm having some trouble connecting right now. Please try again in a moment."
END_CONVERSATION_MESSAGE = "Alright, ending the conversation. Goodbye!"

# ===================================================
# --- API & CLIENT INITIALIZATION ---
# ===================================================
aai.settings.api_key = os.getenv('ASSEMBLYAI_API_KEY')
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    logging.error(f"Failed to configure Gemini API: {e}")

app = Flask(__name__)
chat_histories = {} # In-memory storage for chat histories by session_id

# --- Custom Exceptions for clear error handling ---
class TranscriptionError(Exception): pass
class NoSpeechDetectedError(Exception): pass
class LLMError(Exception): pass
class TTSError(Exception): pass

# We are no longer using the MockMurfClient

try:
    # This is the FIX: Use the real Murf client
    murf_client = Murf() 
    logging.info("Murf client initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize Murf client: {e}")
    murf_client = None

# ===================================================
# --- SERVICE HELPER FUNCTIONS ---
# ===================================================

def transcribe_audio(audio_file):
    """Transcribes audio using AssemblyAI."""
    if not aai.settings.api_key: raise TranscriptionError("AssemblyAI API key not configured.")
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)
    if transcript.status == aai.TranscriptStatus.error: raise TranscriptionError(transcript.error)
    if not transcript.text: raise NoSpeechDetectedError()
    return transcript.text

def get_llm_response(user_text, session_history):
    """Gets a response from the Gemini LLM."""
    model = genai.GenerativeModel(GEMINI_MODEL)
    chat = model.start_chat(history=session_history)
    response = chat.send_message(user_text)
    return response.text, chat.history

def generate_speech_audio(text):
    """Generates speech audio using Murf."""
    if not murf_client: raise TTSError("Murf client not initialized.")
    res = murf_client.text_to_speech.generate(text=text, voice_id=MURF_VOICE_ID, format="mp3")
    return res.audio_file

# ===================================================
# --- FLASK ROUTES ---
# ===================================================

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/generate-fallback-audio', methods=['POST'])
def generate_fallback_audio():
    """Generates a generic fallback audio message for critical frontend errors."""
    try:
        audio_url = generate_speech_audio(FALLBACK_ERROR_MESSAGE)
        return jsonify({'audioUrl': audio_url})
    except Exception as e:
        logging.error(f"CRITICAL: Could not generate fallback audio. {e}")
        return jsonify({'error': 'Failed to generate fallback audio.'}), 500

@app.route('/agent/chat/<session_id>', methods=['POST'])
def agent_chat(session_id):
    """Main endpoint for handling the conversational agent logic."""
    # Handle conversation end request
    if request.is_json and request.get_json().get('end_convo'):
        try:
            audio_url = generate_speech_audio(END_CONVERSATION_MESSAGE)
            return jsonify({'audioUrl': audio_url, 'llm_response': END_CONVERSATION_MESSAGE})
        except TTSError as e:
            logging.error(f"MURF_FAILURE on end_convo: {e}")
            return jsonify({'error': 'Murf TTS Error'}), 502

    if 'audio_file' not in request.files:
        return jsonify({'error': 'No audio file found.'}), 400

    audio_file = request.files['audio_file']

    try:
        # --- Core Logic Pipeline ---
        # 1. Transcribe user's speech
        user_text = transcribe_audio(audio_file)

        # 2. Get LLM response
        if session_id not in chat_histories: chat_histories[session_id] = []
        llm_response_text, updated_history = get_llm_response(user_text, chat_histories[session_id])
        chat_histories[session_id] = updated_history # Update history for the session

        # 3. Convert LLM response to speech
        audio_url = generate_speech_audio(llm_response_text)

        # 4. Send successful response
        return jsonify({
            'audioUrl': audio_url,
            'user_transcript': user_text,
            'llm_response': llm_response_text
        })

    # --- Error Handling ---
    except NoSpeechDetectedError:
        return jsonify({'no_speech': True})
    except TranscriptionError as e:
        logging.error(f"ASSEMBLYAI_FAILURE: {e}")
        return jsonify({'error_code': 'STT_SERVICE_FAILED'}), 500
    except LLMError as e:
        logging.error(f"GEMINI_FAILURE: {e}")
        return jsonify({'error_code': 'LLM_SERVICE_FAILED'}), 500
    except TTSError as e:
        logging.error(f"MURF_FAILURE: {e}")
        return jsonify({'error_code': 'TTS_SERVICE_FAILED'}), 500
    except Exception as e:
        logging.error(f"UNHANDLED_ERROR in agent_chat: {e}")
        return jsonify({'error_code': 'INTERNAL_SERVER_ERROR'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)