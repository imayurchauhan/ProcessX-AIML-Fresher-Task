# ProcessX Falls Management Compliance Checker

A working prototype for the ProcessX AIML interview task.

## What it does

Uploads a resident workbook (Excel), evaluates the 3-day post-fall progress notes against the Falls Management Policy, and produces a completed output sheet flagging every non-compliant field as **Missing**, **Incomplete**, or **Vague** — with a plain-English explanation for each flag.

## Architecture

```
Upload .xlsx
     │
     ▼
Excel Parser  →  Day notes extracted per resident
     │
     ▼
Evaluator  →  Groq LLM (llama-3.3-70b) if API key set
             └─ falls back to Rule-based engine per day if LLM fails
     │
     ▼
Report Generator  →  Styled Excel output + JSON response
```

## Evaluation engines

| Engine | How it works | When used |
|---|---|---|
| Groq LLM | Sends note to `llama-3.3-70b` with a structured prompt | When `GROQ_API_KEY` is set in `.env` |
| Rule-based | Phrase matching + regex against `policy_rules.py` | Fallback when LLM unavailable or fails |

The UI shows a live badge after each analysis — **Groq LLM** (purple) or **Rule-based** (teal).

## Accuracy

Tested against `Sample_Input_Output.xlsx` ground truth:

```
Precision : 100%   (no false alarms)
Recall    : 100%   (all issues caught)
F1 Score  : 100%
```

Run the accuracy test yourself:

```bash
# Rule-based
.venv\Scripts\python.exe -m backend.app.test_sample

# Groq LLM (requires API key)
.venv\Scripts\python.exe -m backend.app.test_sample --llm
```

## Requirements

- Python 3.13
- Node.js 20+ and npm

## Setup

1. Install dependencies and start:

```bash
npm install
npm run dev
```

2. (Optional) Add your Groq API key to enable LLM mode:

```
# .env
GROQ_API_KEY=gsk_your_key_here
```

Get a free key at https://console.groq.com

## Using the checker

1. Open `http://127.0.0.1:5173`
2. Upload a resident workbook (`.xlsx` with paired Input/Output sheets)
3. Click **Analyze workbook** — the engine badge shows which mode ran
4. Review findings per resident
5. Click **Download completed Excel** for the formatted output sheet

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check + active engine |
| GET | `/api/policy` | Policy summary |
| POST | `/api/analyze` | Analyze workbook, returns JSON findings |
| POST | `/api/generate-output` | Analyze and return styled Excel file |

## Key files

| File | Purpose |
|---|---|
| `backend/app/policy_rules.py` | All phrase lists and requirements |
| `backend/app/evaluator.py` | Rule engine + LLM orchestration |
| `backend/app/llm.py` | Groq API client with fresh key reading |
| `backend/app/report_generator.py` | Styled Excel output builder |
| `backend/app/test_sample.py` | Accuracy test against sample file |
| `frontend/src/App.tsx` | React UI with engine badge |
