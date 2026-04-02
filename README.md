<<<<<<< HEAD
# Sige-chatbot-ai
=======
# 🎓 SIGE AI Agent: Customer Support & Lead Management System

Welcome to the **SIGE AI Consultant**! This project is a production-ready AI-powered customer support system specifically built for the **Science Institute for Global Education (SIGE)**. It leverages Retrieval-Augmented Generation (RAG) to provide accurate study-abroad advice for Taiwan and integrates seamlessly with Google Sheets for real-time lead tracking.

---

## 🚀 Key Features

- **💡 Intelligent RAG Consultant:** Uses **Ollama** and **FAISS** to answer complex questions about study-abroad programs, scholarships (1+4), and partner universities in Taiwan with high accuracy.
- **🔄 2-Way Google Sheets Sync:** Real-time synchronization between the local SQLite database and your "LEAD Sige" Google Sheet using a high-performance Webhook architecture.
- **📝 Guided Lead Collection:** A structured, multi-choice Telegram conversation workflow that collects student profiles (Name, GPA, Language, etc.) and syncs them instantly to the sales team.
- **🎯 Smart Intent Suggestion:** Root menu with quick-reply buttons (Scholarships, Programs, Contact) to guide users directly to the most frequent queries.

---

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python 3.10+)
- **Bot Engine:** `python-telegram-bot` (v22+)
- **LLM Engine:** Ollama (Qwen 2.5 / Nomic-embed-text)
- **Database:** SQLite (Relational) + FAISS (Vector Store)
- **Integration:** Google Apps Script (Webhook bridge)

---

## 📦 Installation Guide

### 1. Prerequisites

- **Python 3.10 or higher**
- **Ollama** (Download from [ollama.com](https://ollama.com/))
- **Ngrok** (For exposing your local server to Google Sheets)
- **A Telegram Bot Token** (Get it from [@BotFather](https://t.me/BotFather))

### 2. Setup Environment

Clone the repository and enter the project directory:

```bash
cd ai-agent-cs
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Ollama Models

Pull the necessary models for chat and embeddings:

```bash
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text
```

### 4. Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

**Required Fields in `.env`:**
- `TELEGRAM_BOT_TOKEN`: Your bot token from BotFather.
- `API_BASE_URL`: Your current Ngrok URL (e.g., `https://xxxx.ngrok-free.app`).
- `SIGE_LEADS_SHEET_ID`: The ID of your Google Sheet.
- `GOOGLE_SHEETS_WEBHOOK_URL`: The URL provided after deploying the Google Apps Script.

---

## 🏃 Running the System

### 1. Ingest Knowledge Base
Before starting the bot, build the vector index from the SIGE documentation:

```bash
python -m backend.data_scripts.ingest_sige
```

### 2. Start the API Server (Webhook Handler)
This handles the incoming data from Google Sheets:

```bash
python start_api_server.py
```

### 3. Start the Telegram Bot
This starts the AI Consultant interface:

```bash
python start_telegram_bot.py
```

---

## 🔗 Google Sheets Integration

To enable 2-way sync:
1. Open your Google Sheet.
2. Go to **Extensions > Apps Script**.
3. Paste the code provided in `backend/services/sheets_sync.js` (or similar reference).
4. **Deploy** as a Web App (access: Anyone).
5. Set the **On Edit** trigger in the Apps Script project to point to your `handleEditSync` function.

---

## 👨‍💻 Contributing

This project is optimized for performance and reliability in the education sector. If you find bugs or want to suggest features, please open an issue or contact the SIGE technical team.

**SIGE - Science Institute for Global Education**  
*Building Dreams, Connecting Global Talent.*
>>>>>>> 35d7d27 (Initial commit SIGE: Professional bot)
