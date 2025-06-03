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

- 🛠️ **Full Event Management**  
  Modify, locate, or delete events using natural language like “Reschedule my meeting to 3pm” or “Cancel gym tomorrow.”

- 🧪 **In-Progress Features**  
  - Event summarization  
  - Smart suggestions (e.g. travel time, conflicts)  
  - Voice input support (coming soon)

---

## 🚀 Getting Started

### 📦 Requirements

- Python 3.10+
- Flask
- Supabase Project
- Google OAuth client credentials
- OpenAI API key

### 🛠️ Installation

```bash
git clone https://github.com/yourusername/calgentic.git
#(for frontend)
cd frontend
npm install 
npm dev 

#(for backend)
cd backend
pip install -r requirements.txt
python app.py
