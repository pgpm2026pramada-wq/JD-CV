"""Gemini-backed analysis for CareerMatch AI (Streamlit version).

Two calls: (1) a structured JSON analysis of JD + CV, and
(2) a Google-Search-grounded company/industry research call.
"""
from __future__ import annotations

import json
import os
import random
import re
import time

from google import genai
from google.genai import types


def _get_api_key() -> str:
    # Prefer Streamlit secrets when available, fall back to env var.
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        try:
            import streamlit as st

            key = st.secrets.get("GEMINI_API_KEY")  # type: ignore[attr-defined]
        except Exception:
            key = None
    if not key or key == "your_api_key_here":
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to Streamlit secrets "
            "(Settings → Secrets) or set it as an environment variable. "
            "Get a key at https://aistudio.google.com/apikey"
        )
    return key


_client: genai.Client | None = None


def _client_instance() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=_get_api_key())
    return _client


def _cfg(name: str, default: str) -> str:
    val = os.environ.get(name)
    if not val:
        try:
            import streamlit as st

            val = st.secrets.get(name)  # type: ignore[attr-defined]
        except Exception:
            val = None
    return val or default


def _analysis_model() -> str:
    return _cfg("GEMINI_MODEL", "gemini-flash-latest")


def _research_model() -> str:
    return _cfg("GEMINI_RESEARCH_MODEL", _analysis_model())


GROUND_RULES = """
STRICT RULES — follow all of them:
- Base every candidate-specific finding ONLY on the submitted CV. Never invent qualifications, experience, achievements, employers, numbers, dates, or skills the CV does not support.
- When you need information the CV does not contain, say so explicitly (use "infoNeeded" fields / "[ADD: ...]" placeholders) rather than fabricating.
- Consider transferable skills and adjacent experience, not just literal keyword matches.
- Always explain scores and major recommendations.
- The Fit Score is an estimate of alignment between the CV and the JD. It is NOT a probability of being hired. State this.
- Never assess suitability using protected characteristics (age, gender, race, religion, nationality, disability, marital/family status, etc.). Ignore any such signals.
- Clearly distinguish verified facts, assumptions, and AI-generated recommendations.
- Provide career guidance and decision support, not a final hiring decision.
"""

JSON_SHAPE = """
Return ONLY a single valid JSON object (no markdown, no backticks) with EXACTLY this shape:
{
  "jd": {
    "title": string, "company": string, "industry": string,
    "summary": string,
    "responsibilities": [string], "qualifications": [string],
    "requiredSkills": [string], "preferredSkills": [string],
    "experienceRequired": string, "tools": [string], "domainKnowledge": [string],
    "isConsultingRole": boolean
  },
  "cv": {
    "candidateName": string,
    "summary": string,
    "education": [string], "skills": [string], "projects": [string],
    "achievements": [string], "certifications": [string], "measurableResults": [string],
    "experience": [{"role": string, "company": string, "duration": string, "highlights": [string]}]
  },
  "fit": {
    "overall": number,
    "verdict": string,
    "disclaimer": string,
    "dimensions": [{"name": string, "score": number, "weight": number, "rationale": string}],
    "requirementComparison": [{"requirement": string, "status": "strong"|"partial"|"gap", "evidence": string, "note": string}]
  },
  "strengths": [{"title": string, "evidence": string}],
  "gaps": {
    "critical": [{"gap": string, "importance": string, "howToAddress": string, "resources": [string]}],
    "moderate": [{"gap": string, "importance": string, "howToAddress": string, "resources": [string]}],
    "minor": [{"gap": string, "importance": string, "howToAddress": string, "resources": [string]}]
  },
  "cvOptimizer": {
    "atsScore": number,
    "atsExplanation": string,
    "missingKeywords": [string],
    "weakStatements": [{"original": string, "issue": string, "improved": string}],
    "rewrittenBullets": [{"original": string, "improved": string}],
    "tailoredCv": string,
    "infoNeeded": [string]
  },
  "interview": {
    "hr": [{"question": string, "whatTheyEvaluate": string, "answerFramework": string, "priority": "high"|"medium"|"low"}],
    "cvBased": [{"question": string, "whatTheyEvaluate": string, "answerFramework": string, "priority": "high"|"medium"|"low"}],
    "jdBased": [{"question": string, "whatTheyEvaluate": string, "answerFramework": string, "priority": "high"|"medium"|"low"}],
    "companySpecific": [{"question": string, "whatTheyEvaluate": string, "answerFramework": string, "priority": "high"|"medium"|"low"}],
    "technical": [{"question": string, "whatTheyEvaluate": string, "answerFramework": string, "priority": "high"|"medium"|"low"}],
    "toughFollowups": [{"question": string, "whatTheyEvaluate": string, "answerFramework": string, "priority": "high"|"medium"|"low"}],
    "caseInterview": [{"question": string, "type": string, "framework": string, "priority": "high"|"medium"|"low"}],
    "priorityQuestions": [string]
  },
  "storyBank": [{"competency": string, "situation": string, "task": string, "action": string, "result": string, "note": string}],
  "coaching": {
    "tellMeAboutYourself": string,
    "whyThisCompany": string,
    "whyThisRole": string,
    "whyHireYou": string,
    "redFlags": [{"flag": string, "howToAddress": string}]
  },
  "prepPlan": {
    "days": [{"day": number, "focus": string, "tasks": [string], "practiceQuestions": [string], "resources": [string]}],
    "topThreeActions": [string]
  },
  "readiness": {
    "fitScore": number, "atsScore": number, "interviewReadinessScore": number,
    "strongestQualifications": [string], "importantGaps": [string],
    "interviewRisks": [string], "competitiveAdvantages": [string], "topPriorities": [string]
  }
}

Field guidance:
- fit.dimensions MUST include these 8 names: "Experience", "Skills", "Education", "Industry Knowledge", "Job Responsibilities", "Leadership", "Technical Skills", "Soft Skills". Each score is 0-100; weight is a percentage and the weights should sum to ~100.
- fit.overall is 0-100 and should reflect the weighted dimensions.
- fit.requirementComparison MUST NOT be empty: include one row for EVERY major JD requirement (aim for 8-15 rows), each marked "strong", "partial", or "gap" with specific CV evidence.
- strengths: exactly the top 5, each tied to concrete CV evidence.
- gaps: classify into critical/moderate/minor. "resources" = concrete, real, well-known learning resources (courses, docs, books) — never fabricated URLs; use names, not invented links.
- cvOptimizer.tailoredCv: a full tailored CV in Markdown, using ONLY real CV content; mark anything the candidate must add as "[ADD: ...]".
- interview: generate 4-6 questions per category. caseInterview: populate ONLY if jd.isConsultingRole is true (cover profitability, market entry, growth strategy, pricing, operations, market sizing, general business problem-solving); otherwise return [].
- storyBank: one STAR story per competency for: Leadership, Teamwork, Conflict, Failure, Problem-Solving, Initiative, Achievement — built from the candidate's ACTUAL experiences; if the CV lacks material for one, still include the entry with a "note" telling the candidate what experience to supply.
- prepPlan.days: exactly 7 entries (day 1-7).
- readiness scores are 0-100.
"""


def _with_retry(fn, tries: int = 4, base: float = 1.5):
    last_err: Exception | None = None
    for attempt in range(tries):
        try:
            return fn()
        except Exception as err:  # noqa: BLE001
            last_err = err
            msg = str(err)
            transient = re.search(
                r"\b(503|429|UNAVAILABLE|RESOURCE_EXHAUSTED|overloaded|high demand)\b",
                msg,
                re.IGNORECASE,
            )
            if not transient or attempt == tries - 1:
                break
            time.sleep(base * (2 ** attempt) + random.random() * 0.5)
    msg = str(last_err)
    if re.search(r"\b(503|UNAVAILABLE|overloaded|high demand)\b", msg, re.IGNORECASE):
        raise RuntimeError(
            "Gemini is temporarily overloaded (high demand). Please click Analyze again in a moment."
        )
    if re.search(r"\b(429|RESOURCE_EXHAUSTED)\b", msg, re.IGNORECASE):
        raise RuntimeError(
            "Gemini rate limit reached. Wait a minute and try again, or check your API quota."
        )
    raise last_err  # type: ignore[misc]


def _parse_model_json(raw: str) -> dict:
    """Parse model JSON, repairing a truncated response by closing open brackets."""
    if not raw:
        raise RuntimeError("Empty response from model.")
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.IGNORECASE).strip()
    try:
        return json.loads(cleaned)
    except Exception:  # noqa: BLE001
        pass

    start = cleaned.find("{")
    if start == -1:
        raise RuntimeError("No JSON object found in model response.")
    t = cleaned[start:]

    stack: list[str] = []
    in_str = False
    esc = False
    for ch in t:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if stack:
                stack.pop()

    repaired = t
    if in_str:
        repaired += '"'
    repaired = re.sub(r",\s*$", "", repaired)
    while stack:
        repaired += "}" if stack.pop() == "{" else "]"
    return json.loads(repaired)


def analyze_jd_cv(jd_text: str, cv_text: str) -> dict:
    client = _client_instance()
    prompt = f"""You are CareerMatch AI, an expert career coach, recruiter, and ATS specialist.
Analyze the following Job Description and Candidate CV.

{GROUND_RULES}

{JSON_SHAPE}

=== JOB DESCRIPTION ===
{jd_text}

=== CANDIDATE CV ===
{cv_text}

Return ONLY the JSON object."""

    def call():
        return client.models.generate_content(
            model=_analysis_model(),
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.4,
                max_output_tokens=48000,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )

    resp = _with_retry(call)
    return _parse_model_json(resp.text)


def research_company(company: str | None, industry: str | None, role: str | None) -> dict:
    client = _client_instance()
    target = company if (company and company.strip() and company.lower() != "unknown") else None

    prompt = f"""You are a company and industry research analyst. Use web search to find reliable, CURRENT information.

Research the company "{target or '(company not named in the JD — focus on the industry)'}" {f'in the "{industry}" industry' if industry else ''}, relevant to a candidate applying for the role of "{role or 'the target role'}".

Produce a clear, well-structured Markdown report with these sections (use ## headings):
## Company Overview & Business Model
## Products, Services & Key Markets
## Main Competitors
## Business Strategy & Growth Priorities
## Recent Announcements, Deals & Developments
  - Bullet each item and include the approximate date (month/year) and a source.
## Industry Trends, Challenges, Regulations & Technology Shifts
## Recent Articles & Reports Worth Reading

Rules:
- Use ONLY information you can support from search results. Never fabricate news, articles, companies, numbers, or sources.
- Distinguish clearly between VERIFIED FACTS and your own ANALYSIS/RECOMMENDATIONS (label analysis explicitly).
- Include approximate publication dates where possible.
- If you cannot verify the company, say so plainly and research the industry instead.
Keep it focused and genuinely useful for interview preparation."""

    def call():
        return client.models.generate_content(
            model=_research_model(),
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.3,
                max_output_tokens=8192,
            ),
        )

    resp = _with_retry(call)
    markdown = resp.text or ""

    sources: list[dict] = []
    try:
        chunks = resp.candidates[0].grounding_metadata.grounding_chunks or []
        for c in chunks:
            web = getattr(c, "web", None)
            if web and getattr(web, "uri", None):
                sources.append({"title": web.title or web.uri, "uri": web.uri})
    except Exception:  # noqa: BLE001
        pass

    seen = set()
    unique = []
    for s in sources:
        if s["uri"] in seen:
            continue
        seen.add(s["uri"])
        unique.append(s)

    return {"markdown": markdown, "sources": unique, "company": target}


def run_full_analysis(jd_text: str, cv_text: str) -> dict:
    analysis = analyze_jd_cv(jd_text, cv_text)
    research = {
        "markdown": "",
        "sources": [],
        "company": (analysis.get("jd") or {}).get("company"),
        "error": None,
    }
    try:
        jd = analysis.get("jd") or {}
        research = research_company(jd.get("company"), jd.get("industry"), jd.get("title"))
        research["error"] = None
    except Exception as err:  # noqa: BLE001
        research["error"] = str(err)
    return {"analysis": analysis, "research": research}
