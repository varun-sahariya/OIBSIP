🎙️ AI Voice Assistant Pro

A real-time intelligent voice agent built with Flask, SocketIO, AssemblyAI, Google Gemini, and Murf AI.
It combines speech recognition, natural conversations, and lifelike voices with customizable personas and skills.

✨ Features
🎛 Core Functionality

🗣 Real-time Speech Recognition → Powered by AssemblyAI (streaming + turn detection)

🤖 Intelligent Responses → Google Gemini with function calling

🔊 Natural Text-to-Speech → Murf AI high-quality voice synthesis

👤 Multiple AI Personas → 7 personality types to choose from

⚡ Live Audio Streaming → WebSocket-based low-latency pipeline

🛠 Built-in Skills
Skill	Description
🌦 Weather	Current weather in any location
⏰ Time & Date	Current timestamp and date
🔍 Web Search	Internet search (via Tavily)
📰 Latest News	News headlines (via GNews)
📝 Todo Manager	Add & view personal task lists
💬 General Chat	Natural conversations
👤 AI Personas

🧑‍💼 Default Assistant – Professional & helpful

☠️ Pirate Captain – Nautical slang & adventurous

🔬 Mad Scientist – Excited about discoveries

🧙 Ancient Wizard – Mystical & wise

🤖 Friendly Robot – Logical, curious about humans

👨‍🍳 Master Chef – French cooking flair

🕵️ Detective – Sharp & analytical

🔑 Prerequisites
Required API Keys

AssemblyAI
 → Speech recognition

Google Gemini
 → AI responses

Murf AI
 → Text-to-speech

Optional API Keys

Tavily
 → Web search

GNews
 → News

⚙️ Installation
1️⃣ Clone the Repo
git clone <repository-url>
cd ai-voice-assistant-pro

2️⃣ Install Dependencies
pip install -r requirements.txt

3️⃣ Configure Environment

Create .env in project root:

ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
GEMINI_API_KEY=your_google_gemini_api_key_here
MURF_API_KEY=your_murf_ai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
GNEWS_API_KEY=your_gnews_api_key_here

SECRET_KEY=your_secret_key_here
PORT=5000

4️⃣ Run the App
python app.py


➡️ Open: http://localhost:5000

🎤 Usage

🎙 Grant microphone access

👤 Select persona from dropdown

🗣 Speak naturally (e.g. “What’s the weather in Delhi?”)

🔊 Listen to AI’s voice reply

⚡ Use skills like weather, news, todos, etc.

Example Commands

🌦 “What’s the weather in Mumbai?”

⏰ “What time is it right now?”

📰 “Give me today’s tech news.”

📝 “Add call mom to my todo list.”

😂 “Tell me a joke.”

🏗 Architecture

Backend

Flask + SocketIO (real-time communication)

AssemblyAI (STT)

Gemini (AI reasoning)

Murf AI (TTS)

Tool integrations (Weather, News, Search, Todos)

Frontend

🎨 Glassmorphism UI

🎧 WebAudio API (mic + playback)

📱 Responsive design

⚡ Real-time updates with smooth animations

Data Flow

🎙 User speaks → AssemblyAI transcribes

🧠 Transcript → Gemini processes with skills

🔊 Response → Murf AI converts to speech

🌐 Streamed back to browser

🐞 Troubleshooting
Issue	Fix
🎙 Mic not working	Allow permissions, close other apps
🔇 No audio	Check browser audio, volume
🔑 API error	Re-check .env keys
🐢 Lag	Check internet speed, reduce open tabs
🗂 Project Structure
ai-voice-assistant-pro/
├── app.py               # Main Flask app
├── templates/index.html # Frontend UI
├── static/script.js     # Client-side JS
├── .env                 # Environment keys
├── requirements.txt     # Python deps
└── README.md            # Documentation

🛠 Extending

Add new skills → Create a function in app.py & register in tools list

Add new personas → Extend the PERSONAS dictionary

Customize UI → Edit index.html & style.css

Tune voices → Adjust Murf AI settings

🔒 Security

API keys stored in .env (not in code)

Each client has isolated session & todos

Proper WebSocket cleanup

Input validation

📈 Performance

Efficient audio streaming + buffering

Async + threading for concurrency

Optimized real-time updates

🤝 Contributing

Fork repo

Create feature branch

Add & test your feature

Submit PR

📜 License

Open source – check API providers’ terms.

💡 Support

🔍 Check Troubleshooting

🖥 Open browser console for errors

🔑 Verify .env API keys

🌐 Ensure stable internet

✨ With AI Voice Assistant Pro, every conversation feels smarter, faster, and more natural.