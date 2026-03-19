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
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

    /* Global Typography */
    html, body, [class*="st-"] {
        font-family: 'Outfit', sans-serif !important;
    }

    /* Gorgeous Animated Dark Gradient Background */
    .stApp, [data-testid="stAppViewContainer"] { 
        background: linear-gradient(135deg, #0f172a, #1e1b4b, #1e293b, #0f172a);
        background-size: 300% 300%;
        animation: gradientBG 15s ease infinite;
        color: #f8fafc;
    }

    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(22, 27, 34, 0.45) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Deep Hide Streamlit Branding & Menus */
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}

    /* Premium Chat Bubbles - Base Override */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin-bottom: 1.5rem !important;
    }
    
    /* Hide Avatar Icons for minimal SaaS look */
    [data-testid="chatAvatarIcon-user"], 
    [data-testid="chatAvatarIcon-assistant"] {
        display: none !important;
    }

    /* User Messages (Aligned Right, Blue Glass Accent) */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        flex-direction: row-reverse !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stMarkdown {
        background: linear-gradient(135deg, #4F46E5, #2563EB) !important;
        color: white !important;
        border-radius: 20px 20px 4px 20px !important;
        padding: 12px 18px !important;
        display: inline-block !important;
        margin-left: auto !important;
        box-shadow: 0 5px 15px rgba(37, 99, 235, 0.3) !important;
    }
    /* Stop the internal markdown container from taking 100% width so it bubbles */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] {
        width: max-content !important;
        max-width: 85% !important;
        margin-left: auto !important;
    }

    /* Assistant Messages (Aligned Left, Dark Glass) */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) .stMarkdown {
        background: rgba(30, 41, 59, 0.7) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #f8fafc !important;
        border-radius: 20px 20px 20px 4px !important;
        padding: 12px 18px !important;
        display: inline-block !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stMarkdownContainer"] {
        width: max-content !important;
        max-width: 90% !important;
    }

    /* Floating Chat Input Pill */
    [data-testid="stChatInput"] {
        padding-bottom: 2rem !important;
    }
    [data-testid="stChatInput"] textarea {
        background: rgba(15, 23, 42, 0.85) !important;
        backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 30px !important;
        padding: 15px 50px 15px 25px !important;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4) !important;
        color: white !important;
    }

    /* Glow Primary Buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563EB, #4F46E5) !important;
        border: none !important;
        color: white !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        padding: 0.6rem 2rem !important;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 8px 25px rgba(79, 70, 229, 0.5) !important;
        background: linear-gradient(135deg, #1D4ED8, #4338CA) !important;
    }

    /* Glass Inputs */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 10px !important;
        transition: all 0.3s !important;
    }
    
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3) !important;
        background: rgba(255, 255, 255, 0.08) !important;
    }

    /* Expander Accents */
    .streamlit-expanderHeader { 
        font-weight: 600 !important; 
        color: #818CF8 !important; 
        border-radius: 8px !important;
        background: rgba(255,255,255, 0.02) !important;
    }
    
    [data-testid="stExpander"] {
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        overflow: hidden;
    }

    /* Analysis Result Box */
    .analysis-box {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(10px);
        border-left: 4px solid #6366F1;
        border-radius: 10px;
        padding: 1.5rem;
        margin-top: 1rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    
    /* Custom Scrollbar for modern feel */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.2);
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
                <h2 style='color:#64B5F6;'>👋 Welcome to DOCUS AI!</h2>
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
