
import io
import re
from datetime import datetime

from career_guidance import render_career_guidance
import fitz
import pandas as pd
from job_search import render_job_search
import streamlit as st
from docx import Document
from pathlib import Path
from sidebar import render_sidebar
from dashboard import render_dashboard
from new_analysis import render_new_analysis
from history import render_history
from Privacy import render_privacy
import base64
from pathlib import Path
from auth import (
    register_user,
    login_user,
    logout_user,
    get_current_user,
    get_user_profile,
)

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="SkillLens AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# BRAND THEME: WHITE + GOLD + PURPLE
# --------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: #FFFFFF;
        color: #211128;
    }

    [data-testid="stSidebar"] {
        background: #FBF8FF;
        border-right: 1px solid #E9DDF7;
    }

    .brand {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -1.2px;
        color: #211128;
        margin: 0;
    }

    .brand span {
        background: linear-gradient(90deg, #C65AFF, #E5A52D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .tagline {
        color: #76677F;
        margin-top: 2px;
        margin-bottom: 20px;
    }

    .eyebrow {
        color: #8C6B9C;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
    }

    .panel {
        background: #FFFFFF;
        border: 1px solid #EAE1F1;
        border-radius: 16px;
        padding: 20px;
    }

    .muted {
        color: #76677F;
        font-size: 0.88rem;
    }

    div.stButton > button[kind="primary"] {
        background: #8138B5;
        border: 1px solid #8138B5;
        color: white;
        border-radius: 10px;
        font-weight: 600;
    }

    div.stButton > button[kind="primary"]:hover {
        background: #682B96;
        border-color: #682B96;
        color: white;
    }

    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #EAE1F1;
        border-radius: 14px;
        padding: 16px;
    }

    div[data-testid="stMetricLabel"] {
        color: #76677F;
    }

    div[data-testid="stMetricValue"] {
        color: #211128;
    }

    div[data-baseweb="tab-list"] {
        gap: 8px;
    }

    button[data-baseweb="tab"] {
        border-radius: 8px;
    }


/* Premium SkillLens AI dashboard enhancements */

[data-testid="stMetric"] {
    background: linear-gradient(145deg, #FFFFFF 55%, #FBF6FF 100%);
    border: 1px solid #E8D8F5;
    border-radius: 18px;
    padding: 22px 20px;
    box-shadow: 0 5px 18px rgba(79, 35, 105, 0.045);
    transition: transform 180ms ease, box-shadow 180ms ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 9px 24px rgba(79, 35, 105, 0.09);
}

[data-testid="stMetricLabel"] {
    color: #74617F;
    font-size: 0.88rem;
    font-weight: 600;
}

[data-testid="stMetricValue"] {
    color: #291437;
    font-size: 2rem;
    font-weight: 750;
}

[data-testid="stMetricDelta"] {
    color: #7D35B1;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 18px;
    border-color: #EAE1F1;
}

h2, h3 {
    letter-spacing: -0.45px;
}

div[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #8138B5, #C65AFF, #E5B442);
    border-radius: 20px;
}

div[data-testid="stAlert"] {
    border-radius: 12px;
}

.stDownloadButton button {
    border-radius: 10px;
    border-color: #D9C2EB;
}

    </style>
    """,
    unsafe_allow_html=True,
)




# --------------------------------------------------
# SUPABASE AUTHENTICATION
# Multi-user email/password login and registration.
# Existing SkillLens AI branding is preserved.
# --------------------------------------------------
def _render_login():
    """Render the branded SkillLens AI login and registration page."""
    logo_path = Path(__file__).parent / "assets" / "skilllens_logo.png"

    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 10% 8%, rgba(129,56,181,.12), transparent 34%),
                radial-gradient(circle at 92% 88%, rgba(229,181,66,.13), transparent 32%),
                #FBF8FF;
        }
        [data-testid="stMainBlockContainer"] {
            max-width: 100% !important;
            padding-top: 2rem !important;
            padding-bottom: 3rem !important;
        }
        .sl-login-brand-card {
            box-sizing: border-box;
            width: 100%;
            padding: 28px 28px 24px;
            border: 1px solid #E9DDF7;
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(255,255,255,.98), rgba(250,245,255,.98));
            box-shadow: 0 12px 32px rgba(73,35,99,.08);
            text-align: center;
            margin: 0 0 18px 0;
        }
        .sl-login-logo {
            display: block;
            width: 220px;
            height: auto;
            object-fit: contain;
            margin: 0 auto 24px;
        }
        .sl-login-eyebrow {
            color: #8138B5;
            font-size: .72rem;
            font-weight: 800;
            letter-spacing: 1.8px;
            margin-bottom: 7px;
        }
        .sl-login-brand {
            font-size: 2.15rem;
            line-height: 1.2;
            letter-spacing: -1.1px;
            font-weight: 850;
            color: #211128;
            margin: 0;
        }
        .sl-login-brand span {
            background: linear-gradient(90deg, #8138B5, #C65AFF, #E5B442);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .sl-login-tagline { color: #76677F; margin: 8px 0 0; font-size: .96rem; }
        [data-testid="stForm"] {
            box-sizing: border-box;
            width: 100%;
            padding: 24px 26px 22px;
            border: 1px solid #E9DDF7 !important;
            border-radius: 22px;
            background: rgba(255,255,255,.96);
            box-shadow: 0 12px 32px rgba(73,35,99,.07);
        }
        [data-testid="stForm"] h3 { color: #211128; }
        [data-testid="stForm"] button[kind="primaryFormSubmit"] {
            background: linear-gradient(100deg, #6F18B5, #922BE0) !important;
            border: 1px solid #8138B5 !important;
            border-radius: 11px !important;
            min-height: 44px;
            font-weight: 700;
        }
        [data-testid="stForm"] input {
            border-radius: 10px !important;
            border-color: #DCCBEA !important;
        }
        @media (max-width: 640px) {
            .sl-login-brand-card { padding: 24px 18px 20px; }
            [data-testid="stForm"] { padding: 22px 18px 20px; }
            .sl-login-brand { font-size: 1.85rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1, 1.15, 1])
    with center:
        if logo_path.exists():
            logo_base64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
            logo_markup = (
                f'<img class="sl-login-logo" src="data:image/png;base64,{logo_base64}" '
                'alt="SkillLens AI logo">'
            )
        else:
            logo_markup = (
                '<div style="font-size:2.7rem;margin:0 auto 12px;">'
                '<span style="display:inline-flex;width:68px;height:68px;'
                'align-items:center;justify-content:center;border-radius:20px;'
                'background:linear-gradient(135deg,#8138B5,#C65AFF,#E5B442);'
                'color:white;">⌕</span></div>'
            )

        st.markdown(
            f"""
            <div class="sl-login-brand-card">
              {logo_markup}
              <div class="sl-login-eyebrow">YOUR CAREER, IN FOCUS</div>
              <div class="sl-login-tagline">Discover opportunities. Showcase your potential.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        login_tab, register_tab = st.tabs(["Sign in", "Create account"])

        with login_tab:
            with st.form("skilllens_supabase_login_form", clear_on_submit=False):
                st.subheader("Welcome back")
                st.caption("Sign in to continue to your private workspace.")
                email_input = st.text_input("Email address", autocomplete="username")
                password_input = st.text_input(
                    "Password", type="password", autocomplete="current-password"
                )
                login_submitted = st.form_submit_button(
                    "Sign in", type="primary", use_container_width=True
                )

            if login_submitted:
                if not email_input.strip() or not password_input:
                    st.warning("Please enter your email address and password.")
                else:
                    try:
                        if login_user(email_input.strip(), password_input):
                            st.success("Signed in successfully.")
                            st.rerun()
                        st.error("Login could not be completed. Please try again.")
                    except Exception as exc:
                        st.error(f"Login failed: {exc}")

        with register_tab:
            with st.form("skilllens_supabase_register_form", clear_on_submit=False):
                st.subheader("Create your SkillLens AI account")
                st.caption("Your analyses and activity will be private to your account.")
                full_name = st.text_input("Full name")
                register_email = st.text_input("Email address", key="sl_register_email")
                register_password = st.text_input(
                    "Create password", type="password", key="sl_register_password"
                )
                confirm_password = st.text_input(
                    "Confirm password", type="password", key="sl_confirm_password"
                )
                register_submitted = st.form_submit_button(
                    "Create account", type="primary", use_container_width=True
                )

            if register_submitted:
                if not full_name.strip() or not register_email.strip():
                    st.warning("Please enter your name and email address.")
                elif len(register_password) < 8:
                    st.warning("Your password must contain at least 8 characters.")
                elif register_password != confirm_password:
                    st.error("The passwords do not match.")
                else:
                    try:
                        response = register_user(
                            register_email.strip(),
                            register_password,
                            full_name.strip(),
                        )
                        if response.session:
                            st.success("Your account has been created and you are signed in.")
                            st.rerun()
                        else:
                            st.success(
                                "Registration submitted. Please check your email and "
                                "confirm your address before signing in."
                            )
                    except Exception as exc:
                        st.error(f"Registration failed: {exc}")


def _get_display_name():
    """Get the signed-in user's name from their Supabase profile."""
    try:
        profile = get_user_profile()
        if profile:
            name = str(profile.get("full_name") or "").strip()
            if name:
                return name
    except Exception:
        pass

    user = get_current_user()
    if user:
        email = getattr(user, "email", None)
        if email:
            return str(email).split("@")[0]
    return "SkillLens AI User"


def _render_logout_button():
    """Render the existing compact account card in the sidebar."""
    display_name = _get_display_name()
    initials = "".join(part[0] for part in display_name.split()[:2]).upper() or "SL"

    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] div[data-testid="stSidebarContent"] {
            padding-bottom: 6.5rem;
        }
        .st-key-skilllens_account_footer {
            position: fixed;
            bottom: 1.1rem;
            width: 13.5rem;
            max-width: calc(100vw - 3rem);
            z-index: 999;
            background: linear-gradient(135deg, #fffdf8 0%, #f6f0ff 100%);
            border: 1px solid rgba(129, 56, 181, 0.22);
            border-radius: 14px;
            padding: 0.55rem 0.6rem;
            box-shadow: 0 5px 18px rgba(54, 35, 72, 0.08);
        }
        .sl-account-initials {
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            background: linear-gradient(135deg, #8138B5, #C65AFF);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: .78rem;
            margin: .25rem auto;
        }
        .sl-account-name {
            font-weight: 700;
            font-size: .83rem;
            line-height: 1.2;
            color: #282033;
            margin: .15rem 0;
            align-items: center;
            overflow-wrap: anywhere;
        }
        .st-key-skilllens_account_footer button {
            min-height: 2.2rem;
            padding: .2rem .45rem;
            border-radius: 9px;
            border: 1px solid rgba(129, 56, 181, .25);
            background: white;
            color: #8138B5;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        with st.container(key="skilllens_account_footer"):
            avatar_col, details_col, logout_col = st.columns([0.75, 2.6, 0.75], gap="small")
            with avatar_col:
                st.markdown(
                    f'<div class="sl-account-initials">{initials}</div>',
                    unsafe_allow_html=True,
                )
            with details_col:
                st.markdown(
                    f'<div class="sl-account-name">{display_name}</div>',
                    unsafe_allow_html=True,
                )
            with logout_col:
                if st.button("↪", help="Log out of SkillLens AI", key="skilllens_logout"):
                    logout_user()
                    st.rerun()


# --------------------------------------------------
# SESSION DATA
# Temporary storage; database comes later.
# --------------------------------------------------
if "analyses" not in st.session_state:
    st.session_state.analyses = []

if "activity_log" not in st.session_state:
    st.session_state.activity_log = []


# --------------------------------------------------
# RESUME TEXT EXTRACTION
# --------------------------------------------------
def extract_resume(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    extension = uploaded_file.name.lower().rsplit(".", 1)[-1]

    if extension == "pdf":
        with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
            return "\n".join(
                page.get_text("text") for page in pdf
            ).strip()

    if extension == "docx":
        document = Document(io.BytesIO(file_bytes))
        parts = [
            paragraph.text.strip()
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        for table in document.tables:
            for row in table.rows:
                cells = [
                    cell.text.strip()
                    for cell in row.cells
                    if cell.text.strip()
                ]
                if cells:
                    parts.append(" | ".join(cells))

        return "\n".join(parts).strip()

    raise ValueError("Only PDF and DOCX files are supported.")


# --------------------------------------------------
# BASELINE SKILL EXTRACTOR
# Expand this dictionary as the project grows.
# --------------------------------------------------
SKILLS = [
    "Python", "SQL", "Java", "JavaScript", "C++",
    "HTML", "CSS", "React", "Node.js", "Flask",
    "FastAPI", "Django", "REST API", "Git",
    "Docker", "Kubernetes", "AWS", "Azure",
    "Machine Learning", "Deep Learning", "NLP",
    "Natural Language Processing", "Computer Vision",
    "TensorFlow", "PyTorch", "Scikit-learn",
    "Pandas", "NumPy", "Matplotlib", "Power BI",
    "Tableau", "Excel", "Statistics", "Data Analysis",
    "Data Visualization", "Data Preprocessing",
    "Classification", "Regression", "Clustering",
    "SQL Server", "PostgreSQL", "MongoDB",
    "Spark", "Hadoop", "Linux", "PowerShell",
    "SCCM", "Intune", "CI/CD", "GitHub Actions",
]


def find_skills(text):
    """Find known skill names using case-insensitive boundaries."""
    found = set()
    normalized_text = text.lower()

    aliases = {
        "scikit-learn": "Scikit-learn",
        "sklearn": "Scikit-learn",
        "natural language processing": "Natural Language Processing",
        "nlp": "NLP",
    }

    for skill in SKILLS:
        pattern = r"(?<!\w)" + re.escape(skill.lower()) + r"(?!\w)"
        if re.search(pattern, normalized_text):
            found.add(skill)

    for alias, canonical in aliases.items():
        pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"
        if re.search(pattern, normalized_text):
            found.add(canonical)

    # Avoid double-counting the same NLP capability.
    if "NLP" in found and "Natural Language Processing" in found:
        found.discard("Natural Language Processing")

    return sorted(found, key=str.lower)


# --------------------------------------------------
# TRANSPARENT BASELINE MATCHING
# This is skill coverage, not a hiring probability.
# --------------------------------------------------
def calculate_match(job_text, resume_text):
    required_skills = find_skills(job_text)
    candidate_skills = find_skills(resume_text)

    matched = sorted(
        set(required_skills) & set(candidate_skills),
        key=str.lower,
    )
    missing = sorted(
        set(required_skills) - set(candidate_skills),
        key=str.lower,
    )

    if required_skills:
        score = round(100 * len(matched) / len(required_skills))
    else:
        score = 0

    return {
        "score": score,
        "required": required_skills,
        "candidate_skills": candidate_skills,
        "matched": matched,
        "missing": missing,
    }


# --------------------------------------------------
# SUPABASE AUTHENTICATION GATE + SIDEBAR NAVIGATION
# --------------------------------------------------
current_user = get_current_user()

if not current_user:
    _render_login()
    st.stop()

# The database trigger creates a profile for each registered user.
# Stop safely if profile creation has not completed yet.
try:
    current_profile = get_user_profile()
except Exception as exc:
    st.error(f"Unable to load your account profile: {exc}")
    st.stop()

if not current_profile:
    st.info(
        "Your account is signed in, but its profile is still being prepared. "
        "Please refresh this page in a moment. If the issue continues, contact the administrator."
    )
    st.stop()

st.session_state["skilllens_profile"] = current_profile

page = render_sidebar()
_render_logout_button()


if page == "Dashboard":
    render_dashboard(st.session_state["analyses"])

elif page == "New analysis":
    render_new_analysis()

elif page == "Job Search":
    render_job_search()

elif page == "History":
    render_history()

elif page == "Privacy":
    render_privacy()
    
elif page == "Career Guidance":
    previous_roadmap = st.session_state.get("career_guidance_result")
    render_career_guidance()
    current_roadmap = st.session_state.get("career_guidance_result")
    if current_roadmap and current_roadmap is not previous_roadmap:
        from activity_log import log_activity
        role_title = current_roadmap.get("role_title", "Career roadmap")
        log_activity(
            "Career Roadmap",
            f"Roadmap: {role_title}",
            "Generated a personalised career learning roadmap.",
            {
                "role_title": role_title,
                "estimated_plan": current_roadmap.get("estimated_plan", ""),
                "phase_count": len(current_roadmap.get("phases", [])),
                "roadmap": current_roadmap,
            },
        )


