# CareerMatch AI — JD & CV Matcher

An AI-powered career preparation platform that analyzes how well your CV fits a
job description, then builds a complete, ready-to-use interview prep report.
Powered by **Google Gemini** (with live Google Search grounding for company
research).

> This repo ships the app **two ways**:
> - **Streamlit** (`streamlit_app.py`) — deploy free on Streamlit Community Cloud ⬇️ see below
> - **Node/Express** (`server.js`) — run locally with `npm start`

---

## 🚀 Deploy on Streamlit Community Cloud (free)

1. Push this repo to GitHub (done).
2. Go to **https://share.streamlit.io** → sign in with GitHub.
3. **Create app** → pick this repo, branch `main`, main file **`streamlit_app.py`**.
4. Open **Advanced settings → Secrets** and paste:
   ```toml
   GEMINI_API_KEY = "your_gemini_key_here"
   ```
5. **Deploy** → in ~2 min you get a public URL like `https://<app>.streamlit.app`.

**Run the Streamlit app locally** (needs Python 3.10+):
```bash
pip install -r requirements.txt
# create .streamlit/secrets.toml from the example and add your key
streamlit run streamlit_app.py
```

> ⚠️ Anyone with the public URL can spend your Gemini quota — fine for a demo,
> but watch your usage in Google AI Studio.

---

## What it does

Submit a **Job Description** and your **CV** (paste text, or upload PDF / DOCX /
TXT) and get a navigable dashboard with:

| Section | What you get |
|---|---|
| **Overview** | Fit, ATS & interview-readiness scores at a glance |
| **JD Analysis** | Extracted title, company, responsibilities, skills, tools |
| **CV Analysis** | Extracted experience, skills, education, achievements |
| **Fit Score** | 0–100 score across 8 weighted dimensions + requirement-by-requirement comparison (strong / partial / gap) |
| **Strengths & Gaps** | Top 5 strengths with evidence; critical/moderate/minor gaps with fixes & resources |
| **CV Optimizer** | ATS score, missing keywords, weak-statement rewrites, and a tailored CV |
| **Interview Questions** | HR, CV-based, JD-based, company, technical & tough follow-ups — with evaluation criteria and answer frameworks |
| **Case Interview Prep** | Consulting-style cases (profitability, market entry, pricing, market sizing…) when the role is consulting |
| **Company Research** | Live, cited web research on the company |
| **Industry Research** | Trends, challenges, regulation and tech shifts |
| **Story Bank** | STAR stories from your real experience + career-coaching answers |
| **Preparation Plan** | A 7-day plan + the 3 highest-impact actions |
| **Interview Readiness** | Final dashboard with rings, risks and priorities |

## Setup

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Add your Gemini API key** — get one free at
   <https://aistudio.google.com/apikey>, then:
   ```bash
   copy .env.example .env
   ```
   Open `.env` and set `GEMINI_API_KEY=...`

3. **Run**
   ```bash
   npm start
   ```
   Open <http://localhost:3000>. Click **Load sample data** to try it instantly.

## Notes & guardrails

- Findings are based **only** on the CV you submit. The app is instructed never
  to invent qualifications, numbers, employers, or sources — where more info is
  needed it says so (look for `[ADD: …]` and the "information you need to supply"
  callouts).
- The **Fit Score estimates JD↔CV alignment — not your probability of being
  hired.**
- Company/industry research is grounded in Google Search; always verify facts
  against the linked primary sources.
- Legacy `.doc` files aren't reliably parseable — re-save as `.docx`, PDF, TXT,
  or paste the text.
- Your JD/CV are sent to Google's Gemini API for analysis and are not stored by
  this app.

## Tech

Node.js + Express · Google Gemini (`@google/genai`) · `pdf-parse` + `mammoth`
for file extraction · vanilla-JS single-page front-end.

## Config (`.env`)

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | — | **Required.** Your Gemini key |
| `PORT` | `3000` | Server port |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Model for structured analysis |
| `GEMINI_RESEARCH_MODEL` | `gemini-2.5-flash` | Model for grounded research |
