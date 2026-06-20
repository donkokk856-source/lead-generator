# 🗺️ Google Maps Lead Generator & AI Analyzer

An automated pipeline that scrapes business leads from Google Maps, qualifies them using AI, and routes the results into Google Sheets, Notion, and Telegram — built for outreach by web design / automation agencies.

## 🎯 What it does

1. **Scrapes** businesses from Google Maps by niche + location (e.g. "hotels in Kochi")
2. **Extracts** name, phone, email, website, rating, reviews, and address
3. **Stores** raw leads in Google Sheets
4. **Analyzes** each lead with Google Gemini AI to score how likely they need a new/redesigned website
5. **Outputs** a qualified lead list — with lead score, reasoning, approach strategy, and a ready-to-send outreach message — into Google Sheets and Notion

## 🏗️ Architecture

```
Telegram Trigger (e.g. "hotels Kochi 10")
        │
        ▼
n8n Code Node → parses niche / location / count
        │
        ▼
FastAPI (Python + Playwright) → scrapes Google Maps
        │
        ▼
n8n Split Out → Google Sheets (raw leads)
        │
        ▼
Google Gemini AI → lead scoring + outreach strategy
        │
        ▼
n8n Code Node → parses AI JSON response
        │
        ├──► Google Sheets (qualified leads)
        └──► Notion Database (qualified leads)
```

## 🧩 Tech Stack

| Layer | Tool |
|---|---|
| Scraper | Python, Playwright |
| API | FastAPI |
| Automation | n8n (Docker) |
| AI Analysis | Google Gemini |
| Storage | Google Sheets, Notion |
| Trigger / Notify | Telegram Bot |
| Tunneling | ngrok |

## 📁 Project Structure

```
lead-generator/
├── scraper/
│   ├── google_maps.py        # Searches & scrolls Google Maps results
│   ├── business_scraper.py   # Extracts details per business
│   ├── email_finder.py       # Finds email/socials from business website
│   └── csv_exporter.py       # Saves scraped data to CSV
├── n8n-workflows/
│   └── lead-gen-workflow.json   # Full n8n automation (import into n8n)
├── api.py                    # FastAPI endpoint wrapping the scraper
├── main.py                   # CLI version of the scraper
├── requirements.txt
└── .gitignore
```

## ⚙️ Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
playwright install
```

### 2. Run the scraper API
```bash
uvicorn api:app --reload --port 8000
```

### 3. Run n8n (Docker)
```bash
docker run -d --name n8n -p 5678:5678 \
  -e WEBHOOK_URL=https://your-ngrok-url.ngrok-free.dev \
  -e N8N_EDITOR_BASE_URL=https://your-ngrok-url.ngrok-free.dev \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n:latest
```

### 4. Expose it publicly (for Telegram webhook)
```bash
ngrok http 5678
```

### 5. Import the workflow
In n8n: **Workflows → Import from File** → select `n8n-workflows/lead-gen-workflow.json`, then connect your own credentials for Google Sheets, Gemini, Notion, and Telegram.

## 🔑 Required Credentials

- Google Sheets OAuth (or Service Account)
- Google Gemini API key — [aistudio.google.com](https://aistudio.google.com)
- Notion Internal Integration token
- Telegram Bot token

> None of these are stored in the workflow JSON — only credential references. You'll need to reconnect each one in your own n8n instance.

## 🚀 Usage

Send a message to your Telegram bot in the format:
```
hotels Kochi 10
```
`niche` `location` `count` — and the pipeline runs end-to-end automatically.

## 📄 License

Private / personal project.
