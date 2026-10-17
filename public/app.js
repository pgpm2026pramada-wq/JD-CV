/* CareerMatch AI — front-end SPA */
"use strict";

const $ = (id) => document.getElementById(id);
const esc = (s) =>
  String(s ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

const state = { data: null, active: "overview" };

/* ---------------- File upload ---------------- */
async function handleUpload(fileInput, textArea, hintEl) {
  const file = fileInput.files[0];
  if (!file) return;
  hintEl.textContent = `Reading ${file.name}…`;
  hintEl.className = "hint";
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res = await fetch("/api/extract", { method: "POST", body: fd });
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || "Could not read file.");
    textArea.value = json.text;
    hintEl.textContent = `✓ Loaded ${file.name} (${json.text.length.toLocaleString()} chars)`;
    hintEl.className = "hint ok";
  } catch (err) {
    hintEl.textContent = err.message;
    hintEl.className = "hint err";
  }
}

$("jdFile").addEventListener("change", (e) =>
  handleUpload(e.target, $("jdText"), $("jdFileHint")));
$("cvFile").addEventListener("change", (e) =>
  handleUpload(e.target, $("cvText"), $("cvFileHint")));

/* ---------------- Analyze ---------------- */
const LOADING_STEPS = [
  "Reading the job description and CV",
  "Extracting requirements and candidate evidence",
  "Scoring fit across 8 dimensions",
  "Finding strengths, gaps and ATS keywords",
  "Writing interview questions and your story bank",
  "Researching the company with live web sources",
  "Assembling your readiness dashboard",
];

let stepTimer = null;
function runLoadingSteps() {
  let i = 0;
  $("loadingStep").textContent = LOADING_STEPS[0];
  stepTimer = setInterval(() => {
    i = Math.min(i + 1, LOADING_STEPS.length - 1);
    $("loadingStep").textContent = LOADING_STEPS[i];
  }, 4500);
}

$("analyzeBtn").addEventListener("click", analyze);

async function analyze() {
  const jdText = $("jdText").value.trim();
  const cvText = $("cvText").value.trim();
  const errEl = $("inputError");
  errEl.textContent = "";

  if (jdText.length < 40) { errEl.textContent = "Please add a job description."; return; }
  if (cvText.length < 40) { errEl.textContent = "Please add your CV."; return; }

  $("inputView").classList.add("hidden");
  $("loadingView").classList.remove("hidden");
  runLoadingSteps();

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ jdText, cvText }),
    });
    const json = await res.json();
    clearInterval(stepTimer);
    if (!res.ok) throw new Error(json.error || "Analysis failed.");
    state.data = json;
    renderResults();
  } catch (err) {
    clearInterval(stepTimer);
    $("loadingView").classList.add("hidden");
    $("inputView").classList.remove("hidden");
    errEl.textContent = err.message;
  }
}

$("newAnalysisBtn").addEventListener("click", () => {
  $("resultsView").classList.add("hidden");
  $("inputView").classList.remove("hidden");
  window.scrollTo(0, 0);
});

/* ---------------- Sample data ---------------- */
$("sampleBtn").addEventListener("click", () => {
  $("jdText").value = SAMPLE_JD;
  $("cvText").value = SAMPLE_CV;
  $("jdFileHint").textContent = "Sample job description loaded.";
  $("jdFileHint").className = "hint ok";
  $("cvFileHint").textContent = "Sample CV loaded.";
  $("cvFileHint").className = "hint ok";
});

/* ===================================================================
   RENDERING
   =================================================================== */
const NAV = [
  ["overview", "▦", "Overview"],
  ["jd", "▤", "JD Analysis"],
  ["cv", "▥", "CV Analysis"],
  ["fit", "◎", "Fit Score"],
  ["strengths", "✦", "Strengths & Gaps"],
  ["optimizer", "✎", "CV Optimizer"],
  ["interview", "❓", "Interview Questions"],
  ["case", "◈", "Case Interview Prep"],
  ["company", "▣", "Company Research"],
  ["industry", "◍", "Industry Research"],
  ["story", "✧", "Story Bank"],
  ["plan", "▦", "Preparation Plan"],
  ["readiness", "★", "Interview Readiness"],
];

function renderResults() {
  $("loadingView").classList.add("hidden");
  $("resultsView").classList.remove("hidden");

  const nav = $("nav");
  nav.innerHTML = "";
  NAV.forEach(([id, ic, label]) => {
    const b = document.createElement("button");
    b.innerHTML = `<span class="ic">${ic}</span> ${label}`;
    b.dataset.id = id;
    b.onclick = () => selectSection(id);
    nav.appendChild(b);
  });
  selectSection("overview");
}

function selectSection(id) {
  state.active = id;
  document.querySelectorAll(".nav button").forEach((b) =>
    b.classList.toggle("active", b.dataset.id === id));
  const host = $("sections");
  host.innerHTML = RENDERERS[id] ? RENDERERS[id]() : "<p>Section unavailable.</p>";
  bindCopyButtons();
  window.scrollTo(0, 0);
}

/* ---------- small building blocks ---------- */
const d = () => state.data.analysis;
const scoreColor = (v) => (v >= 75 ? "var(--good)" : v >= 50 ? "var(--warn)" : "var(--bad)");

function head(title, sub) {
  return `<div class="section-head"><h2>${esc(title)}</h2>${sub ? `<p>${esc(sub)}</p>` : ""}</div>`;
}
function list(arr, cls = "clean") {
  if (!arr || !arr.length) return `<p style="color:var(--faint)">None identified.</p>`;
  return `<ul class="${cls}">${arr.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`;
}
function tags(arr, cls = "") {
  if (!arr || !arr.length) return `<p style="color:var(--faint)">None.</p>`;
  return `<div class="tag-wrap">${arr.map((t) => `<span class="tag ${cls}">${esc(t)}</span>`).join("")}</div>`;
}
function ring(value, label) {
  const v = Math.max(0, Math.min(100, Number(value) || 0));
  const r = 62, c = 2 * Math.PI * r, off = c - (v / 100) * c;
  return `<div class="ring">
    <svg width="150" height="150">
      <circle cx="75" cy="75" r="${r}" fill="none" stroke="var(--bg-2)" stroke-width="12"/>
      <circle cx="75" cy="75" r="${r}" fill="none" stroke="${scoreColor(v)}" stroke-width="12"
        stroke-linecap="round" stroke-dasharray="${c}" stroke-dashoffset="${off}"/>
    </svg>
    <div class="ring-txt"><b>${v}</b><span>${esc(label)}</span></div>
  </div>`;
}
function bar(name, score, rationale, weight) {
  const v = Math.max(0, Math.min(100, Number(score) || 0));
  return `<div class="bar-row">
    <div class="bar-top"><span>${esc(name)}${weight ? ` <span style="color:var(--faint)">· ${weight}% weight</span>` : ""}</span><b style="color:${scoreColor(v)}">${v}</b></div>
    <div class="bar-track"><div class="bar-fill" style="width:${v}%;background:${scoreColor(v)}"></div></div>
    ${rationale ? `<div class="bar-rationale">${esc(rationale)}</div>` : ""}
  </div>`;
}
function qBlock(items) {
  if (!items || !items.length) return `<p style="color:var(--faint)">None generated.</p>`;
  return items.map((q) => `
    <details class="accordion">
      <summary><span>${esc(q.question)}</span> ${q.priority ? `<span class="pill ${esc(q.priority)}">${esc(q.priority)}</span>` : ""}</summary>
      <div class="acc-body">
        ${q.whatTheyEvaluate ? `<span class="lbl">What they're evaluating</span>${esc(q.whatTheyEvaluate)}` : ""}
        ${q.answerFramework ? `<span class="lbl">Answer framework</span>${esc(q.answerFramework)}` : ""}
        ${q.framework ? `<span class="lbl">Framework</span>${esc(q.framework)}` : ""}
        ${q.type ? `<span class="lbl">Case type</span>${esc(q.type)}` : ""}
      </div>
    </details>`).join("");
}
function mdToHtml(md) {
  if (!md) return `<p style="color:var(--faint)">No content available.</p>`;
  try { return window.marked.parse(md); } catch { return `<pre>${esc(md)}</pre>`; }
}

/* ---------- section renderers ---------- */
const RENDERERS = {
  overview() {
    const a = d(), r = a.readiness || {}, jd = a.jd || {};
    return head("Overview", `${jd.title || "Target role"}${jd.company ? " · " + jd.company : ""}`) + `
      <div class="verdict-banner">${esc(a.fit?.verdict || "Analysis complete. Explore each section from the sidebar.")}</div>
      <div class="grid-3">
        <div class="stat"><div class="label">Job Fit</div><div class="value" style="color:${scoreColor(r.fitScore ?? a.fit?.overall)}">${r.fitScore ?? a.fit?.overall ?? "—"}</div><div class="sub">JD ↔ CV alignment</div></div>
        <div class="stat"><div class="label">ATS Ready</div><div class="value" style="color:${scoreColor(r.atsScore ?? a.cvOptimizer?.atsScore)}">${r.atsScore ?? a.cvOptimizer?.atsScore ?? "—"}</div><div class="sub">Resume parse-ability</div></div>
        <div class="stat"><div class="label">Interview Ready</div><div class="value" style="color:${scoreColor(r.interviewReadinessScore)}">${r.interviewReadinessScore ?? "—"}</div><div class="sub">Preparation level</div></div>
      </div>
      <div class="grid-2">
        <div class="card"><h3>Strongest qualifications</h3>${list((r.strongestQualifications) || (a.strengths||[]).map(s=>s.title))}</div>
        <div class="card"><h3>Most important gaps</h3>${list(r.importantGaps || (a.gaps?.critical||[]).map(g=>g.gap))}</div>
      </div>
      <div class="card"><h3>Top 3 preparation priorities</h3>${list(r.topPriorities || a.prepPlan?.topThreeActions)}</div>
      <div class="callout">${esc(a.fit?.disclaimer || "This Fit Score estimates alignment between your CV and the JD. It is not a probability of being hired.")}</div>`;
  },

  jd() {
    const jd = d().jd || {};
    return head("Job Description Analysis", "Extracted from the posting you submitted") + `
      <div class="card">
        <div class="kv"><span class="k">Job title</span><span>${esc(jd.title || "—")}</span></div>
        <div class="kv"><span class="k">Company</span><span>${esc(jd.company || "Not specified")}</span></div>
        <div class="kv"><span class="k">Industry</span><span>${esc(jd.industry || "—")}</span></div>
        <div class="kv"><span class="k">Experience required</span><span>${esc(jd.experienceRequired || "—")}</span></div>
        ${jd.summary ? `<div class="kv"><span class="k">Summary</span><span>${esc(jd.summary)}</span></div>` : ""}
      </div>
      <div class="grid-2">
        <div class="card"><h3>Key responsibilities</h3>${list(jd.responsibilities)}</div>
        <div class="card"><h3>Qualifications</h3>${list(jd.qualifications)}</div>
      </div>
      <div class="card"><h3>Required skills</h3>${tags(jd.requiredSkills)}</div>
      <div class="grid-2">
        <div class="card"><h3>Preferred skills</h3>${tags(jd.preferredSkills)}</div>
        <div class="card"><h3>Tools & technologies</h3>${tags(jd.tools)}</div>
      </div>
      <div class="card"><h3>Domain knowledge</h3>${tags(jd.domainKnowledge)}</div>`;
  },

  cv() {
    const cv = d().cv || {};
    const expHtml = (cv.experience || []).map((e) => `
      <div class="card">
        <h3>${esc(e.role || "Role")} ${e.company ? `· ${esc(e.company)}` : ""} ${e.duration ? `<span style="color:var(--faint);font-weight:400">(${esc(e.duration)})</span>` : ""}</h3>
        ${list(e.highlights)}
      </div>`).join("") || `<p style="color:var(--faint)">No structured experience extracted.</p>`;
    return head("CV Analysis", `${cv.candidateName ? cv.candidateName + " — " : ""}extracted from your resume`) + `
      ${cv.summary ? `<div class="card"><h3>Profile summary</h3><p>${esc(cv.summary)}</p></div>` : ""}
      <h3 style="margin:8px 0 12px;font-size:18px">Experience</h3>${expHtml}
      <div class="grid-2">
        <div class="card"><h3>Skills</h3>${tags(cv.skills)}</div>
        <div class="card"><h3>Education</h3>${list(cv.education)}</div>
      </div>
      <div class="grid-2">
        <div class="card"><h3>Projects</h3>${list(cv.projects)}</div>
        <div class="card"><h3>Certifications</h3>${list(cv.certifications)}</div>
      </div>
      <div class="grid-2">
        <div class="card"><h3>Achievements</h3>${list(cv.achievements)}</div>
        <div class="card"><h3>Measurable results</h3>${list(cv.measurableResults)}</div>
      </div>`;
  },

  fit() {
    const f = d().fit || {};
    const rows = (f.requirementComparison || []).map((c) => `
      <tr>
        <td>${esc(c.requirement)}</td>
        <td><span class="pill ${esc(c.status)}">${esc(c.status)}</span></td>
        <td>${esc(c.evidence || "")}${c.note ? `<br><span style="color:var(--faint)">${esc(c.note)}</span>` : ""}</td>
      </tr>`).join("");
    return head("Fit Score", "AI-estimated alignment between your CV and the JD") + `
      <div class="card ring-wrap">
        ${ring(f.overall, "Fit Score")}
        <div style="flex:1;min-width:240px">
          <p style="font-size:15px;margin-bottom:10px">${esc(f.verdict || "")}</p>
          <div class="callout">${esc(f.disclaimer || "This score estimates JD↔CV alignment, not your probability of being hired.")}</div>
        </div>
      </div>
      <div class="card"><h3>Score breakdown (8 dimensions)</h3>
        ${(f.dimensions || []).map((dim) => bar(dim.name, dim.score, dim.rationale, dim.weight)).join("")}
      </div>
      <div class="card"><h3>Requirement-by-requirement comparison</h3>
        <div class="legend">
          <span><i style="background:var(--good)"></i> Strong match</span>
          <span><i style="background:var(--warn)"></i> Partial match</span>
          <span><i style="background:var(--bad)"></i> Gap</span>
        </div>
        <table class="tbl"><thead><tr><th>Requirement</th><th>Status</th><th>Evidence / note</th></tr></thead>
        <tbody>${rows || `<tr><td colspan="3" style="color:var(--faint)">No comparison available.</td></tr>`}</tbody></table>
      </div>`;
  },

  strengths() {
    const a = d(), g = a.gaps || {};
    const strengthCards = (a.strengths || []).map((s, i) => `
      <div class="card"><h3>${i + 1}. ${esc(s.title)}</h3><p style="color:var(--muted)">${esc(s.evidence)}</p></div>`).join("");
    const gapGroup = (arr, cls, title) => {
      if (!arr || !arr.length) return "";
      return `<h3 style="margin:16px 0 10px;font-size:17px"><span class="pill ${cls}">${title}</span></h3>` +
        arr.map((gap) => `
          <div class="card">
            <h3>${esc(gap.gap)}</h3>
            <p style="color:var(--muted);margin-bottom:8px"><b style="color:var(--text)">Why it matters:</b> ${esc(gap.importance)}</p>
            <p style="margin-bottom:8px"><b>How to address:</b> ${esc(gap.howToAddress)}</p>
            ${gap.resources && gap.resources.length ? `<div class="tag-wrap">${gap.resources.map((r) => `<span class="tag">${esc(r)}</span>`).join("")}</div>` : ""}
          </div>`).join("");
    };
    return head("Strengths & Gaps", "Your top 5 strengths and what's missing") + `
      <h3 style="margin-bottom:12px;font-size:18px">Top 5 strengths</h3>
      <div class="grid-2">${strengthCards || `<p style="color:var(--faint)">None identified.</p>`}</div>
      <h3 style="margin:24px 0 4px;font-size:18px">Gaps</h3>
      ${gapGroup(g.critical, "critical", "Critical")}
      ${gapGroup(g.moderate, "moderate", "Moderate")}
      ${gapGroup(g.minor, "minor", "Minor")}`;
  },

  optimizer() {
    const o = d().cvOptimizer || {};
    const weak = (o.weakStatements || []).map((w) => `
      <div class="rewrite">
        <div class="before">${esc(w.original)}</div>
        <div style="color:var(--faint);font-size:12.5px;margin:2px 0">Issue: ${esc(w.issue)}</div>
        <div class="after">${esc(w.improved)}</div>
      </div>`).join("") || `<p style="color:var(--faint)">No weak statements flagged.</p>`;
    const rewrites = (o.rewrittenBullets || []).map((w) => `
      <div class="rewrite"><div class="before">${esc(w.original)}</div><div class="after">${esc(w.improved)}</div></div>`).join("")
      || `<p style="color:var(--faint)">None.</p>`;
    return head("CV Optimizer", "ATS readiness, keywords, and a tailored rewrite") + `
      <div class="card ring-wrap">
        ${ring(o.atsScore, "ATS Score")}
        <div style="flex:1;min-width:240px"><p>${esc(o.atsExplanation || "")}</p></div>
      </div>
      <div class="card"><h3>Missing keywords & requirements</h3>${tags(o.missingKeywords, "missing")}</div>
      <div class="card"><h3>Weak / vague statements → stronger versions</h3>${weak}</div>
      <div class="card"><h3>Rewritten achievement bullets</h3>${rewrites}</div>
      ${o.infoNeeded && o.infoNeeded.length ? `<div class="callout warn"><b>Information you need to supply</b> (never invented): <br>${o.infoNeeded.map((x) => esc(x)).join("<br>")}</div>` : ""}
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
          <h3 style="margin:0">Tailored CV for this role</h3>
          <button class="copy-btn" data-copy="tailoredCv">Copy</button>
        </div>
        <div class="md" id="tailoredCv">${mdToHtml(o.tailoredCv)}</div>
      </div>`;
  },

  interview() {
    const iv = d().interview || {};
    const cat = (title, items) => `<div class="card"><h3>${title}</h3>${qBlock(items)}</div>`;
    return head("Interview Questions", "With evaluation criteria and answer frameworks — a ready-to-use questionnaire") + `
      ${iv.priorityQuestions && iv.priorityQuestions.length ? `<div class="callout"><b>Prioritize these first:</b><br>${iv.priorityQuestions.map((q) => esc(q)).join("<br>")}</div>` : ""}
      ${cat("HR & Behavioral", iv.hr)}
      ${cat("Based on your CV", iv.cvBased)}
      ${cat("Based on the JD", iv.jdBased)}
      ${cat("Company-specific", iv.companySpecific)}
      ${cat("Technical", iv.technical)}
      ${cat("Tough follow-ups", iv.toughFollowups)}`;
  },

  case() {
    const iv = d().interview || {};
    const jd = d().jd || {};
    const cases = iv.caseInterview || [];
    if (!cases.length) {
      return head("Case Interview Preparation", "") + `
        <div class="card"><p style="color:var(--muted)">No case interview questions were generated — this role${jd.isConsultingRole ? "" : " was not detected as a consulting role"}.
        Case prep covers profitability, market entry, growth, pricing, operations, market sizing, and general business problems. If you expect cases, re-run with a consulting JD.</p></div>`;
    }
    return head("Case Interview Preparation", "Consulting-style cases with frameworks") +
      `<div class="card">${qBlock(cases)}</div>`;
  },

  company() {
    const r = state.data.research || {};
    const { company, industry } = splitResearch(r.markdown || "");
    const sources = (r.sources || []);
    return head("Company Research", `${r.company || "Company"} — researched with live web sources`) + `
      ${r.error ? `<div class="callout warn">${esc(r.error)}</div>` : ""}
      <div class="card"><div class="md">${mdToHtml(company || r.markdown)}</div></div>
      ${sources.length ? `<div class="card"><h3>Sources</h3><div class="source-list">
        ${sources.map((s, i) => `<a href="${esc(s.uri)}" target="_blank" rel="noopener"><span class="num">${i + 1}.</span> ${esc(s.title)}</a>`).join("")}
      </div><p style="color:var(--faint);font-size:12px;margin-top:10px">Verify facts against primary sources before relying on them.</p></div>` : ""}`;
  },

  industry() {
    const r = state.data.research || {};
    const { industry } = splitResearch(r.markdown || "");
    return head("Industry Research", "Trends, challenges, regulation and technology shifts") + `
      ${r.error ? `<div class="callout warn">${esc(r.error)}</div>` : ""}
      <div class="card"><div class="md">${mdToHtml(industry || "Industry-specific sections appear here when available. See the Company Research tab for the full report.")}</div></div>`;
  },

  story() {
    const bank = d().storyBank || [];
    if (!bank.length) return head("Story Bank", "") + `<div class="card"><p style="color:var(--faint)">No stories generated.</p></div>`;
    return head("STAR Story Bank", "Built from your actual experiences — for behavioral questions") +
      bank.map((s) => `
        <details class="accordion">
          <summary><span>${esc(s.competency)}</span></summary>
          <div class="acc-body">
            <span class="lbl">Situation</span>${esc(s.situation)}
            <span class="lbl">Task</span>${esc(s.task)}
            <span class="lbl">Action</span>${esc(s.action)}
            <span class="lbl">Result</span>${esc(s.result)}
            ${s.note ? `<div class="callout warn" style="margin-top:12px">${esc(s.note)}</div>` : ""}
          </div>
        </details>`).join("") + `
      <div class="card" style="margin-top:20px"><h3>Career coaching answers</h3>${coachingBlock()}</div>`;
  },

  plan() {
    const p = d().prepPlan || {};
    const days = (p.days || []).map((day) => `
      <div class="day-card">
        <div class="day-head"><span class="day-num">${esc(day.day)}</span><h4>${esc(day.focus)}</h4></div>
        <span class="lbl" style="color:var(--accent);font-size:12px;font-weight:600">Tasks</span>${list(day.tasks)}
        ${day.practiceQuestions && day.practiceQuestions.length ? `<span class="lbl" style="color:var(--accent);font-size:12px;font-weight:600;display:block;margin-top:8px">Practice</span>${list(day.practiceQuestions)}` : ""}
        ${day.resources && day.resources.length ? `<div class="tag-wrap" style="margin-top:10px">${day.resources.map((r) => `<span class="tag">${esc(r)}</span>`).join("")}</div>` : ""}
      </div>`).join("");
    return head("7-Day Preparation Plan", "Tailored to your gaps and this role") + `
      ${days || `<p style="color:var(--faint)">No plan generated.</p>`}
      <div class="card"><h3>3 most effective actions to become more competitive</h3>${list(p.topThreeActions)}</div>`;
  },

  readiness() {
    const a = d(), r = a.readiness || {};
    return head("Interview Readiness Dashboard", "Your complete readiness snapshot") + `
      <div class="card ring-wrap">
        ${ring(r.fitScore ?? a.fit?.overall, "Job Fit")}
        ${ring(r.atsScore ?? a.cvOptimizer?.atsScore, "ATS Ready")}
        ${ring(r.interviewReadinessScore, "Interview Ready")}
      </div>
      <div class="grid-2">
        <div class="card"><h3>✦ Strongest qualifications</h3>${list(r.strongestQualifications)}</div>
        <div class="card"><h3>▲ Most important skill gaps</h3>${list(r.importantGaps)}</div>
      </div>
      <div class="grid-2">
        <div class="card"><h3>⚠ Biggest interview risks</h3>${list(r.interviewRisks)}</div>
        <div class="card"><h3>★ Competitive advantages</h3>${list(r.competitiveAdvantages)}</div>
      </div>
      <div class="card"><h3>Top 3 preparation priorities</h3>${list(r.topPriorities)}</div>`;
  },
};

function coachingBlock() {
  const c = d().coaching || {};
  const item = (label, text) => text ? `
    <details class="accordion"><summary><span>${label}</span></summary>
    <div class="acc-body">${esc(text)}</div></details>` : "";
  const flags = (c.redFlags || []).map((f) => `
    <div class="rewrite"><div style="font-weight:600;color:var(--warn)">⚠ ${esc(f.flag)}</div><div class="after">${esc(f.howToAddress)}</div></div>`).join("");
  return item("Tell me about yourself", c.tellMeAboutYourself) +
    item("Why this company?", c.whyThisCompany) +
    item("Why this role?", c.whyThisRole) +
    item("Why should we hire you?", c.whyHireYou) +
    (flags ? `<div style="margin-top:14px"><h3 style="font-size:14.5px;margin-bottom:8px">Potential CV red flags</h3>${flags}</div>` : "");
}

/* Split research markdown into company vs industry parts by heading. */
function splitResearch(md) {
  if (!md) return { company: "", industry: "" };
  const lines = md.split("\n");
  let company = [], industry = [], target = company;
  for (const line of lines) {
    if (/^#{1,3}\s/.test(line)) {
      const h = line.toLowerCase();
      target = /industry|trend|regulation|technolog|market shift/.test(h) ? industry : company;
    }
    target.push(line);
  }
  return { company: company.join("\n").trim(), industry: industry.join("\n").trim() };
}

function bindCopyButtons() {
  document.querySelectorAll("[data-copy]").forEach((btn) => {
    btn.onclick = () => {
      const src = d().cvOptimizer?.[btn.dataset.copy] || "";
      navigator.clipboard.writeText(src).then(() => {
        const t = btn.textContent; btn.textContent = "Copied!";
        setTimeout(() => (btn.textContent = t), 1500);
      });
    };
  });
}

/* ---------------- Sample data ---------------- */
const SAMPLE_JD = `Management Consultant — Strategy & Operations
Company: Bain & Company
Location: Mumbai, India

About the role:
We are seeking a Management Consultant to join our Strategy & Operations practice. You will work in small teams to solve complex business problems for Fortune 500 clients across growth strategy, market entry, pricing, and operational improvement.

Responsibilities:
- Structure and solve ambiguous business problems using hypothesis-driven analysis
- Build financial and operational models; synthesize insights from data
- Conduct market sizing, competitor analysis, and customer research
- Communicate recommendations to senior client stakeholders
- Manage workstreams and mentor junior analysts

Qualifications:
- MBA from a top-tier business school
- 2-4 years of experience in consulting, strategy, or analytics
- Strong quantitative and problem-solving skills
- Excellent communication and executive presence
- Experience with Excel, PowerPoint, and data tools (SQL/Tableau a plus)
- Demonstrated leadership and teamwork

Industry: Management Consulting`;

const SAMPLE_CV = `PRAMADA SHARAN
MBA Candidate (PGPM) | SP Jain Institute of Management & Research
Email: pramada@example.com | Mumbai

PROFILE
Analytical MBA candidate with 3 years of experience in business analytics and project management. Strong quantitative skills with a track record of driving measurable operational improvements.

EDUCATION
- PGPM (MBA), SP Jain Institute of Management & Research, 2024-2025
- B.Tech, Computer Science, VIT University, 2017-2021 (GPA 8.4/10)

EXPERIENCE
Business Analyst, TechCorp Solutions (2021-2024)
- Analyzed sales data across 5 regions and identified a pricing gap that improved margins by 12%
- Built automated Excel/SQL dashboards reducing monthly reporting time by 40%
- Led a cross-functional team of 6 to launch a new CRM process, improving lead conversion by 18%
- Presented quarterly insights to senior leadership

Intern, Operations, LogiServe (Summer 2020)
- Conducted a market sizing study for a new delivery service in 3 cities
- Mapped warehouse workflows and recommended changes cutting handling time by 15%

SKILLS
Excel, SQL, Tableau, PowerPoint, data analysis, problem-solving, stakeholder communication, project management

PROJECTS
- Capstone: Market entry strategy for an EV startup entering South India
- Built a profitability model for a retail client as part of an MBA case competition (2nd place)

ACHIEVEMENTS
- Runner-up, National B-School Case Competition 2024
- Promoted to Senior Analyst within 2 years`;
