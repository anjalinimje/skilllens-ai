"""
SkillLens AI — Job Search
Uses the Adzuna Jobs API. API credentials belong in .streamlit/secrets.toml.
Official docs: https://developer.adzuna.com/docs/search
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import requests
import streamlit as st
from activity_log import log_activity


ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs"


def _adzuna_credentials() -> tuple[str, str]:
    """Read credentials from Streamlit secrets; never hard-code keys."""
    try:
        app_id = str(st.secrets["adzuna"]["app_id"]).strip()
        app_key = str(st.secrets["adzuna"]["app_key"]).strip()
    except Exception:
        app_id = ""
        app_key = ""

    return app_id, app_key


def search_adzuna_jobs(
    keywords: str,
    location: str = "",
    country: str = "in",
    page: int = 1,
    results_per_page: int = 10,
    sort_by: str = "date",
    max_days_old: int | None = None,
    full_time: bool = False,
    permanent: bool = False,
) -> list[dict[str, Any]]:
    """Search current Adzuna listings and return normalized job records."""
    app_id, app_key = _adzuna_credentials()
    if not app_id or not app_key:
        raise RuntimeError(
            "Adzuna credentials are missing. Add app_id and app_key to "
            ".streamlit/secrets.toml under [adzuna]."
        )

    params: dict[str, Any] = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": min(max(int(results_per_page), 1), 20),
        "what": keywords.strip(),
        "content-type": "application/json",
        "sort_by": sort_by if sort_by in {"date", "salary", "relevance"} else "date",
    }
    if location.strip():
        params["where"] = location.strip()
    if max_days_old is not None:
        params["max_days_old"] = max(1, min(int(max_days_old), 30))
    if full_time:
        params["full_time"] = 1
    if permanent:
        params["permanent"] = 1

    url = f"{ADZUNA_BASE_URL}/{country}/search/{max(1, int(page))}"
    response = requests.get(url, params=params, timeout=20)
    if response.status_code == 401:
        raise RuntimeError("Adzuna rejected the API credentials. Check app_id and app_key.")
    if response.status_code == 429:
        raise RuntimeError("Adzuna rate limit reached. Please wait before searching again.")
    response.raise_for_status()

    payload = response.json()
    results = payload.get("results", [])
    jobs: list[dict[str, Any]] = []

    for item in results:
        company = item.get("company") or {}
        place = item.get("location") or {}
        category = item.get("category") or {}
        jobs.append(
            {
                "id": str(item.get("id", "")),
                "title": item.get("title") or "Untitled role",
                "company": company.get("display_name") or "Company not listed",
                "location": place.get("display_name") or "Location not listed",
                "description": item.get("description") or "",
                "url": item.get("redirect_url") or "",
                "created": item.get("created") or "",
                "salary_min": item.get("salary_min"),
                "salary_max": item.get("salary_max"),
                "salary_predicted": bool(item.get("salary_is_predicted", 0)),
                "contract_type": item.get("contract_type") or "",
                "contract_time": item.get("contract_time") or "",
                "category": category.get("label") or "",
            }
        )

    return jobs


def _format_salary(job: dict[str, Any]) -> str:
    low, high = job.get("salary_min"), job.get("salary_max")
    if low is None and high is None:
        return "Salary not listed"
    if low is not None and high is not None:
        return f"₹{low:,.0f} – ₹{high:,.0f} per year"
    if low is not None:
        return f"From ₹{low:,.0f} per year"
    return f"Up to ₹{high:,.0f} per year"


def render_job_search() -> None:
    """Render the SkillLens AI job search page."""
    # SkillLens AI styling: override Streamlit's red primary theme accent.
    st.markdown(
        """
        <style>
        div[data-testid="stForm"] {
            background: linear-gradient(145deg, #FBF8FE 0%, #FFFFFF 72%, #FFFCF4 100%);
            border: 1px solid #E8DDF0;
            border-radius: 20px;
            padding: 20px 18px 16px;
            box-shadow: 0 7px 22px rgba(65, 35, 85, .055);
        }
        div[data-testid="stTextInput"] input {
            border: 1px solid #DED1E9 !important;
            border-radius: 10px !important;
            background: #FFFFFF !important;
            color: #291437 !important;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #A875C8 !important;
            box-shadow: 0 0 0 2px rgba(129, 56, 181, .12) !important;
        }
        div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
            border: 1px solid #DED1E9 !important;
            border-radius: 10px !important;
            background: #FFFFFF !important;
        }
        div[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within {
            border-color: #A875C8 !important;
            box-shadow: 0 0 0 2px rgba(129, 56, 181, .12) !important;
        }
        div[data-testid="stCheckbox"] label span[data-testid="stCheckboxIcon"] {
            border-color: #B99ACD !important;
        }
        div[data-testid="stCheckbox"] [data-checked="true"] {
            background-color: #8138B5 !important;
            border-color: #8138B5 !important;
        }

        /* Target every common Streamlit DOM hook for this form's submit button. */
        div[data-testid="stFormSubmitButton"] button,
        div[data-testid="stForm"] button[data-testid="stBaseButton-primary"],
        div[data-testid="stForm"] button[kind="primary"] {
            background: linear-gradient(100deg, #8138B5 0%, #A653CF 100%) !important;
            background-color: #8138B5 !important;
            color: #FFFFFF !important;
            border: 1px solid #8138B5 !important;
            border-radius: 11px !important;
            font-weight: 750 !important;
            box-shadow: 0 5px 13px rgba(129, 56, 181, .20) !important;
            transition: transform .16s ease, box-shadow .16s ease !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover,
        div[data-testid="stForm"] button[data-testid="stBaseButton-primary"]:hover,
        div[data-testid="stForm"] button[kind="primary"]:hover {
            background: linear-gradient(100deg, #71309F 0%, #9143BD 100%) !important;
            background-color: #71309F !important;
            border-color: #71309F !important;
            color: #FFFFFF !important;
            transform: translateY(-1px);
            box-shadow: 0 7px 17px rgba(129, 56, 181, .25) !important;
        }
        div[data-testid="stFormSubmitButton"] button:focus,
        div[data-testid="stForm"] button[data-testid="stBaseButton-primary"]:focus {
            outline: 3px solid rgba(129, 56, 181, .18) !important;
            outline-offset: 2px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="
            padding:24px 26px; margin:4px 0 22px; border-radius:20px;
            border:1px solid #E7D8F5;
            background:linear-gradient(115deg,#F7EFFF 0%,#FFFAEF 100%);
        ">
          <div style="font-size:11px;letter-spacing:2px;font-weight:800;color:#8138B5;">
            CAREER OPPORTUNITIES
          </div>
          <div style="font-size:27px;font-weight:850;color:#291437;margin-top:5px;">
            Find your next opportunity
          </div>
          <div style="font-size:14px;color:#76677F;margin-top:7px;">
            Search job listings and explore roles that fit your career goals.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("skilllens_job_search_form"):
        first, second = st.columns([1.35, 1])
        with first:
            keywords = st.text_input(
                "Job title or keywords",
                value="",
                placeholder="e.g. Python Developer, Data Scientist",
            )
        with second:
            location = st.text_input(
                "Location",
                value="India",
                placeholder="e.g. Nagpur, Pune, Remote",
            )

        f1, f2, f3, f4 = st.columns([1, 1, 1, 1])
        with f1:
            country_label = st.selectbox(
                "Job market",
                ["India", "United Kingdom", "United States", "Canada", "Australia", "Germany"],
                index=0,
            )
        country_codes = {
            "India": "in",
            "United Kingdom": "gb",
            "United States": "us",
            "Canada": "ca",
            "Australia": "au",
            "Germany": "de",
        }
        with f2:
            sort_by = st.selectbox(
                "Sort results",
                ["date", "relevance", "salary"],
                format_func=lambda x: {
                    "date": "Newest",
                    "relevance": "Relevance",
                    "salary": "Salary",
                }[x],
            )
        with f3:
            max_days = st.selectbox(
                "Posted within",
                ["Any time", "3 days", "7 days", "14 days", "30 days"],
                index=2,
            )
        with f4:
            result_count = st.selectbox("Results", [5, 10, 15, 20], index=1)

        g1, g2 = st.columns(2)
        with g1:
            full_time = st.checkbox("Full-time roles only", value=False)
        with g2:
            permanent = st.checkbox("Permanent roles only", value=False)

        submitted = st.form_submit_button(
            "🔎 Search jobs",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        st.info("Enter your preferred role and location, then select **Search jobs**.")
        return

    if not keywords.strip():
        st.warning("Enter a job title or keyword to search.")
        return

    max_days_old = None if max_days == "Any time" else int(max_days.split()[0])

    with st.spinner("Searching job listings…"):
        try:
            jobs = search_adzuna_jobs(
                keywords=keywords,
                location=location,
                country=country_codes[country_label],
                results_per_page=result_count,
                sort_by=sort_by,
                max_days_old=max_days_old,
                full_time=full_time,
                permanent=permanent,
            )
        except requests.Timeout:
            st.error("The job search timed out. Please try again.")
            return
        except requests.RequestException as exc:
            st.error(f"Could not retrieve jobs from Adzuna: {exc}")
            return
        except (RuntimeError, ValueError) as exc:
            st.error(str(exc))
            return

    search_details = {
        "keywords": keywords.strip(),
        "location": location.strip(),
        "country": country_label,
        "sort_by": sort_by,
        "posted_within": max_days,
        "full_time": full_time,
        "permanent": permanent,
        "results_count": len(jobs),
        "jobs": jobs,
    }
    log_activity(
        "Job Search",
        f"Job search: {keywords.strip()}",
        f"{location.strip() or country_label} · {len(jobs)} result(s)",
        search_details,
        activity_id=f"job-search:{datetime.now().astimezone().isoformat(timespec='seconds')}:{keywords.strip()}:{location.strip()}",
    )

    if not jobs:
        st.warning("No jobs matched this search. Try broader keywords or a nearby location.")
        return

    st.success(f"Found {len(jobs)} job listing(s).")
    st.caption(
        "Listings are supplied by Adzuna. Salary information may be estimated or unavailable. "
        "Use the employer's application page to verify the role is still open."
    )

    for index, job in enumerate(jobs):
        with st.container(border=True):
            title_col, action_col = st.columns([4, 1])
            with title_col:
                st.markdown(f"### {job['title']}")
                st.markdown(
                    f"**{job['company']}** · {job['location']}"
                )
            with action_col:
                if job["url"]:
                    st.link_button(
                        "View job ↗",
                        job["url"],
                        use_container_width=True,
                    )

            details = [
                _format_salary(job),
                job["contract_time"].replace("_", " ").title() or "Type not listed",
                job["contract_type"].replace("_", " ").title() or "Contract not listed",
            ]
            st.caption("  ·  ".join(details))

            if job["created"]:
                try:
                    posted_date = datetime.fromisoformat(
                        job["created"].replace("Z", "+00:00")
                    ).strftime("%d %b %Y")
                    st.caption(f"Posted: {posted_date}")
                except ValueError:
                    pass

            description = job["description"].strip()
            if description:
                st.write(description[:650] + ("…" if len(description) > 650 else ""))

            # Keep the selected job available for later phases (matching and application tracking).
            if st.button("Save for later", key=f"save_job_{job['id'] or index}"):
                saved_jobs = st.session_state.setdefault("saved_jobs", [])
                existing_ids = {str(saved.get("id", "")) for saved in saved_jobs}
                if job["id"] not in existing_ids:
                    saved_jobs.append(job)
                    log_activity(
                        "Saved Job",
                        f"Saved job: {job.get('title', 'Untitled role')}",
                        f"{job.get('company', 'Company not listed')} · {job.get('location', 'Location not listed')}",
                        {"job": job},
                        activity_id=f"saved-job:{job.get('id') or job.get('url') or job.get('title')}",
                    )
                    st.success("Job saved and added to your activity history.")
                else:
                    st.info("This job is already saved in this session.")

    if st.session_state.get("saved_jobs"):
        st.markdown("#### Saved jobs in this session")
        st.caption(f"{len(st.session_state['saved_jobs'])} job(s) saved. These are not yet stored permanently.")
