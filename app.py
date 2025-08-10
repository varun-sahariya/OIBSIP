import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from murf.client import Murf
import assemblyai as aai
import google.generativeai as genai

# --- Load API Keys ---
load_dotenv()
aai.settings.api_key = os.getenv('ASSEMBLYAI_API_KEY')
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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
    return render_template('index.html')


# --- Endpoint for the Text-Based AI Voice Generator ---
@app.route('/generate-audio', methods=['POST'])
def generate_audio():
    if not murf_client:
        return jsonify({'error': 'Murf client not initialized.'}), 500

    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    text_to_convert = data.get('text')
    try:
        res = murf_client.text_to_speech.generate(
            text=text_to_convert,
            voice_id="en-US-terrell",
            format="mp3"
        )
        return jsonify({'audioUrl': res.audio_file})
    except Exception as e:
        return jsonify({'error': f'Error calling Murf API: {str(e)}'}), 502


# ===================================================
# --- UPDATED ENDPOINT FOR DAY 9 (THE FULL PIPELINE) ---
# ===================================================
@app.route('/llm/query', methods=['POST'])
def llm_query():
    """Receives audio, transcribes, gets LLM response, and returns TTS audio."""
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No audio file found'}), 400

    audio_file = request.files['audio_file']
    transcript_text = ""
    llm_response_text = ""

    # Step 1: Transcribe the audio using AssemblyAI
    try:
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_file)
        if transcript.status == aai.TranscriptStatus.error:
            return jsonify({'error': transcript.error}), 500
        transcript_text = transcript.text
        if not transcript_text:
            return jsonify({'error': 'No speech detected in the audio.'}), 400
        print(f"Transcription successful: '{transcript_text}'")
    except Exception as e:
        return jsonify({'error': f'Transcription failed: {str(e)}'}), 500

    # Step 2: Get a response from the Gemini LLM
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"Please provide a concise answer to the following question: {transcript_text}"
        response = model.generate_content(prompt)
        llm_response_text = response.text
        print(f"LLM Response: '{llm_response_text}'")
    except Exception as e:
        return jsonify({'error': f'Error calling Gemini API: {str(e)}'}), 500

    # Step 3: Generate new audio from the LLM's response using Murf
    try:
        if not murf_client:
            return jsonify({'error': 'Murf client not initialized.'}), 500
        res = murf_client.text_to_speech.generate(
            text=llm_response_text,
            voice_id="en-US-linda",
            format="mp3"
        )
        print(f"Murf TTS successful. Audio URL: {res.audio_file}")
        return jsonify({'audioUrl': res.audio_file})
    except Exception as e:
        return jsonify({'error': f'Murf TTS failed: {str(e)}'}), 502


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
