
import streamlit as st
from auth import register_user, login_user


def render_auth_page():

    st.markdown(
        """
        <div style="text-align:center; padding:25px 0;">
            <h1 style="color:#6C4AB6;">SkillLens AI</h1>
            <p style="color:#777;">
                AI-powered Resume Screening & Career Intelligence
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    login_tab, register_tab = st.tabs(["Login", "Create Account"])

    # LOGIN
    with login_tab:
        st.subheader("Welcome Back")

        with st.form("skilllens_login_form"):
            email = st.text_input("Email Address")
            password = st.text_input(
                "Password",
                type="password"
            )

            submitted = st.form_submit_button(
                "Login",
                use_container_width=True
            )

            if submitted:
                if not email or not password:
                    st.warning("Please enter your email and password.")
                else:
                    try:
                        if login_user(email.strip(), password):
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Login failed. Please try again.")

                    except Exception:
                        st.error(
                            "Unable to log in. Check your credentials "
                            "and email verification."
                        )

    # REGISTRATION
    with register_tab:
        st.subheader("Create Your Account")

        with st.form("skilllens_register_form"):
            full_name = st.text_input("Full Name")
            email = st.text_input("Email Address", key="register_email")
            password = st.text_input(
                "Create Password",
                type="password",
                key="register_password"
            )
            confirm_password = st.text_input(
                "Confirm Password",
                type="password"
            )

            submitted = st.form_submit_button(
                "Create Account",
                use_container_width=True
            )

            if submitted:
                if not full_name.strip() or not email.strip():
                    st.warning("Please complete all required fields.")
                elif len(password) < 8:
                    st.warning("Password must contain at least 8 characters.")
                elif password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    try:
                        response = register_user(
                            email.strip(),
                            password,
                            full_name.strip()
                        )

                        if response.session:
                            st.success("Account created successfully!")
                            st.rerun()
                        else:
                            st.success(
                                "Registration submitted! "
                                "Please check your email to verify "
                                "your account before logging in."
                            )

                    except Exception:
                        st.error(
                            "Registration failed. Please check your "
                            "details or try another email address."
                        )


def render_logout_button():
    from auth import logout_user

    if st.button("Logout", key="skilllens_logout"):
        logout_user()
        st.rerun()
