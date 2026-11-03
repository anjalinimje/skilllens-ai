"""Unified activity history for SkillLens AI."""
from datetime import datetime
import pandas as pd
import streamlit as st


PURPLE = "#8138B5"
DARK = "#291437"
MUTED = "#76677F"
GOLD = "#D9A83E"


def _normalise_activities():
    """Return unified events, including legacy analyses from older sessions."""
    activities = list(st.session_state.get("activity_log", []))
    logged_analysis_ids = {
        str(item.get("details", {}).get("date", "")) + "|" +
        str(item.get("details", {}).get("role", ""))
        for item in activities if item.get("type") == "Resume Analysis"
    }

    for index, analysis in enumerate(st.session_state.get("analyses", [])):
        legacy_id = str(analysis.get("date", "")) + "|" + str(analysis.get("role", ""))
        if legacy_id not in logged_analysis_ids:
            results = analysis.get("results", [])
            valid = [r for r in results if not r.get("error")]
            average = round(sum(r.get("score", 0) for r in valid) / max(len(valid), 1))
            activities.append({
                "activity_id": f"legacy-analysis-{index}",
                "type": "Resume Analysis",
                "title": f"Resume analysis: {analysis.get('role', 'Untitled role')}",
                "summary": f"{len(valid)} resume(s) analysed · {average}% average skill match",
                "details": {
                    **analysis,
                    "average_score": average,
                    "resume_count": len(valid),
                },
                "timestamp": "",
                "display_time": analysis.get("date", "Earlier session"),
            })

    def sort_key(item):
        raw = item.get("timestamp", "")
        try:
            return datetime.fromisoformat(raw).timestamp()
        except (TypeError, ValueError):
            return 0

    return sorted(activities, key=sort_key, reverse=True)


def _activity_icon(activity_type):
    return {
        "Resume Analysis": "▤",
        "Job Search": "⌕",
        "Saved Job": "☆",
        "Career Roadmap": "✦",
        "Tailored Resume": "✎",
    }.get(activity_type, "•")


def _render_activity(item, index):
    kind = item.get("type", "Activity")
    details = item.get("details", {}) or {}
    timestamp = item.get("display_time", "Date unavailable")
    icon = _activity_icon(kind)

    with st.container(border=True):
        left, body, right = st.columns([0.65, 5.2, 1.2], vertical_alignment="center")
        with left:
            st.markdown(
                f'<div class="sl-history-icon">{icon}</div>',
                unsafe_allow_html=True,
            )
        with body:
            st.markdown(f"**{item.get('title', kind)}**")
            st.caption(f"{kind}  ·  {timestamp}")
            if item.get("summary"):
                st.write(item["summary"])
        with right:
            st.markdown(
                f'<div class="sl-history-type">{kind}</div>',
                unsafe_allow_html=True,
            )

        with st.expander("View details", expanded=False):
            if kind == "Resume Analysis":
                st.markdown(f"**Target role:** {details.get('role', 'Not recorded')}")
                if details.get("average_score") is not None:
                    st.metric("Average skill match", f"{details['average_score']}%")
                st.markdown("**Resume results**")
                for result in details.get("results", []):
                    st.markdown(
                        f"- **{result.get('filename', 'Resume')}** — "
                        f"{result.get('score', 0)}% match"
                    )
                    if result.get("error"):
                        st.warning(result["error"])
                    else:
                        st.caption(
                            "Matched: " + (", ".join(result.get("matched", [])) or "None")
                        )
                        st.caption(
                            "Skills to develop/verify: " +
                            (", ".join(result.get("missing", [])) or "None")
                        )
                export_rows = [{
                    "Job title": details.get("role", ""),
                    "Date": details.get("date", timestamp),
                    "Resume": result.get("filename", ""),
                    "Match score (%)": result.get("score", 0),
                    "Matched skills": ", ".join(result.get("matched", [])),
                    "Missing skills": ", ".join(result.get("missing", [])),
                    "Error": result.get("error") or "",
                } for result in details.get("results", [])]
                if export_rows:
                    st.download_button(
                        "Export analysis to CSV",
                        data=pd.DataFrame(export_rows).to_csv(index=False),
                        file_name=f"skilllens_analysis_{index + 1}.csv",
                        mime="text/csv",
                        key=f"history_analysis_export_{index}",
                    )

            elif kind == "Job Search":
                st.write(f"**Keywords:** {details.get('keywords', '—')}")
                st.write(f"**Location:** {details.get('location') or 'Not specified'}")
                st.write(f"**Market:** {details.get('country', '—')}")
                st.write(f"**Filters:** {details.get('posted_within', 'Any time')}; "
                         f"{'Full-time; ' if details.get('full_time') else ''}"
                         f"{'Permanent' if details.get('permanent') else 'Any contract'}")
                jobs = details.get("jobs", [])
                if jobs:
                    st.markdown("**Listings returned**")
                    for job in jobs:
                        st.markdown(
                            f"- **{job.get('title', 'Untitled role')}** — "
                            f"{job.get('company', 'Company not listed')} · "
                            f"{job.get('location', 'Location not listed')}"
                        )
                        if job.get("url"):
                            st.markdown(f"  [View listing]({job['url']})")
                else:
                    st.caption("No listings matched this search.")

            elif kind == "Saved Job":
                job = details.get("job", {})
                st.write(f"**Company:** {job.get('company', 'Not listed')}")
                st.write(f"**Location:** {job.get('location', 'Not listed')}")
                st.write(f"**Description:** {job.get('description', 'Not available')}")
                if job.get("url"):
                    st.link_button("Open job listing ↗", job["url"])

            elif kind == "Career Roadmap":
                st.write(f"**Target role:** {details.get('role_title', 'Not recorded')}")
                st.write(f"**Estimated plan:** {details.get('estimated_plan', 'Flexible')}")
                st.write(f"**Learning phases:** {details.get('phase_count', 0)}")
                roadmap = details.get("roadmap", {})
                for phase_no, phase in enumerate(roadmap.get("phases", []), start=1):
                    with st.expander(f"Phase {phase_no}: {phase.get('title', 'Learning phase')}"):
                        st.write(phase.get("objective", ""))
                        for topic in phase.get("topics", []):
                            st.markdown(f"- {topic}")


def render_history():
    st.markdown(
        """
        <style>
        .sl-history-hero {
            padding: 28px 30px;
            margin: 4px 0 22px;
            border-radius: 22px;
            border: 1px solid #E5D8F0;
            background: linear-gradient(115deg, #F6EEFF 0%, #FFFFFF 58%, #FFF8E7 100%);
            box-shadow: 0 10px 26px rgba(79, 35, 105, .07);
        }
        .sl-history-eyebrow {
            color: #8138B5; font-size: 11px; font-weight: 800;
            letter-spacing: 1.8px; text-transform: uppercase;
        }
        .sl-history-title {
            color: #291437; font-size: 30px; font-weight: 850;
            letter-spacing: -.7px; margin: 5px 0 6px;
        }
        .sl-history-subtitle { color: #76677F; font-size: 14px; }
        .sl-history-icon {
            width: 42px; height: 42px; border-radius: 13px;
            display: flex; align-items: center; justify-content: center;
            background: linear-gradient(135deg, #F1E5FF, #FFF4D9);
            border: 1px solid #E7D7F2; color: #8138B5;
            font-size: 21px; font-weight: 800;
        }
        .sl-history-type {
            color: #8138B5; background: #F5EDFC;
            border: 1px solid #E8D9F2; border-radius: 999px;
            padding: 5px 9px; text-align: center;
            font-size: 10px; font-weight: 800;
            white-space: nowrap;
        }
        .sl-history-metric {
            min-height: 142px; padding: 17px 16px 15px;
            border-radius: 18px; border: 1px solid #E9E0EF;
            background: linear-gradient(145deg, var(--metric-tint) 0%, #FFFFFF 78%);
            box-shadow: 0 5px 16px rgba(48, 25, 65, .045);
            transition: transform .18s ease, box-shadow .18s ease;
        }
        .sl-history-metric:hover { transform: translateY(-3px); box-shadow: 0 10px 22px rgba(48,25,65,.09); }
        .sl-history-metric-top { display:flex; align-items:center; justify-content:space-between; gap:8px; }
        .sl-history-metric-icon {
            display:inline-flex; align-items:center; justify-content:center;
            width:34px; height:34px; border-radius:11px; background:rgba(255,255,255,.82);
            color:var(--metric-accent); font-size:20px; font-weight:800;
            border:1px solid rgba(120,90,140,.10);
        }
        .sl-history-metric-label { color:#76677F; font-size:11px; font-weight:750; text-align:right; line-height:1.25; }
        .sl-history-metric-value { color:var(--metric-accent); font-size:31px; line-height:1.15; font-weight:850; letter-spacing:-.8px; margin-top:12px; }
        .sl-history-metric-helper { color:#887B90; font-size:10px; margin-top:4px; }
        /* Rounded History filters with a light-lavender selected state. */
        div[data-testid="stRadio"] div[role="radiogroup"] {
            display:flex;
            flex-wrap:wrap;
            gap:8px;
        }
        div[data-testid="stRadio"] div[role="radiogroup"] label {
            background:#FFFFFF !important;
            border:1px solid #E7DCEE !important;
            border-radius:999px !important;
            padding:7px 14px !important;
            color:#65566E !important;
            margin:0 !important;
            transition:background .15s ease, border-color .15s ease;
        }
        div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
            background:#F1E5FA !important;
            border:1px solid #DCC5EC !important;
            color:#71349D !important;
            box-shadow:0 3px 9px rgba(129,56,181,.10) !important;
        }
        div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p,
        div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) span {
            color:#71349D !important;
        }
        div[data-testid="stRadio"] div[role="radiogroup"] input {
            accent-color:#8138B5 !important;
        }
        @media (max-width:850px) { .sl-history-metric { min-height:128px; padding:13px; } .sl-history-metric-label {font-size:10px;} }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 17px; border-color: #EAE1F1;
        }
        </style>
        <div class="sl-history-hero">
          <div class="sl-history-eyebrow">YOUR SKILLLENS WORKSPACE</div>
          <div class="sl-history-title">Activity History</div>
          <div class="sl-history-subtitle">
            Your resume analyses, job searches, saved opportunities and career roadmaps — all in one place.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    activities = _normalise_activities()
    total = len(activities)
    analysis_count = sum(a.get("type") == "Resume Analysis" for a in activities)
    search_count = sum(a.get("type") == "Job Search" for a in activities)
    saved_count = sum(a.get("type") == "Saved Job" for a in activities)
    roadmap_count = sum(a.get("type") == "Career Roadmap" for a in activities)

    # Custom KPI cards matching SkillLens AI's purple, gold and soft-neutral palette.
    metric_cards = [
        ("Total activities", total, "▦", "#F4EAFB", PURPLE, "All recorded actions"),
        ("Resume analyses", analysis_count, "⌕", "#FFF7E7", "#B88725", "Candidate screening"),
        ("Job searches", search_count, "▣", "#EEF2FF", "#5572B5", "Opportunities explored"),
        ("Career roadmaps", roadmap_count, "⌁", "#EDF7F0", "#39845C", "Growth plans created"),
    ]
    metric_cols = st.columns(4, gap="medium")
    for col, (label, value, icon_char, tint, accent, helper) in zip(metric_cols, metric_cards):
        with col:
            st.markdown(
                f"""
                <div class="sl-history-metric" style="--metric-tint:{tint};--metric-accent:{accent}">
                    <div class="sl-history-metric-top">
                        <span class="sl-history-metric-icon">{icon_char}</span>
                        <span class="sl-history-metric-label">{label}</span>
                    </div>
                    <div class="sl-history-metric-value">{value}</div>
                    <div class="sl-history-metric-helper">{helper}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### Your recent activity")
    filter_options = ["All Activities", "Resume Analysis", "Job Search", "Saved Job", "Career Roadmap"]
    filter_labels = {
        "All Activities": "All activities",
        "Resume Analysis": "Resume analysis",
        "Job Search": "Job search",
        "Saved Job": "Saved jobs",
        "Career Roadmap": "Career roadmaps",
    }
    # Use a horizontal radio group styled as filter pills. This avoids
    # Streamlit's segmented-control theme accent overriding the lavender CSS.
    selected = st.radio(
        "Filter activity",
        options=filter_options,
        format_func=lambda option: filter_labels[option],
        horizontal=True,
        label_visibility="collapsed",
        key="history_activity_filter_lavender",
    )
    selected = selected or "All Activities"
    filtered = activities if selected == "All Activities" else [
        item for item in activities if item.get("type") == selected
    ]

    if not filtered:
        st.info(
            "No activities in this category yet. Upload a resume, search for jobs, "
            "save a listing or generate a career roadmap to see it here."
        )
        return

    st.caption(f"Showing {len(filtered)} of {total} recorded activities · newest first")
    for index, item in enumerate(filtered):
        _render_activity(item, index)

    export = [{
        "Activity": item.get("type", ""),
        "Title": item.get("title", ""),
        "Summary": item.get("summary", ""),
        "Date": item.get("display_time", ""),
    } for item in activities]
    st.download_button(
        "Download activity history (CSV)",
        data=pd.DataFrame(export).to_csv(index=False),
        file_name="skilllens_activity_history.csv",
        mime="text/csv",
        key="export_all_activity_history",
    )

    st.caption(
        "History currently lasts for the active Streamlit session. "
        "Persistent storage across sign-outs, sessions and server restarts is a separate next step."
    )
