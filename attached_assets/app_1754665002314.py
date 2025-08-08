import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from murf.client import Murf
import assemblyai as aai

# --- Load API Keys ---
load_dotenv()
aai.settings.api_key = os.getenv('ASSEMBLYAI_API_KEY')

app = Flask(__name__)

# --- Initialize Murf Client ---
try:
    murf_client = Murf()
except Exception as e:
    print(f"Failed to initialize Murf client: {e}")
    murf_client = None

# --- Main Route ---
@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

# --- Existing Endpoint for AI Voice Generator Tab ---
@app.route('/generate-audio', methods=['POST'])
def generate_audio():
    if not murf_client:
        return jsonify({'error': 'Murf client not initialized.'}), 500
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    text_to_convert = data.get('text')
    try:
        res = murf_client.text_to_speech.generate(text=text_to_convert, voice_id="en-US-terrell", format="mp3")
        return jsonify({'audioUrl': res.audio_file})
    except Exception as e:
        return jsonify({'error': f'Error calling Murf API: {str(e)}'}), 502

# ===================================================
# --- ENDPOINT FOR DAY 7 (Echo Bot v2) ---
# ===================================================
@app.route('/tts/echo', methods=['POST'])
def tts_echo():
    """Receives audio, transcribes it, and returns TTS audio of the transcript."""
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No audio file found'}), 400

    # Corrected from request.file to request.files
    audio_file = request.files['audio_file']
    transcript_text = ""

    # Step 1: Transcribe the audio using AssemblyAI
    try:
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_file)

        if transcript.status == aai.TranscriptStatus.error:
            return jsonify({'error': transcript.error}), 500
        
        transcript_text = transcript.text
        print(f"Transcription successful: '{transcript_text}'")

        if not transcript_text:
            return jsonify({'error': 'No speech detected in the audio.'}), 400

    except Exception as e:
        print(f"--- ERROR DURING TRANSCRIPTION ---: {str(e)}")
        return jsonify({'error': f'Transcription failed: {str(e)}'}), 500

    # Step 2: Generate new audio from the transcript using Murf
    try:
        if not murf_client:
            return jsonify({'error': 'Murf client not initialized.'}), 500
        
        res = murf_client.text_to_speech.generate(text=transcript_text, voice_id="en-US-linda", format="mp3")
        
        print(f"Murf TTS successful. Audio URL: {res.audio_file}")
        return jsonify({'audioUrl': res.audio_file})

    except Exception as e:
        print(f"--- ERROR DURING MURF TTS ---: {str(e)}")
        return jsonify({'error': f'Murf TTS failed: {str(e)}'}), 502


if __name__ == '__main__':
    # The one and only run command, with the watchdog reloader
    app.run(debug=True)