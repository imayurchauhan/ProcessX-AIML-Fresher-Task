# ProcessX — AIML Fresher Interview Task

Welcome. This repo contains everything you need for your take-home task.  
Read this file fully before starting.Please feel free to Clone the repo and work

---

## What's in this repo

| File | What it is |
|---|---|
| `ProcessX_AIML_Task_Brief.docx` | Start here — the full task brief |
| `Falls_Management_Policy_ProcessX.docx` | The policy document — your source of truth for evaluation criteria |
| `Sample_Input_Output.xlsx` | Sample data with expected output — use this to build and validate |
| `Your_Output_File.xlsx` | The file your checker runs against — input notes for 4 residents, output sheets for you to fill |

---

## The task in one paragraph

Build a working checker that reads a nurse's daily progress note and flags whether it meets the documentation requirements in the Falls Management Policy. Each day's note is submitted separately — Day 1, Day 2, Day 3. The checker outputs what is missing or incomplete, specific enough that a nurse knows exactly what to fix. The policy is your source of truth. The sample file shows you what good output looks like.

---

## How to use the files

### Step 1 — Read the brief and the policy
`ProcessX_AIML_Task_Brief.docx` tells you what to build and what to submit.  
`Falls_Management_Policy_ProcessX.docx` tells you what the checker needs to evaluate against. Section 5 is the most important section.

### Step 2 — Study the sample
`Sample_Input_Output.xlsx` has four sheets:

| Sheet | What it contains |
|---|---|
| `John Doe - Input` | 3 days of progress notes — all correct, all complete |
| `John Doe - Output` | Expected checker output for John Doe — no flags raised |
| `Peter Parker - Input` | 3 days of progress notes — has missing and vague entries |
| `Peter Parker - Output` | Expected checker output for Peter Parker — flags raised across all 3 days |

Build your checker until it produces output that matches the Peter Parker expected output. John Doe is your sanity check — your checker should produce no flags for him.

### Step 3 — Run your checker on the real input
`Your_Output_File.xlsx` has 8 sheets — one input sheet and one output sheet per resident:

| Resident | Notes |
|---|---|
| Alice Nguyen | 3 days |
| Robert Singh | 3 days |
| Edna Kowalski | 3 days |
| Thomas Brennan | 3 days |

Run your checker on each resident's input sheet and fill in the corresponding `Your Output` sheet with the flags your checker produces. The output sheets are pre-formatted — same columns as the sample. Add rows as needed.

---

## What to submit

1. **Your GitHub repo** — must run with `npm install && npm run dev` (or equivalent). Include setup steps in your own README inside the repo.
2. **The completed `Your_Output_File.xlsx`** — with your checker's flags filled into all four output sheets.
3. **A decision log** — a short text file (bullet points are fine) covering:
   - How you structured the policy as input to your AI
   - One thing the AI suggested that you changed or rejected, and why
   - One decision the AI could not make for you and how you resolved it
4. **A Loom walkthrough (2–3 min)** — show your checker running on one of the residents, point to one part of your code, and explain why you wrote it that way.

---

## What we are evaluating

We are not evaluating polished code or a polished UI. A simple working solution is the right target.

What matters:
- You understood what the policy actually requires and used that to drive your solution
- You made deliberate decisions about how to pass the policy to the AI — and can explain them
- Your flags are specific and useful — not generic
- You can explain every part of your solution in the debrief

---

## In the interview

We will go through your output for one of the residents and ask you to explain how your checker arrived at each flag. We may also run an unseen set of notes through your checker live — be ready to predict what it will flag before you run it.

---

*Questions about the task? Email [psajjan@process-x.com.au] before the submission deadline.*
