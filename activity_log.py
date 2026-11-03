"""Shared activity logging helpers for SkillLens AI."""
from datetime import datetime
import uuid
import streamlit as st


def log_activity(activity_type, title, summary="", details=None, activity_id=None):
    """Append one structured activity to the current authenticated session."""
    activities = st.session_state.setdefault("activity_log", [])
    if activity_id and any(item.get("activity_id") == activity_id for item in activities):
        return
    activities.append({
        "activity_id": activity_id or str(uuid.uuid4()),
        "type": activity_type,
        "title": title,
        "summary": summary,
        "details": details or {},
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "display_time": datetime.now().astimezone().strftime("%d %b %Y · %I:%M %p"),
    })
