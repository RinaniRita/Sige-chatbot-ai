# 🚀 Deployment Guide: SIGE AI Consultant Bot

This guide provides step-by-step instructions for deploying and running the **SIGE AI Agent** system.

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
- **Ollama**: [Download Ollama](https://ollama.com/)
- **Ngrok**: [Download Ngrok](https://ngrok.com/) (Required for local development and Google Sheets sync)
- **Telegram Bot Token**: Get one from [@BotFather](https://t.me/BotFather).

---

## 🛠️ Step 1: Initialize Project

1. **Clone & Enter Directory**:
   ```bash
   cd ai-agent-cs
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🧠 Step 2: Set Up Ollama Models

The AI uses **Qwen 2.5** for reasoning and **Nomic Embed Text** for searching your documentation.

1. **Start Ollama** (make sure the application is running).
2. **Download Models**:
   ```bash
   ollama pull qwen2.5:7b-instruct
   ollama pull nomic-embed-text
   ```

---

## 📝 Step 3: Configure Environment (.env)

1. **Create the `.env` file**:
   ```bash
   cp .env.example .env
   ```
2. **Edit `.env`** with your actual credentials:
   - `TELEGRAM_BOT_TOKEN`: Your token from BotFather.
   - `SIGE_LEADS_SHEET_ID`: The ID from your Google Sheet URL.
   - `GOOGLE_SHEETS_WEBHOOK_URL`: (Wait for Step 4).

---

## 📊 Step 4: Google Sheets Webhook

To sync leads from the bot to your spreadsheet:

1. **Open Spreadsheet**: Open your "LEAD Sige" sheet.
2. **Apps Script**: Go to **Extensions > Apps Script**.
3. **Copy Source**: Copy the code from `backend/services/sheets_sync.gs`.
4. **Deploy**:
   - Click **Deploy > New Deployment**.
   - Select **Web App**.
   - **Execute as**: Me.
   - **Who has access**: Anyone.
   - Click **Deploy** and copy the **Web App URL**.
5. **Update .env**: Paste this URL into `GOOGLE_SHEETS_WEBHOOK_URL` in your `.env`.

---

## 📚 Step 5: Ingest Knowledge Base

Build the AI's memory from your SIGE documents:

```bash
python -m backend.data_scripts.ingest_sige
```

---

## 🚀 Step 6: Start the Services

You need to run **two** separate commands in **two** terminals:

1. **Terminal 1: Start API Server** (Handles incoming Google Sheets data):
   ```bash
   python start_api_server.py
   ```

2. **Terminal 2: Start Telegram Bot** (The AI interface):
   ```bash
   python start_telegram_bot.py
   ```

---

## 🔍 Troubleshooting

- **Bot not responding?**: Check if Ollama is running and your `TELEGRAM_BOT_TOKEN` is correct.
- **Data not in Sheets?**: Ensure the Apps Script "Web App URL" is correctly pasted in `.env` and that you've deployed it with "Access: Anyone".
- **Incorrect Column?**: If you change your spreadsheet layout, remember to update the indices in the Apps Script and redeploy.

---

**SIGE AI Agent v1.0**  
*Professional Education Consultant Systems*
