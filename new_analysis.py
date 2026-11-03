"""New resume analysis page for SkillLens AI.

Provides transparent skill matching, learning roadmaps, resume-tailoring support,
and role-specific interview practice questions. Matching is a baseline keyword
comparison and must be reviewed by a human.
"""
import io
import html
import re
import textwrap
from datetime import datetime

import fitz
import streamlit as st
from docx import Document
from ai_engine import generate_ai_response
from activity_log import log_activity


# --------------------------------------------------
# RESUME TEXT EXTRACTION
# --------------------------------------------------
def extract_resume(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    extension = uploaded_file.name.lower().rsplit(".", 1)[-1]

    if extension == "pdf":
        with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
            return "\n".join(page.get_text("text") for page in pdf).strip()

    if extension == "docx":
        document = Document(io.BytesIO(file_bytes))
        parts = [
            paragraph.text.strip()
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]
        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
        return "\n".join(parts).strip()

    raise ValueError("Only PDF and DOCX files are supported.")


# --------------------------------------------------
# BASELINE SKILL EXTRACTOR
# Add skills here as the project grows.
# --------------------------------------------------
SKILLS = [
    "Python", "SQL", "Java", "JavaScript", "C++", "HTML", "CSS", "React",
    "Node.js", "Flask", "FastAPI", "Django", "REST API", "Git", "Docker",
    "Kubernetes", "AWS", "Azure", "Machine Learning", "Deep Learning", "NLP",
    "Natural Language Processing", "Computer Vision", "TensorFlow", "PyTorch",
    "Scikit-learn", "Pandas", "NumPy", "Matplotlib", "Power BI", "Tableau",
    "Excel", "Statistics", "Data Analysis", "Data Visualization",
    "Data Preprocessing", "Classification", "Regression", "Clustering",
    "SQL Server", "PostgreSQL", "MongoDB", "Spark", "Hadoop", "Linux",
    "PowerShell", "SCCM", "Intune", "CI/CD", "GitHub Actions",
]

ALIASES = {
    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "natural language processing": "Natural Language Processing",
    "nlp": "NLP",
}


def find_skills(text):
    """Find known skill names using case-insensitive word boundaries."""
    found = set()
    normalized_text = text.lower()

    for skill in SKILLS:
        pattern = r"(?<!\w)" + re.escape(skill.lower()) + r"(?!\w)"
        if re.search(pattern, normalized_text):
            found.add(skill)

    for alias, canonical in ALIASES.items():
        pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"
        if re.search(pattern, normalized_text):
            found.add(canonical)

    if "NLP" in found and "Natural Language Processing" in found:
        found.discard("Natural Language Processing")

    return sorted(found, key=str.lower)


def calculate_match(job_text, resume_text):
    required_skills = find_skills(job_text)
    candidate_skills = find_skills(resume_text)
    matched = sorted(set(required_skills) & set(candidate_skills), key=str.lower)
    missing = sorted(set(required_skills) - set(candidate_skills), key=str.lower)
    score = round(100 * len(matched) / len(required_skills)) if required_skills else 0

    return {
        "score": score,
        "required": required_skills,
        "candidate_skills": candidate_skills,
        "matched": matched,
        "missing": missing,
    }


def evidence_for_skill(text, skill, max_chars=220):
    """Return a short line/sentence from the supplied text that mentions a skill."""
    for line in re.split(r"[\n\r]+|(?<=[.!?])\s+", text):
        if re.search(r"(?<!\w)" + re.escape(skill) + r"(?!\w)", line, re.IGNORECASE):
            clean = " ".join(line.split())
            if clean:
                return clean[:max_chars] + ("…" if len(clean) > max_chars else "")
    return "Skill name detected, but no concise evidence sentence could be extracted."


# --------------------------------------------------
# LEARNING ROADMAPS
# These are starter suggestions, not a guarantee of proficiency.
# --------------------------------------------------
ROADMAPS = {
    "Python": [
        "Review variables, collections, conditions, loops, functions, and exceptions.",
        "Practise file handling, modules, virtual environments, and package management.",
        "Build a small project using clean functions, logging, and unit tests.",
    ],
    "SQL": [
        "Practise SELECT, filtering, sorting, and aggregations.",
        "Learn JOINs, subqueries, CTEs, and window functions.",
        "Build queries on a sample database and explain query performance basics.",
    ],
    "Machine Learning": [
        "Review supervised vs. unsupervised learning and train/validation/test splits.",
        "Practise preprocessing, feature engineering, and baseline models with Scikit-learn.",
        "Evaluate models with suitable metrics and document limitations in a small project.",
    ],
    "Deep Learning": [
        "Review tensors, gradient descent, loss functions, and backpropagation.",
        "Implement a small neural network using a framework such as PyTorch or TensorFlow.",
        "Compare training and validation performance; investigate overfitting and regularisation.",
    ],
    "PyTorch": [
        "Learn tensors, datasets, dataloaders, and automatic differentiation.",
        "Train a small model with an explicit training and validation loop.",
        "Practise saving/loading checkpoints and running inference reproducibly.",
    ],
    "TensorFlow": [
        "Learn tensors, Keras layers, model compilation, and training callbacks.",
        "Train a small classification model and evaluate it on held-out data.",
        "Practise exporting a model and running inference on new examples.",
    ],
    "NLP": [
        "Review tokenisation, text normalisation, vectorisation, and embeddings.",
        "Build a text-classification baseline and compare suitable evaluation metrics.",
        "Explore transformer concepts and document bias, data quality, and error cases.",
    ],
    "Natural Language Processing": [
        "Review tokenisation, text normalisation, vectorisation, and embeddings.",
        "Build a text-classification baseline and compare suitable evaluation metrics.",
        "Explore transformer concepts and document bias, data quality, and error cases.",
    ],
    "Computer Vision": [
        "Review image formats, resizing, normalisation, and train/validation splits.",
        "Build an image-classification or object-detection baseline.",
        "Evaluate with appropriate metrics and test on varied real-world examples.",
    ],
    "Docker": [
        "Learn images, containers, Dockerfiles, ports, and environment variables.",
        "Containerise a small application and run it locally.",
        "Practise logs, volumes, image versioning, and basic security hygiene.",
    ],
    "Kubernetes": [
        "Learn Pods, Deployments, Services, ConfigMaps, and Secrets.",
        "Deploy a small containerised application to a local test cluster.",
        "Practise health checks, scaling, rolling updates, and troubleshooting.",
    ],
    "AWS": [
        "Identify the AWS services relevant to the target role and learn IAM fundamentals.",
        "Complete a small guided deployment using least-privilege access.",
        "Practise monitoring, cost awareness, and secure configuration.",
    ],
    "Azure": [
        "Review identity/access management and the Azure services relevant to the role.",
        "Deploy a small test workload using a guided lab.",
        "Practise monitoring, cost controls, and secure configuration.",
    ],
    "Git": [
        "Practise commits, branches, merges, and resolving conflicts.",
        "Use pull requests and clear commit messages in a small project.",
        "Learn how to inspect history and recover from common mistakes.",
    ],
    "REST API": [
        "Review HTTP methods, status codes, headers, and JSON payloads.",
        "Call a public test API and build a small endpoint/client.",
        "Practise validation, authentication concepts, error handling, and API documentation.",
    ],
    "Pandas": [
        "Practise Series/DataFrames, filtering, missing values, and data types.",
        "Use groupby, merge, pivot, and date/time operations on a real dataset.",
        "Create a reproducible cleaning and analysis notebook or script.",
    ],
    "NumPy": [
        "Practise arrays, shapes, indexing, broadcasting, and vectorised operations.",
        "Implement common numerical operations without Python loops where appropriate.",
        "Use NumPy alongside Pandas or Scikit-learn in a small data project.",
    ],
    "Scikit-learn": [
        "Learn estimators, transformers, train/test splits, and Pipelines.",
        "Build a preprocessing-and-model Pipeline with cross-validation.",
        "Compare metrics and save a reproducible model workflow.",
    ],
    "Power BI": [
        "Practise importing data, cleaning it in Power Query, and building relationships.",
        "Create measures with DAX and design a clear report page.",
        "Validate totals and communicate the decisions the dashboard supports.",
    ],
    "PowerShell": [
        "Review objects, pipelines, functions, parameters, and error handling.",
        "Write a reusable script with logging, validation, and safe failure handling.",
        "Add tests and document execution context, permissions, and edge cases.",
    ],
    "SCCM": [
        "Review applications/packages, detection methods, deployment types, and collections.",
        "Practise deployment monitoring and interpreting client/server logs in a lab.",
        "Document install context, return codes, detection logic, and rollback considerations.",
    ],
    "Intune": [
        "Review Win32 app packaging, install/uninstall commands, and detection rules.",
        "Practise assignments, requirement rules, and device/user targeting in a test tenant.",
        "Learn troubleshooting through IME logs and document deployment outcomes.",
    ],
}


def roadmap_for(skill):
    return ROADMAPS.get(
        skill,
        [
            f"Learn the core concepts and terminology of {skill} from official documentation or a structured course.",
            f"Complete a beginner hands-on exercise using {skill}, then explain the steps and trade-offs.",
            f"Build a small portfolio project with {skill}; document your approach, results, and limitations.",
        ],
    )


QUESTION_BANK = {
    "Python": [
        "What is the difference between a list, tuple, set, and dictionary?",
        "How do exceptions work, and when would you use a context manager?",
        "How would you test and debug a Python function?",
    ],
    "SQL": [
        "Explain INNER JOIN vs LEFT JOIN with an example.",
        "What is the difference between WHERE and HAVING?",
        "How would you identify and improve a slow SQL query?",
    ],
    "Machine Learning": [
        "How do you detect and reduce overfitting?",
        "How would you choose an evaluation metric for an imbalanced dataset?",
        "Explain data leakage and how to prevent it.",
    ],
    "Deep Learning": [
        "What is backpropagation, and how does it update model weights?",
        "What are common causes of overfitting in neural networks?",
        "When might you use dropout or weight decay?",
    ],
    "PyTorch": [
        "What is the difference between model.train() and model.eval()?",
        "What do Dataset and DataLoader do?",
        "How would you save a model and run inference?",
    ],
    "TensorFlow": [
        "What are the main steps in compiling and training a Keras model?",
        "How can callbacks help during training?",
        "How would you evaluate a model on unseen data?",
    ],
    "NLP": [
        "What is tokenisation, and why does it matter?",
        "How would you represent text for a classification baseline?",
        "How would you evaluate a text classifier and inspect its errors?",
    ],
    "Natural Language Processing": [
        "What is tokenisation, and why does it matter?",
        "How would you represent text for a classification baseline?",
        "How would you evaluate a text classifier and inspect its errors?",
    ],
    "Computer Vision": [
        "What is the difference between image classification and object detection?",
        "Which metrics can be used to evaluate an object detector?",
        "How can you reduce overfitting when training on images?",
    ],
    "Docker": [
        "What is the difference between a Docker image and a container?",
        "What belongs in a Dockerfile, and what should not be baked into an image?",
        "How would you inspect logs and troubleshoot a container that exits?",
    ],
    "Git": [
        "What is the difference between merge and rebase?",
        "How would you resolve a merge conflict?",
        "How do branches and pull requests support collaboration?",
    ],
    "REST API": [
        "Explain common HTTP methods and status codes.",
        "How should an API validate input and handle errors?",
        "What are authentication and authorisation, and how do they differ?",
    ],
    "PowerShell": [
        "What is the difference between Write-Output and Write-Host?",
        "How do try/catch/finally and error action preferences work?",
        "How would you make a deployment script idempotent and add useful logging?",
    ],
    "SCCM": [
        "How do application detection methods affect deployment results?",
        "How would you troubleshoot an application that reports installed but is missing?",
        "What is the difference between user-context and system-context installation?",
    ],
    "Intune": [
        "How do Win32 app detection rules work in Intune?",
        "How would you troubleshoot an app deployment failure on a Windows device?",
        "What factors influence user vs. system installation context?",
    ],
    "Pandas": [
        "When would you use merge, concat, and join?",
        "How do you handle missing values and duplicate records?",
        "What is the difference between apply and vectorised operations?",
    ],
    "Scikit-learn": [
        "Why use a Pipeline for preprocessing and model training?",
        "How does cross-validation help model selection?",
        "How do you avoid fitting preprocessing steps on the test set?",
    ],
}


def questions_for(skill):
    return QUESTION_BANK.get(
        skill,
        [
            f"What are the core concepts and common use cases of {skill}?",
            f"Describe a practical project where you would use {skill}. What trade-offs would you consider?",
            f"How would you troubleshoot a common issue when working with {skill}?",
        ],
    )


def build_tailored_draft(role, resume_text, matched_skills):
    """Create a truthful starter draft using only detected skills already in the resume."""
    skill_line = ", ".join(matched_skills) if matched_skills else "Review the resume and add relevant skills you can substantiate"
    heading = f"TARGET ROLE: {role.strip() or 'Target role'}"
    summary = (
        "PROFILE SUMMARY (review and personalise before using):\n"
        f"Resume content indicates experience or exposure to: {skill_line}.\n"
        "Add only verified achievements, years of experience, and measurable outcomes "
        "that accurately reflect your background.\n"
    )
    return f"{heading}\n\n{summary}\n--- ORIGINAL RESUME CONTENT ---\n{resume_text.strip()}"

def build_ai_tailored_draft(role, job_description, resume_text):
    """Use the local AI model to tailor a resume without inventing facts."""

    prompt = f"""
You are the resume-tailoring assistant for SkillLens AI.

TASK:
Tailor the candidate's resume for the target role using the job description.

TARGET ROLE:
{role}

JOB DESCRIPTION:
{job_description}

CANDIDATE'S ORIGINAL RESUME:
{resume_text}

STRICT RULES:
1. Use only facts supported by the original resume.
2. Never invent skills, qualifications, employers, projects, dates,
   achievements, metrics, certifications, or years of experience.
3. Do not claim a required skill unless the resume supports that claim.
4. Reorganise existing information to highlight relevant experience.
5. Improve clarity, grammar, and professional wording.
6. Use relevant job-description terminology naturally when truthful.
7. If information is missing, do not fabricate it or fill the gap with guesses.
8. Preserve the candidate's actual employment and education history.
9. Return the tailored resume text only, without introductory commentary.
10. If the resume lacks evidence for a job requirement, do not claim that
    the candidate meets it.

Produce a professional, ATS-friendly resume draft with clear headings
and bullet points where appropriate.
"""

    return generate_ai_response(prompt)

# --------------------------------------------------
# PAGE
# --------------------------------------------------
def render_new_analysis():
    # Page-specific styling: retain the existing SkillLens AI purple-and-gold brand.
    st.markdown("""
        <style>
        .sl-analysis-hero {
            position: relative;
            overflow: hidden;
            padding: 30px 32px 28px;
            margin: 4px 0 22px;
            border-radius: 22px;
            border: 1px solid #E5D5FF;
            background: linear-gradient(120deg, #F5EEFF 0%, #FFFFFF 58%, #FFF7E4 100%);
            box-shadow: 0 12px 30px rgba(79, 35, 130, .08);
        }
        .sl-analysis-hero:after {
            content: "";
            position: absolute;
            width: 170px; height: 170px;
            right: -48px; top: -70px;
            border-radius: 50%;
            border: 22px solid rgba(124, 58, 237, .08);
            box-shadow: 0 0 0 16px rgba(234, 179, 8, .06);
        }
        .sl-analysis-eyebrow {
            display: inline-block;
            padding: 6px 11px;
            border-radius: 999px;
            color: #6D28D9;
            background: #EDE2FF;
            border: 1px solid #DCC8FF;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            margin-bottom: 12px;
        }
        .sl-analysis-title {
            color: #241334;
            font-size: clamp(27px, 3vw, 36px);
            line-height: 1.15;
            font-weight: 850;
            letter-spacing: -.8px;
            margin: 0 0 10px;
        }
        .sl-analysis-description {
            max-width: 690px;
            color: #665675;
            font-size: 15px;
            line-height: 1.65;
            margin: 0;
        }
        .sl-flow {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
            margin: 0 0 22px;
        }
        .sl-flow-step {
            display: flex;
            align-items: center;
            gap: 9px;
            padding: 10px 14px;
            border-radius: 13px;
            background: #FFFFFF;
            border: 1px solid #E9DFFF;
            color: #59456F;
            font-size: 12px;
            font-weight: 700;
        }
        .sl-flow-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 25px; height: 25px;
            border-radius: 8px;
            background: #6D28D9;
            color: #FFFFFF;
            font-size: 12px;
            font-weight: 800;
        }
        .sl-flow-step:last-child .sl-flow-number { background: #EAB308; color: #493400; }
        .sl-section-heading {
            color: #321B49;
            font-size: 19px;
            font-weight: 800;
            margin: 4px 0 4px;
        }
        .sl-section-subtitle {
            color: #806F8E;
            font-size: 13px;
            margin: 0 0 14px;
        }
        div[data-testid="stTextInput"] input {
            border-radius: 11px !important;
            border-color: #DCCBEE !important;
            background: #FCFAFF !important;
            min-height: 46px;
        }
        div[data-testid="stTextArea"] textarea {
            border-radius: 11px !important;
            border-color: #DCCBEE !important;
            background: #FCFAFF !important;
            line-height: 1.55;
        }
        div[data-testid="stFileUploader"] section {
            border: 1.5px dashed #B99AE8 !important;
            border-radius: 16px !important;
            background: linear-gradient(135deg, #FBF8FF, #FFFCF2) !important;
            padding: 16px !important;
        }
        div[data-testid="stFileUploader"] section:hover {
            border-color: #7C3AED !important;
            background: #F8F2FF !important;
        }
        div[data-testid="stButton"] > button[kind="primary"] {
            border: 0 !important;
            border-radius: 12px !important;
            min-height: 48px;
            padding: 0 22px;
            background: linear-gradient(100deg, #6D28D9, #8B5CF6) !important;
            color: white !important;
            font-weight: 800 !important;
            box-shadow: 0 7px 17px rgba(109, 40, 217, .22);
            transition: transform .15s ease, box-shadow .15s ease;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 10px 22px rgba(109, 40, 217, .28);
        }
        </style>
        
        <div class="sl-flow">
            <div class="sl-flow-step"><span class="sl-flow-number">1</span> Define the role</div>
            <div class="sl-flow-step"><span class="sl-flow-number">2</span> Add resumes</div>
            <div class="sl-flow-step"><span class="sl-flow-number">3</span> Analyse &amp; discover</div>
        </div>
        <div class="sl-section-heading">Set up your analysis</div>
        <p class="sl-section-subtitle">Add the job requirements and upload one or more resumes to begin.</p>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### ✦ Target role details")
        role = st.text_input(
            "Job title",
            placeholder="e.g. Machine Learning Engineer",
            help="Enter the role you want to screen candidates against.",
        )
        job_text = st.text_area(
            "Job description",
            placeholder="Paste the job description here — include responsibilities, required skills, preferred qualifications, and tools...",
            height=180,
            help="The analysis compares resume text against skills detected in this description.",
        )
        st.markdown("#### ✦ Candidate resumes")
        st.caption("Upload PDF or DOCX files. You can analyse multiple resumes in one run.")
        files = st.file_uploader(
            "Choose resume files",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            help="Maximum 10 MB per file. Text-based PDF and DOCX files are supported.",
        )

        if files:
            st.caption(f"{len(files)} file(s) selected")

        oversized = [f.name for f in files if f.size > 10 * 1024 * 1024] if files else []

        if oversized:
            st.error("Files over 10 MB: " + ", ".join(oversized))

        if st.button(
            "✦ Analyse resumes",
            type="primary",
            disabled=not bool(job_text.strip()) or not bool(files) or bool(oversized),
        ):
            required = find_skills(job_text)
            if not required:
                st.warning(
                    "No supported skills were detected in the job description. "
                    "Add explicit skills such as Python, SQL, or Machine Learning."
                )
            else:
                results = []
                with st.spinner("Extracting and analysing resumes..."):
                    for file in files:
                        try:
                            resume_text = extract_resume(file)
                            if not resume_text:
                                results.append({
                                    "filename": file.name,
                                    "score": 0,
                                    "required": required,
                                    "candidate_skills": [],
                                    "matched": [],
                                    "missing": required,
                                    "resume_text": "",
                                    "error": "No readable text found. This may be a scanned PDF.",
                                })
                                continue

                            match = calculate_match(job_text, resume_text)
                            results.append({
                                "filename": file.name,
                                **match,
                                "resume_text": resume_text,
                                "error": None,
                            })
                        except Exception as exc:
                            results.append({
                                "filename": file.name,
                                "score": 0,
                                "required": required,
                                "candidate_skills": [],
                                "matched": [],
                                "missing": required,
                                "resume_text": "",
                                "error": f"Unable to read this file ({type(exc).__name__}). Check that it is a valid PDF or DOCX.",
                            })

                valid_results = [r for r in results if r["error"] is None]
                if valid_results:
                    record = {
                        "role": role.strip() or "Untitled role",
                        "date": datetime.now().strftime("%d %b %Y, %I:%M %p"),
                        "job_description": job_text,
                        "results": results,
                    }
                    st.session_state.analyses.append(record)
                    average_score = round(
                        sum(item["score"] for item in valid_results)
                        / max(len(valid_results), 1)
                    )
                    log_activity(
                        "Resume Analysis",
                        f"Resume analysis: {record['role']}",
                        f"{len(valid_results)} resume(s) analysed · {average_score}% average skill match",
                        {
                            "role": record["role"],
                            "date": record["date"],
                            "job_description": record["job_description"],
                            "results": results,
                            "average_score": average_score,
                            "resume_count": len(valid_results),
                        },
                        activity_id=f"analysis:{record['date']}:{len(st.session_state.analyses)}",
                    )
                    st.session_state.latest_results = record
                    st.session_state.pop("tailored_resume_drafts", None)
                    st.success("Analysis completed.")
                else:
                    st.warning("No readable resumes were found. Check the uploaded documents.")

    record = st.session_state.get("latest_results")
    if not record:
        return

    st.divider()
    st.markdown("""
        <style>
        .sl-results-hero {
            position: relative;
            padding: 24px 26px;
            margin: 8px 0 18px 0;
            border-radius: 20px;
            background: linear-gradient(120deg, #F7F0FF 0%, #FFFFFF 58%, #FFF8E7 100%);
            border: 1px solid #E5D5FF;
            box-shadow: 0 8px 24px rgba(91, 33, 182, 0.07);
            overflow: hidden;
        }
        .sl-results-hero:after {
            content: "";
            position: absolute;
            right: -35px; top: -65px;
            width: 175px; height: 175px;
            border-radius: 50%;
            border: 22px solid rgba(124, 58, 237, 0.07);
        }
        .sl-results-eyebrow {
            color: #7C3AED; text-transform: uppercase;
            font-size: 11px; font-weight: 800; letter-spacing: 2px;
            margin-bottom: 7px;
        }
        .sl-results-heading {
            color: #24163B; font-size: 30px; line-height: 1.2;
            font-weight: 850; letter-spacing: -0.8px; margin: 0 0 9px 0;
        }
        .sl-results-description {
            color: #71657F; font-size: 13px; line-height: 1.65;
            max-width: 760px; margin: 0;
        }
        .sl-file-banner {
            display: flex; align-items: center; gap: 14px;
            padding: 16px 18px; margin: 8px 0 14px 0;
            border-radius: 16px; border: 1px solid #E4D8F7;
            background: linear-gradient(110deg, #FBF8FF, #F4EEFF);
        }
        .sl-file-icon {
            display: flex; align-items: center; justify-content: center;
            width: 48px; height: 48px; flex-shrink: 0;
            border-radius: 14px; color: #FFFFFF; font-size: 23px;
            background: linear-gradient(140deg, #8B5CF6, #5B21B6);
            box-shadow: 0 5px 13px rgba(109, 40, 217, 0.22);
        }
        .sl-file-label { color: #8B7A9D; font-size: 10px; font-weight: 800; letter-spacing: 1.4px; text-transform: uppercase; margin-bottom: 3px; }
        .sl-file-name { color: #2D2040; font-size: 19px; font-weight: 800; overflow-wrap: anywhere; }
        div[data-testid="stMetric"] {
            padding: 17px 18px 15px 18px;
            border-radius: 16px;
            border: 1px solid #E6DDF4;
            background: linear-gradient(145deg, #FFFFFF, #F8F4FF);
            box-shadow: 0 4px 14px rgba(52, 30, 83, 0.05);
            min-height: 108px;
        }
        div[data-testid="stMetric"] label { color: #6D5C80 !important; font-weight: 700 !important; }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #4C1D95 !important; font-weight: 850 !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stMetric"] {
            background: linear-gradient(145deg, #F5FFF9, #E7F8EF);
            border-color: #BFE8D0;
        }
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #087443 !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stMetric"] {
            background: linear-gradient(145deg, #FFFCF2, #FFF2D2);
            border-color: #F0DCA3;
        }
        div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #946200 !important; }
        </style>
        <section class="sl-results-hero">
            <div class="sl-results-eyebrow">SkillLens AI · Candidate insights</div>
            <div class="sl-results-heading">Screening results</div>
            <p class="sl-results-description">A transparent snapshot of how the resume aligns with the target role. Explore matched skills, evidence, development areas, and interview preparation below.</p>
        </section>
    """, unsafe_allow_html=True)

    for result_index, result in enumerate(record["results"]):
        with st.container(border=True):
            safe_filename = html.escape(str(result["filename"]))
            st.markdown(
                f"""
                <div class="sl-file-banner">
                    <div class="sl-file-icon">▤</div>
                    <div>
                        <div class="sl-file-label">Resume under review</div>
                        <div class="sl-file-name">{safe_filename}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if result["error"]:
                st.warning(result["error"])
                continue

            metric_col, matched_col, missing_col = st.columns([1, 1, 1])
            metric_col.metric("Skill coverage", f"{result['score']}%")
            matched_col.metric("Matched skills", len(result["matched"]))
            missing_col.metric("Skills to develop / verify", len(result["missing"]))

            
            # Style the screening navigation tabs
            st.markdown("""
                <style>
                div[data-baseweb="tab-list"] {
                    gap: 10px;
                    background-color: #F4F0FF;
                    padding: 8px;
                    border-radius: 12px;
                    border: 1px solid #E4D7FF;
                }

                div[data-baseweb="tab-list"] button[data-baseweb="tab"] {
                    height: 44px;
                    padding: 0 16px;
                    border-radius: 9px;
                    border: 1px solid transparent;
                    background-color: transparent;
                    font-weight: 600;
                    transition: all 0.2s ease;
                }

                div[data-baseweb="tab-list"] button[data-baseweb="tab"]
                p {
                    font-size: 14px;
                }

                div[data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] {
                    background-color: #6D28D9;
                    border-color: #6D28D9;
                }

                div[data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] p {
                    color: #FFFFFF;
                    font-weight: 700;
                }

                div[data-baseweb="tab-list"] button[data-baseweb="tab"]:hover {
                    border-color: #A78BFA;
                    color: #6D28D9;
                }

                div[data-baseweb="tab-highlight"] {
                    background-color: transparent;
                }
                </style>
            """, unsafe_allow_html=True)

            tab_match, tab_gap, tab_roadmap, tab_interview, tab_resume = st.tabs([
                "Skill matches",
                "Missing skills",
                "Learning roadmap",
                "Interview practice",
                "Tailor resume",
            ])

            
            with tab_match:
                st.markdown("### Skill Evidence Explorer")
                st.caption(
                    "Select a matched skill to compare the evidence from the "
                    "resume with the corresponding job requirement."
                )

                matched_skills = result["matched"]
                selected_key = f"selected_skill_{result_index}"

                if matched_skills:
                    # Keep the selected skill valid across Streamlit reruns.
                    if st.session_state.get(selected_key) not in matched_skills:
                        st.session_state[selected_key] = matched_skills[0]

                    # Display two large skill cards per row.
                    for start in range(0, len(matched_skills), 2):
                        skill_row = matched_skills[start:start + 2]
                        card_columns = st.columns(2)

                        for column, skill in zip(card_columns, skill_row):
                            with column:
                                is_selected = (
                                    st.session_state[selected_key] == skill
                                )

                                
                                card_class = "selected-skill-card" if is_selected else "skill-card"

                                st.markdown(
                                f"""
                                <style>
                                .skill-card {{
                                    background: #FFFFFF;
                                    border: 1px solid #E7E0F5;
                                    border-radius: 14px;
                                    padding: 18px;
                                    margin-bottom: 8px;
                                }}

                                .selected-skill-card {{
                                    background: #F3EDFF;
                                    border: 1.5px solid #8B5CF6;
                                    border-left: 4px solid #6D28D9;
                                    border-radius: 14px;
                                    padding: 18px;
                                    margin-bottom: 8px;
                                    box-shadow: 0 3px 12px rgba(109, 40, 217, 0.08);
                                }}
                                </style>
                                """,
                                unsafe_allow_html=True,
                                )

                                with st.container(border=True):
                                    st.markdown(f"**🟣 {skill}**")


                                    st.caption(
                                        "✓ Detected in resume and job description"
                                    )

                                    st.markdown(
                                        f"**{'SELECTED SKILL' if is_selected else 'SKILL MATCH'}**"
                                    )

                                    skill_button_key = (
                                        f"select_skill_{result_index}_"
                                        f"{re.sub(r'[^A-Za-z0-9_-]+', '_', skill)}"
                                    )

                                    if st.button(
                                        "✓ Viewing evidence"
                                        if is_selected
                                        else "View evidence →",
                                        key=skill_button_key,
                                        type=(
                                            "primary"
                                            if is_selected
                                            else "secondary"
                                        ),
                                        use_container_width=True,
                                    ):
                                        st.session_state[selected_key] = skill
                                        st.rerun()

                    # Show one clean, styled comparison for the selected skill.
                    selected_skill = st.session_state[selected_key]
                    resume_evidence = evidence_for_skill(
                        result["resume_text"], selected_skill
                    )
                    job_evidence = evidence_for_skill(
                        record["job_description"], selected_skill
                    )

                    safe_skill = html.escape(str(selected_skill or "Selected skill"))
                    safe_resume = html.escape(
                        str(resume_evidence or "No resume evidence found.")
                    )
                    safe_job = html.escape(
                        str(job_evidence or "No matching job requirement found.")
                    )

                    st.markdown(
                        """
                        <style>
                        .sl-evidence-title {
                            color: #29213F;
                            font-size: 25px;
                            font-weight: 800;
                            letter-spacing: -0.4px;
                            margin: 18px 0 5px 0;
                        }
                        .sl-evidence-subtitle {
                            color: #81768F;
                            font-size: 13px;
                            margin-bottom: 16px;
                        }
                        .sl-evidence-card {
                            border-radius: 16px;
                            padding: 22px;
                            min-height: 230px;
                            box-sizing: border-box;
                            overflow-wrap: anywhere;
                            white-space: normal;
                        }
                        .sl-resume-card {
                            background: linear-gradient(145deg, #FCFAFF, #F3ECFF);
                            border: 1px solid #DDCCFF;
                            border-top: 4px solid #7C3AED;
                        }
                        .sl-job-card {
                            background: linear-gradient(145deg, #FFFEFA, #FFF7E5);
                            border: 1px solid #F0DFB1;
                            border-top: 4px solid #D4A72C;
                        }
                        .sl-evidence-header {
                            display: flex;
                            align-items: center;
                            gap: 11px;
                            margin-bottom: 18px;
                        }
                        .sl-evidence-icon {
                            width: 38px;
                            height: 38px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            border-radius: 11px;
                            font-size: 21px;
                            font-weight: 800;
                            flex-shrink: 0;
                        }
                        .sl-resume-icon { background: #E8DAFF; color: #6D28D9; }
                        .sl-job-icon { background: #F9EBC4; color: #99710D; }
                        .sl-resume-label {
                            color: #6D28D9;
                            font-size: 12px;
                            font-weight: 850;
                            letter-spacing: 1px;
                        }
                        .sl-job-label {
                            color: #99710D;
                            font-size: 12px;
                            font-weight: 850;
                            letter-spacing: 1px;
                        }
                        .sl-evidence-source {
                            color: #8B8198;
                            font-size: 10px;
                            margin-top: 5px;
                            letter-spacing: 0.5px;
                        }
                        .sl-evidence-body {
                            color: #383247;
                            font-size: 14px;
                            line-height: 1.85;
                            overflow-wrap: anywhere;
                            white-space: pre-wrap;
                            word-break: normal;
                        }
                        .sl-evidence-badge {
                            display: inline-block;
                            margin-top: 18px;
                            padding: 7px 12px;
                            border-radius: 8px;
                            font-size: 11px;
                            font-weight: 800;
                        }
                        .sl-resume-badge { background: #E8DAFF; color: #6025B5; }
                        .sl-job-badge { background: #F9EBC4; color: #89650A; }
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        '<div class="sl-evidence-title">Skill Evidence Breakdown</div>'
                        '<div class="sl-evidence-subtitle">Compare the evidence found in the resume with the requirement for the target role. A keyword match does not prove proficiency.</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<span style="display:inline-block;background:#F0E7FF;color:#6D28D9;'
                        f'padding:7px 13px;border-radius:20px;font-size:11px;font-weight:800;">'
                        f'✓ KEYWORD MATCH</span>'
                        f'<span style="color:#81768F;font-size:12px;margin-left:10px;">'
                        f'Selected skill: <b>{safe_skill}</b> · 2 sources compared</span>',
                        unsafe_allow_html=True,
                    )
                    st.write("")

                    evidence_columns = st.columns(2, gap="large")
                    with evidence_columns[0]:
                        st.markdown(
                            f"""
                            <div class="sl-evidence-card sl-resume-card">
                                <div class="sl-evidence-header">
                                    <div class="sl-evidence-icon sl-resume-icon">▤</div>
                                    <div>
                                        <div class="sl-resume-label">RESUME EVIDENCE</div>
                                        <div class="sl-evidence-source">SOURCE 01 · CANDIDATE PROFILE</div>
                                    </div>
                                </div>
                                <div class="sl-evidence-body">{safe_resume}</div>
                                <span class="sl-evidence-badge sl-resume-badge">{safe_skill}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    with evidence_columns[1]:
                        st.markdown(
                            f"""
                            <div class="sl-evidence-card sl-job-card">
                                <div class="sl-evidence-header">
                                    <div class="sl-evidence-icon sl-job-icon">✦</div>
                                    <div>
                                        <div class="sl-job-label">JOB REQUIREMENT</div>
                                        <div class="sl-evidence-source">SOURCE 02 · TARGET ROLE</div>
                                    </div>
                                </div>
                                <div class="sl-evidence-body">{safe_job}</div>
                                <span class="sl-evidence-badge sl-job-badge">{safe_skill}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                # Keep additional resume skills visible below the explorer.
                st.markdown("---")
                st.markdown("### Additional skills in the resume")

                extra_skills = sorted(
                    set(result["candidate_skills"])
                    - set(result["required"]),
                    key=str.lower,
                )

                if extra_skills:
                    st.write("  ·  ".join(extra_skills))
                else:
                    st.caption(
                        "No additional supported skills were detected."
                    )

            
            with tab_gap:
                

                missing_skills = result.get("missing", [])
                matched_skills = result.get("matched", [])
                role_name = html.escape(str(record.get("role", "Target Role")))

                
                # Summary metrics
                metric_cols = st.columns(3)

                metric_data = [
                    (
                        "SKILLS TO REVIEW",
                        len(missing_skills),
                        "#6D28D9",
                        "#F1E8FF",
                        "Skills not detected",
                    ),
                    (
                        "SKILLS DETECTED",
                        len(matched_skills),
                        "#16805D",
                        "#E5F7EF",
                        "Skills found in resume",
                    ),
                    (
                        "TOTAL SKILLS CHECKED",
                        len(missing_skills) + len(matched_skills),
                        "#A87908",
                        "#FFF4D6",
                        "Matched + not detected",
                    ),
                ]

                for col, (label, value, accent, background, caption) in zip(
                    metric_cols, metric_data
                ):
                    with col:
                        st.markdown(
                            f"""
                            <div style="
                                background:{background};
                                border:1px solid {accent}33;
                                border-left:4px solid {accent};
                                border-radius:15px;
                                padding:18px;
                                min-height:125px;">
                                <div style="
                                    color:{accent};
                                    font-size:12px;
                                    font-weight:800;
                                    letter-spacing:1px;">
                                    {label}
                                </div>
                                <div style="
                                    color:#302044;
                                    font-size:32px;
                                    font-weight:850;
                                    margin:8px 0 3px;">
                                    {value}
                                </div>
                                <div style="
                                    color:#786C82;
                                    font-size:12px;">
                                    {caption}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                st.markdown("### 🧭 Skills to Review")
                st.caption(
                    "A missing keyword does not necessarily mean you lack the skill. "
                    "Check your actual experience before deciding what to learn."
                )

                if not missing_skills:
                    st.success(
                        "No missing skills were detected. Review the job requirements "
                        "and continue building practical evidence for your existing skills."
                    )
                else:
                    
                    # Single-column compact skill cards
                    for index, skill in enumerate(missing_skills):
                        skill = str(skill)

                        accent = (
                            "#7C3AED"
                            if index % 2 == 0
                            else "#C09218"
                        )
                        icon = "✦" if index % 2 == 0 else "◇"

                        with st.container(border=True):
                            icon_col, skill_col, status_col = st.columns(
                                [0.08, 0.62, 0.30],
                                vertical_alignment="center",
                                gap="small",
                            )

                            with icon_col:
                                st.markdown(
                                    f"<span style='color:{accent};"
                                    f"font-size:18px;'>{icon}</span>",
                                    unsafe_allow_html=True,
                                )

                            with skill_col:
                                st.markdown(
                                    f"<span style='color:#302044;"
                                    f"font-size:14px;font-weight:800;'>"
                                    f"{html.escape(skill)}</span>",
                                    unsafe_allow_html=True,
                                )

                            with status_col:
                                st.markdown(
                                    f"<span style='color:{accent};"
                                    f"font-size:12px;font-weight:800;"
                                    f"white-space:nowrap;'>"
                                    f"NOT DETECTED</span>",
                                    unsafe_allow_html=True,
                                )


                                





                                

                # Visual action workflow
                st.markdown("### ✨ Your Skill-Gap Action Plan")

                workflow_cols = st.columns(4, gap="small")
                workflow = [
                    ("01", "VERIFY", "Check existing experience", "#7C3AED", "#F1E8FF"),
                    ("02", "PRACTISE", "Work through exercises", "#9B70D6", "#F6F0FF"),
                    ("03", "BUILD", "Create a practical project", "#C09218", "#FFF4D6"),
                    ("04", "DOCUMENT", "Show genuine evidence", "#16805D", "#E5F7EF"),
                ]

                for col, (number, title, description, accent, background) in zip(
                    workflow_cols, workflow
                ):
                    with col:
                        st.markdown(
                            f"""
                            <div style="
                                text-align:center;
                                background:{background};
                                border:1px solid {accent}44;
                                border-radius:14px;
                                padding:15px 9px;
                                min-height:120px;">
                                <div style="
                                    width:34px;
                                    height:34px;
                                    border-radius:50%;
                                    background:{accent};
                                    color:white;
                                    display:flex;
                                    align-items:center;
                                    justify-content:center;
                                    margin:0 auto 10px;
                                    font-size:12px;
                                    font-weight:800;">
                                    {number}
                                </div>
                                <div style="
                                    color:{accent};
                                    font-size:12px;
                                    font-weight:850;
                                    letter-spacing:.6px;">
                                    {title}
                                </div>
                                <div style="
                                    color:#786C82;
                                    font-size:12px;
                                    line-height:1.5;
                                    margin-top:5px;">
                                    {description}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                


            with tab_roadmap:
                

                st.markdown(
                    """
                    <style>
                    .sl-roadmap-hero {
                        padding: 24px 26px;
                        margin: 8px 0 22px;
                        border-radius: 20px;
                        background: linear-gradient(120deg, #f4eaff 0%, #fff9e9 100%);
                        border: 1px solid #e4d2ff;
                        position: relative;
                        overflow: hidden;
                    }

                    .sl-roadmap-hero:after {
                        content: '✦';
                        position: absolute;
                        right: 25px;
                        top: 2px;
                        font-size: 78px;
                        color: rgba(113, 40, 190, .10);
                    }

                    .sl-roadmap-eyebrow {
                        font-size: 11px;
                        letter-spacing: 2px;
                        font-weight: 800;
                        color: #7936bd;
                        margin-bottom: 7px;
                    }

                    .sl-roadmap-title {
                        font-size: 24px;
                        font-weight: 800;
                        color: #29163d;
                        line-height: 1.25;
                        margin-bottom: 7px;
                    }

                    .sl-roadmap-subtitle {
                        font-size: 14px;
                        color: #65556f;
                        max-width: 680px;
                    }

                    .sl-roadmap-legend {
                        display: flex;
                        gap: 18px;
                        flex-wrap: wrap;
                        margin-top: 17px;
                        font-size: 12px;
                        font-weight: 700;
                        color: #51445c;
                    }

                    .sl-roadmap-legend span {
                        display: flex;
                        align-items: center;
                        gap: 6px;
                    }

                    .sl-dot {
                        width: 9px;
                        height: 9px;
                        border-radius: 50%;
                        display: inline-block;
                    }

                    .sl-purple {
                        background: #7c3aed;
                    }

                    .sl-gold {
                        background: #d6a11d;
                    }

                    .sl-dark {
                        background: #3c2851;
                    }

                    .sl-roadmap-flow {
                        display: flex;
                        align-items: stretch;
                        gap: 0;
                        margin: 16px 0 20px;
                    }

                    .sl-roadmap-node {
                        flex: 1;
                        min-width: 0;
                        position: relative;
                        padding: 17px 13px 15px;
                        border-radius: 15px;
                        border: 1px solid #e5d9f5;
                        background: linear-gradient(160deg, #fff 0%, #f8f2ff 100%);
                        box-shadow: 0 5px 16px rgba(65, 31, 95, .06);
                    }

                    .sl-roadmap-node:nth-of-type(2) {
                        background: linear-gradient(160deg, #fff 0%, #fff8e6 100%);
                        border-color: #f0dfad;
                    }

                    .sl-roadmap-node:nth-of-type(3) {
                        background: linear-gradient(160deg, #fff 0%, #f7f1ff 100%);
                    }

                    .sl-roadmap-node:nth-of-type(4) {
                        background: linear-gradient(160deg, #fff 0%, #fff8e6 100%);
                        border-color: #f0dfad;
                    }

                    .sl-roadmap-step {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        margin-bottom: 10px;
                    }

                    .sl-roadmap-number {
                        width: 30px;
                        height: 30px;
                        border-radius: 10px;
                        background: #7436bc;
                        color: #fff;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: 800;
                        font-size: 13px;
                        flex-shrink: 0;
                    }

                    .sl-roadmap-node h4 {
                        font-size: 13px;
                        margin: 0;
                        color: #342143;
                    }

                    .sl-roadmap-node p {
                        font-size: 12px;
                        line-height: 1.5;
                        color: #6c5e75;
                        margin: 0;
                    }

                    .sl-roadmap-connector {
                        width: 18px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: #a58bc3;
                        font-size: 20px;
                        font-weight: 800;
                        flex-shrink: 0;
                    }

                    .sl-roadmap-detail {
                        border: 1px solid #eadff7;
                        border-radius: 14px;
                        padding: 15px 17px;
                        background: #fff;
                        margin: 12px 0;
                    }

                    .sl-roadmap-detail-head {
                        font-size: 12px;
                        font-weight: 800;
                        letter-spacing: 1px;
                        text-transform: uppercase;
                        color: #7b3bb9;
                        margin-bottom: 10px;
                    }

                    .sl-roadmap-task {
                        display: flex;
                        gap: 12px;
                        align-items: flex-start;
                        padding: 11px 0;
                        border-bottom: 1px solid #f0eaf6;
                    }

                    .sl-roadmap-task:last-child {
                        border-bottom: 0;
                        padding-bottom: 0;
                    }

                    .sl-roadmap-tasknum {
                        width: 28px;
                        height: 28px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 9px;
                        background: #efe3ff;
                        color: #6d28b8;
                        font-weight: 800;
                        flex-shrink: 0;
                    }

                    .sl-roadmap-tasktext {
                        font-size: 13px;
                        line-height: 1.55;
                        color: #392d43;
                        padding-top: 3px;
                    }

                    /* Four-stage roadmap cards */

                    .sl-map-heading {
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        gap: 16px;
                        margin: 8px 0 18px;
                        padding: 20px 22px;
                        border: 1px solid #e7d8fb;
                        border-radius: 18px;
                        background: linear-gradient(
                            115deg,
                            #f7efff 0%,
                            #fffaf0 100%
                        );
                    }

                    .sl-map-kicker {
                        font-size: 10px;
                        letter-spacing: 2px;
                        font-weight: 900;
                        color: #7c3aed;
                        margin-bottom: 6px;
                    }

                    .sl-map-heading h3 {
                        margin: 0 0 6px;
                        color: #2e1b40;
                        font-size: 22px;
                        font-weight: 850;
                    }

                    .sl-map-heading p {
                        margin: 0;
                        color: #71627c;
                        font-size: 13px;
                        line-height: 1.5;
                    }

                    .sl-map-badge {
                        white-space: nowrap;
                        padding: 8px 12px;
                        border-radius: 999px;
                        background: #6d28d9;
                        color: white;
                        font-size: 10px;
                        font-weight: 900;
                        letter-spacing: 1px;
                    }

                    .sl-map-track {
                        display: flex;
                        align-items: stretch;
                        gap: 8px;
                        margin: 16px 0 18px;
                    }

                    .sl-map-stage {
                        flex: 1;
                        min-width: 0;
                        padding: 17px 14px 14px;
                        border-radius: 17px;
                        border: 1px solid #e5d7f7;
                        background: linear-gradient(
                            160deg,
                            #fff 0%,
                            #f7efff 100%
                        );
                        box-shadow: 0 7px 20px rgba(63, 35, 88, .07);
                        position: relative;
                        overflow: hidden;
                    }

                    .sl-map-stage:before {
                        content: '';
                        position: absolute;
                        left: 0;
                        top: 0;
                        width: 100%;
                        height: 4px;
                        background: #7c3aed;
                    }

                    .sl-map-practice {
                        background: linear-gradient(
                            160deg,
                            #fff 0%,
                            #fff8e6 100%
                        );
                        border-color: #f0dfad;
                    }

                    .sl-map-practice:before,
                    .sl-map-prove:before {
                        background: #d6a11d;
                    }

                    .sl-map-build {
                        background: linear-gradient(
                            160deg,
                            #fff 0%,
                            #f4f0ff 100%
                        );
                    }

                    .sl-map-prove {
                        background: linear-gradient(
                            160deg,
                            #fff 0%,
                            #fff8e6 100%
                        );
                        border-color: #f0dfad;
                    }

                    .sl-map-icon {
                        width: 42px;
                        height: 42px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 13px;
                        background: #eee2ff;
                        font-size: 22px;
                        margin-bottom: 13px;
                    }

                    .sl-map-practice .sl-map-icon,
                    .sl-map-prove .sl-map-icon {
                        background: #ffefc2;
                    }

                    .sl-map-step {
                        font-size: 9px;
                        letter-spacing: 1.5px;
                        font-weight: 900;
                        color: #8762a6;
                        margin-bottom: 5px;
                    }

                    .sl-map-stage h4 {
                        font-size: 17px;
                        font-weight: 850;
                        color: #322044;
                        margin: 0 0 8px;
                    }

                    .sl-map-stage p {
                        font-size: 12px;
                        line-height: 1.55;
                        color: #6e6178;
                        min-height: 56px;
                        margin: 0 0 14px;
                    }

                    .sl-map-outcome {
                        display: inline-block;
                        border-radius: 7px;
                        padding: 6px 8px;
                        background: #eee2ff;
                        color: #6d28d9;
                        font-size: 9px;
                        font-weight: 900;
                        letter-spacing: .5px;
                    }

                    .sl-map-practice .sl-map-outcome,
                    .sl-map-prove .sl-map-outcome {
                        background: #ffefc2;
                        color: #8b6500;
                    }

                    .sl-map-arrow {
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: #a78acb;
                        font-size: 22px;
                        font-weight: 900;
                        flex: 0 0 18px;
                    }

                    .sl-map-footer {
                        display: flex;
                        align-items: flex-start;
                        gap: 10px;
                        padding: 13px 16px;
                        margin: 8px 0 20px;
                        border: 1px dashed #d8c4f0;
                        border-radius: 13px;
                        background: #fcf9ff;
                        color: #5f506c;
                        font-size: 12px;
                        line-height: 1.55;
                    }

                    .sl-map-footer-icon {
                        color: #d6a11d;
                        font-size: 18px;
                        line-height: 1;
                    }

                    @media (max-width: 850px) {
                        .sl-map-track {
                            display: grid;
                            grid-template-columns: 1fr 1fr;
                            gap: 12px;
                        }

                        .sl-map-arrow {
                            display: none;
                        }

                        .sl-map-stage p {
                            min-height: 0;
                        }
                    }

                    @media (max-width: 520px) {
                        .sl-map-track {
                            grid-template-columns: 1fr;
                        }

                        .sl-map-heading {
                            align-items: flex-start;
                            flex-direction: column;
                        }

                        .sl-map-heading h3 {
                            font-size: 19px;
                        }
                    }

                    @media (max-width: 700px) {
                        .sl-roadmap-flow {
                            flex-direction: column;
                            gap: 7px;
                        }

                        .sl-roadmap-connector {
                            height: 12px;
                            width: 100%;
                            transform: rotate(90deg);
                        }

                        .sl-roadmap-title {
                            font-size: 20px;
                        }
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )

                # --------------------------------------------------
                # FOUR BEAUTIFUL ROADMAP CARDS
                # Always visible before the personalised explore area.
                # --------------------------------------------------

                st.markdown(
                    """
                    <div class="sl-map-heading">
                      <div>
                        <div class="sl-map-kicker">YOUR LEARNING JOURNEY</div>
                        <h3>From skill gap to job-ready proof</h3>
                        <p>
                            Follow the path from understanding a concept
                            to demonstrating it with a practical project.
                        </p>
                      </div>
                      <div class="sl-map-badge">4 STAGES</div>
                    </div>

                    <div class="sl-map-track">

                      <div class="sl-map-stage sl-map-learn">
                        <div class="sl-map-icon">📚</div>
                        <div class="sl-map-step">STAGE 01</div>
                        <h4>Learn</h4>
                        <p>
                            Understand core concepts, terminology,
                            and when the skill is used.
                        </p>
                        <div class="sl-map-outcome">FOUNDATION</div>
                      </div>

                      <div class="sl-map-arrow">➜</div>

                      <div class="sl-map-stage sl-map-practice">
                        <div class="sl-map-icon">🧩</div>
                        <div class="sl-map-step">STAGE 02</div>
                        <h4>Practise</h4>
                        <p>
                            Work through guided exercises and
                            small real-world examples.
                        </p>
                        <div class="sl-map-outcome">HANDS-ON SKILL</div>
                      </div>

                      <div class="sl-map-arrow">➜</div>

                      <div class="sl-map-stage sl-map-build">
                        <div class="sl-map-icon">🛠️</div>
                        <div class="sl-map-step">STAGE 03</div>
                        <h4>Build</h4>
                        <p>
                            Create a mini-project that applies
                            the skill to a realistic problem.
                        </p>
                        <div class="sl-map-outcome">PROJECT EVIDENCE</div>
                      </div>

                      <div class="sl-map-arrow">➜</div>

                      <div class="sl-map-stage sl-map-prove">
                        <div class="sl-map-icon">🚀</div>
                        <div class="sl-map-step">STAGE 04</div>
                        <h4>Demonstrate</h4>
                        <p>
                            Test the result, document it, and
                            explain your decisions clearly.
                        </p>
                        <div class="sl-map-outcome">PORTFOLIO READY</div>
                      </div>

                    </div>

                    <div class="sl-map-footer">
                      <span class="sl-map-footer-icon">✦</span>
                      <span>
                        <strong>Your goal:</strong>
                        turn each missing keyword into genuine,
                        demonstrable experience — not just a line on a resume.
                      </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # --------------------------------------------------
                # EXPLORE THE ROADMAP — redesigned skill cards
                # The four-stage roadmap above remains unchanged.
                # --------------------------------------------------
                st.markdown(
                    """
                    <style>
                    .sl-explore-heading{margin:24px 0 6px;color:#30203f;font-size:23px;font-weight:850;}
                    .sl-explore-subtitle{color:#766982;font-size:13px;line-height:1.6;margin:0 0 18px;}
                    .sl-skill-card{min-height:155px;padding:18px;margin:0 0 8px;border:1px solid #e5d8f5;border-radius:17px;background:linear-gradient(145deg,#fff 0%,#faf6ff 100%);box-shadow:0 5px 18px rgba(65,35,90,.055);}
                    .sl-skill-card-top{display:flex;align-items:center;gap:11px;margin-bottom:12px;}
                    .sl-skill-card-icon{display:flex;align-items:center;justify-content:center;width:42px;height:42px;flex:0 0 42px;border-radius:13px;background:#eee3ff;color:#6d28d9;font-size:21px;}
                    .sl-skill-card-kicker{color:#8a6aa8;font-size:9px;font-weight:900;letter-spacing:1.5px;margin-bottom:3px;text-transform:uppercase;}
                    .sl-skill-card-title{color:#332143;font-size:17px;line-height:1.25;font-weight:850;overflow-wrap:anywhere;}
                    .sl-skill-card-description{color:#71647b;font-size:12px;line-height:1.55;min-height:38px;margin-bottom:14px;}
                    .sl-skill-card-meta{display:inline-block;padding:6px 9px;border-radius:8px;background:#fff2c9;color:#886300;font-size:10px;font-weight:800;letter-spacing:.2px;}
                    div[data-testid="stExpander"]{border:1px solid #e4d8f2!important;border-radius:13px!important;background:#fff!important;overflow:hidden;margin:0 0 18px;}
                    div[data-testid="stExpander"] summary{background:#fcf9ff;color:#5d3480;font-weight:750;font-size:12px;padding:12px 14px;}
                    div[data-testid="stExpander"] summary:hover{color:#6d28d9;background:#f7f0ff;}
                    .sl-roadmap-detail{border:0;border-radius:0;padding:12px 14px 8px;background:#fff;margin:0;}
                    .sl-roadmap-detail-head{font-size:10px;font-weight:900;letter-spacing:1.2px;text-transform:uppercase;color:#7b3bb9;margin-bottom:10px;}
                    .sl-roadmap-task{display:flex;gap:11px;align-items:flex-start;padding:11px 0;border-bottom:1px solid #f0eaf6;}
                    .sl-roadmap-task:last-child{border-bottom:0;}
                    .sl-roadmap-tasknum{width:27px;height:27px;display:flex;align-items:center;justify-content:center;border-radius:9px;background:#eee3ff;color:#6d28b8;font-size:11px;font-weight:900;flex-shrink:0;}
                    .sl-roadmap-tasktext{font-size:12px;line-height:1.6;color:#493b54;padding-top:3px;}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown(
                    '<div class="sl-explore-heading">✦ Explore Your Personalised Roadmap</div>'
                    '<div class="sl-explore-subtitle">Choose a skill to reveal a focused learning path. Each path moves from understanding the concept to practising it and building practical evidence.</div>',
                    unsafe_allow_html=True,
                )

                if not result["missing"]:
                    st.success(
                        "No missing skills were detected. Use the roadmap "
                        "to deepen existing skills and build stronger "
                        "portfolio evidence."
                    )
                else:
                    missing_skills = result["missing"]
                    for row_start in range(0, len(missing_skills), 2):
                        card_columns = st.columns(2, gap="medium")
                        for offset, column in enumerate(card_columns):
                            skill_index = row_start + offset
                            if skill_index >= len(missing_skills):
                                continue
                            skill = missing_skills[skill_index]
                            steps = roadmap_for(skill) or []
                            safe_skill = html.escape(str(skill))
                            icon = "✧" if offset == 0 else "✦"
                            with column:
                                st.markdown(
                                    f'''<div class="sl-skill-card">
                                        <div class="sl-skill-card-top">
                                            <div class="sl-skill-card-icon">{icon}</div>
                                            <div><div class="sl-skill-card-kicker">Skill to strengthen</div>
                                            <div class="sl-skill-card-title">{safe_skill}</div></div>
                                        </div>
                                        <div class="sl-skill-card-description">Build confidence in {safe_skill} through guided learning and practical application.</div>
                                        <span class="sl-skill-card-meta">{len(steps)} LEARNING STEPS &nbsp; · &nbsp; PERSONAL LEARNING PATH</span>
                                    </div>''',
                                    unsafe_allow_html=True,
                                )
                                with st.expander("Explore Learning Path  →", expanded=False):
                                    task_html = (
                                        '<div class="sl-roadmap-detail">'
                                        '<div class="sl-roadmap-detail-head">YOUR ACTION PLAN · '
                                        + safe_skill + '</div>'
                                    )
                                    for step_no, step in enumerate(steps, start=1):
                                        task_html += (
                                            '<div class="sl-roadmap-task"><div class="sl-roadmap-tasknum">'
                                            + str(step_no) + '</div><div class="sl-roadmap-tasktext">'
                                            + html.escape(str(step)) + '</div></div>'
                                        )
                                    task_html += '</div>'
                                    st.markdown(task_html, unsafe_allow_html=True)
                                    st.caption(
                                        "Suggested starting point: adapt these activities to your current level "
                                        "and keep evidence of what you can genuinely demonstrate."
                                    )

            with tab_interview:
                st.markdown("#### Interview questions based on the target role")
                focus_skills = result["required"][:]
                if not focus_skills:
                    st.info("No skills were detected to generate questions.")
                else:
                    for skill in focus_skills:
                        with st.expander(f"💬 {skill}", expanded=(len(focus_skills) == 1)):
                            for number, question in enumerate(questions_for(skill), start=1):
                                st.markdown(f"{number}. {question}")
                st.caption("These are practice prompts generated from a built-in question bank, not a prediction of the employer's actual interview.")

            with tab_resume:
                st.markdown("#### Create a role-focused resume draft")
                st.write(
                    "This creates an editable text draft using the uploaded resume text and skills detected in it. "
                    "It does not invent experience or automatically rewrite a PDF/DOCX layout."
                )
                draft_key = f"tailored_resume_{record['date']}_{result_index}"
                if st.button(
                    "✨ Generate AI-Tailored Resume",
                    key=f"prepare_ai_draft_{result_index}",
                    type="primary",
                ):
                    try:
                        with st.spinner("AI is tailoring your resume locally..."):
                            st.session_state[draft_key] = build_ai_tailored_draft(
                                record["role"],
                                record["job_description"],
                                result["resume_text"],
                            )
                        
                        log_activity(
                            "Tailored Resume",
                            f"Tailored resume: {result['filename']}",
                            f"Draft prepared for {record['role']}.",
                            {
                                "role": record["role"],
                                "filename": result["filename"],
                                "draft": st.session_state[draft_key],
                            },
                            activity_id=f"tailored-resume:{record['date']}:{result['filename']}",
                        )
                        st.success("AI-tailored resume generated successfully!")

                    except Exception as exc:
                        st.error(
                            "Could not generate the AI-tailored resume. "
                            "Check that Ollama is running and the model is available."
                        )
                        st.caption(f"Technical details: {exc}")
                if draft_key in st.session_state:
                    edited_draft = st.text_area(
                        "Edit the draft before downloading",
                        value=st.session_state[draft_key],
                        height=360,
                        key=f"edit_draft_{result_index}",
                    )
                    st.download_button(
                        "Download tailored resume draft (.txt)",
                        data=edited_draft,
                        file_name=f"tailored_resume_{re.sub(r'[^A-Za-z0-9_-]+', '_', record['role']).strip('_') or 'role'}.txt",
                        mime="text/plain",
                        key=f"download_draft_{result_index}",
                    )
                    st.info(
                        "Before using the draft, replace the review note with a truthful professional summary, "
                        "verify every claim, and add only genuine achievements and measurable results."
                    )

   
