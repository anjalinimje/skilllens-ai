
import streamlit as st
from supabase_client import get_supabase_client


def register_user(email, password, full_name):
    supabase = get_supabase_client()

    response = supabase.auth.sign_up({
        "email": email,
        "password": password,
        "options": {
            "data": {
                "full_name": full_name
            }
        }
    })

    return response


def login_user(email, password):
    supabase = get_supabase_client()

    response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })

    if response.session:
        st.session_state["access_token"] = response.session.access_token
        st.session_state["refresh_token"] = response.session.refresh_token
        st.session_state["user"] = response.user

        return True

    return False


def logout_user():
    supabase = get_supabase_client()

    try:
        supabase.auth.sign_out()
    finally:
        for key in [
            "access_token",
            "refresh_token",
            "user",
            "user_profile",
            "_supabase_client"
        ]:
            st.session_state.pop(key, None)


def get_current_user():
    return st.session_state.get("user")


def get_user_profile():
    user = get_current_user()

    if not user:
        return None

    supabase = get_supabase_client()

    response = (
        supabase.table("profiles")
        .select("*")
        .eq("id", user.id)
        .maybe_single()
        .execute()
    )

    return response.data


def is_admin():
    profile = get_user_profile()

    return bool(
        profile and profile.get("role") == "admin"
    )
