import os
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from murf.client import Murf
import assemblyai as aai

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure API keys
aai.settings.api_key = os.getenv('ASSEMBLYAI_API_KEY')

# Initialize Murf Client
try:
    murf_client = Murf()
    app.logger.info("Murf client initialized successfully")
except Exception as e:
    app.logger.error(f"Failed to initialize Murf client: {e}")
    murf_client = None

@app.route('/')
def index():
    """Serve the main page with the voice processing interface"""
    return render_template('index.html')

@app.route('/generate-audio', methods=['POST'])
def generate_audio():
    """Generate audio from text using Murf AI TTS"""
    if not murf_client:
        app.logger.error("Murf client not initialized")
        return jsonify({'error': 'Murf client not initialized.'}), 500
    
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    text_to_convert = data.get('text')
    if not text_to_convert.strip():
        return jsonify({'error': 'Empty text provided'}), 400
    
    try:
        app.logger.info(f"Generating audio for text: {text_to_convert[:50]}...")
        res = murf_client.text_to_speech.generate(
            text=text_to_convert, 
            voice_id="en-US-terrell", 
            format="mp3"
        )
        app.logger.info(f"Audio generated successfully: {res.audio_file}")
        return jsonify({'audioUrl': res.audio_file})
    except Exception as e:
        app.logger.error(f"Error calling Murf API: {str(e)}")
        return jsonify({'error': f'Error calling Murf API: {str(e)}'}), 502

@app.route('/tts/echo', methods=['POST'])
def tts_echo():
    """
    Echo Bot endpoint: Receives audio, transcribes it with AssemblyAI, 
    and returns TTS audio of the transcript using Murf AI
    """
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No audio file found'}), 400

    audio_file = request.files['audio_file']
    
    # Validate audio file
    if audio_file.filename == '':
        return jsonify({'error': 'No audio file selected'}), 400

    app.logger.info(f"Processing audio file: {audio_file.filename}")

    # Step 1: Transcribe the audio using AssemblyAI
    try:
        app.logger.info("Starting transcription with AssemblyAI...")
        transcriber = aai.Transcriber()
        
        # Convert FileStorage to bytes for AssemblyAI
        audio_file.seek(0)  # Reset file pointer to beginning
        audio_data = audio_file.read()
        
        transcript = transcriber.transcribe(audio_data)

        if transcript.status == aai.TranscriptStatus.error:
            app.logger.error(f"Transcription error: {transcript.error}")
            return jsonify({'error': f'Transcription failed: {transcript.error}'}), 500
        
        transcript_text = transcript.text
        app.logger.info(f"Transcription successful: '{transcript_text}'")

        if not transcript_text or transcript_text.strip() == '':
            return jsonify({'error': 'No speech detected in the audio.'}), 400

    except Exception as e:
        app.logger.error(f"Error during transcription: {str(e)}")
        return jsonify({'error': f'Transcription failed: {str(e)}'}), 500

    # Step 2: Generate new audio from the transcript using Murf
    try:
        if not murf_client:
            return jsonify({'error': 'Murf client not initialized.'}), 500
        
        app.logger.info(f"Generating TTS for transcribed text: '{transcript_text[:50]}...'")
        res = murf_client.text_to_speech.generate(
            text=transcript_text, 
            voice_id="en-US-linda", 
            format="mp3"
        )
        
        app.logger.info(f"Murf TTS successful. Audio URL: {res.audio_file}")
        return jsonify({
            'audioUrl': res.audio_file,
            'transcription': transcript_text
        })

    except Exception as e:
        app.logger.error(f"Error during Murf TTS: {str(e)}")
        return jsonify({'error': f'Murf TTS failed: {str(e)}'}), 502

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Run the Flask app on port 5000 as specified
    app.run(host='0.0.0.0', port=5000, debug=True)
