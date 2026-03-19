import streamlit as st
from datetime import datetime, timedelta
from config.app_config import SESSION_TIMEOUT_MINUTES


class SessionManager:
    """
    Manages Streamlit session state lifecycle:
    - Initialization of default state variables
    - Session timeout enforcement
    - Create / switch / delete chat sessions
    """

    def init_session(self):
        """Initialize all required session state variables with defaults."""
        defaults = {
            "user": None,
            "auth_token": None,
            "refresh_token": None,
            "current_session_id": None,
            "chat_history": [],
            "report_text": None,
            "analysis_result": None,
            "vector_store_cache": {},   # session_id -> FAISS vectorstore
            "last_active": datetime.now(),
            "analysis_count": 0,
            "last_analysis_reset": datetime.now(),
            "analysis_limit": 15,
            "models_used": {},
            "knowledge_base": {},
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def check_session_timeout(self) -> bool:
        """
        Enforce inactivity timeout. Returns True if session is still valid.
        If timed out, clears auth-related state so the user is shown the login page.
        """
        if "last_active" not in st.session_state or "user" not in st.session_state:
            return True

        if st.session_state.user is None:
            return True

        elapsed = datetime.now() - st.session_state.last_active
        if elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            # Clear auth state
            for key in ["auth_token", "refresh_token", "user", "current_session_id",
                        "chat_history", "report_text", "analysis_result"]:
                st.session_state.pop(key, None)
            st.warning("⏰ Session timed out due to inactivity. Please sign in again.")
            return False

        # Update last active timestamp
        st.session_state.last_active = datetime.now()
        return True

    def create_new_session(self, auth_service) -> bool:
        """Create a new chat session in Supabase and reset current state."""
        user = st.session_state.get("user")
        if not user:
            return False

        session = auth_service.create_chat_session(user["id"])
        if not session:
            st.error("Failed to create a new session.")
            return False

        st.session_state.current_session_id = session["id"]
        st.session_state.chat_history = []
        st.session_state.report_text = None
        st.session_state.analysis_result = None
        return True

    def switch_session(self, session_id: str, auth_service):
        """Load a different chat session and restore its messages."""
        # Fetch messages from Supabase
        messages = auth_service.get_messages(session_id)
        st.session_state.current_session_id = session_id
        st.session_state.chat_history = [
            {"role": msg["role"], "content": msg["content"]} for msg in messages
        ]

        # Try to restore report_text and analysis_result from the session row
        try:
            result = (
                auth_service.supabase.table("chat_sessions")
                .select("report_text, analysis_result")
                .eq("id", session_id)
                .execute()
            )
            if result.data:
                st.session_state.report_text = result.data[0].get("report_text")
                st.session_state.analysis_result = result.data[0].get("analysis_result")
        except Exception:
            st.session_state.report_text = None
            st.session_state.analysis_result = None

    def delete_session(self, session_id: str, auth_service) -> bool:
        """Delete a session from Supabase and reset state if it was the current one."""
        success = auth_service.delete_chat_session(session_id)
        if success and st.session_state.get("current_session_id") == session_id:
            st.session_state.current_session_id = None
            st.session_state.chat_history = []
            st.session_state.report_text = None
            st.session_state.analysis_result = None
            # Remove cached vector store for this session
            st.session_state.vector_store_cache.pop(session_id, None)
        return success
