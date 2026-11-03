"""SkillLens AI — AI-powered Career Guidance.

This module renders only the Career Guidance page; it does not create or modify
sidebar navigation, the sidebar logo, or the app shell. It generates role-specific
career roadmaps for a wide range of occupations using
a locally running Ollama model. No paid API key is required.
"""

import json
import re
import html
import requests
import streamlit as st


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.2"


def _safe_text(value):
    """Escape user/model text before placing it inside HTML."""
    return html.escape(str(value or ""))


def _career_prompt(role, experience, weekly_hours):
    return f"""
You are the career guidance engine inside SkillLens AI.
Create a practical, accurate, detailed career roadmap for this target role:
"{role}"

User's current level: {experience}
Study time available: {weekly_hours} per week.

The role may be from ANY legitimate industry or function (technology, business,
finance, healthcare, design, engineering, education, operations, law, marketing,
trades, public sector, science, etc.). Do not assume the role is a technology role.
If the title is broad or ambiguous, state the most common interpretation and
briefly mention that specialisations may differ. Do not invent mandatory
certifications, legal requirements, salaries, or guaranteed timelines.

Return ONLY valid JSON with exactly this structure:
{{
  "role_title": "clear role title",
  "role_summary": "plain-language explanation of what this professional does",
  "day_to_day": ["5 to 7 realistic daily responsibilities"],
  "work_outputs": ["4 to 6 examples of deliverables or outcomes"],
  "skills": [
    {{"category": "skill group", "items": ["specific skill", "specific skill"], "why": "why this group matters"}}
  ],
  "phases": [
    {{
      "title": "phase title",
      "duration": "suggested duration",
      "objective": "what the learner should achieve",
      "topics": ["specific topics to learn"],
      "practice": ["practical exercise"],
      "project": "one portfolio or workplace-style project",
      "milestone": "observable evidence that the learner is ready to continue"
    }}
  ],
  "portfolio_projects": [
    {{"title": "project name", "description": "what to build and what it demonstrates"}}
  ],
  "career_progression": [
    {{"title": "next role or specialisation", "level": "typical experience band", "description": "how the role can progress"}}
  ],
  "tools_and_resources": [
    {{"name": "tool, platform, standard or resource type", "purpose": "how it is used"}}
  ],
  "job_readiness": ["interview or job-search preparation actions"],
  "important_note": "role-specific caveat, specialisation note or responsible-practice reminder",
  "estimated_plan": "realistic suggested duration, explicitly not a guarantee"
}}

Quality requirements:
- Include 5 to 8 progressive phases, from foundations to job readiness.
- Every phase must have a meaningful, specific title; an objective of 2 to 3 sentences;
  4 to 7 concrete topics; 2 to 4 hands-on practice tasks; a realistic project brief
  with expected deliverables; and a measurable milestone. Avoid vague phrases such as
  "learn the basics" or "complete this stage".
- Tailor every skill, exercise and project to the requested occupation.
- Distinguish essential skills from optional/specialist tools where appropriate.
- Include practical work, not just course topics.
- Include 3 to 5 realistic career progression options in career_progression, from early-career to senior or adjacent specialisations.
- Avoid generic filler and avoid claiming the roadmap guarantees employment.
- If the occupation is regulated, explain that local licensing/qualification rules
  must be checked with the relevant authority; do not give legal advice.
- Keep each list concise, useful and specific.
"""


def _generate_roadmap(role, experience, weekly_hours, model):
    payload = {
        "model": model,
        "prompt": _career_prompt(role, experience, weekly_hours),
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.25},
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=240)
    response.raise_for_status()
    body = response.json()
    raw = body.get("response", "")
    data = json.loads(raw)
    required = ["role_title", "role_summary", "day_to_day", "skills", "phases"]
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError("The AI response is missing: " + ", ".join(missing))
    if not isinstance(data["phases"], list) or not data["phases"]:
        raise ValueError("The AI did not return any roadmap phases.")
    return data


def _section_heading(kicker, title, subtitle):
    st.markdown(
        f"""
        <div style="margin:24px 0 12px;">
          <div style="font-size:10px;font-weight:850;letter-spacing:2px;color:#8652B5;">{_safe_text(kicker)}</div>
          <div style="font-size:23px;font-weight:850;color:#291044;margin-top:3px;">{_safe_text(title)}</div>
          <div style="font-size:13px;color:#756681;margin-top:4px;">{_safe_text(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_bullets(items):
    if not isinstance(items, list):
        return
    for item in items:
        st.markdown(f"- {item}")


def _tool_logo(name):
    """Return a recognisable brand logo, with a second SVG and favicon fallback."""
    value = re.sub(r"[^a-z0-9]+", " ", str(name).lower()).strip()

    # (match pattern, Simple Icons slug, brand colour, official domain, Devicon slug)
    # Use the dedicated Devicon SVG as the first source where available. The
    # Simple Icons SVG is the second source; the official-domain favicon is last.
    rules = [
        (r"\bpower\s*bi\b", "powerbi", "F2C811", "powerbi.microsoft.com", "powerbi"),
        (r"\btableau\b", "tableau", "E97627", "tableau.com", "tableau"),
        (r"\bpython\b", "python", "3776AB", "python.org", "python"),
        (r"\btensor\s*flow\b", "tensorflow", "FF6F00", "tensorflow.org", "tensorflow"),
        (r"\bpytorch\b|\btorch\b", "pytorch", "EE4C2C", "pytorch.org", "pytorch"),
        (r"\bkeras\b", "keras", "D00000", "keras.io", "keras"),
        (r"\bscikit[ -]?learn\b|\bsklearn\b", "scikitlearn", "F7931E", "scikit-learn.org", "scikitlearn"),
        (r"\bjupyter(?:\s*notebook|\s*lab)?\b", "jupyter", "F37626", "jupyter.org", "jupyter"),
        (r"\bkaggle\b", "kaggle", "20BEFF", "kaggle.com", "kaggle"),
        (r"\bkubernetes\b|\bk8s\b", "kubernetes", "326CE5", "kubernetes.io", "kubernetes"),
        (r"\baws\b|amazon web services", "amazonaws", "232F3E", "aws.amazon.com", "amazonwebservices"),
        (r"\bgoogle cloud(?: platform)?\b|\bgcp\b", "googlecloud", "4285F4", "cloud.google.com", "googlecloud"),
        (r"\bazure\b|microsoft azure", "microsoftazure", "0078D4", "azure.microsoft.com", "azure"),
        (r"\bdocker\b", "docker", "2496ED", "docker.com", "docker"),
        (r"\bgithub\b", "github", "181717", "github.com", "github"),
        (r"\bstreamlit\b", "streamlit", "FF4B4B", "streamlit.io", "streamlit"),
        (r"\bpandas\b", "pandas", "150458", "pandas.pydata.org", "pandas"),
        (r"\bnumpy\b", "numpy", "013243", "numpy.org", "numpy"),
        (r"\bmatplotlib\b", "matplotlib", "11557C", "matplotlib.org", "matplotlib"),
        (r"\bseaborn\b", "seaborn", "4C72B0", "seaborn.pydata.org", "python"),
        (r"\bnltk\b", "nltk", "154F3C", "nltk.org", "python"),
        (r"\bopencv\b", "opencv", "5C3EE8", "opencv.org", "opencv"),
        (r"\bexcel\b|microsoft excel", "microsoftexcel", "217346", "microsoft.com", "excel"),
        (r"\bfigma\b", "figma", "F24E1E", "figma.com", "figma"),
        (r"\bcanva\b", "canva", "00C4CC", "canva.com", "canva"),
        (r"\bnotion\b", "notion", "000000", "notion.so", "notion"),
        (r"\bjira\b", "jira", "0052CC", "atlassian.com", "jira"),
        (r"\bjavascript\b", "javascript", "F7DF1E", "developer.mozilla.org", "javascript"),
        (r"\breact\b", "react", "61DAFB", "react.dev", "react"),
        (r"\br\b|\br programming\b", "r", "276DC3", "r-project.org", "r"),
        (r"\bsql\b|\bpostgres(?:ql)?\b", "postgresql", "4169E1", "postgresql.org", "postgresql"),
        (r"\bapache spark\b|\bspark\b", "apachespark", "E25A1C", "spark.apache.org", "apachespark"),
    ]
    for pattern, simple_slug, color, domain, devicon_slug in rules:
        if re.search(pattern, value):
            devicon_url = f"https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/{devicon_slug}/{devicon_slug}-original.svg"
            simple_url = f"https://cdn.simpleicons.org/{simple_slug}/{color}"
            return devicon_url, simple_url, color, domain
    return "", "", "8652B5", ""


def _render_roadmap(data):
    """Render the generated roadmap in the richer SkillLens reference layout."""
    role = data.get("role_title", "Your selected career")
    safe_role = _safe_text(role)
    phases = data.get("phases", [])
    skills = data.get("skills", [])
    projects = data.get("portfolio_projects", [])
    tools = data.get("tools_and_resources", [])
    progression = data.get("career_progression", [])
    responsibilities = data.get("day_to_day", [])
    outputs = data.get("work_outputs", [])

    # Career overview banner
    st.markdown(
        f"""
        <div class="sl-overview-banner">
          <div class="sl-overview-mark">✦</div>
          <div class="sl-overview-copy">
            <div class="sl-eyebrow">YOUR CAREER ROADMAP</div>
            <div class="sl-overview-title">Become a {safe_role}</div>
            <div class="sl-overview-sub">A practical learning journey, tailored to your selected role.</div>
          </div>
          <div class="sl-overview-metrics">
            <div class="sl-overview-metric"><span>◷</span><b>{_safe_text(data.get('estimated_plan', 'Flexible plan'))}</b><small>Estimated timeline</small></div>
            <div class="sl-overview-metric"><span>▥</span><b>{len(phases)}</b><small>Learning phases</small></div>
          </div>
          <div class="sl-overview-spark">✧</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Role explained: compact, visual information cards
    _section_heading("ROLE EXPLAINED", f"What does a {role} do?", "Understand the purpose of the role and the outcomes you may be expected to deliver.")
    st.markdown(
        f'<div class="sl-role-summary"><span class="sl-summary-symbol">✦</span>{_safe_text(data.get("role_summary", ""))}</div>',
        unsafe_allow_html=True,
    )
    rows = "".join(
        f'<div class="sl-info-row"><span class="sl-info-dot purple">✓</span><span>{_safe_text(item)}</span></div>'
        for item in responsibilities
    )
    st.markdown(
        '<div class="sl-info-panel"><div class="sl-info-panel-title"><span>◈</span> A typical working day</div>' + rows + '</div>',
        unsafe_allow_html=True,
    )

    rows = "".join(
        f'<div class="sl-info-row"><span class="sl-info-dot gold">✓</span><span>{_safe_text(item)}</span></div>'
        for item in outputs
    )
    st.markdown(
        '<div class="sl-info-panel gold"><div class="sl-info-panel-title"><span>✧</span> Typical work outputs</div>' + rows + '</div>',
        unsafe_allow_html=True,
    )

    # Connected roadmap timeline remains the centrepiece
    _section_heading("YOUR LEARNING JOURNEY", "Your career roadmap", "Follow the connected stages from core knowledge to job readiness. Open any phase for its detailed plan.")
    phase_html = ['<div class="sl-phase-flow">']
    for i, phase in enumerate(phases, start=1):
        tint = "gold" if i % 2 == 0 else "purple"
        phase_html.append(
            f"""<div class="sl-phase-card {tint}">
              <div class="sl-phase-top"><span class="sl-phase-number">{i:02d}</span><span class="sl-phase-duration">{_safe_text(phase.get('duration',''))}</span></div>
              <div class="sl-phase-title">{_safe_text(phase.get('title','Learning phase'))}</div>
              <div class="sl-phase-objective">{_safe_text(phase.get('objective',''))}</div>
              <div class="sl-phase-tag">MILESTONE · {_safe_text(phase.get('milestone','Complete this stage'))}</div>
            </div>"""
        )
        if i < len(phases):
            phase_html.append('<div class="sl-phase-arrow">➜</div>')
    phase_html.append("</div>")
    st.markdown("".join(phase_html), unsafe_allow_html=True)

    for index, phase in enumerate(phases, start=1):
        with st.expander(
            f"{index:02d}  ·  {phase.get('title', 'Learning phase')}  ·  {phase.get('duration', 'Suggested duration')}",
            expanded=(index == 1),
        ):
            st.markdown(
                f'<div class="sl-phase-objective-panel"><span>PHASE LEARNING OBJECTIVE</span><b>{_safe_text(phase.get("objective", ""))}</b></div>',
                unsafe_allow_html=True,
            )
            topic_col, practice_col = st.columns(2, gap="large")
            with topic_col:
                st.markdown('<div class="sl-phase-detail-heading purple">▤ &nbsp; KNOWLEDGE TO BUILD</div>', unsafe_allow_html=True)
                _render_bullets(phase.get("topics", []))
            with practice_col:
                st.markdown('<div class="sl-phase-detail-heading gold">✧ &nbsp; APPLY YOUR LEARNING</div>', unsafe_allow_html=True)
                _render_bullets(phase.get("practice", []))
            st.markdown(
                f'<div class="sl-phase-project-panel"><span>✦ &nbsp; SIGNATURE PROJECT / WORKPLACE CHALLENGE</span><p>{_safe_text(phase.get("project", ""))}</p></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="sl-phase-milestone-panel"><span>✓ &nbsp; MILESTONE — EVIDENCE YOU ARE READY</span><p>{_safe_text(phase.get("milestone", ""))}</p></div>',
                unsafe_allow_html=True,
            )

    # Capability mind map: central role hub with connected skill branches.
    st.markdown('<div class="sl-section-spacer"></div>', unsafe_allow_html=True)
    _section_heading("SKILL MAP", "Skills mind map", "A connected view of the capabilities that combine to make you effective in this role.")
    visible_skills = skills[:6]
    if visible_skills:
        # Place exactly one branch and one connector arrow for each skill group.
        # The centre remains fixed; unused branch positions stay empty.
        position_specs = [
            ("left-top", 270, 100),
            ("right-top", 730, 100),
            ("left-mid", 270, 300),
            ("right-mid", 730, 300),
            ("left-bottom", 270, 500),
            ("right-bottom", 730, 500),
        ]
        count = len(visible_skills)
        if count == 1:
            selected_positions = [position_specs[2]]
        elif count == 2:
            selected_positions = [position_specs[2], position_specs[3]]
        elif count == 3:
            selected_positions = [position_specs[0], position_specs[1], position_specs[4]]
        elif count == 4:
            selected_positions = [position_specs[0], position_specs[1], position_specs[4], position_specs[5]]
        elif count == 5:
            selected_positions = [position_specs[0], position_specs[1], position_specs[2], position_specs[3], position_specs[4]]
        else:
            selected_positions = position_specs[:count]

        branch_cards = []
        connector_paths = []
        for i, (skill, position_spec) in enumerate(zip(visible_skills, selected_positions)):
            position, target_x, target_y = position_spec
            tone = "gold" if i % 2 else "purple"
            chips = "".join(
                f'<span class="slx-chip">{_safe_text(item)}</span>'
                for item in skill.get("items", [])[:4]
            )
            branch_cards.append(
                f'<article class="slx-radial-branch {tone} {position}">'
                f'<div class="slx-branch-head"><span class="slx-branch-icon">✦</span><b>{_safe_text(skill.get("category", "Capability group"))}</b></div>'
                f'<p>{_safe_text(skill.get("why", "Build this capability through focused practice."))}</p>'
                f'<div class="slx-chips">{chips}</div></article>'
            )
            # Each arrow starts at the central role hub and ends at its own branch.
            mid_x = (500 + target_x) / 2
            mid_y = (300 + target_y) / 2
            marker = "slxArrowGold" if tone == "gold" else "slxArrowPurple"
            connector_paths.append(
                f'<path class="{tone}" d="M500 300 Q{mid_x:.0f} {mid_y:.0f} {target_x} {target_y}" '
                f'marker-end="url(#{marker})"/>'
            )

        radial_svg = (
            '<svg class="slx-radial-lines" viewBox="0 0 1000 600" '
            'preserveAspectRatio="none" aria-hidden="true">'
            '<defs>'
            '<marker id="slxArrowPurple" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto">'
            '<path d="M0,0 L8,4 L0,8" fill="none" stroke="#8652B5" stroke-width="1.5"/></marker>'
            '<marker id="slxArrowGold" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto">'
            '<path d="M0,0 L8,4 L0,8" fill="none" stroke="#C7A34B" stroke-width="1.5"/></marker>'
            '</defs>' + ''.join(connector_paths) +
            '<circle cx="500" cy="300" r="8"/></svg>'
        )
        hub = (
            f'<div class="slx-radial-hub"><span>YOUR TARGET ROLE</span><b>{safe_role}</b>'
            f'<small>Core capability hub</small><div class="slx-hub-caption">Skills that work together</div></div>'
        )
        st.markdown(
            '<div class="slx-radial-map">' + radial_svg + hub + ''.join(branch_cards) + '</div>'
            + '<div class="slx-map-note"><span>✧</span> Follow each branch outward from your target role. Build the capabilities, then connect them through practical projects.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("No skill groups were returned for this role.")

    _section_heading("TOOLS & RESOURCES", "Tools you will learn", "Recognisable application marks and the purpose each tool serves in this career.")
    if tools:
        # Split combined labels so each application gets its own correct logo.
        expanded_tools = []
        for item in tools:
            name = str(item.get("name", "Resource"))
            purpose = item.get("purpose", "")
            parts = re.split(r"\s*(?:/|\+|\band\b)\s*", name, flags=re.I)
            if len(parts) > 1 and all(part.strip() for part in parts):
                for part in parts:
                    expanded_tools.append({"name": part.strip(), "purpose": purpose})
            else:
                expanded_tools.append({"name": name, "purpose": purpose})
        tool_html = ['<div class="slx-tool-grid">']
        for i, item in enumerate(expanded_tools[:18]):
            tool_name = str(item.get("name", "Resource"))
            logo_url, secondary_logo_url, brand_color, official_domain = _tool_logo(tool_name)
            initials = "".join(word[0] for word in re.findall(r"[A-Za-z0-9]+", tool_name)[:2]).upper() or "TO"
            if logo_url:
                simple_fallback = secondary_logo_url or f"https://www.google.com/s2/favicons?domain={official_domain}&sz=128"
                favicon_fallback = f"https://www.google.com/s2/favicons?domain={official_domain}&sz=128"
                logo = (
                    f'<img src="{logo_url}" alt="{_safe_text(tool_name)} official logo" loading="lazy" '
                    f'data-fallback="0" data-simple="{simple_fallback}" data-favicon="{favicon_fallback}" '
                    f'onerror="if(this.dataset.fallback===&quot;0&quot;){{this.dataset.fallback=&quot;1&quot;;this.src=this.dataset.simple;}}'
                    f'else if(this.dataset.fallback===&quot;1&quot;){{this.dataset.fallback=&quot;2&quot;;this.src=this.dataset.favicon;}}'
                    f'else{{this.style.display=&quot;none&quot;;this.nextElementSibling.style.display=&quot;flex&quot;;}}">'
                    f'<span class="slx-logo-fallback">{_safe_text(initials)}</span>'
                )
            else:
                logo = f'<span class="slx-logo-fallback visible">{_safe_text(initials)}</span>'
            tone = "gold" if i % 2 else "purple"
            tool_html.append(
                f'<article class="slx-tool {tone}"><div class="slx-tool-mark">{logo}</div>'
                f'<b>{_safe_text(tool_name)}</b><p>{_safe_text(item.get("purpose", ""))}</p></article>'
            )
        tool_html.append('</div>')
        st.markdown(''.join(tool_html), unsafe_allow_html=True)
    else:
        st.caption("No specific tools or resources were returned for this role.")

    # Portfolio and career progression side by side
    st.markdown('<div class="sl-section-spacer"></div>', unsafe_allow_html=True)
    _section_heading("PORTFOLIO", "Projects to build your skills", "Hands-on work that turns learning into demonstrable experience.")
    if projects:
        cols = st.columns(min(3, len(projects)), gap="small")
        for index, project in enumerate(projects):
            with cols[index % len(cols)]:
                tone = "#F5EEFF" if index % 2 == 0 else "#FFF8E8"
                accent = "#7541A5" if index % 2 == 0 else "#A87908"
                st.markdown(
                    f"""<div class="sl-project-card" style="--project-tint:{tone};--project-accent:{accent};">
                    <div class="sl-project-icon">{'▣' if index % 2 == 0 else '✧'}</div>
                    <b>{_safe_text(project.get('title','Project'))}</b>
                    <p>{_safe_text(project.get('description',''))}</p>
                    <span>PORTFOLIO EVIDENCE</span></div>""",
                    unsafe_allow_html=True,
                )
    else:
        st.caption("No portfolio projects were returned for this role.")

    if progression:
        _section_heading("CAREER PATH", "Career opportunities", "Possible next roles and adjacent specialisations.")
        path_html = ['<div class="sl-career-path">']
        for i, item in enumerate(progression):
            path_html.append(
                f'<div class="sl-career-step"><span class="sl-career-step-icon">{"✦" if i == 1 else "⌖"}</span><b>{_safe_text(item.get("title", "Career option"))}</b><small>{_safe_text(item.get("level", ""))}</small><p>{_safe_text(item.get("description", ""))}</p></div>'
            )
            if i < len(progression) - 1:
                path_html.append('<div class="sl-career-path-arrow">➜</div>')
        path_html.append("</div>")
        st.markdown("".join(path_html), unsafe_allow_html=True)
    else:
        _section_heading("CAREER PATH", "Career opportunities", "Possible next roles and adjacent specialisations.")
        st.info("Career progression options were not returned for this role.")

    # Job readiness: clear, scannable action cards
    _section_heading("NEXT STEPS", "Prepare to enter the industry", "Turn your learning into credible evidence and prepare for applications.")
    readiness = data.get("job_readiness", [])
    if readiness:
        checklist_html = ['<div class="sl-checklist">']
        for item in readiness:
            if isinstance(item, dict):
                item_title = _safe_text(item.get("title", "Next step"))
                item_description = _safe_text(item.get("description", ""))
                item_content = (
                    f'<b class="sl-check-title">{item_title}</b>'
                    + (f'<div class="sl-check-description">{item_description}</div>' if item_description else "")
                )
            else:
                item_content = _safe_text(item)
            checklist_html.append(
                f'<div class="sl-check-item"><span>✓</span><div>{item_content}</div></div>'
            )
        checklist_html.append("</div>")
        st.markdown("".join(checklist_html), unsafe_allow_html=True)
    if data.get("important_note"):
        st.warning(data["important_note"])
    st.caption(
        "This is an AI-generated learning guide. Verify current employer expectations and any regulated-profession requirements. A roadmap cannot guarantee employment."
    )

def render_career_guidance():
    st.markdown(
        """
        <style>
        [data-testid="stMainBlockContainer"] {max-width:1500px;padding-top:1.3rem;}
        .career-hero {
          display:flex;align-items:center;gap:19px;
          padding:24px 28px;border-radius:21px;border:1px solid #E7D8F2;
          background:linear-gradient(112deg,#F1E8FA 0%,#FAF6FD 56%,#FFF7E5 100%);
          box-shadow:0 5px 18px rgba(93,55,125,.07);margin-bottom:22px;color:#2F1745;
        }
        .career-hero-icon {
          flex:0 0 62px;width:62px;height:62px;border-radius:18px;
          display:flex;align-items:center;justify-content:center;
          background:linear-gradient(145deg,#8050B0 0%,#A477C8 68%,#D9B65F 100%);
          box-shadow:0 6px 14px rgba(128,80,176,.18);
        }
        .career-hero-icon svg {width:34px;height:34px;display:block;}
        .career-kicker {font-size:10px;letter-spacing:2px;font-weight:850;color:#8050A5;}
        .career-title {font-size:27px;font-weight:850;color:#2F1745;margin:5px 0;}
        .career-sub {font-size:14px;color:#6F5C7B;line-height:1.55;}
        div[data-testid="stForm"] {
          border:1px solid #E8D8F1;border-radius:18px;padding:20px 22px;
          background:linear-gradient(135deg,#FFFFFF 0%,#FFFEFB 100%);
          box-shadow:0 5px 18px rgba(93,55,125,.055);
        }
        div[data-testid="stForm"] label p {color:#49345D;font-weight:650;}
        div[data-testid="stForm"] input,
        div[data-testid="stForm"] [data-baseweb="select"] > div {
          border-radius:10px !important;border-color:#E4D8ED !important;
          background:#FCFAFE !important;
        }
        div[data-testid="stForm"] input:focus,
        div[data-testid="stForm"] [data-baseweb="select"] > div:focus-within {
          border-color:#A477C8 !important;box-shadow:0 0 0 1px #A477C8 !important;
        }
        div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button,
        div[data-testid="stForm"] button[kind="primary"],
        div[data-testid="stForm"] button[type="submit"] {
          background:linear-gradient(90deg,#B99AD8 0%,#A982CC 58%,#D9BD78 100%) !important;
          color:#FFFFFF !important;border:0 !important;border-radius:11px !important;
          font-weight:750 !important;min-height:46px;
          box-shadow:0 4px 11px rgba(128,80,176,.14) !important;
        }
        div[data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover,
        div[data-testid="stForm"] button[kind="primary"]:hover,
        div[data-testid="stForm"] button[type="submit"]:hover {
          background:linear-gradient(90deg,#A982CC 0%,#946AB9 58%,#C9AA60 100%) !important;
          color:#FFFFFF !important;transform:translateY(-1px);
        }
        .career-helper {font-size:12px;color:#766783;margin-top:4px;}
        .sl-selected-career{display:flex;align-items:center;gap:15px;padding:17px 20px;margin:18px 0 8px;border:1px solid #E7D8F2;border-radius:18px;background:linear-gradient(105deg,#F4ECFB 0%,#FFFFFF 58%,#FFF8E8 100%);box-shadow:0 4px 15px rgba(93,55,125,.05)}
        .sl-selected-icon{width:48px;height:48px;flex:0 0 48px;border-radius:15px;display:flex;align-items:center;justify-content:center;background:linear-gradient(145deg,#8150B2,#B18AD0 68%,#D9BD78);color:#fff;font-size:25px}
        .sl-selected-copy{flex:1;min-width:0}.sl-eyebrow{font-size:9px;font-weight:900;letter-spacing:1.7px;color:#8050A5}.sl-selected-title{font-size:21px;font-weight:850;color:#2F1745;margin-top:3px}.sl-selected-sub{font-size:12px;color:#766783;margin-top:3px}
        .sl-selected-stat{min-width:105px;padding:9px 13px;border:1px solid #E8D8F1;border-radius:12px;background:#fff;text-align:center;color:#7541A5}.sl-selected-stat span{font-size:18px}.sl-selected-stat b{display:block;font-size:20px;color:#32134F}.sl-selected-stat small{font-size:10px;color:#766783}
        .sl-role-summary{padding:16px 18px;border:1px solid #E8D8F1;border-left:4px solid #A982CC;border-radius:14px;background:linear-gradient(100deg,#FBF7FF,#FFFFFF);color:#5E506B;font-size:13px;line-height:1.7;margin:8px 0 15px}
        .sl-mini-heading{font-weight:800;color:#3B2450;margin:4px 0 8px}.sl-mini-heading span{color:#8756B1;font-size:17px;margin-right:7px}.sl-mini-heading.gold span{color:#C49A32}
        .sl-phase-flow{display:flex;align-items:stretch;gap:8px;overflow-x:auto;padding:7px 2px 16px;margin-bottom:6px}
        .sl-phase-card{flex:1 0 155px;min-width:145px;padding:13px 13px 12px;border:1px solid #E5D6F3;border-radius:15px;background:linear-gradient(155deg,#F7F0FF,#FFFFFF 72%);box-shadow:0 4px 12px rgba(93,55,125,.045)}
        .sl-phase-card.gold{border-color:#EEDFB4;background:linear-gradient(155deg,#FFFAED,#FFFFFF 72%)}
        .sl-phase-top{display:flex;align-items:center;justify-content:space-between;gap:6px}.sl-phase-number{display:inline-flex;width:29px;height:29px;align-items:center;justify-content:center;border-radius:50%;background:#7C3AED;color:white;font-weight:900;font-size:12px;box-shadow:0 0 0 4px #EDE2FA}.sl-phase-card.gold .sl-phase-number{background:#C69A2E;box-shadow:0 0 0 4px #F8EDCC}.sl-phase-duration{font-size:9px;color:#766783;font-weight:750}
        .sl-phase-title{font-size:13px;font-weight:850;color:#32134F;margin:13px 0 7px}.sl-phase-objective{font-size:11px;line-height:1.5;color:#6E6178;min-height:58px}.sl-phase-tag{font-size:8px;font-weight:850;letter-spacing:.5px;color:#7541A5;background:#EEE2FF;padding:6px 7px;border-radius:7px;margin-top:10px}.sl-phase-card.gold .sl-phase-tag{color:#89650A;background:#FFF0C8}.sl-phase-arrow{display:flex;align-items:center;justify-content:center;flex:0 0 18px;color:#9466BC;font-size:21px;font-weight:900}
        .sl-mindmap{padding:18px;border:1px solid #E7D8F2;border-radius:19px;background:linear-gradient(135deg,#FBF8FF,#FFFFFF 58%,#FFFCF4);margin:8px 0 14px}
        .sl-mindmap-center{width:min(340px,100%);margin:0 auto 18px;padding:15px 18px;text-align:center;border-radius:15px;background:linear-gradient(100deg,#8753B6,#A77BCB 68%,#D3B56B);color:white;box-shadow:0 6px 15px rgba(128,80,176,.15);position:relative}
        .sl-mindmap-center:after{content:"↓";position:absolute;left:50%;bottom:-25px;transform:translateX(-50%);color:#A982CC;font-size:23px;font-weight:900}.sl-mindmap-center span{display:block;font-size:8px;letter-spacing:1.7px;font-weight:900;opacity:.9}.sl-mindmap-center b{display:block;font-size:19px;margin:3px 0}.sl-mindmap-center small{font-size:10px;opacity:.9}
        .sl-mindmap-branches{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;padding-top:7px}.sl-skill-node{position:relative;padding:14px 15px;border:1px solid #E5D6F3;border-radius:14px;background:#fff;box-shadow:0 3px 10px rgba(93,55,125,.035)}.sl-skill-node:before{content:"↗";position:absolute;top:-12px;left:18px;color:#A982CC;font-size:16px;font-weight:900}.sl-skill-node.gold{border-color:#EEDFB4;background:linear-gradient(145deg,#FFFCF3,#FFFFFF)}.sl-skill-node.gold:before{color:#C49A32}.sl-skill-node-title{font-size:13px;font-weight:850;color:#32134F}.sl-skill-node-title span{color:#8756B1;margin-right:7px}.sl-skill-node.gold .sl-skill-node-title span{color:#C49A32}.sl-skill-why{font-size:11px;line-height:1.5;color:#756681;margin:6px 0 9px}.sl-skill-chips{display:flex;flex-wrap:wrap;gap:6px}.sl-skill-chip{font-size:10px;color:#65477D;background:#F2EAFB;border:1px solid #E7D8F2;border-radius:20px;padding:5px 8px}.sl-skill-node.gold .sl-skill-chip{color:#80600D;background:#FFF6DD;border-color:#F0E2B9}
        .sl-tool-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.sl-tool-card{display:flex;align-items:flex-start;gap:10px;padding:13px;border:1px solid #E5D6F3;border-radius:13px;background:linear-gradient(145deg,#F8F2FF,#FFFFFF)}.sl-tool-card.gold{border-color:#EEDFB4;background:linear-gradient(145deg,#FFFAEC,#FFFFFF)}.sl-tool-symbol{width:30px;height:30px;flex:0 0 30px;border-radius:10px;background:#E9DDF7;color:#7541A5;display:flex;align-items:center;justify-content:center;font-size:17px}.sl-tool-card.gold .sl-tool-symbol{background:#F8EDCC;color:#A87908}.sl-tool-card b{font-size:12px;color:#32134F}.sl-tool-card p{font-size:10px;line-height:1.45;color:#756681;margin:4px 0 0}
        .sl-project-card{height:100%;min-height:155px;padding:15px;border:1px solid #E7D8F2;border-radius:15px;background:linear-gradient(145deg,var(--project-tint),#FFFFFF 75%);margin:4px 0 10px}.sl-project-icon{font-size:20px;color:var(--project-accent);margin-bottom:8px}.sl-project-card b{font-size:13px;color:#32134F}.sl-project-card p{font-size:11px;line-height:1.5;color:#756681;margin:7px 0 12px}.sl-project-card span{font-size:8px;letter-spacing:.8px;font-weight:900;color:var(--project-accent)}
        .sl-checklist{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.sl-check-item{display:flex;gap:9px;align-items:flex-start;padding:11px 13px;border:1px solid #E7D8F2;border-radius:12px;background:#fff;color:#5E506B;font-size:12px;line-height:1.5}.sl-check-item span{display:flex;align-items:center;justify-content:center;flex:0 0 21px;height:21px;border-radius:50%;background:#EEE2FF;color:#7541A5;font-weight:900}.sl-check-title{display:block;color:#3D2454;font-size:12px;font-weight:800;margin-bottom:3px}.sl-check-description{color:#756681;font-size:11px;line-height:1.5}

        .sl-mindmap{padding:22px;border:1px solid #E4D5F2;border-radius:20px;background:linear-gradient(135deg,#F9F5FF 0%,#FFFFFF 55%,#FFFCF2 100%);box-shadow:0 5px 18px rgba(75,40,110,.045)}
        .sl-mindmap-center{background:linear-gradient(110deg,#6825C8 0%,#9155C9 65%,#D5B45F 100%);box-shadow:0 8px 20px rgba(104,37,200,.18);width:min(300px,100%);padding:17px 20px}
        .sl-mindmap-branches{gap:14px;position:relative}
        .sl-skill-node{min-height:112px;padding:16px 17px 14px;border-radius:16px;box-shadow:0 4px 13px rgba(75,40,110,.055)}
        .sl-skill-node:before{content:"↗";font-size:19px;top:-15px}
        .sl-skill-node-title{font-size:14px}
        .sl-skill-why{font-size:11px}
        .sl-skill-chip{font-size:10px;padding:5px 9px}
        .sl-mindmap-foot{margin-top:15px;padding:11px 13px;border:1px dashed #DCC9ED;border-radius:11px;background:#FCF9FF;color:#6B587B;font-size:11px}
        .sl-tool-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:11px}
        .sl-tool-card{display:flex;flex-direction:column;align-items:center;text-align:center;justify-content:flex-start;gap:6px;min-height:126px;padding:14px 10px;border-radius:15px;box-shadow:0 3px 12px rgba(75,40,110,.04)}
        .sl-tool-symbol{width:42px;height:42px;flex:0 0 42px;border-radius:13px;font-size:25px}
        .sl-tool-card b{font-size:12px}.sl-tool-card p{font-size:10px;line-height:1.45}
        .sl-project-card{min-height:180px;padding:17px;border-radius:16px;box-shadow:0 4px 13px rgba(75,40,110,.045)}
        .sl-project-icon{width:34px;height:34px;display:flex;align-items:center;justify-content:center;border-radius:11px;background:rgba(255,255,255,.8);font-size:20px}
        .sl-project-card b{font-size:14px}.sl-project-card p{font-size:11px;line-height:1.55}
        .sl-career-path{display:flex;align-items:stretch;gap:9px;padding:14px;border:1px solid #E7D8F2;border-radius:17px;background:linear-gradient(110deg,#FBF8FF,#FFFFFF 60%,#FFFCF4);overflow-x:auto}
        .sl-career-step{flex:1 0 145px;padding:13px;border:1px solid #E8D8F1;border-radius:13px;background:#fff;text-align:center}
        .sl-career-step-icon{display:flex;width:32px;height:32px;margin:0 auto 8px;align-items:center;justify-content:center;border-radius:10px;background:#EEE2FF;color:#7541A5;font-size:18px}
        .sl-career-step b{display:block;font-size:12px;color:#32134F}.sl-career-step small{display:block;font-size:9px;color:#A87908;margin-top:4px}.sl-career-step p{font-size:10px;line-height:1.45;color:#756681;margin:7px 0 0}
        .sl-career-path-arrow{display:flex;align-items:center;color:#8756B1;font-size:20px;font-weight:900}
        @media(max-width:850px){.sl-tool-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
        @media(max-width:560px){.sl-tool-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.sl-career-path{flex-direction:column}.sl-career-path-arrow{justify-content:center;transform:rotate(90deg)}}

        @media(max-width:850px){.sl-phase-flow{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));overflow:visible}.sl-phase-card{min-width:0}.sl-phase-arrow{display:none}.sl-tool-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
        @media(max-width:560px){.sl-selected-career{align-items:flex-start;flex-wrap:wrap}.sl-selected-stat{margin-left:63px}.sl-mindmap-branches,.sl-checklist{grid-template-columns:1fr}.sl-tool-grid{grid-template-columns:1fr}.sl-phase-flow{grid-template-columns:1fr 1fr}.sl-phase-objective{min-height:0}}

        /* Reference-inspired overview and role detail panels */
        .sl-overview-banner{position:relative;display:flex;align-items:center;gap:16px;padding:18px 20px;margin:18px 0 20px;border:1px solid #E4D5F2;border-radius:20px;background:linear-gradient(108deg,#F0E5FC 0%,#FBF8FF 52%,#FFF5DC 100%);box-shadow:0 7px 22px rgba(81,43,120,.07);overflow:hidden}
        .sl-overview-mark{display:flex;align-items:center;justify-content:center;flex:0 0 54px;width:54px;height:54px;border-radius:16px;background:linear-gradient(145deg,#6725C8,#9B65D0 65%,#D8B75F);color:#fff;font-size:27px;box-shadow:0 6px 15px rgba(104,37,200,.2)}
        .sl-overview-copy{flex:1;min-width:180px;z-index:1}.sl-overview-title{font-size:22px;font-weight:900;color:#291044;margin-top:3px}.sl-overview-sub{font-size:12px;color:#6E5B7B;margin-top:4px}
        .sl-overview-metrics{display:flex;gap:9px;z-index:1}.sl-overview-metric{min-width:112px;padding:9px 12px;text-align:center;border:1px solid rgba(225,210,239,.95);border-radius:12px;background:rgba(255,255,255,.82)}.sl-overview-metric span{display:block;color:#8652B5;font-size:17px}.sl-overview-metric b{display:block;color:#32134F;font-size:12px;margin-top:2px}.sl-overview-metric small{display:block;color:#81718B;font-size:9px;margin-top:2px}.sl-overview-spark{position:absolute;right:8px;top:-13px;color:#D6B65E;font-size:68px;opacity:.25}
        .sl-info-panel{height:100%;padding:15px 16px;border:1px solid #E5D6F3;border-radius:16px;background:linear-gradient(145deg,#F9F4FF,#FFFFFF 78%);box-shadow:0 4px 14px rgba(75,40,110,.04)}
        .sl-info-panel.gold{border-color:#EEDFB4;background:linear-gradient(145deg,#FFFAEF,#FFFFFF 78%)}
        .sl-info-panel-title{font-size:13px;font-weight:850;color:#32134F;margin-bottom:10px}.sl-info-panel-title span{color:#8756B1;margin-right:7px;font-size:17px}.sl-info-panel.gold .sl-info-panel-title span{color:#C49A32}
        .sl-info-row{display:flex;align-items:flex-start;gap:9px;padding:7px 0;border-top:1px solid rgba(231,216,242,.65);font-size:11px;line-height:1.5;color:#665772}
        .sl-info-dot{display:flex;align-items:center;justify-content:center;flex:0 0 18px;width:18px;height:18px;border-radius:50%;font-size:10px;font-weight:900}.sl-info-dot.purple{background:#EEE2FF;color:#7541A5}.sl-info-dot.gold{background:#FFF0C8;color:#98700B}
        .sl-summary-symbol{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;margin-right:9px;border-radius:7px;background:#EEE2FF;color:#7541A5;font-size:12px;vertical-align:middle}
        .sl-section-spacer{height:4px}
        @media(max-width:850px){.sl-overview-banner{flex-wrap:wrap}.sl-overview-metrics{width:100%;margin-left:70px}.sl-overview-metric{flex:1}}
        @media(max-width:560px){.sl-overview-title{font-size:18px}.sl-overview-metrics{margin-left:0}.sl-info-panel{margin-bottom:10px}}


        /* Enhanced mind map, real brand marks, and editorial phase details */
        .sl-mindmap-real{padding:18px 14px 14px;background:linear-gradient(135deg,#FAF6FF 0%,#FFFFFF 52%,#FFFCF1 100%);overflow:hidden}
        .sl-map-canvas{height:545px;max-width:1000px;margin:0 auto;position:relative}
        .sl-map-connectors{position:absolute;inset:0;width:100%;height:100%;z-index:0;overflow:visible}
        .sl-map-link{fill:none;stroke-width:3.2;stroke-linecap:round;opacity:.88}
        .sl-map-link.purple{stroke:#8652B5}.sl-map-link.gold{stroke:#C7A34B}
        .sl-map-hub{position:absolute;left:38.5%;top:40.5%;width:23%;min-height:100px;padding:17px 13px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;border-radius:20px;background:linear-gradient(125deg,#6524C7 0%,#9154CB 62%,#D6B65E 100%);color:#fff;box-shadow:0 10px 25px rgba(94,43,153,.22);z-index:2;border:3px solid rgba(255,255,255,.8)}
        .sl-map-hub span{font-size:8px;letter-spacing:1.8px;font-weight:900;opacity:.9}.sl-map-hub b{font-size:17px;line-height:1.2;margin:6px 0}.sl-map-hub small{font-size:9px;opacity:.9}
        .sl-map-node{position:absolute;width:30%;min-height:130px;padding:13px 14px;border-radius:17px;border:1px solid #E3D3F1;background:linear-gradient(145deg,#F7F0FF,#FFFFFF 80%);box-shadow:0 6px 17px rgba(77,43,111,.07);z-index:1}
        .sl-map-node.gold{border-color:#EADBAF;background:linear-gradient(145deg,#FFFAEC,#FFFFFF 80%)}
        .sl-map-node-title{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:900;color:#32134F}.sl-map-node-icon{display:inline-flex;width:24px;height:24px;align-items:center;justify-content:center;border-radius:8px;background:#EEE2FF;color:#7541A5}.sl-map-node.gold .sl-map-node-icon{background:#FFF0C8;color:#A87908}
        .sl-map-node-why{font-size:10px;line-height:1.45;color:#756681;margin:7px 0 9px}.sl-map-node .sl-skill-chip{font-size:9px;padding:4px 7px}
        .sl-extra-skills{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:10px}.sl-extra-skill{padding:10px 12px;border:1px solid #E7D8F2;border-radius:11px;background:#fff}.sl-extra-skill b{display:block;color:#4B2D66;font-size:11px}.sl-extra-skill span{display:block;color:#766783;font-size:10px;margin-top:4px}
        .sl-tool-card{min-height:145px}.sl-tool-logo{width:48px;height:48px;display:flex;align-items:center;justify-content:center;border-radius:14px;background:#fff;border:1px solid #EEE5F5;box-shadow:0 3px 10px rgba(60,35,80,.06);padding:9px}.sl-tool-card.gold .sl-tool-logo{border-color:#F0E4C5}.sl-tool-logo img{display:block;width:30px;height:30px;object-fit:contain}.sl-tool-fallback{width:30px;height:30px;align-items:center;justify-content:center;border-radius:8px;background:#EEE2FF;color:#7541A5;font-size:12px;font-weight:900}.sl-tool-card.gold .sl-tool-fallback{background:#FFF0C8;color:#A87908}
        .sl-phase-objective-panel,.sl-phase-project-panel,.sl-phase-milestone-panel{padding:14px 16px;border-radius:14px;margin:10px 0;border:1px solid #E5D6F3;background:linear-gradient(110deg,#F7F0FF,#FFFFFF);}
        .sl-phase-objective-panel span,.sl-phase-project-panel span,.sl-phase-milestone-panel span{display:block;font-size:9px;letter-spacing:1.2px;font-weight:900;color:#8050A5;margin-bottom:6px}.sl-phase-objective-panel b{font-size:13px;line-height:1.6;color:#38224D;font-weight:700}
        .sl-phase-detail-heading{font-size:11px;font-weight:900;letter-spacing:.8px;padding:9px 11px;border-radius:10px;margin:6px 0 10px;background:#F1E8FA;color:#68408A}.sl-phase-detail-heading.gold{background:#FFF5D9;color:#98700B}
        .sl-phase-project-panel{background:linear-gradient(110deg,#FFF9E9,#FFFFFF);border-color:#EEDFB4}.sl-phase-project-panel span{color:#98700B}.sl-phase-project-panel p,.sl-phase-milestone-panel p{font-size:12px;line-height:1.6;color:#5F5269;margin:0}
        .sl-phase-milestone-panel{background:linear-gradient(110deg,#F1FAF4,#FFFFFF);border-color:#D6EBDD}.sl-phase-milestone-panel span{color:#34734A}
        div[data-testid="stExpander"]{border:1px solid #E5D8EF!important;border-radius:13px!important;background:linear-gradient(100deg,#FFFEFF,#FFFCF5)!important;margin:8px 0!important}
        div[data-testid="stExpander"] summary p{font-weight:750;color:#39234F}
        @media(max-width:900px){.sl-map-canvas{height:auto;display:grid;grid-template-columns:1fr 1fr;gap:10px;padding-top:10px}.sl-map-connectors{display:none}.sl-map-hub{position:relative;left:auto;top:auto;grid-column:1/-1;width: min(360px,100%);margin:0 auto 8px}.sl-map-node{position:relative;left:auto!important;top:auto!important;width:auto;min-height:0}.sl-extra-skills{grid-template-columns:1fr}}
        @media(max-width:560px){.sl-map-canvas{grid-template-columns:1fr}.sl-map-hub{grid-column:auto}.sl-map-node{width:100%}}

        /* Final hub-and-spoke mind map layout: three aligned columns. */
        .sl-map-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(150px,.72fr) minmax(0,1fr);gap:12px;align-items:stretch;max-width:1100px;margin:0 auto}
        .sl-map-side{display:grid;grid-template-rows:repeat(var(--map-rows,3),minmax(125px,auto));gap:12px;min-width:0}
        .sl-map-node{position:relative;left:auto!important;top:auto!important;width:auto!important;min-height:125px;padding:13px 14px;display:flex;flex-direction:column;justify-content:center}
        .sl-map-node.left:after{content:"➜";position:absolute;right:-22px;top:50%;transform:translateY(-50%);font-size:20px;font-weight:900;color:#8652B5;z-index:3}
        .sl-map-node.right:before{content:"←";position:absolute;left:-22px;top:50%;transform:translateY(-50%);font-size:20px;font-weight:900;color:#C7A34B;z-index:3}
        .sl-map-empty{min-height:125px}
        .sl-map-hub{position:sticky;top:35%;align-self:center;left:auto;top:auto;width:100%;min-height:150px;padding:18px 12px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;border-radius:20px;background:linear-gradient(135deg,#6524C7 0%,#9154CB 65%,#D6B65E 100%);color:#fff;box-shadow:0 10px 25px rgba(94,43,153,.22);z-index:2;border:3px solid rgba(255,255,255,.85)}
        .sl-map-hub span{font-size:8px;letter-spacing:1.5px;font-weight:900}.sl-map-hub b{font-size:17px;line-height:1.25;margin:7px 0}.sl-map-hub small{font-size:9px;opacity:.9}.sl-hub-caption{font-size:9px;margin-top:10px;padding:5px 8px;border-radius:20px;background:rgba(255,255,255,.17)}
        .sl-tool-grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
        .sl-tool-card{display:flex;flex-direction:column;align-items:center;text-align:center;gap:8px;padding:13px 9px;min-height:150px}
        .sl-tool-logo{width:54px;height:54px;flex:0 0 54px;padding:10px;border-radius:15px}
        .sl-tool-logo img{width:34px;height:34px}.sl-tool-card b{font-size:11px}.sl-tool-card p{font-size:10px;line-height:1.45}
        @media(max-width:900px){.sl-map-grid{grid-template-columns:minmax(0,1fr) minmax(125px,.65fr) minmax(0,1fr);gap:9px}.sl-map-node{min-height:135px;padding:10px}.sl-map-node-title{font-size:11px}.sl-map-node-why{font-size:9px}.sl-map-node.left:after{right:-17px}.sl-map-node.right:before{left:-17px}}
        @media(max-width:650px){.sl-map-grid{grid-template-columns:1fr}.sl-map-hub{grid-row:1;min-height:110px;max-width:360px;margin:0 auto 8px}.sl-map-side{grid-template-rows:none;grid-template-columns:1fr;gap:9px}.sl-map-node.left:after,.sl-map-node.right:before{content:"↓";left:50%;right:auto;top:auto;bottom:-17px;transform:translateX(-50%);font-size:16px}.sl-map-empty{display:none}.sl-tool-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}

        /* Mind map v2: isolated classes prevent legacy positioning rules from shifting nodes. */
        .slx-mindmap{position:relative;padding:18px 16px 14px;border:1px solid #E5D8EF;border-radius:20px;background:linear-gradient(145deg,#F8F2FF 0%,#FFFFFF 55%,#FFFAEA 100%);box-shadow:0 5px 18px rgba(75,40,110,.05);overflow:hidden}
        .slx-hub{position:relative;z-index:2;width:min(310px,90%);margin:0 auto;padding:17px 18px;text-align:center;border-radius:17px;color:#fff;background:linear-gradient(115deg,#6D2BC2 0%,#8E55C8 70%,#D2B45F 100%);box-shadow:0 8px 20px rgba(104,37,200,.18);border:3px solid #fff}
        .slx-hub span{display:block;font-size:8px;letter-spacing:1.8px;font-weight:900;opacity:.9}.slx-hub b{display:block;font-size:17px;line-height:1.25;margin:6px 0}.slx-hub small{font-size:9px;opacity:.9}
        .slx-connector-area{height:72px;position:relative;margin:0 0 -2px}.slx-connectors{position:absolute;inset:0;width:100%;height:100%;overflow:visible}.slx-connectors path{fill:none;stroke:#9870C0;stroke-width:4;stroke-linecap:round;stroke-linejoin:round}.slx-connectors circle{fill:#C6A04A;stroke:#fff;stroke-width:3}
        .slx-branches{position:relative;z-index:1;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
        .slx-branch{min-width:0;padding:14px 14px 13px;border:1px solid #E3D4F0;border-radius:15px;background:linear-gradient(145deg,#F6EEFF,#fff 78%);box-shadow:0 4px 13px rgba(75,40,110,.055)}
        .slx-branch.gold{border-color:#EADBAF;background:linear-gradient(145deg,#FFFAEB,#fff 78%)}
        .slx-branch-head{display:flex;align-items:center;gap:8px;color:#32134F;font-size:12px}.slx-branch-icon{display:flex;width:26px;height:26px;align-items:center;justify-content:center;border-radius:9px;background:#EBDDFA;color:#7541A5}.slx-branch.gold .slx-branch-icon{background:#FFF0C8;color:#A87908}
        .slx-branch p{font-size:10px;line-height:1.5;color:#756681;margin:8px 0}.slx-chips{display:flex;flex-wrap:wrap;gap:5px}.slx-chip{font-size:9px;line-height:1.3;padding:5px 7px;border-radius:20px;background:#EEE5F7;color:#65477D;border:1px solid #E5D8EF}.slx-branch.gold .slx-chip{background:#FFF4D9;color:#80600D;border-color:#F0E2B9}
        .slx-map-note{margin-top:13px;padding:10px 12px;border:1px dashed #DCC9ED;border-radius:11px;background:rgba(255,255,255,.78);color:#6B587B;font-size:10px;line-height:1.5}.slx-map-note span{color:#A87908;margin-right:5px}
        .slx-tool-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}.slx-tool{display:flex;min-width:0;min-height:140px;flex-direction:column;align-items:center;text-align:center;gap:7px;padding:12px 8px;border:1px solid #E3D4F0;border-radius:14px;background:linear-gradient(145deg,#F8F2FF,#fff 75%);box-shadow:0 3px 10px rgba(75,40,110,.04)}.slx-tool.gold{border-color:#EADBAF;background:linear-gradient(145deg,#FFFAEB,#fff 75%)}
        .slx-tool-mark{display:flex;width:48px;height:48px;align-items:center;justify-content:center;padding:8px;border:1px solid #EEE5F5;border-radius:13px;background:#fff}.slx-tool.gold .slx-tool-mark{border-color:#F0E4C5}.slx-tool-mark img{display:block;width:30px;height:30px;object-fit:contain}.slx-logo-fallback{display:none;width:30px;height:30px;align-items:center;justify-content:center;border-radius:8px;background:#EEE2FF;color:#7541A5;font-size:11px;font-weight:900}.slx-logo-fallback.visible{display:flex}.slx-tool.gold .slx-logo-fallback{background:#FFF0C8;color:#98700B}
        .slx-tool b{font-size:10px;line-height:1.3;color:#32134F}.slx-tool p{font-size:9px;line-height:1.4;color:#756681;margin:0}
        @media(max-width:900px){.slx-tool-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
        @media(max-width:600px){.slx-branches{grid-template-columns:1fr}.slx-connector-area{height:48px}.slx-tool-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}

        
        /* Reference-matched radial skills mind map */
        .slx-radial-map{position:relative;isolation:isolate;display:grid;grid-template-columns:minmax(0,1fr) minmax(150px,.78fr) minmax(0,1fr);grid-template-rows:repeat(3,minmax(132px,auto));gap:13px 14px;min-height:455px;padding:18px 12px;border:1px solid #E8DDF1;border-radius:19px;background:linear-gradient(145deg,#FCF8FF 0%,#FFFFFF 54%,#FFFCF1 100%);overflow:hidden}
        .slx-radial-lines{position:absolute;inset:0;width:100%;height:100%;z-index:0;pointer-events:none}
        .slx-radial-lines path{fill:none;stroke-width:3.2;stroke-linecap:round;opacity:.9}
        .slx-radial-lines path.purple{stroke:#8652B5}.slx-radial-lines path.gold{stroke:#C7A34B}.slx-radial-lines circle{fill:#8652B5;stroke:#fff;stroke-width:3}
        .slx-radial-hub{grid-column:2;grid-row:2;align-self:center;justify-self:center;position:relative;z-index:2;width:100%;min-height:145px;padding:17px 12px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;border:3px solid #fff;border-radius:20px;color:#fff;background:linear-gradient(135deg,#6421C7 0%,#8D4BCB 68%,#D4B65D 100%);box-shadow:0 9px 25px rgba(93,43,150,.22)}
        .slx-radial-hub span{font-size:8px;letter-spacing:1.4px;font-weight:900}.slx-radial-hub b{font-size:15px;line-height:1.25;margin:7px 0}.slx-radial-hub small{font-size:9px;opacity:.92}.slx-radial-hub .slx-hub-caption{margin-top:9px;padding:5px 8px;border-radius:20px;background:rgba(255,255,255,.17);font-size:8px}
        .slx-radial-branch{position:relative;z-index:1;min-width:0;align-self:stretch;padding:12px 12px 10px;border:1px solid #E4D5F1;border-radius:15px;background:linear-gradient(145deg,#F7F0FF,#fff 78%);box-shadow:0 4px 13px rgba(75,40,110,.06)}
        .slx-radial-branch.gold{border-color:#EADBAF;background:linear-gradient(145deg,#FFFAEC,#fff 78%)}
        .slx-radial-branch.left-top{grid-column:1;grid-row:1}.slx-radial-branch.right-top{grid-column:3;grid-row:1}
        .slx-radial-branch.left-mid{grid-column:1;grid-row:2}.slx-radial-branch.right-mid{grid-column:3;grid-row:2}
        .slx-radial-branch.left-bottom{grid-column:1;grid-row:3}.slx-radial-branch.right-bottom{grid-column:3;grid-row:3}
        .slx-radial-branch .slx-branch-head{font-size:11px;line-height:1.3}.slx-radial-branch .slx-branch-icon{flex:0 0 24px}
        .slx-radial-branch p{font-size:9px;line-height:1.45;margin:7px 0;color:#74647F}
        .slx-radial-branch .slx-chips{gap:4px}.slx-radial-branch .slx-chip{font-size:8px;padding:4px 6px}
        .slx-tool-grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}
        .slx-tool{min-height:132px;padding:11px 7px}
        .slx-tool-mark{width:52px;height:52px;flex:0 0 52px}
        .slx-tool-mark img{width:36px;height:36px;object-fit:contain}
        @media(max-width:1050px){.slx-radial-map{grid-template-columns:minmax(0,1fr) minmax(125px,.7fr) minmax(0,1fr);gap:9px;min-height:430px;padding:12px 8px}.slx-radial-branch{padding:10px 8px}.slx-radial-hub{min-height:130px}.slx-tool-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
        @media(max-width:700px){.slx-radial-map{grid-template-columns:1fr 1fr;grid-template-rows:auto;min-height:0;padding:12px}.slx-radial-lines{display:none}.slx-radial-hub{grid-column:1/-1;grid-row:1;width:min(330px,100%);min-height:110px}.slx-radial-branch.left-top{grid-column:1;grid-row:auto}.slx-radial-branch.right-top{grid-column:2;grid-row:auto}.slx-radial-branch.left-mid{grid-column:1;grid-row:auto}.slx-radial-branch.right-mid{grid-column:2;grid-row:auto}.slx-radial-branch.left-bottom{grid-column:1;grid-row:auto}.slx-radial-branch.right-bottom{grid-column:2;grid-row:auto}}
        @media(max-width:460px){.slx-radial-map{grid-template-columns:1fr}.slx-radial-hub{grid-column:1}.slx-radial-branch.left-top,.slx-radial-branch.right-top,.slx-radial-branch.left-mid,.slx-radial-branch.right-mid,.slx-radial-branch.left-bottom,.slx-radial-branch.right-bottom{grid-column:1}}

        /* Readability improvements for the full-width stacked sections. */
        .sl-info-panel{padding:19px 22px;margin:10px 0 16px}
        .sl-info-panel-title{font-size:16px;margin-bottom:12px}
        .sl-info-row{font-size:14px;line-height:1.65;padding:9px 0}
        .slx-radial-branch .slx-branch-head{font-size:13px}
        .slx-radial-branch p{font-size:11px;line-height:1.6}
        .slx-radial-branch .slx-chip{font-size:10px;padding:5px 8px}
        .slx-tool b{font-size:12px}
        .slx-tool p{font-size:11px;line-height:1.55}
        .sl-project-card b{font-size:15px}
        .sl-project-card p{font-size:13px;line-height:1.6}
        .sl-career-step b{font-size:14px}
        .sl-career-step small{font-size:11px}
        .sl-career-step p{font-size:12px;line-height:1.6}
        </style>
        <div class="career-hero">
          <div class="career-hero-icon" aria-hidden="true">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 35.5V13.8C9 11.7 10.7 10 12.8 10H29" stroke="white" stroke-width="2.6" stroke-linecap="round"/>
              <path d="M9 35.5H30.5" stroke="white" stroke-width="2.6" stroke-linecap="round"/>
              <path d="M16 18H27M16 24H24" stroke="white" stroke-width="2.4" stroke-linecap="round"/>
              <circle cx="31.5" cy="29.5" r="9.5" stroke="white" stroke-width="2.6"/>
              <path d="M38.5 36.5L43 41" stroke="#FFE8A8" stroke-width="3.2" stroke-linecap="round"/>
              <path d="M31.5 24.5V29.5L35 31.5" stroke="#FFE8A8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div>
            <div class="career-kicker">CAREER DEVELOPMENT • PERSONALIZED LEARNING</div>
            <div class="career-title">Turn your career goal into a clear roadmap.</div>
            <div class="career-sub">Explore what the role involves, discover the skills employers value and build a practical learning plan for your chosen career.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### What career are you working towards?")
    st.caption("Enter a role from any industry — technology, business, finance, healthcare, design, engineering, education and more.")

    with st.form("career_goal_form_v2", clear_on_submit=False):
        role_col, exp_col, hours_col = st.columns([1.25, 1.15, 1.0], gap="medium")
        with role_col:
            goal_input = st.text_input(
                "Enter your target role",
                value="",
                placeholder="e.g. Data Scientist, Product Manager, UX Designer...",
                key="career_goal_input_v2",
            )
        with exp_col:
            exp = st.selectbox(
                "Your current experience level",
                ["Beginner", "Intermediate", "Experienced"],
                key="career_exp_v2",
            )
        with hours_col:
            hours = st.selectbox(
                "Time available each week",
                ["2–4 hours", "5–7 hours", "8–10 hours", "11–15 hours", "15+ hours"],
                index=2,
                key="career_hours_v2",
            )
        submitted = st.form_submit_button(
            "✦  Generate my career roadmap",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        cleaned = goal_input.strip()
        if not cleaned:
            st.session_state.pop("career_guidance_result", None)
            st.error("Please enter your target role.")
        else:
            st.session_state["career_guidance_requested_role"] = cleaned
            st.session_state["career_guidance_experience"] = exp
            st.session_state["career_guidance_hours"] = hours
            st.session_state.pop("career_guidance_result", None)
            st.session_state["career_guidance_error"] = ""

            model = st.session_state.get("career_ollama_model", DEFAULT_MODEL)
            with st.spinner(f"Building a tailored roadmap for {cleaned}..."):
                try:
                    result = _generate_roadmap(cleaned, exp, hours, model)
                    st.session_state["career_guidance_result"] = result
                except requests.exceptions.ConnectionError:
                    st.session_state["career_guidance_error"] = (
                        "SkillLens AI cannot reach Ollama on this Mac. Start the Ollama app, "
                        "then download a model in Terminal using: ollama pull llama3.2"
                    )
                except requests.exceptions.Timeout:
                    st.session_state["career_guidance_error"] = (
                        "The local AI took too long to respond. Try again, or use a smaller Ollama model."
                    )
                except requests.exceptions.HTTPError as exc:
                    st.session_state["career_guidance_error"] = (
                        f"Ollama returned an HTTP error: {exc}. Check that the selected model is installed."
                    )
                except (ValueError, json.JSONDecodeError, KeyError) as exc:
                    st.session_state["career_guidance_error"] = (
                        f"The AI response could not be formatted as a roadmap: {exc}. Please try again."
                    )
                except Exception as exc:
                    st.session_state["career_guidance_error"] = (
                        f"Could not generate the roadmap: {exc}"
                    )

    error = st.session_state.get("career_guidance_error", "")
    if error:
        st.error(error)
        st.info(
            "This version uses Ollama locally, so it does not require a paid API subscription. "
            "The model runs on your own computer. Install Ollama and run `ollama pull llama3.2` once."
        )

    result = st.session_state.get("career_guidance_result")
    if result:
        _render_roadmap(result)
    elif not error:
        st.markdown(
            """
            <div style="margin-top:18px;padding:19px 21px;border:1px solid #E8D8F1;
            border-left:4px solid #D9BD78;border-radius:15px;
            background:linear-gradient(110deg,#FBF7FF 0%,#FFFFFF 72%,#FFFBF0 100%);
            box-shadow:0 4px 14px rgba(93,55,125,.045);color:#766783;font-size:13px;">
              <strong style="color:#32134F;">Your career roadmap will appear here.</strong><br>
              Enter your target role and select <strong>Generate my career roadmap</strong>.
              SkillLens AI will create role-specific guidance after submission.
            </div>
            """,
            unsafe_allow_html=True,
        )
