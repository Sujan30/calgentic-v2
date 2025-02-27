# AI Calendar Assistant

An AI-powered calendar assistant that allows users to manage their Google Calendar using natural language commands.

## Features

- Create calendar events using natural language
- View upcoming events
- OAuth integration with Google Calendar
- Dark mode support
- Responsive UI

## Installation

### Prerequisites

- Python 3.8+
- Node.js 16+
- Google Cloud Platform account with Calendar API enabled

### Backend Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/repo-name.git
   cd repo-name
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables
   Create a `.env` file with the following variables:
   ```
   openai_key=your_openai_api_key
   google_client_id=your_google_client_id
   google_client_secret=your_google_client_secret
   redirect_url=http://localhost:5000/auth/callback
   ```

5. Run the backend
   ```bash
   python src/app.py
   ```

### Frontend Setup

1. Install dependencies
   ```bash
   cd calgentic-UI
   npm install
   ```

2. Run the development server
   ```bash
   npm run dev
   ```

## Usage

1. Open your browser and navigate to `http://localhost:5000`
2. Log in with your Google account
3. Use the command bar to interact with your calendar
   - Example: "Schedule a meeting with John at 3 PM tomorrow"
   - Example: "What events do I have this Friday?"
