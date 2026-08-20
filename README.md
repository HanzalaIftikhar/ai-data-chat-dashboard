# 📊 AI Sales Chat Assistant

An AI-powered dashboard that lets e-commerce sellers (Shopify, Etsy, Amazon) upload their sales data and instantly get business insights — plus a chat interface to ask questions about their data in plain English.

**🔗 Live Demo:** [ai-data-chat-dashboard-sx7ghgx8i7vmlncmtlwpof.streamlit.app](https://ai-data-chat-dashboard-sx7ghgx8i7vmlncmtlwpof.streamlit.app/)

---

## The Problem

Small e-commerce sellers export sales data from Shopify, Etsy, or Amazon as spreadsheets — but most don't have the time or skills to dig through rows of data in Excel to answer basic questions like *"What's my best-selling product?"* or *"Are my sales declining?"*

This tool closes that gap: upload a file, get an instant summary, and ask follow-up questions like you're talking to a business analyst.

---

## Features

- **Multi-platform column detection** — automatically recognizes sales export formats from Shopify, Etsy, Amazon, and generic retail exports, without requiring a specific template
- **Instant auto-summary on upload** — total revenue, top-performing products, and a notable trend insight, generated the moment a file is uploaded
- **Conversational Q&A powered by AI function calling** — instead of relying on a fixed set of pre-computed metrics, the AI dynamically queries the actual dataset for any question asked, ensuring answers are grounded in real numbers rather than guesses
- **Robust file handling** — gracefully handles missing columns, mixed encodings (UTF-8/Latin-1), empty files, and non-product entries (fees, adjustments) that can appear in raw exports
- **Production-style error handling** — clear, user-friendly messages instead of raw crashes (missing API keys, rate limits, corrupted files)

---

## How It Works

Upload CSV/Excel
│
▼
Detect platform-specific columns (Shopify / Etsy / Amazon / generic)
│
▼
Normalize to a standard schema
│
▼
Generate instant summary (revenue, top products, trend insight)
│
▼
Chat interface ──▶ AI decides if it needs real data ──▶ runs a live
query against the dataset ──▶ explains the result
in plain business language


The AI never guesses numbers. When a question requires a specific calculation, it requests a live query against the actual data (via function calling), and only then explains the result — keeping every number accurate.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Data processing | Pandas |
| AI / LLM | Groq API (Llama-based models) |
| Package management | uv |
| Secrets management | python-dotenv |
| Deployment | Streamlit Community Cloud |

---

## Project Structure

```
ai-data-chat-dashboard/
├── src/
│   ├── config.py           # Secure API key loading
│   ├── data_processing.py  # File reading, column detection, summary generation
│   ├── ai_engine.py        # AI chat engine with function calling
│   └── logger_config.py    # Centralized logging setup
├── app.py                  # Streamlit UI
├── requirements.txt
└── pyproject.toml
```

The architecture separates data logic, AI logic, and UI into independent modules — the AI engine and data processing layer have no dependency on Streamlit, making it straightforward to swap the frontend (e.g., to Flask or a custom UI) without touching the core logic.

## Running Locally

**Requirements:** Python 3.11+, a free [Groq API key](https://console.groq.com)

```bash
git clone https://github.com/HanzalaIftikhar/ai-data-chat-dashboard.git
cd ai-data-chat-dashboard
uv sync
```

Create a `.env` file in the project root:

GROQ_API_KEY=your_key_here


Run the app:
```bash
uv run streamlit run app.py
```

---

## Roadmap

- [ ] Support for additional platform export formats
- [ ] Custom theming and enhanced UI
- [ ] Multi-file comparison (month-over-month analysis)
- [ ] Export chat insights as a PDF report

---

## Author

Built by **Hanzala Iftikhar** — final-year CS student, freelance developer.
[GitHub](https://github.com/HanzalaIftikhar)