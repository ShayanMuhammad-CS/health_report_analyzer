import streamlit as st


def show_sidebar(auth_service, session_manager, ai_service):
    """
    Render the sidebar with:
    - User profile
    - New session button
    - Session list (click to switch, delete button)
    - Daily analysis limit countdown
    - Logout button
    """
    with st.sidebar:
        user = st.session_state.get("user", {})
        name = user.get("name", "User") if user else "User"
        email = user.get("email", "") if user else ""

        st.markdown(f"### <span style='color:var(--accent-primary);'>●</span> {name}", unsafe_allow_html=True)
        st.caption(email)
        st.divider()

        # ── New Session Button ───────────────────────────────────────────────
        if st.button("New Session", use_container_width=True, type="primary"):
            session_manager.create_new_session(auth_service)
            st.rerun()

        st.markdown("<br/><h4>Your Sessions</h4>", unsafe_allow_html=True)

        # ── Session List ─────────────────────────────────────────────────────
        sessions = auth_service.get_chat_sessions(user.get("id", "")) if user else []
        current_id = st.session_state.get("current_session_id")

        if not sessions:
            st.caption("No sessions yet. Create one above!")
        else:
            for session in sessions:
                sid = session["id"]
                title = session.get("title", "Untitled Session")
                is_active = sid == current_id

                col1, col2 = st.columns([4, 1])
                with col1:
                    label = f"**{title}**" if is_active else title
                    if st.button(label, key=f"switch_{sid}", use_container_width=True):
                        session_manager.switch_session(sid, auth_service)
                        st.rerun()
                with col2:
                    if st.button("✖", key=f"del_{sid}", help="Delete session"):
                        session_manager.delete_session(sid, auth_service)
                        st.rerun()

        st.divider()

        # ── Daily Analysis Countdown ─────────────────────────────────────────
        remaining = ai_service.get_remaining_analyses()
        total = st.session_state.get("analysis_limit", 15)
        st.markdown(f"#### Daily Analyses")
        st.progress(remaining / total)
        st.caption(f"{remaining} / {total} remaining today")

        st.divider()

        # ── Logout ───────────────────────────────────────────────────────────
        if st.button("Sign Out", use_container_width=True):
            auth_service.sign_out()
            st.rerun()
