"""SkillLens AI — Privacy & Data Protection page.

The content describes the current prototype implementation. Keep this page
in sync with actual data flows whenever the application changes.
"""
import streamlit as st


def _card(title: str, description: str, icon: str, tone: str, detail_title: str, detail: str):
    border = "#E7D2FF" if tone == "purple" else "#F5DFA0"
    background = "linear-gradient(145deg,#FBF7FF 0%,#F5EDFF 100%)" if tone == "purple" else "linear-gradient(145deg,#FFFCF4 0%,#FFF6E4 100%)"
    icon_bg = "linear-gradient(135deg,#7C22D5,#B34CE8)" if tone == "purple" else "linear-gradient(135deg,#FFF0C2,#FFE09A)"
    icon_color = "#FFFFFF" if tone == "purple" else "#6E3A00"
    st.markdown(
        f"""
        <div style="height:178px;padding:18px 17px;border:1px solid {border};
        border-radius:18px;background:{background};box-shadow:0 5px 16px rgba(73,35,105,.045);">
          <div style="display:flex;gap:13px;align-items:flex-start;">
            <div style="min-width:48px;width:48px;height:48px;border-radius:13px;
            background:{icon_bg};display:flex;align-items:center;justify-content:center;
            color:{icon_color};font-size:23px;box-shadow:0 4px 10px rgba(94,35,150,.13);">
              {icon}
            </div>
            <div>
              <div style="font-weight:800;color:#28104F;font-size:16px;line-height:1.3;margin:2px 0 8px;">
                {title}
              </div>
              <div style="font-size:13px;color:#604B70;line-height:1.48;">
                {description}
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander(f"Read details: {detail_title}"):
        st.write(detail)


def render_privacy():
    st.markdown(
        """
        <style>
        .stApp { background:#FFFFFF; }
        [data-testid="stMainBlockContainer"] { padding-top:1.5rem; max-width:1500px; }
        .privacy-hero {
          position:relative; overflow:hidden; padding:27px 30px; margin:0 0 16px;
          border:1px solid #E4CCFF; border-radius:22px;
          background:linear-gradient(112deg,#F6EAFE 0%,#FCF7FF 56%,#FFF3D7 100%);
          box-shadow:0 8px 24px rgba(89,42,132,.07);
        }
        .privacy-kicker { color:#7B35B1; font-size:11px; font-weight:850; letter-spacing:2px; }
        .privacy-title { color:#271044; font-size:29px; font-weight:850; margin:5px 0 4px; }
        .privacy-sub { color:#684D7D; font-size:15px; margin-bottom:8px; }
        .privacy-copy { color:#614B72; font-size:13px; line-height:1.55; max-width:850px; }
        .privacy-shield {
          float:left; margin:0 22px 8px 0; width:76px;height:76px;border-radius:22px;
          display:flex;align-items:center;justify-content:center;font-size:42px;
          background:linear-gradient(145deg,#7B24D1,#B54BE8 65%,#F2C45B);
          box-shadow:0 8px 18px rgba(103,37,165,.22);
        }
        .privacy-notice {
          padding:15px 19px; margin:0 0 17px; border-radius:17px;
          border:1px solid #F2D58A; background:linear-gradient(110deg,#FFF9E9,#FFFDF7);
          color:#60491D; font-size:13px; line-height:1.5;
        }
        .privacy-notice strong { color:#4D2D00; font-size:14px; }
        .privacy-contact {
          padding:18px 22px;border:1px solid #E4CCFF;border-radius:18px;
          background:linear-gradient(110deg,#FBF7FF,#F4EAFE);
          color:#30104F;display:flex;align-items:center;gap:15px;margin-top:16px;
        }
        div[data-testid="stExpander"] { border:1px solid #E5D6F3; border-radius:12px; background:rgba(255,255,255,.75); }
        div[data-testid="stExpander"] summary p { color:#54217F;font-weight:650;font-size:12px; }
        </style>
        <div class="privacy-hero">
          <div class="privacy-shield">🛡️</div>
          <div class="privacy-kicker">TRUST & DATA PROTECTION</div>
          <div class="privacy-title">Privacy &amp; Data Protection</div>
          <div class="privacy-sub">Your data. Your trust. Our responsibility.</div>
          <div class="privacy-copy">At SkillLens AI, we are committed to handling your information with transparency, security, and care.
          This page explains what data we process, how it is used, and what controls are currently available to you.</div>
          <div style="clear:both"></div>
        </div>
        <div class="privacy-notice">
          <strong>ⓘ &nbsp; Prototype transparency notice</strong><br>
          This page describes the current implementation reviewed for SkillLens AI. It is not a legal privacy notice
          or a guarantee of compliance with any particular privacy law. Review your hosting provider's policies and
          organisational requirements before processing real candidate personal data.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div style='font-size:21px;font-weight:850;color:#291044;margin:8px 0 13px;'>"
        "Privacy at a glance <span style='color:#B88A2C;'>✦</span></div>",
        unsafe_allow_html=True,
    )

    cards = [
        ("1. Our privacy approach", "Learn how SkillLens AI handles your data and our commitment to transparency, security, and responsible use.",
         "👤", "purple", "Our privacy approach",
         "SkillLens AI helps users review resume content against job requirements. The prototype uses information to perform the requested screening or job-search task. Match scores are indicators of detected skill coverage, not automated hiring decisions."),
        ("2. Information processed", "See what information we collect, including account details, resumes, extracted text, job descriptions and analysis results.",
         "▤", "gold", "Information processed",
         "Account and sign-in: the current single-user sign-in reads a configured username, password salt, and password hash from Streamlit secrets (or supported environment variables). The entered password is checked against the hash; the login code does not need to store the plain-text password. Authentication state is maintained in the Streamlit session.\n\nResume files and extracted text: the analysis page accepts PDF and DOCX resumes, with a 10 MB per-file limit in the current interface. PyMuPDF extracts PDF text and python-docx extracts DOCX text, including tables. Extracted resume text and screening results may be retained in the current session's analysis history. No persistent resume database is configured.\n\nJob descriptions and screening results: the supplied job title and description are used to detect supported skills and compare them with skills found in the resume. Session-held results can include filename, extracted text, detected skills, matched skills, missing skills, and match score.\n\nJob search: search keywords, location, selected country, and filters are sent to the Adzuna Jobs API. Returned listing details can include title, employer, location, description, salary fields, and listing URL. Saved jobs are currently held in session state."),
        ("3. How we use your data", "Understand how information is used for resume screening, skill matching, job search and application improvements.",
         "⚙", "purple", "How information is used",
         "Information is used to extract readable resume text, detect skills from the application's supported skill list, compare resume skills with a supplied job description, display screening results, and retrieve job listings from Adzuna. The current prototype does not automatically make hiring decisions, contact employers, or submit job applications."),
        ("4. Resume processing", "Understand what happens when you upload a resume, how text is extracted, and how skills are identified.",
         "▤", "gold", "Resume processing",
         "The browser uploads the selected PDF or DOCX to the server hosting this Streamlit application. The Python application reads the uploaded bytes and extracts text using PyMuPDF for PDFs and python-docx for DOCX files. The extracted text is then checked against the application's predefined skill list and compared with the supplied job description. The reviewed code does not explicitly write the original resume to an application-managed archive."),
        ("5. Third-party services", "Learn about external services such as Adzuna for job search and how data is shared with them.",
         "↗", "purple", "Third-party services",
         "Job-search requests go to Adzuna's API. Search keywords, location, country, filters, and API authentication parameters are included in the request. The reviewed resume-analysis code does not send resume files or extracted resume text to Adzuna. The implementation reviewed for this page does not show Gmail, calendar, or a generative-AI provider integration for resume analysis. Review Adzuna's privacy information for its handling of API requests and listing data."),
        ("6. Data storage and retention", "Find out where your data is stored, how long it is kept and when it may be deleted.",
         "▤", "gold", "Storage and retention",
         "Analysis history and saved jobs are held in Streamlit session state. This is temporary session storage, not a durable user database. Information may be lost when a session ends, the server restarts, or a new session is created. The prototype code reviewed for this page does not configure a persistent database for resumes, analysis history, or saved jobs. Hosting infrastructure may have its own temporary storage, logs, backups, or operational retention."),
        ("7. Security measures", "See the technical and organisational measures used to protect your information.",
         "🛡", "purple", "Security measures and limitations",
         "The configured password is verified using PBKDF2-HMAC-SHA256 rather than being stored as plain text in the login code. Adzuna API credentials are read from Streamlit secrets and should never be hard-coded or committed to a public repository. The current login is a simple single-user, session-based gate, not a full multi-user identity system. The application code alone cannot guarantee transport encryption, server hardening, secure backups, access logging, or deletion from hosting-provider infrastructure; these depend on deployment and hosting configuration."),
        ("8. Your rights and controls", "Learn how you can view, export or delete your data, and what your responsibilities are when using SkillLens AI.",
         "♙", "gold", "Your choices and data controls",
         "Only upload resumes you have permission to process. Review results because skill detection uses a predefined list and may miss skills or misunderstand context. A match score is not a probability of interview selection, job performance, or hiring success. The current prototype does not provide dedicated controls to export or permanently delete individual records from a persistent database. Ending a session or starting a new one may clear session-held records, but this is not a verified deletion process for server logs, backups, browser data, or hosting infrastructure. Logging out changes authenticated session state; it does not guarantee deletion of records."),
        ("9. Cookies and sessions", "Understand how session data works, what is stored in your browser, and what happens when you log out.",
         "◉", "purple", "Cookies and session behavior",
         "SkillLens AI runs as a Streamlit web application. Streamlit and the browser may use session-related mechanisms required to operate the app. Exact cookies, telemetry, and browser storage behavior depends on the Streamlit version and deployment configuration. This application page does not independently configure an advertising cookie or tracking system. The exact lifetime of session information also depends on hosting and session configuration."),
    ]

    for row in range(3):
        cols = st.columns(3, gap="medium")
        for col_index, col in enumerate(cols):
            with col:
                _card(*cards[row * 3 + col_index])

    st.markdown(
        """
        <div class="privacy-contact">
          <div style="font-size:29px;">✉️</div>
          <div style="flex:1;">
            <div style="font-size:16px;font-weight:850;color:#30104F;">10. Contact and privacy questions</div>
            <div style="font-size:13px;color:#654D79;margin-top:4px;">
              Have questions about your data or our privacy practices? Contact the SkillLens AI project owner.
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Additional information")
    st.write(
        "This page must be updated whenever SkillLens AI adds persistent profiles, resume storage, AI model providers, "
        "email or calendar access, application submission, analytics, or other external integrations. The explanation "
        "should always match the actual running code and deployment setup."
    )
    with st.expander("Technical summary — current prototype"):
        st.markdown(
            """
            | Area | Current implementation |
            |---|---|
            | Resume formats | PDF and DOCX |
            | Maximum upload size | 10 MB per file in the analysis interface |
            | PDF extraction | PyMuPDF |
            | DOCX extraction | python-docx |
            | Skill detection | Predefined application skill list |
            | Analysis history | Streamlit session state |
            | Saved jobs | Streamlit session state |
            | Persistent database | Not configured |
            | Job-search provider | Adzuna Jobs API |
            | Login | Single-user, PBKDF2 password-hash verification |
            """
        )
    st.caption(
        "Last reviewed: 31 October 2026 · Implementation description for the current SkillLens AI prototype; not legal advice."
    )
