# AI Voice Suite

## Overview

This is a Flask-based web application that provides AI-powered voice processing capabilities through a clean, tabbed interface. The application integrates with Murf AI for text-to-speech generation and AssemblyAI for speech-to-text transcription, creating a comprehensive voice processing suite. The frontend features a modern dark-themed UI with multiple tabs for different voice processing functionalities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Single Page Application**: Uses vanilla JavaScript with tab-based navigation for different voice processing features
- **Modern UI Design**: Dark theme with CSS custom properties for consistent styling and Inter font family
- **Responsive Layout**: Flexbox-based layout that adapts to different screen sizes
- **Component-based Structure**: Modular tab system with separate sections for different functionalities

### Backend Architecture
- **Flask Framework**: Lightweight Python web framework serving as the main application server
- **RESTful API Design**: JSON-based endpoints for voice processing operations
- **Error Handling**: Comprehensive error handling with appropriate HTTP status codes
- **Logging**: Debug-level logging for development and troubleshooting
- **Environment Configuration**: Uses dotenv for secure API key management

### Voice Processing Pipeline
- **Text-to-Speech**: Murf AI integration for high-quality voice generation
- **Speech-to-Text**: AssemblyAI integration for audio transcription
- **Audio Format Support**: MP3 format for generated audio files
- **Real-time Processing**: Asynchronous JavaScript for smooth user experience

### Security and Configuration
- **Environment Variables**: Secure storage of API keys using .env files
- **Session Management**: Flask session secret for secure user sessions
- **API Key Validation**: Proper initialization checks for external services

## External Dependencies

### AI Services
- **Murf AI**: Primary text-to-speech service for voice generation
  - Uses specific voice models (e.g., "en-US-terrell")
  - Generates MP3 audio files
  - Requires Murf API credentials
- **AssemblyAI**: Speech-to-text transcription service
  - Processes uploaded audio files
  - Requires AssemblyAI API key

### Python Libraries
- **Flask**: Web framework for routing and request handling
- **python-dotenv**: Environment variable management
- **murf**: Official Murf AI client library
- **assemblyai**: Official AssemblyAI client library

### Frontend Dependencies
- **Google Fonts**: Inter font family for modern typography
- **Native Browser APIs**: File upload, audio playback, and fetch for API calls

### Development Tools
- **Python Logging**: Built-in logging for debugging and monitoring
- **Static File Serving**: Flask's static file handling for CSS and JavaScript