import streamlit as st
from utils.validators import validate_email, validate_password


def show_auth_page(auth_service):
    """Render the login / signup page with two tabs."""
    st.markdown(
        """
        <div style='text-align:center; padding: 2rem 0 1rem;'>
            <h1 style='font-size:3rem; margin-bottom:0;'>🩺 HIA</h1>
            <p style='color:#64B5F6; font-size:1.2rem; margin-top:0;'>
                Health Insights Agent — Analyze your blood report with AI
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_signup = st.tabs(["🔑 Sign In", "📝 Sign Up"])

    # ── Sign In ──────────────────────────────────────────────────────────────
    with tab_login:
        st.subheader("Welcome back!")
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Please fill in all fields.")
            else:
                with st.spinner("Signing in..."):
                    success, result = auth_service.sign_in(email, password)
                if success:
                    st.success(f"Welcome back, {result.get('name', email.split('@')[0])}! 👋")
                    st.rerun()
                else:
                    st.error(result)

    # ── Sign Up ──────────────────────────────────────────────────────────────
    with tab_signup:
        st.subheader("Create your account")
        with st.form("signup_form"):
            name = st.text_input("Full Name", placeholder="Jane Doe")
            email_su = st.text_input("Email", placeholder="you@example.com", key="su_email")
            password_su = st.text_input("Password", type="password", placeholder="Min. 8 chars", key="su_pass")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Repeat password", key="su_confirm")
            submitted_su = st.form_submit_button("Create Account", use_container_width=True)

        if submitted_su:
            errors = []
            if not name:
                errors.append("Name is required.")
            is_email_valid, email_err = validate_email(email_su)
            if not is_email_valid:
                errors.append(email_err)
            is_pass_valid, pass_err = validate_password(password_su)
            if not is_pass_valid:
                errors.append(pass_err)
            if password_su != confirm_password:
                errors.append("Passwords do not match.")

            if errors:
                for err in errors:
                    st.error(err)
            else:
                with st.spinner("Creating account..."):
                    success, result = auth_service.sign_up(email_su, password_su, name)
                if success:
                    st.success("Account created! You are now signed in. 🎉")
                    st.rerun()
                else:
                    st.error(result)
