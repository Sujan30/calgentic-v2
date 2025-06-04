# 📆 Calgentic

Calgentic is your AI-powered calendar assistant that transforms plain English into structured Google Calendar events. Whether you're scheduling meetings, workouts, study sessions, or reminders, Calgentic understands your intent and creates precise, timezone-aware events—automatically.

---

## ✨ Features

- 🧠 **Natural Language Understanding**  
  Type “Lunch with Sarah on Friday at 2pm” — we’ll turn it into a real event.

- 🌍 **Timezone-Aware Scheduling**  
  Automatically adapts to your local timezone.

- 📅 **Google Calendar Integration**  
  Syncs seamlessly with your existing calendar.

- 💬 **Real-Time Event Parsing**  
  Fast, server-side parsing with GPT-backed logic.

- 🔒 **Secure Auth with Supabase**  
  Fully authenticated user experience, backed by JWT and row-level security.

---

## 🚀 How It Works

1. **User types** a prompt like “meeting with Jason tomorrow at 11am”.
2. Calgentic uses **NLP models** (GPT-4) to extract date, time, and event info.
3. The backend formats this into a **Google Calendar event** and adds it to your calendar.
4. Everything happens in your **local timezone**.

---

## 🛠️ Tech Stack

- **Frontend:** React + Tailwind (ShadCN UI)
- **Backend:** Python (Flask)
- **AI:** OpenAI GPT-4
- **Authentication & DB:** Supabase
- **Calendar API:** Google Calendar API

---

## 🧪 Example Prompt

> “Dinner with mom on Sunday at 7pm”

Calgentic will convert this into a properly formatted Google Calendar event with title "Dinner with mom", time set to the upcoming Sunday at 7:00 PM, and adjust for your timezone.

---

## 🔐 Permissions & Scopes

Calgentic requests access to both **read and write** permissions on your Google Calendar:

- `https://www.googleapis.com/auth/calendar.readonly`
- `https://www.googleapis.com/auth/calendar.events`

These scopes are necessary so Calgentic can check for existing events and create/update new ones on your behalf.

---

## ⚙️ Running Locally

```bash
git clone https://github.com/Sujan30/Calgentic.git
cd Calgentic
# Setup virtual environment and install requirements
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Add your .env file with OpenAI key, Supabase, and Google creds
flask run
