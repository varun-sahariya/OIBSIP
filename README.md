🤖 AI Conversational Voice Agent
This project is a fully functional, voice-powered conversational AI agent built as part of the #30DaysOfAIVoiceAgents challenge by Murf AI. The agent can listen to a user's voice, understand the context of a conversation, generate an intelligent response, and speak that response back in a natural-sounding AI voice.

This repository documents the core application built up to Day 13 of the challenge.

✨ Features
This application is packed with features that create a seamless and intelligent conversational experience:

Voice-to-Text Transcription: Utilizes AssemblyAI's powerful speech-to-text engine to accurately transcribe user's spoken words in real-time.

Intelligent Conversational AI: Leverages Google's Gemini Pro model to understand context, answer questions, and generate human-like text responses.

Persistent Memory: The agent remembers previous turns in the conversation. You can ask follow-up questions, and it will know what you're talking about.

Text-to-Speech Synthesis: Uses Murf AI to convert the AI's text responses into high-quality, natural-sounding audio.

Continuous Conversation Loop: The agent automatically starts listening for the user's next turn after it finishes speaking, creating a fluid, back-and-forth chat experience.

Robust Error Handling: The application is designed to fail gracefully. If any of the external API services are unavailable, the user will hear a helpful audio message instead of the application crashing.

Standalone Voice Generator: Includes a separate utility to quickly convert any typed text into speech for testing or other purposes.

🛠️ Tech Stack & Architecture
The project follows a simple client-server architecture.

Backend: A Python server using the Flask web framework. It exposes API endpoints to handle the core logic.

Frontend: A clean, modern user interface built with vanilla HTML, CSS, and JavaScript. No complex frameworks are needed.

The application's logic is a three-step pipeline orchestrated by the Flask server:

Speech-to-Text (STT): The frontend records the user's voice and sends the audio file to the server. The server forwards this to the AssemblyAI API for transcription.

Language Model (LLM): The transcribed text, along with the session's chat history, is sent to the Google Gemini API. Gemini generates a context-aware response.

Text-to-Speech (TTS): The text response from Gemini is sent to the Murf AI API, which returns a URL for the final audio file. This URL is sent back to the frontend to be played automatically.

🚀 Getting Started
Follow these instructions to get the project running locally or on a cloud environment like Replit.

1. Clone the Repository
git clone <your-repository-url>
cd <your-project-directory>

2. Install Dependencies
This project uses pip for package management.

pip install flask python-dotenv murf-ai assemblyai google-generativeai

3. Set Up Environment Variables
You need to get API keys from three services. Create a file named .env in the root of your project and add your keys to it.

# Get from [https://assemblyai.com/](https://assemblyai.com/)
ASSEMBLYAI_API_KEY="YOUR_ASSEMBLYAI_API_KEY"

# Get from [https://aistudio.google.com/](https://aistudio.google.com/)
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

# Get from [https://murf.ai/](https://murf.ai/)
MURF_API_KEY="YOUR_MURF_API_KEY"

Note: If you are using Replit, you should use the built-in Secrets manager instead of a .env file. The variable names are the same.

4. Run the Application
Once the dependencies are installed and your environment variables are set, you can start the Flask server.

python app.py

The server will start, and you can access the application by opening http://127.0.0.1:5000 in your web browser.

Enjoy your conversation! 🎙️