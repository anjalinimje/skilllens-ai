
from pathlib import Path

import streamlit as st


def render_sidebar():
    """Render SkillLens AI branding and clickable navigation."""

    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            background: #FFFFFF;
            border-right: 1px solid #EAE1F1;
        }

        [data-testid="stSidebar"] > div:first-child {
            padding: 0.5rem 0.8rem 1rem;
        }

        .sl-section {
            color: #9A7AA9;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.5px;
            margin: 7px 0 5px 4px;
        }

        .sl-tagline {
            color: #76677F;
            font-size: 12px;
            line-height: 1.5;
            margin-top: 6px;
        }

        [data-testid="stSidebar"] hr {
    margin-top: 0.6rem;
    margin-bottom: 0.6rem;
}

        
/* Consistent full-width sidebar navigation */

[data-testid="stSidebar"] div.stButton {
    width: 100%;
}

[data-testid="stSidebar"] div.stButton > button {
    display: flex;
    width: 100%;
    min-height: 46px;
    justify-content: flex-start !important;
    text-align: left !important;
    padding: 0 14px !important;
    margin: 4px 0 !important;
    border-radius: 10px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    box-sizing: border-box;
}

[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
    background: #F3E9FF !important;
    color: #54227A !important;
    border: 1px solid #E5D1FA !important;
    box-shadow: inset 3px 0 0 #8138B5 !important;
}

[data-testid="stSidebar"] div.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: #46394E !important;
    border: 1px solid transparent !important;
}

[data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover {
    background: #FBF7FF !important;
    color: #8138B5 !important;
    border-color: #EAE1F1 !important;
}


        .sl-status {
            color: #46394E;
            font-size: 13px;
            font-weight: 600;
            margin: 12px 0 3px;
        }

        .sl-detail {
            color: #76677F;
            font-size: 11px;
            margin-bottom: 10px;
        }

        .sl-footer {
            background: #FFF8E6;
            border: 1px solid #F2E1B2;
            border-radius: 12px;
            padding: 13px;
            margin-top: 18px;
        }

        .sl-footer-title {
            color: #6D4A0B;
            font-weight: 700;
            font-size: 13px;
        }

        .sl-footer-text {
            color: #806B48;
            font-size: 11px;
            line-height: 1.6;
            margin-top: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "skilllens_current_page" not in st.session_state:
        st.session_state["skilllens_current_page"] = "Dashboard"

    pages = [
    ("Dashboard", "▦", "nav_dashboard"),
    ("New Analysis", "＋", "nav_analysis"),
    ("Job Search", "🔍", "nav_job_search"),
    ("History", "◷", "nav_history"),
    ("Privacy", "🔒", "nav_privacy"),
]

    with st.sidebar:
        logo_path = (
            Path(__file__).parent
            / "assets"
            / "skilllens_logo.png"
        )

        if logo_path.exists():
            st.image(str(logo_path), use_container_width=True)
        else:
            st.markdown(
                "<h2 style='color:#291437;margin-bottom:0'>"
                "SkillLens <span style='color:#8138B5'>AI</span>"
                "</h2>",
                unsafe_allow_html=True,
            )

        

        st.divider()

        st.markdown(
            '<div class="sl-section">WORKSPACE</div>',
            unsafe_allow_html=True,
        )

        
        nav_items = [
            ("Dashboard", "nav_dashboard", ":material/dashboard:"),
            ("New analysis", "nav_analysis", ":material/description:"),
            ("Job Search", "nav_job_search", ":material/search:"),
            ("Career Guidance", "nav_career_guidance", ":material/psychology:"),
            ("History", "nav_history", ":material/history:"),
            ("Privacy", "nav_privacy", ":material/lock:"),
        ]

        for label, key, icon_name in nav_items:
            selected = (
                st.session_state["skilllens_current_page"] == label
            )

            if st.button(
                label,
                key=key,
                icon=icon_name,
                type="primary" if selected else "secondary",
                use_container_width=True,
            ):
                if not selected:
                    st.session_state["skilllens_current_page"] = label
                    st.rerun()



        st.divider()

        

        st.markdown(
            """
            
            <div class="sl-footer">
                <div class="sl-footer-title">✦ SkillLens AI</div>
                <div class="sl-footer-text">
                    Intelligent screening.<br>
                    Human-led decisions.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return st.session_state["skilllens_current_page"]
