
import streamlit as st
from supabase import create_client


def get_supabase_client():
    """
    Return a Supabase client isolated to the current
    Streamlit user's session.
    """

    if "_supabase_client" not in st.session_state:

        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["key"]

        st.session_state["_supabase_client"] = create_client(
            supabase_url,
            supabase_key
        )

    return st.session_state["_supabase_client"]
