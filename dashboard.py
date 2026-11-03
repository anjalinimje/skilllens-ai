
import pandas as pd
import streamlit as st


PURPLE = "#6D28D9"
LAVENDER = "#A78BFA"
GOLD = "#F2C94C"


def _valid_results(analysis):
    """Return successfully processed resume results."""
    return [
        result
        for result in analysis.get("results", [])
        if result.get("error") is None
    ]


def _matched_skills(result):
    """Read matched skills when the result includes them."""
    for key in ("matched_skills", "matched", "skills_matched"):
        value = result.get(key)

        if isinstance(value, (list, tuple, set)):
            return [str(skill) for skill in value if skill]

        if isinstance(value, dict):
            return [
                str(skill)
                for skill, matched in value.items()
                if matched
            ]

    return []


def render_dashboard(analyses):
    """Render the SkillLens AI recruitment dashboard."""

    # Search is available at the top of the dashboard and filters the visible
    # dashboard data without modifying the original analysis records.
    search_query = st.text_input(
            "",
            placeholder=" 🔍 Search analyses, job roles or skills…",
            key="dashboard_search",
            label_visibility="collapsed",
        ).strip().lower()
    if search_query:
            analyses = [
                analysis for analysis in analyses
                if search_query in str(analysis).lower()
            ]
            st.caption(f"Showing {len(analyses)} of {len(analyses)} screening runs")
    analyses = analyses or []

    # Aggregate real screening results.
    completed = []
    for analysis in analyses:
        completed.extend(_valid_results(analysis))

    scores = []
    for result in completed:
        score = result.get("score")
        if isinstance(score, (int, float)):
            scores.append(float(score))

    average_score = (
        round(sum(scores) / len(scores))
        if scores else None
    )

    unique_skills = set()
    for result in completed:
        unique_skills.update(_matched_skills(result))

    roles = {
        str(item.get("role", "")).strip()
        for item in analyses
        if str(item.get("role", "")).strip()
    }

    # Styling scoped to the dashboard.
    st.markdown(
        """
        <style>
        .sl-eyebrow {
            color: #6D28D9;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1.8px;
            text-transform: uppercase;
        }

        .sl-hero {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 22px;
            background: linear-gradient(115deg, #F5F3FF 0%, #FFFFFF 58%, #FFFBEB 100%);
            border: 1px solid #E8DFF7;
            border-right: 3px solid #F2C94C;
            border-radius: 20px;
            padding: 28px 30px;
            margin: 8px 0 24px;
            box-shadow: 0 8px 28px rgba(79, 35, 105, 0.045);
            overflow: hidden;
        }
        .sl-hero-copy { flex: 1 1 62%; min-width: 0; }
        .sl-hero h1 {
            color: #1E1B4B; font-size: 30px; line-height: 1.2;
            margin: 9px 0 12px;
        }
        .sl-hero p {
            color: #64708B; font-size: 14px; line-height: 1.65;
            margin-bottom: 0; max-width: 650px;
        }
        .sl-hero-art {
            flex: 0 0 220px; display: flex; align-items: center;
            justify-content: center; min-height: 150px;
        }
        .sl-hero-art svg { display: block; width: 100%; max-width: 220px; height: auto; }
        .sl-empty-state {
            display: flex; align-items: center; gap: 15px;
            padding: 18px 20px; border: 1px solid #E9DDF8;
            border-radius: 16px; background: linear-gradient(110deg, #F5F3FF 0%, #FFFFFF 72%, #FFFBEB 100%);
            box-shadow: 0 5px 18px rgba(79, 35, 105, 0.035);
            margin: 0 0 18px;
        }
        .sl-empty-icon {
            flex: 0 0 44px; width: 44px; height: 44px;
            display: grid; place-items: center; border-radius: 13px;
            color: #6D28D9; background: linear-gradient(135deg, #F1E5FA, #FFF4C7); font-size: 22px;
        }
        .sl-empty-state strong { display: block; color: #1E1B4B; margin-bottom: 4px; }
        .sl-empty-state span { color: #64708B; font-size: 13px; line-height: 1.5; }
        @media (max-width: 760px) {
            .sl-hero { padding: 22px; }
            .sl-hero-art { display: none; }
            .sl-hero h1 { font-size: 25px; }
        }

        .sl-kpi-card {
            display: flex; align-items: center; gap: 14px; min-width: 0;
            min-height: 112px; padding: 17px 15px; box-sizing: border-box;
            background: linear-gradient(135deg, #FFFFFF 45%, #F7F2FF 100%);
            border: 1px solid #E6DDF5; border-top: 3px solid #7C3AED;
            border-radius: 16px; box-shadow: 0 5px 17px rgba(79, 35, 105, .055);
            position: relative; overflow: hidden;
        }
        .sl-kpi-card::after {
            content: ""; position: absolute; width: 42px; height: 42px;
            right: -18px; bottom: -20px; border-radius: 50%;
            background: #FFF0B8; opacity: .7;
        }
        .sl-kpi-icon {
            flex: 0 0 48px; width: 48px; height: 48px; position: relative;
            display: grid; place-items: center; border-radius: 14px;
            color: #6D28D9; background: linear-gradient(145deg, #F1E8FF, #FFFFFF);
            border: 1px solid #E8D9FF;
        }
        .sl-kpi-icon svg { width: 27px; height: 27px; }
        .sl-kpi-icon .gold { stroke: #D6A91D; }
        .sl-kpi-gold-dot {
            position: absolute; width: 7px; height: 7px; right: 5px; top: 5px;
            background: #F2C94C; border: 2px solid #FFFFFF; border-radius: 50%;
        }
        .sl-kpi-copy { min-width: 0; position: relative; z-index: 1; }
        .sl-kpi-label { color: #64708B; font-size: 12px; line-height: 1.4; font-weight: 600; }
        .sl-kpi-value { color: #1E1B4B; font-size: 28px; line-height: 1.25; font-weight: 800; margin-top: 5px; }
        @media (max-width: 900px) {
            .sl-kpi-card { gap: 10px; padding: 14px 10px; }
            .sl-kpi-icon { flex-basis: 40px; width: 40px; height: 40px; }
            .sl-kpi-value { font-size: 24px; }
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(
                145deg, #FFFFFF 52%, #F7F5FF 82%, #FFFCF0 100%
            );
            border: 1px solid #E5E0F2;
            border-top: 2px solid #F2D36F;
            border-radius: 16px;
            padding: 17px 18px;
            min-height: 120px;
            box-shadow: 0 4px 15px rgba(79, 35, 105, 0.04);
        }

        div[data-testid="stMetricLabel"] {
            color: #64708B;
            font-size: 12px;
            font-weight: 600;
        }

        div[data-testid="stMetricValue"] {
            color: #1E1B4B;
            font-weight: 750;
        }

        .sl-section-note {
            color: #64708B;
            font-size: 13px;
            margin-top: -7px;
        }
        .sl-panel-title {
            display: flex; align-items: center; gap: 11px;
            color: #1E1B4B; font-size: 19px; line-height: 1.35;
            font-weight: 750; margin: 0 0 14px;
        }
        .sl-panel-icon {
            display: inline-grid; place-items: center; flex: 0 0 38px;
            width: 38px; height: 38px; border-radius: 12px;
            color: #6D28D9;
            background: linear-gradient(145deg, #F1E8FF, #FFFFFF 72%, #FFF7D6);
            border: 1px solid #E8D9FF;
            box-shadow: inset 0 -2px 0 rgba(242, 201, 76, .28);
        }
        .sl-panel-icon svg { width: 22px; height: 22px; display: block; }
        .sl-panel-icon .gold { stroke: #D6A91D; }

        div[data-testid="stButton"] button[kind="primary"] {
            background: linear-gradient(135deg, #7C3AED, #5B21B6);
            border: 1px solid #6D28D9;
            box-shadow: 0 4px 12px rgba(109, 40, 217, 0.16), inset 0 0 0 1px rgba(242, 201, 76, 0.18);
            color: #FFFFFF;
            border-radius: 11px;
            font-weight: 650;
            box-shadow: 0 4px 12px rgba(109, 40, 217, 0.16);
        }
        div[data-testid="stButton"] button[kind="primary"]:hover {
            background: #5B21B6;
            border-color: #5B21B6;
            color: #FFFFFF;
        }
        div[data-testid="stAlert"] {
            border-radius: 12px;
            border-color: #DDD6FE;
            background: linear-gradient(110deg, #F5F3FF, #FFFCF0);
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid #E5E7F5;
            border-radius: 12px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Hero: visual interest without external image dependencies.
    st.markdown(
        """
        <div class="sl-hero">
            <div class="sl-hero-copy">
                <div class="sl-eyebrow">Resume intelligence</div>
                <h1>See exactly where your resume stands — before a recruiter does.</h1>
                <p>
                    Compare candidate skills against job requirements, spot skill gaps,
                    and explore evidence-backed screening insights — all in one workspace.
                </p>
            </div>
            <div class="sl-hero-art" aria-hidden="true">
                <svg viewBox="0 0 240 180" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="slPurple" x1="0" y1="0" x2="1" y2="1">
                            <stop offset="0%" stop-color="#A45BD0"/>
                            <stop offset="100%" stop-color="#6D269D"/>
                        </linearGradient>
                        <linearGradient id="slAccent" x1="0" y1="0" x2="1" y2="1">
                            <stop offset="0%" stop-color="#F2C94C"/>
                            <stop offset="48%" stop-color="#A78BFA"/>
                            <stop offset="100%" stop-color="#7C3AED"/>
                        </linearGradient>
                    </defs>
                    <circle cx="128" cy="87" r="69" fill="#F2E7FA"/>
                    <circle cx="128" cy="87" r="53" fill="#FFFFFF" opacity=".85"/>
                    <path d="M29 122 C8 104 20 78 43 76 C50 47 83 42 102 60"
                          fill="none" stroke="url(#slAccent)" stroke-width="7" stroke-linecap="round"/>
                    <rect x="62" y="27" width="86" height="112" rx="12"
                          fill="url(#slPurple)" transform="rotate(-7 105 83)"/>
                    <rect x="73" y="38" width="64" height="91" rx="7"
                          fill="#FFFFFF" transform="rotate(-7 105 83)"/>
                    <circle cx="91" cy="58" r="8" fill="#F2C94C"/>
                    <path d="M83 75 Q91 64 99 75" fill="none" stroke="#6D28D9" stroke-width="4" stroke-linecap="round"/>
                    <rect x="105" y="53" width="23" height="4" rx="2" fill="#CBB3DC"/>
                    <rect x="105" y="62" width="18" height="4" rx="2" fill="#CBB3DC"/>
                    <rect x="82" y="88" width="45" height="4" rx="2" fill="#D8C8E4"/>
                    <rect x="82" y="98" width="38" height="4" rx="2" fill="#D8C8E4"/>
                    <rect x="82" y="108" width="42" height="4" rx="2" fill="#D8C8E4"/>
                    <circle cx="151" cy="105" r="31" fill="url(#slPurple)"/>
                    <circle cx="151" cy="105" r="23" fill="#FFFFFF"/>
                    <circle cx="151" cy="105" r="15" fill="#F7F0FC" stroke="#DCC5EC" stroke-width="2"/>
                    <path d="M161 126 L180 145" stroke="#6D28D9" stroke-width="10" stroke-linecap="round"/>
                    <path d="M144 105 L149 110 L159 98" fill="none" stroke="#D6A91D" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="195" cy="41" r="13" fill="#FFF4C7"/>
                    <path d="M195 33 L197.5 38.5 L203 41 L197.5 43.5 L195 49 L192.5 43.5 L187 41 L192.5 38.5 Z" fill="#D6A91D"/>
                    <circle cx="47" cy="145" r="5" fill="#7C3AED" opacity=".75"/>
                    <circle cx="204" cy="132" r="4" fill="#A45BD0" opacity=".8"/>
                </svg>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Give first-time users a useful next step instead of an empty-looking dashboard.
    if not completed:
        st.markdown(
            """
            <div class="sl-empty-state">
                <div class="sl-empty-icon">✦</div>
                <div>
                    <strong>Your workspace is ready for its first screening</strong>
                    <span>Add a job description and upload resumes to see match scores,
                    matched skills, and areas to review. Dashboard metrics populate after
                    a successful analysis.</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # KPI cards
    st.markdown("### Screening overview")

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    # Custom KPI cards use purple line icons with subtle gold accents.
    # Values continue to come from the existing analysis aggregation above.
    metric_cards = [
        (c1, 'Resumes analysed', str(len(completed)), '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h4"/>'),
        (c2, 'Average match score', f"{average_score}%" if average_score is not None else '—', '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/><path class="gold" d="M16 8l4-4"/>'),
        (c3, 'Matched skills', str(len(unique_skills)), '<path d="M12 3 21 8 12 13 3 8 12 3Z"/><path d="m3 12 9 5 9-5M3 16l9 5 9-5"/>'),
        (c4, 'Roles screened', str(len(roles)), '<circle cx="9" cy="8" r="3"/><path d="M3 20v-2a6 6 0 0 1 12 0v2M16 5a3 3 0 0 1 0 6M18 14a5 5 0 0 1 3 4v2"/>'),
    ]
    for column, label, value, icon_paths in metric_cards:
        with column:
            st.markdown(
                f'''<div class="sl-kpi-card">
                    <div class="sl-kpi-icon" aria-hidden="true">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                           stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        {icon_paths}
                      </svg>
                      <span class="sl-kpi-gold-dot"></span>
                    </div>
                    <div class="sl-kpi-copy">
                      <div class="sl-kpi-label">{label}</div>
                      <div class="sl-kpi-value">{value}</div>
                    </div>
                  </div>''',
                unsafe_allow_html=True,
            )

    st.markdown("")

    # Analytics panels
    left, right = st.columns([1.15, 1], gap="medium")

    with left:
        with st.container(border=True):
            st.markdown(
                '''<div class="sl-panel-title">
                    <span class="sl-panel-icon" aria-hidden="true">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                             stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M3 3v18h18"/><path d="m6 15 4-5 4 3 6-7"/>
                            <path class="gold" d="M16 6h4v4"/>
                        </svg>
                    </span>
                    <span>Match score trend</span>
                </div>''',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<p class="sl-section-note">'
                'Average resume match score by screening run'
                '</p>',
                unsafe_allow_html=True,
            )

            trend_rows = []

            for index, analysis in enumerate(analyses, start=1):
                valid = _valid_results(analysis)
                run_scores = [
                    float(r["score"])
                    for r in valid
                    if isinstance(r.get("score"), (int, float))
                ]

                if run_scores:
                    trend_rows.append({
                        "Screening run": (
                            str(analysis.get("date", f"Run {index}"))
                        ),
                        "Average score (%)": round(
                            sum(run_scores) / len(run_scores), 1
                        ),
                    })

            if trend_rows:
                trend_df = pd.DataFrame(trend_rows)
                st.line_chart(
                    trend_df.set_index("Screening run"),
                    y="Average score (%)",
                    color=PURPLE,
                    height=240,
                )
            else:
                st.info(
                    "Your score trend will appear after a successful "
                    "resume analysis."
                )

    with right:
        with st.container(border=True):
            st.markdown(
                '''<div class="sl-panel-title">
                    <span class="sl-panel-icon" aria-hidden="true">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                             stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M4 19V10M10 19V5M16 19v-7M22 19V8"/>
                            <path class="gold" d="M2 21h21"/>
                        </svg>
                    </span>
                    <span>Top matched skills</span>
                </div>''',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<p class="sl-section-note">'
                'Skills found in successfully processed resumes'
                '</p>',
                unsafe_allow_html=True,
            )

            from collections import Counter

            skill_counts = Counter()
            for result in completed:
                skill_counts.update(set(_matched_skills(result)))

            top_skills = skill_counts.most_common(7)

            if top_skills:
                skills_df = pd.DataFrame(
                    top_skills,
                    columns=["Skill", "Occurrences"],
                ).set_index("Skill")

                st.bar_chart(
                    skills_df,
                    color=PURPLE,
                    horizontal=True,
                    height=240,
                )
            else:
                st.info(
                    "Matched skills will appear here when your analysis "
                    "results include matched-skill details."
                )

    # Recent analyses table
    st.markdown("")
    with st.container(border=True):
        st.markdown(
            '''<div class="sl-panel-title">
                <span class="sl-panel-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                         stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="9"/>
                        <path d="M12 7v5l3 2"/>
                        <path class="gold" d="M16.5 3.8 19 5.5"/>
                    </svg>
                </span>
                <span>Recent analyses</span>
            </div>''',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="sl-section-note">'
            'Your latest screening activity'
            '</p>',
            unsafe_allow_html=True,
        )

        if analyses:
            rows = []

            for analysis in reversed(analyses):
                results = analysis.get("results", [])
                valid = _valid_results(analysis)

                run_scores = [
                    float(r["score"])
                    for r in valid
                    if isinstance(r.get("score"), (int, float))
                ]

                rows.append({
                    "Job role": analysis.get("role", "Untitled role"),
                    "Date": analysis.get("date", "—"),
                    "Resumes uploaded": len(results),
                    "Status": "Completed" if valid else "Not completed",
                    "Average match": (
                        f"{round(sum(run_scores) / len(run_scores))}%"
                        if run_scores else "—"
                    ),
                })

            st.dataframe(
    pd.DataFrame(rows).style.map(
        lambda status: (
            "color: #15803D; background-color: #DCFCE7; "
            "font-weight: 600; border-radius: 12px;"
            if status == "Completed"
            else
            "color: #B91C1C; background-color: #FEE2E2; "
            "font-weight: 600; border-radius: 12px;"
        ),
        subset=["Status"],
    ),
    hide_index=True,
    use_container_width=True,
)
        else:
            st.info(
                "No analyses yet. Start your first screening to populate "
                "your dashboard with real results."
            )

    st.markdown("")

    if st.button(
        "＋  Start a new analysis",
        type="primary",
        use_container_width=False,
        key="dashboard_new_analysis",
    ):
        st.session_state["skilllens_current_page"] = "New analysis"
        st.rerun()

    
