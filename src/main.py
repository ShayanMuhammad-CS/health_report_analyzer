import sys
import os

# Ensure 'src' is on the Python path for clean imports
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from config.app_config import APP_NAME, APP_ICON, APP_DESCRIPTION
from auth.auth_service import AuthService
from auth.session_manager import SessionManager
from services.ai_service import AIService
from components.auth_pages import show_auth_page
from components.header import show_header
from components.sidebar import show_sidebar
from components.analysis_form import show_analysis_form
from components.footer import show_footer

# ── Page Configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"{APP_ICON} {APP_NAME} — {APP_DESCRIPTION}",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Dark background */
    .stApp { background-color: #0e1117; }

    /* Chat bubbles */
    [data-testid="stChatMessage"] {
        border-radius: 12px;
        padding: 0.5rem 1rem;
        margin-bottom: 0.4rem;
    }

    /* Primary button style */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1976D2, #64B5F6);
        border: none;
        color: white;
        font-weight: 600;
        border-radius: 8px;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #1565C0, #42A5F5);
        transform: translateY(-1px);
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #161b22;
    }

    /* Expander */
    .streamlit-expanderHeader { font-weight: 600; color: #64B5F6; }

    /* Analysis result box */
    .analysis-box {
        background: #1a2233;
        border-left: 4px solid #64B5F6;
        border-radius: 6px;
        padding: 1rem 1.2rem;
        margin-top: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Loading AI Models... This may take a moment.")
def get_ai_service():
    """Cached initialization of the AI Service to prevent reloading on reruns."""
    return AIService()


def main():
    """Main application entry point."""
    # ── Initialize core services ─────────────────────────────────────────────
    session_manager = SessionManager()
    session_manager.init_session()

    try:
        auth_service = AuthService()
    except Exception as e:
        st.error(f"❌ Failed to connect to the database: {str(e)}")
        st.stop()

    ai_service = get_ai_service()

    # ── Session timeout check ────────────────────────────────────────────────
    session_manager.check_session_timeout()

    # ── Routing ──────────────────────────────────────────────────────────────
    user = st.session_state.get("user")

    if not user:
        show_auth_page(auth_service)
        return

    # ── Authenticated Layout ─────────────────────────────────────────────────
    show_sidebar(auth_service, session_manager, ai_service)

    user_name = user.get("name", user.get("email", "User").split("@")[0])
    show_header(user_name)

    current_session_id = st.session_state.get("current_session_id")

    if not current_session_id:
        # ── No active session ────────────────────────────────────────────────
        st.markdown(
            """
            <div style='text-align:center; padding: 4rem 1rem;'>
                <h2 style='color:#64B5F6;'>👋 Welcome to HIA!</h2>
                <p style='color:#aaa; font-size:1.1rem;'>
                    Start by creating a <strong>New Session</strong> from the sidebar,
                    then upload your blood report PDF or use the sample report.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        show_footer()
        return

    # ── Active session layout ────────────────────────────────────────────────
    # Show existing analysis result if already computed
    existing_report = st.session_state.get("report_text")
    existing_analysis = st.session_state.get("analysis_result")

    if existing_analysis:
        with st.expander("📊 View Report Analysis", expanded=True):
            st.markdown(existing_analysis)
    else:
        # Show the analysis form only if no analysis yet
        new_report, new_analysis = show_analysis_form(ai_service, auth_service, current_session_id)
        if new_report and new_analysis:
            st.session_state.report_text = new_report
            st.session_state.analysis_result = new_analysis

            # Store initial analysis message in history and Supabase
            analysis_message = f"**Blood Report Analysis:**\n\n{new_analysis}"
            st.session_state.chat_history.append(
                {"role": "assistant", "content": analysis_message}
            )
            auth_service.save_message(current_session_id, "assistant", analysis_message)

            with st.expander("📊 Analysis Result", expanded=True):
                st.markdown(new_analysis)

    # ── Chat Interface ───────────────────────────────────────────────────────
    if existing_analysis or st.session_state.get("analysis_result"):
        st.markdown("---")
        st.markdown("### 💬 Follow-up Chat")
        st.caption(
            "Ask follow-up questions about your blood report. "
            "The AI will answer using RAG (Retrieval-Augmented Generation) over your report."
        )

        # Render existing chat history
        chat_history = st.session_state.get("chat_history", [])
        for message in chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if user_input := st.chat_input("Ask a question about your blood report..."):
            # Display user message
            with st.chat_message("user"):
                st.markdown(user_input)

            # Save user message
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            auth_service.save_message(current_session_id, "user", user_input)

            # Get AI response
            report_text = st.session_state.get("report_text", "")
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = ai_service.get_chat_response(
                        user_input,
                        report_text,
                        current_session_id,
                        st.session_state.chat_history[:-1],  # Exclude the current user message
                    )
                st.markdown(response)

            # Save assistant message
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            auth_service.save_message(current_session_id, "assistant", response)

    show_footer()


if __name__ == "__main__":
    main()
