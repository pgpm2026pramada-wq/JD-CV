"""CareerMatch AI — Streamlit app.

JD & CV matcher, ATS checker, CV optimizer, company research assistant,
career coach, and interview preparation tool. Powered by Google Gemini.
"""
from __future__ import annotations

import html as _html

import streamlit as st

from backend import run_full_analysis
from extractors import extract_text

SAMPLE_JD = """Management Consultant — Strategy & Operations
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

Industry: Management Consulting"""

SAMPLE_CV = """PRAMADA SHARAN
MBA Candidate (PGPM) | SP Jain Institute of Management & Research
Mumbai

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
- Promoted to Senior Analyst within 2 years"""

st.set_page_config(
    page_title="CareerMatch AI",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------------
CSS = """
<style>
:root {
  --panel:#141c2e; --panel2:#1a2438; --border:#243049; --text:#e8edf6;
  --muted:#94a3bc; --faint:#64748b; --accent:#6366f1; --accent2:#8b5cf6;
  --good:#22c55e; --warn:#f59e0b; --bad:#ef4444;
}
.stApp { background:
  radial-gradient(1200px 600px at 80% -10%, rgba(99,102,241,0.12), transparent 60%),
  radial-gradient(900px 500px at -10% 10%, rgba(139,92,246,0.09), transparent 55%), #0b0f1a; }
.block-container { padding-top: 2.2rem; max-width: 1150px; }
h1,h2,h3,h4,p,li,span,div { color: var(--text); }
.brand-title { font-size:34px; font-weight:800; letter-spacing:-0.02em; margin:0; }
.brand-title .ai { background:linear-gradient(90deg,var(--accent),var(--accent2));
  -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }
.brand-sub { color:var(--muted); font-size:15px; margin-top:2px; }
.cm-card { background:var(--panel); border:1px solid var(--border); border-radius:14px;
  padding:18px 20px; margin-bottom:16px; }
.cm-card h3 { font-size:16px; font-weight:700; margin:0 0 10px; }
.stat { background:var(--panel); border:1px solid var(--border); border-radius:14px;
  padding:18px; text-align:center; }
.stat .label { color:var(--muted); font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:.04em; }
.stat .value { font-size:38px; font-weight:800; margin:6px 0 2px; }
.stat .sub { color:var(--faint); font-size:12px; }
.pill { display:inline-block; padding:3px 11px; border-radius:999px; font-size:12px; font-weight:600; }
.pill.strong,.pill.high { background:rgba(34,197,94,.15); color:#4ade80; }
.pill.partial,.pill.medium,.pill.moderate { background:rgba(245,158,11,.15); color:#fbbf24; }
.pill.gap,.pill.low,.pill.critical { background:rgba(239,68,68,.15); color:#f87171; }
.pill.minor { background:rgba(148,163,184,.15); color:var(--muted); }
.tag { display:inline-block; background:var(--panel2); border:1px solid var(--border);
  padding:4px 11px; border-radius:8px; font-size:13px; margin:0 6px 6px 0; }
.tag.missing { background:rgba(239,68,68,.1); border-color:rgba(239,68,68,.3); color:#f87171; }
.bar-top { display:flex; justify-content:space-between; font-size:13px; margin:12px 0 5px; }
.bar-track { height:9px; background:#0f1524; border-radius:6px; overflow:hidden; }
.bar-fill { height:100%; border-radius:6px; }
.bar-rat { color:var(--muted); font-size:12px; margin-top:4px; }
.kv { display:flex; gap:10px; padding:5px 0; font-size:14px; }
.kv .k { color:var(--muted); min-width:150px; font-weight:500; }
.callout { border-left:3px solid var(--accent); background:rgba(99,102,241,.07);
  padding:11px 15px; border-radius:0 10px 10px 0; font-size:13px; color:var(--muted); margin:12px 0; }
.callout.warn { border-color:var(--warn); background:rgba(245,158,11,.07); }
.verdict { background:linear-gradient(90deg,rgba(99,102,241,.14),rgba(139,92,246,.08));
  border:1px solid var(--border); border-radius:14px; padding:16px 20px; margin-bottom:16px; font-size:15px; }
.rw-before { color:var(--muted); font-size:13px; text-decoration:line-through; opacity:.7; }
.rw-after { font-size:14px; margin-top:3px; }
.rw-after:before { content:"→ "; color:var(--good); font-weight:700; }
.src a { color:#a5b4fc; font-size:13px; text-decoration:none; display:block;
  padding:8px 10px; background:#0f1524; border-radius:8px; border:1px solid var(--border); margin-bottom:7px; }
.cm-ul { margin:0; padding-left:0; list-style:none; }
.cm-ul li { padding:6px 0; border-bottom:1px solid var(--border); font-size:14px; }
.cm-ul li:last-child { border-bottom:none; }
.cm-ul li:before { content:"▸ "; color:var(--accent); }
section[data-testid="stSidebar"] { background:#0f1524; border-right:1px solid var(--border); }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def H(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def esc(x) -> str:
    return _html.escape(str(x if x is not None else ""))


def score_color(v) -> str:
    try:
        v = float(v)
    except Exception:  # noqa: BLE001
        return "var(--muted)"
    return "var(--good)" if v >= 75 else "var(--warn)" if v >= 50 else "var(--bad)"


def ul(items) -> str:
    if not items:
        return '<p style="color:var(--faint)">None identified.</p>'
    return '<ul class="cm-ul">' + "".join(f"<li>{esc(x)}</li>" for x in items) + "</ul>"


def tags(items, cls="") -> str:
    if not items:
        return '<p style="color:var(--faint)">None.</p>'
    return "".join(f'<span class="tag {cls}">{esc(t)}</span>' for t in items)


def stat(label, value, sub="") -> str:
    return (
        f'<div class="stat"><div class="label">{esc(label)}</div>'
        f'<div class="value" style="color:{score_color(value)}">{esc(value)}</div>'
        f'<div class="sub">{esc(sub)}</div></div>'
    )


def ring(value, label) -> str:
    try:
        v = max(0, min(100, int(round(float(value)))))
    except Exception:  # noqa: BLE001
        v = 0
    r = 62
    c = 2 * 3.14159 * r
    off = c - (v / 100) * c
    col = score_color(v)
    return f"""<div style="position:relative;width:150px;height:150px;margin:auto">
      <svg width="150" height="150" style="transform:rotate(-90deg)">
        <circle cx="75" cy="75" r="{r}" fill="none" stroke="#0f1524" stroke-width="12"/>
        <circle cx="75" cy="75" r="{r}" fill="none" stroke="{col}" stroke-width="12"
          stroke-linecap="round" stroke-dasharray="{c:.1f}" stroke-dashoffset="{off:.1f}"/>
      </svg>
      <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">
        <b style="font-size:34px;font-weight:800">{v}</b>
        <span style="font-size:12px;color:var(--muted)">{esc(label)}</span>
      </div></div>"""


def bar(name, score, rationale="", weight=None) -> str:
    try:
        v = max(0, min(100, int(round(float(score)))))
    except Exception:  # noqa: BLE001
        v = 0
    col = score_color(v)
    wt = f' · {weight}% weight' if weight else ""
    return (
        f'<div class="bar-top"><span>{esc(name)}<span style="color:var(--faint)">{wt}</span></span>'
        f'<b style="color:{col}">{v}</b></div>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{v}%;background:{col}"></div></div>'
        f'<div class="bar-rat">{esc(rationale)}</div>'
    )


def card(inner: str) -> str:
    return f'<div class="cm-card">{inner}</div>'


# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
st.session_state.setdefault("results", None)
st.session_state.setdefault("jd_input", "")
st.session_state.setdefault("cv_input", "")
st.session_state.setdefault("_load_sample", False)

if st.session_state._load_sample:
    st.session_state.jd_input = SAMPLE_JD  # noqa: F821  (defined at bottom)
    st.session_state.cv_input = SAMPLE_CV  # noqa: F821
    st.session_state._load_sample = False


# ----------------------------------------------------------------------------
# Input view
# ----------------------------------------------------------------------------
def input_view() -> None:
    H('<p class="brand-title">◆ CareerMatch <span class="ai">AI</span></p>'
      '<p class="brand-sub">Your all-in-one CV matcher, ATS checker, company researcher &amp; interview coach.</p>')
    st.write("")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Job Description")
        jd_file = st.file_uploader("Upload JD (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], key="jd_file")
        st.text_area("Or paste the job description", key="jd_input", height=260,
                     label_visibility="collapsed", placeholder="Paste the job description here…")
    with col2:
        st.subheader("Your CV / Resume")
        cv_file = st.file_uploader("Upload CV (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], key="cv_file")
        st.text_area("Or paste your CV", key="cv_input", height=260,
                     label_visibility="collapsed", placeholder="Paste your CV here…")

    c1, c2, _ = st.columns([1, 1, 3])
    analyze = c1.button("Analyze My Fit", type="primary", use_container_width=True)
    if c2.button("Load sample data", use_container_width=True):
        st.session_state._load_sample = True
        st.rerun()

    H('<p style="color:var(--faint);font-size:12.5px;margin-top:14px">CareerMatch AI gives career '
      'guidance and decision support — not hiring decisions. Findings are based only on the CV you '
      'submit; scores estimate JD↔CV alignment, not your odds of being hired.</p>')

    if analyze:
        # Resolve input text: uploaded file takes priority over pasted text.
        try:
            jd_text = (extract_text(jd_file.name, jd_file.getvalue()) if jd_file
                       else st.session_state.jd_input).strip()
            cv_text = (extract_text(cv_file.name, cv_file.getvalue()) if cv_file
                       else st.session_state.cv_input).strip()
        except Exception as err:  # noqa: BLE001
            st.error(f"Couldn't read a file: {err}")
            return

        if len(jd_text) < 40:
            st.error("Please provide a job description (at least a few lines).")
            return
        if len(cv_text) < 40:
            st.error("Please provide a CV (at least a few lines).")
            return

        with st.spinner("Analyzing your fit, researching the company, and building your prep report… "
                        "(this takes ~30–60s)"):
            try:
                st.session_state.results = run_full_analysis(jd_text, cv_text)
            except Exception as err:  # noqa: BLE001
                st.error(str(err))
                return
        st.rerun()


# ----------------------------------------------------------------------------
# Result sections
# ----------------------------------------------------------------------------
def sec_overview(a, r):
    rd = a.get("readiness", {}) or {}
    jd = a.get("jd", {}) or {}
    fit = a.get("fit", {}) or {}
    st.header("Overview")
    H(f'<p class="brand-sub">{esc(jd.get("title","Target role"))}'
      f'{" · " + esc(jd.get("company")) if jd.get("company") else ""}</p>')
    H(f'<div class="verdict">{esc(fit.get("verdict","Analysis complete. Explore each section from the sidebar."))}</div>')
    c1, c2, c3 = st.columns(3)
    c1.markdown(stat("Job Fit", rd.get("fitScore", fit.get("overall", "—")), "JD ↔ CV alignment"), unsafe_allow_html=True)
    c2.markdown(stat("ATS Ready", rd.get("atsScore", (a.get("cvOptimizer") or {}).get("atsScore", "—")), "Resume parse-ability"), unsafe_allow_html=True)
    c3.markdown(stat("Interview Ready", rd.get("interviewReadinessScore", "—"), "Preparation level"), unsafe_allow_html=True)
    st.write("")
    c1, c2 = st.columns(2)
    c1.markdown(card("<h3>Strongest qualifications</h3>" + ul(rd.get("strongestQualifications") or [s.get("title") for s in a.get("strengths", [])])), unsafe_allow_html=True)
    c2.markdown(card("<h3>Most important gaps</h3>" + ul(rd.get("importantGaps") or [g.get("gap") for g in (a.get("gaps", {}) or {}).get("critical", [])])), unsafe_allow_html=True)
    H(card("<h3>Top 3 preparation priorities</h3>" + ul(rd.get("topPriorities") or (a.get("prepPlan", {}) or {}).get("topThreeActions"))))
    H(f'<div class="callout">{esc(fit.get("disclaimer","This Fit Score estimates alignment between your CV and the JD. It is not a probability of being hired."))}</div>')


def sec_jd(a, r):
    jd = a.get("jd", {}) or {}
    st.header("Job Description Analysis")
    rows = "".join([
        f'<div class="kv"><span class="k">Job title</span><span>{esc(jd.get("title","—"))}</span></div>',
        f'<div class="kv"><span class="k">Company</span><span>{esc(jd.get("company","Not specified"))}</span></div>',
        f'<div class="kv"><span class="k">Industry</span><span>{esc(jd.get("industry","—"))}</span></div>',
        f'<div class="kv"><span class="k">Experience required</span><span>{esc(jd.get("experienceRequired","—"))}</span></div>',
        (f'<div class="kv"><span class="k">Summary</span><span>{esc(jd.get("summary"))}</span></div>' if jd.get("summary") else ""),
    ])
    H(card(rows))
    c1, c2 = st.columns(2)
    c1.markdown(card("<h3>Key responsibilities</h3>" + ul(jd.get("responsibilities"))), unsafe_allow_html=True)
    c2.markdown(card("<h3>Qualifications</h3>" + ul(jd.get("qualifications"))), unsafe_allow_html=True)
    H(card("<h3>Required skills</h3>" + tags(jd.get("requiredSkills"))))
    c1, c2 = st.columns(2)
    c1.markdown(card("<h3>Preferred skills</h3>" + tags(jd.get("preferredSkills"))), unsafe_allow_html=True)
    c2.markdown(card("<h3>Tools &amp; technologies</h3>" + tags(jd.get("tools"))), unsafe_allow_html=True)
    H(card("<h3>Domain knowledge</h3>" + tags(jd.get("domainKnowledge"))))


def sec_cv(a, r):
    cv = a.get("cv", {}) or {}
    st.header("CV Analysis")
    if cv.get("candidateName"):
        H(f'<p class="brand-sub">{esc(cv.get("candidateName"))}</p>')
    if cv.get("summary"):
        H(card("<h3>Profile summary</h3><p>" + esc(cv.get("summary")) + "</p>"))
    st.subheader("Experience")
    exp = cv.get("experience") or []
    if not exp:
        H('<p style="color:var(--faint)">No structured experience extracted.</p>')
    for e in exp:
        title = f'{esc(e.get("role","Role"))}'
        if e.get("company"):
            title += f' · {esc(e.get("company"))}'
        if e.get("duration"):
            title += f' <span style="color:var(--faint);font-weight:400">({esc(e.get("duration"))})</span>'
        H(card(f"<h3>{title}</h3>" + ul(e.get("highlights"))))
    c1, c2 = st.columns(2)
    c1.markdown(card("<h3>Skills</h3>" + tags(cv.get("skills"))), unsafe_allow_html=True)
    c2.markdown(card("<h3>Education</h3>" + ul(cv.get("education"))), unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.markdown(card("<h3>Projects</h3>" + ul(cv.get("projects"))), unsafe_allow_html=True)
    c2.markdown(card("<h3>Certifications</h3>" + ul(cv.get("certifications"))), unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.markdown(card("<h3>Achievements</h3>" + ul(cv.get("achievements"))), unsafe_allow_html=True)
    c2.markdown(card("<h3>Measurable results</h3>" + ul(cv.get("measurableResults"))), unsafe_allow_html=True)


def sec_fit(a, r):
    f = a.get("fit", {}) or {}
    st.header("Fit Score")
    c1, c2 = st.columns([1, 2])
    c1.markdown(ring(f.get("overall"), "Fit Score"), unsafe_allow_html=True)
    c2.markdown(
        f'<p style="font-size:15px">{esc(f.get("verdict",""))}</p>'
        f'<div class="callout">{esc(f.get("disclaimer","This score estimates JD↔CV alignment, not your probability of being hired."))}</div>',
        unsafe_allow_html=True,
    )
    bars = "".join(bar(d.get("name"), d.get("score"), d.get("rationale", ""), d.get("weight")) for d in f.get("dimensions", []))
    H(card("<h3>Score breakdown (8 dimensions)</h3>" + bars))
    comp = f.get("requirementComparison") or []
    rows = "".join(
        f'<tr><td style="padding:10px 12px;border-bottom:1px solid var(--border);vertical-align:top">{esc(c.get("requirement"))}</td>'
        f'<td style="padding:10px 12px;border-bottom:1px solid var(--border)"><span class="pill {esc(c.get("status"))}">{esc(c.get("status"))}</span></td>'
        f'<td style="padding:10px 12px;border-bottom:1px solid var(--border)">{esc(c.get("evidence",""))}'
        + (f'<br><span style="color:var(--faint)">{esc(c.get("note"))}</span>' if c.get("note") else "")
        + "</td></tr>"
        for c in comp
    )
    table = (
        '<table style="width:100%;border-collapse:collapse;font-size:13.5px">'
        '<thead><tr>'
        '<th style="text-align:left;color:var(--muted);padding:8px 12px;font-size:12px;text-transform:uppercase">Requirement</th>'
        '<th style="text-align:left;color:var(--muted);padding:8px 12px;font-size:12px;text-transform:uppercase">Status</th>'
        '<th style="text-align:left;color:var(--muted);padding:8px 12px;font-size:12px;text-transform:uppercase">Evidence / note</th>'
        '</tr></thead><tbody>' + (rows or '<tr><td style="padding:10px;color:var(--faint)">No comparison available.</td></tr>') + "</tbody></table>"
    )
    H(card("<h3>Requirement-by-requirement comparison</h3>" + table))


def sec_strengths(a, r):
    st.header("Strengths & Gaps")
    st.subheader("Top 5 strengths")
    strengths = a.get("strengths") or []
    cols = st.columns(2)
    for i, s in enumerate(strengths):
        cols[i % 2].markdown(card(f'<h3>{i+1}. {esc(s.get("title"))}</h3><p style="color:var(--muted)">{esc(s.get("evidence"))}</p>'), unsafe_allow_html=True)
    if not strengths:
        H('<p style="color:var(--faint)">None identified.</p>')
    st.subheader("Gaps")
    g = a.get("gaps", {}) or {}
    for key, cls, title in [("critical", "critical", "Critical"), ("moderate", "moderate", "Moderate"), ("minor", "minor", "Minor")]:
        arr = g.get(key) or []
        if not arr:
            continue
        H(f'<h3 style="margin:14px 0 8px"><span class="pill {cls}">{title}</span></h3>')
        for gap in arr:
            res = "".join(f'<span class="tag">{esc(x)}</span>' for x in (gap.get("resources") or []))
            H(card(
                f'<h3>{esc(gap.get("gap"))}</h3>'
                f'<p style="color:var(--muted);margin-bottom:6px"><b style="color:var(--text)">Why it matters:</b> {esc(gap.get("importance"))}</p>'
                f'<p style="margin-bottom:6px"><b>How to address:</b> {esc(gap.get("howToAddress"))}</p>' + res
            ))


def sec_optimizer(a, r):
    o = a.get("cvOptimizer", {}) or {}
    st.header("CV Optimizer")
    c1, c2 = st.columns([1, 2])
    c1.markdown(ring(o.get("atsScore"), "ATS Score"), unsafe_allow_html=True)
    c2.markdown(f'<p>{esc(o.get("atsExplanation",""))}</p>', unsafe_allow_html=True)
    H(card("<h3>Missing keywords &amp; requirements</h3>" + tags(o.get("missingKeywords"), "missing")))
    weak = "".join(
        f'<div style="margin-bottom:12px"><div class="rw-before">{esc(w.get("original"))}</div>'
        f'<div style="color:var(--faint);font-size:12px">Issue: {esc(w.get("issue"))}</div>'
        f'<div class="rw-after">{esc(w.get("improved"))}</div></div>'
        for w in (o.get("weakStatements") or [])
    ) or '<p style="color:var(--faint)">No weak statements flagged.</p>'
    H(card("<h3>Weak / vague statements → stronger versions</h3>" + weak))
    rw = "".join(
        f'<div style="margin-bottom:10px"><div class="rw-before">{esc(w.get("original"))}</div><div class="rw-after">{esc(w.get("improved"))}</div></div>'
        for w in (o.get("rewrittenBullets") or [])
    ) or '<p style="color:var(--faint)">None.</p>'
    H(card("<h3>Rewritten achievement bullets</h3>" + rw))
    if o.get("infoNeeded"):
        H('<div class="callout warn"><b>Information you need to supply</b> (never invented):<br>'
          + "<br>".join(esc(x) for x in o["infoNeeded"]) + "</div>")
    st.subheader("Tailored CV for this role")
    st.markdown(o.get("tailoredCv") or "_No tailored CV generated._")
    st.download_button("⬇ Download tailored CV (.md)", o.get("tailoredCv") or "", file_name="tailored_cv.md")


def _q_expanders(items):
    if not items:
        H('<p style="color:var(--faint)">None generated.</p>')
        return
    for q in items:
        prio = q.get("priority")
        label = q.get("question", "")
        with st.expander(f"{label}   ·   {prio}" if prio else label):
            if q.get("whatTheyEvaluate"):
                st.markdown(f"**What they're evaluating:** {q['whatTheyEvaluate']}")
            if q.get("answerFramework"):
                st.markdown(f"**Answer framework:** {q['answerFramework']}")
            if q.get("framework"):
                st.markdown(f"**Framework:** {q['framework']}")
            if q.get("type"):
                st.markdown(f"**Case type:** {q['type']}")


def sec_interview(a, r):
    iv = a.get("interview", {}) or {}
    st.header("Interview Questions")
    st.caption("A ready-to-use questionnaire with evaluation criteria and answer frameworks.")
    if iv.get("priorityQuestions"):
        H('<div class="callout"><b>Prioritize these first:</b><br>' + "<br>".join(esc(q) for q in iv["priorityQuestions"]) + "</div>")
    for title, key in [("HR & Behavioral", "hr"), ("Based on your CV", "cvBased"),
                       ("Based on the JD", "jdBased"), ("Company-specific", "companySpecific"),
                       ("Technical", "technical"), ("Tough follow-ups", "toughFollowups")]:
        st.subheader(title)
        _q_expanders(iv.get(key))


def sec_case(a, r):
    iv = a.get("interview", {}) or {}
    jd = a.get("jd", {}) or {}
    st.header("Case Interview Preparation")
    cases = iv.get("caseInterview") or []
    if not cases:
        note = "" if jd.get("isConsultingRole") else " This role was not detected as a consulting role."
        st.info("No case interview questions were generated." + note +
                " Case prep covers profitability, market entry, growth, pricing, operations and market sizing.")
        return
    _q_expanders(cases)


def _split_research(md: str):
    if not md:
        return "", ""
    company, industry, target = [], [], None
    import re as _re
    for line in md.split("\n"):
        if _re.match(r"^#{1,3}\s", line):
            low = line.lower()
            target = industry if _re.search(r"industry|trend|regulation|technolog|market shift", low) else company
        (target if target is not None else company).append(line)
    return "\n".join(company).strip(), "\n".join(industry).strip()


def sec_company(a, r):
    st.header("Company Research")
    st.caption(f'{r.get("company") or "Company"} — researched with live web sources')
    if r.get("error"):
        st.warning(r["error"])
    company_md, _ = _split_research(r.get("markdown", ""))
    st.markdown(company_md or r.get("markdown") or "_No research available._")
    srcs = r.get("sources") or []
    if srcs:
        st.subheader("Sources")
        H('<div class="src">' + "".join(
            f'<a href="{esc(s.get("uri"))}" target="_blank">{i+1}. {esc(s.get("title"))}</a>'
            for i, s in enumerate(srcs)) + "</div>")
        st.caption("Verify facts against primary sources before relying on them.")


def sec_industry(a, r):
    st.header("Industry Research")
    st.caption("Trends, challenges, regulation and technology shifts.")
    if r.get("error"):
        st.warning(r["error"])
    _, industry_md = _split_research(r.get("markdown", ""))
    st.markdown(industry_md or "Industry-specific sections appear here when available. See the Company Research tab for the full report.")


def sec_story(a, r):
    st.header("STAR Story Bank")
    st.caption("Built from your actual experiences — for behavioral questions.")
    for s in a.get("storyBank", []) or []:
        with st.expander(s.get("competency", "Story")):
            st.markdown(f"**Situation:** {s.get('situation','')}")
            st.markdown(f"**Task:** {s.get('task','')}")
            st.markdown(f"**Action:** {s.get('action','')}")
            st.markdown(f"**Result:** {s.get('result','')}")
            if s.get("note"):
                st.warning(s["note"])
    st.subheader("Career coaching answers")
    c = a.get("coaching", {}) or {}
    for label, key in [("Tell me about yourself", "tellMeAboutYourself"), ("Why this company?", "whyThisCompany"),
                       ("Why this role?", "whyThisRole"), ("Why should we hire you?", "whyHireYou")]:
        if c.get(key):
            with st.expander(label):
                st.write(c[key])
    if c.get("redFlags"):
        st.subheader("Potential CV red flags")
        for f in c["redFlags"]:
            H(f'<div style="margin-bottom:10px"><div style="font-weight:600;color:var(--warn)">⚠ {esc(f.get("flag"))}</div>'
              f'<div class="rw-after">{esc(f.get("howToAddress"))}</div></div>')


def sec_plan(a, r):
    p = a.get("prepPlan", {}) or {}
    st.header("7-Day Preparation Plan")
    st.caption("Tailored to your gaps and this role.")
    for day in p.get("days", []) or []:
        with st.expander(f"Day {day.get('day')} — {day.get('focus','')}", expanded=False):
            if day.get("tasks"):
                st.markdown("**Tasks**")
                for t in day["tasks"]:
                    st.markdown(f"- {t}")
            if day.get("practiceQuestions"):
                st.markdown("**Practice**")
                for q in day["practiceQuestions"]:
                    st.markdown(f"- {q}")
            if day.get("resources"):
                H("".join(f'<span class="tag">{esc(x)}</span>' for x in day["resources"]))
    H(card("<h3>3 most effective actions to become more competitive</h3>" + ul(p.get("topThreeActions"))))


def sec_readiness(a, r):
    rd = a.get("readiness", {}) or {}
    fit = a.get("fit", {}) or {}
    st.header("Interview Readiness Dashboard")
    c1, c2, c3 = st.columns(3)
    c1.markdown(ring(rd.get("fitScore", fit.get("overall")), "Job Fit"), unsafe_allow_html=True)
    c2.markdown(ring(rd.get("atsScore", (a.get("cvOptimizer") or {}).get("atsScore")), "ATS Ready"), unsafe_allow_html=True)
    c3.markdown(ring(rd.get("interviewReadinessScore"), "Interview Ready"), unsafe_allow_html=True)
    st.write("")
    c1, c2 = st.columns(2)
    c1.markdown(card("<h3>✦ Strongest qualifications</h3>" + ul(rd.get("strongestQualifications"))), unsafe_allow_html=True)
    c2.markdown(card("<h3>▲ Most important skill gaps</h3>" + ul(rd.get("importantGaps"))), unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.markdown(card("<h3>⚠ Biggest interview risks</h3>" + ul(rd.get("interviewRisks"))), unsafe_allow_html=True)
    c2.markdown(card("<h3>★ Competitive advantages</h3>" + ul(rd.get("competitiveAdvantages"))), unsafe_allow_html=True)
    H(card("<h3>Top 3 preparation priorities</h3>" + ul(rd.get("topPriorities"))))


SECTIONS = [
    ("Overview", sec_overview),
    ("JD Analysis", sec_jd),
    ("CV Analysis", sec_cv),
    ("Fit Score", sec_fit),
    ("Strengths & Gaps", sec_strengths),
    ("CV Optimizer", sec_optimizer),
    ("Interview Questions", sec_interview),
    ("Case Interview Prep", sec_case),
    ("Company Research", sec_company),
    ("Industry Research", sec_industry),
    ("Story Bank", sec_story),
    ("Preparation Plan", sec_plan),
    ("Interview Readiness", sec_readiness),
]


def results_view() -> None:
    data = st.session_state.results
    a = data.get("analysis", {}) or {}
    r = data.get("research", {}) or {}
    with st.sidebar:
        H('<p style="font-size:18px;font-weight:700;margin-bottom:12px">◆ CareerMatch '
          '<span class="ai" style="background:linear-gradient(90deg,var(--accent),var(--accent2));'
          '-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent">AI</span></p>')
        choice = st.radio("Sections", [s[0] for s in SECTIONS], label_visibility="collapsed")
        st.write("")
        if st.button("↻ New analysis", use_container_width=True):
            st.session_state.results = None
            st.rerun()
    for name, fn in SECTIONS:
        if name == choice:
            fn(a, r)
            break


# ----------------------------------------------------------------------------
# Router
# ----------------------------------------------------------------------------
if st.session_state.results:
    results_view()
else:
    input_view()
