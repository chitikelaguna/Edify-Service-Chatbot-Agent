# Frontend Files

This directory contains the lightweight frontend for the Edify Admin AI Chatbot.

## Files

- `index.html` - Main HTML structure
- `styles.css` - Modern, responsive CSS styling
- `app.js` - JavaScript for API communication and UI interactions

## Features

- Simple login interface with Admin ID and Token
- Real-time chat interface
- Session management
- Responsive design for mobile and desktop
- Clean, modern UI with smooth animations

## Usage

1. Start the FastAPI backend server
2. Open your browser and navigate to `http://localhost:8000`
3. Enter your Admin ID and Token to start a session
4. Start chatting with the AI assistant

## API Endpoints Used

- `POST /session/start` - Start a new session
- `POST /session/end` - End current session
- `POST /chat/message` - Send a message and get AI response

