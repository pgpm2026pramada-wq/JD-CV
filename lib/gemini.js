// Gemini-backed analysis for CareerMatch AI.
// Two calls: (1) a structured JSON analysis of JD + CV, and
// (2) a Google-Search-grounded company/industry research call.
import { GoogleGenAI } from "@google/genai";

let client = null;
function getClient() {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey || apiKey === "your_api_key_here") {
    throw new Error(
      "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key from https://aistudio.google.com/apikey"
    );
  }
  if (!client) client = new GoogleGenAI({ apiKey });
  return client;
}

// Retry transient Gemini errors (503 overloaded, 429 rate limit) with backoff.
async function withRetry(fn, { tries = 4, baseMs = 1500 } = {}) {
  let lastErr;
  for (let attempt = 0; attempt < tries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      const msg = String(err?.message || err);
      const transient = /\b(503|429|UNAVAILABLE|RESOURCE_EXHAUSTED|overloaded|high demand)\b/i.test(msg);
      if (!transient || attempt === tries - 1) break;
      const wait = baseMs * Math.pow(2, attempt) + Math.random() * 500;
      await new Promise((r) => setTimeout(r, wait));
    }
  }
  const m = String(lastErr?.message || lastErr);
  if (/\b(503|UNAVAILABLE|overloaded|high demand)\b/i.test(m)) {
    throw new Error("Gemini is temporarily overloaded (high demand). Please click Analyze again in a moment.");
  }
  if (/\b(429|RESOURCE_EXHAUSTED)\b/i.test(m)) {
    throw new Error("Gemini rate limit reached. Wait a minute and try again, or check your API quota.");
  }
  throw lastErr;
}

const ANALYSIS_MODEL = () => process.env.GEMINI_MODEL || "gemini-2.5-flash";
const RESEARCH_MODEL = () =>
  process.env.GEMINI_RESEARCH_MODEL || process.env.GEMINI_MODEL || "gemini-2.5-flash";

const GROUND_RULES = `
STRICT RULES — follow all of them:
- Base every candidate-specific finding ONLY on the submitted CV. Never invent qualifications, experience, achievements, employers, numbers, dates, or skills the CV does not support.
- When you need information the CV does not contain, say so explicitly (use "infoNeeded" fields / "[ADD: ...]" placeholders) rather than fabricating.
- Consider transferable skills and adjacent experience, not just literal keyword matches.
- Always explain scores and major recommendations.
- The Fit Score is an estimate of alignment between the CV and the JD. It is NOT a probability of being hired. State this.
- Never assess suitability using protected characteristics (age, gender, race, religion, nationality, disability, marital/family status, etc.). Ignore any such signals.
- Clearly distinguish verified facts, assumptions, and AI-generated recommendations.
- Provide career guidance and decision support, not a final hiring decision.
`;

const JSON_SHAPE = `
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
`;

function stripFences(text) {
  return String(text || "")
    .trim()
    .replace(/^```(?:json)?\s*/i, "")
    .replace(/\s*```$/i, "")
    .trim();
}

// Parse model JSON, repairing a truncated response by closing any open
// strings/brackets so a cut-off reply still yields a usable object.
function parseModelJson(raw) {
  if (!raw) throw new Error("Empty response from model.");
  const cleaned = stripFences(raw);
  try {
    return JSON.parse(cleaned);
  } catch {
    /* fall through to repair */
  }

  const start = cleaned.indexOf("{");
  if (start === -1) throw new Error("No JSON object found in model response.");
  let t = cleaned.slice(start);

  // Walk the string tracking structure so we can close what's left open.
  const stack = [];
  let inStr = false, esc = false;
  for (let i = 0; i < t.length; i++) {
    const ch = t[i];
    if (inStr) {
      if (esc) esc = false;
      else if (ch === "\\") esc = true;
      else if (ch === '"') inStr = false;
      continue;
    }
    if (ch === '"') inStr = true;
    else if (ch === "{" || ch === "[") stack.push(ch);
    else if (ch === "}" || ch === "]") stack.pop();
  }

  let repaired = t;
  if (inStr) repaired += '"';
  repaired = repaired.replace(/,\s*$/, "");
  while (stack.length) {
    repaired += stack.pop() === "{" ? "}" : "]";
  }
  return JSON.parse(repaired);
}

/**
 * Structured JD + CV analysis.
 * @param {string} jdText
 * @param {string} cvText
 */
export async function analyzeJdCv(jdText, cvText) {
  const ai = getClient();
  const prompt = `You are CareerMatch AI, an expert career coach, recruiter, and ATS specialist.
Analyze the following Job Description and Candidate CV.

${GROUND_RULES}

${JSON_SHAPE}

=== JOB DESCRIPTION ===
${jdText}

=== CANDIDATE CV ===
${cvText}

Return ONLY the JSON object.`;

  const resp = await withRetry(() =>
    ai.models.generateContent({
      model: ANALYSIS_MODEL(),
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        temperature: 0.4,
        maxOutputTokens: 48000,
        // Disable "thinking" so the whole output budget goes to the JSON reply
        // (prevents truncation mid-object on large reports).
        thinkingConfig: { thinkingBudget: 0 },
      },
    })
  );

  return parseModelJson(resp.text);
}

/**
 * Grounded company + industry research using Google Search.
 * @param {string} company
 * @param {string} industry
 * @param {string} role
 */
export async function researchCompany(company, industry, role) {
  const ai = getClient();
  const target = company && company.trim() && company.toLowerCase() !== "unknown"
    ? company
    : null;

  const prompt = `You are a company and industry research analyst. Use web search to find reliable, CURRENT information.

Research the company "${target || "(company not named in the JD — focus on the industry)"}" ${industry ? `in the "${industry}" industry` : ""}, relevant to a candidate applying for the role of "${role || "the target role"}".

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
Keep it focused and genuinely useful for interview preparation.`;

  const resp = await withRetry(() =>
    ai.models.generateContent({
      model: RESEARCH_MODEL(),
      contents: prompt,
      config: {
        tools: [{ googleSearch: {} }],
        temperature: 0.3,
        maxOutputTokens: 8192,
      },
    })
  );

  const markdown = resp.text || "";

  // Pull grounding sources if present.
  const sources = [];
  try {
    const gm = resp.candidates?.[0]?.groundingMetadata;
    const chunks = gm?.groundingChunks || [];
    for (const c of chunks) {
      if (c.web?.uri) {
        sources.push({ title: c.web.title || c.web.uri, uri: c.web.uri });
      }
    }
  } catch {
    /* no grounding metadata */
  }

  // De-duplicate sources by uri.
  const seen = new Set();
  const uniqueSources = sources.filter((s) => {
    if (seen.has(s.uri)) return false;
    seen.add(s.uri);
    return true;
  });

  return { markdown, sources: uniqueSources, company: target };
}
