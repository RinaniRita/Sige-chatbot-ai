# 🎓 SIGE AI Agent: Customer Support & Lead Management System

Welcome to the **SIGE AI Consultant**! This project is a production-ready AI-powered customer support system specifically built for the **Science Institute for Global Education (SIGE)**. 

It is now exclusively optimized for **Facebook Messenger**, leveraging Retrieval-Augmented Generation (RAG) to provide accurate study-abroad advice for Taiwan and integrating seamlessly with Google Sheets for real-time lead tracking.

---

## 🚀 Key Features

- **💡 Intelligent RAG Consultant:** Uses **Ollama** and **FAISS** to answer complex questions about study-abroad programs, scholarships (1+4), and partner universities in Taiwan with high accuracy.
- **🔢 Sequential Lead IDs:** Automatically tracks and assigns numeric IDs (e.g., "5", "6", "7") to new customers, keeping your records perfectly organized.
- **💬 Facebook Messenger First:** Native integration with Meta's platform, including **Quick Replies** ("popups") for high-engagement follow-ups and a **Persistent Menu** for easy navigation.
- **🔄 2-Way Google Sheets Sync:** Real-time synchronization between the local SQLite database and your "LEAD Sige" Google Sheet using a high-performance Webhook architecture.
- **📝 Professional Lead Collection:** A structured conversation workflow that collects student profiles (Name, Phone, GPA, Birth Year, etc.) with a built-in **Edit Engine** for user corrections.

---

## 🛠️ Tech Stack

- **Backend:** Flask / FastAPI (Python 3.10+)
- **Bot Engine:** Facebook Graph API (v19+)
- **LLM Engine:** Ollama (Qwen 2.5 / Nomic-embed-text)
- **Database:** SQLite (Relational) + FAISS (Vector Store)
- **Integration:** Google Apps Script (Webhook bridge)

---

## 📦 Installation Guide

### 1. Prerequisites

- **Python 3.10 or higher**
- **Ollama** (Download from [ollama.com](https://ollama.com/))
- **Ngrok** (For exposing your local server to Facebook)
- **Facebook Developer Account**: A Page Access Token, Verify Token, and App Secret.

### 2. Setup Environment

Clone the repository and enter the project directory:

```bash
cd ai-agent-cs
python -m venv .venv
# Activate virtual environment
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

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
- `FB_PAGE_ACCESS_TOKEN`: From your Meta Developer Portal.
- `FB_VERIFY_TOKEN`: A string you define (e.g., `SIGE_BOT_2026`).
- `FB_APP_SECRET`: From your Meta App settings.
- `API_BASE_URL`: Your current Ngrok URL (e.g., `https://xxxx.ngrok-free.app`).
- `SIGE_LEADS_SHEET_ID`: The ID of your Google Sheet.

---

## 🚀 Automation & Startup Sequence

To make deployment as simple as possible, the project includes several automation scripts in the root directory. Follow this sequence for a complete setup:

### 1️⃣ Step 1: Initialize Facebook UI
Run this **once** (or whenever you change your menu/greeting) to configure the Messenger interface:
```bash
python run_setup.py
```
*Configures: Welcome Message, "Get Started" button, and the Persistent Menu.*

### 2️⃣ Step 2: Build the Knowledge Base
Process your markdown documents in `SIGE_KB/` to update the AI's "brain":
```bash
python start_ingest.py
```
*Creates: FAISS vector index and metadata for RAG retrieval.*

### 3️⃣ Step 3: Start the API Server (Backend)
Launch the FastAPI server to handle database initialization and Google Sheets sync:
```bash
python start_api_server.py
```
*Handles: `init_db()`, 2-way Google Sheets sync (Port 8000), and lead verification.*

### 4️⃣ Step 4: Start the AI Bot (Interface)
Finally, start the main interaction layer to begin chatting with students:
```bash
python start_bot.py
```
*Handles: Real-time Messenger chats, Lead Forms, and AI responses (Port 5000).*

---

## 🛠️ Script Summary

| Script | Function | Role |
| :--- | :--- | :--- |
| `run_setup.py` | Facebook Platform Setup | Configuration |
| `start_ingest.py` | RAG Knowledge Ingestion | AI Training |
| `start_api_server.py`| Lead Sync & DB initialization | Data Backend |
| `start_bot.py` | Messenger Webhook Handler | User Interface |

---

## 🧹 Maintenance & Tools

### Resetting the Database
If you need to clear your test data and restart the lead counter at #1:

```bash
python tmp/cleanup_db.py
```

### Deployment Diagnostics
Located in `backend/tools/`:
- `test_connection.py`: Verifies your Facebook Page Access Token.
- `check_subscriptions.py`: Ensures your Webhook is correctly linked to your Page.

---

## 👨‍💻 Project Structure (Backend)

- `backend/bot_server.py`: The primary Facebook Messenger handler (Flask).
- `backend/api_server.py`: The data-layer and sync handler (FastAPI).
- `backend/tools/`: Utility scripts for platform-specific setup and diagnostics.
- `backend/database/`: SQLite schema and data persistence logic.
- `backend/services/`: Core logic for LLM, RAG retrieval, and scripted answers.

---

**SIGE - Science Institute for Global Education**  
*Building Dreams, Connecting Global Talent.*
