<<<<<<< HEAD
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
=======
# Welcome to your Lovable project

## Project info

**URL**: https://lovable.dev/projects/ac96ed7b-88b2-4e44-bcbb-0c6a3371a67e

## How can I edit this code?

There are several ways of editing your application.

**Use Lovable**

Simply visit the [Lovable Project](https://lovable.dev/projects/ac96ed7b-88b2-4e44-bcbb-0c6a3371a67e) and start prompting.

Changes made via Lovable will be committed automatically to this repo.

**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes. Pushed changes will also be reflected in Lovable.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with .

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/ac96ed7b-88b2-4e44-bcbb-0c6a3371a67e) and click on Share -> Publish.

## I want to use a custom domain - is that possible?

We don't support custom domains (yet). If you want to deploy your project under your own domain then we recommend using Netlify. Visit our docs for more details: [Custom domains](https://docs.lovable.dev/tips-tricks/custom-domain/)
>>>>>>> 4c4d936e148251cda583f3681017deab75a6bc99
