import streamlit as st
from config.app_config import APP_NAME, APP_ICON, APP_DESCRIPTION


def show_header(user_name: str = None):
    """Render the app header with user greeting."""
    greeting = f"Hello, {user_name}!" if user_name else ""
    st.markdown(
        f"""
        <div style='display:flex; align-items:center; justify-content:space-between;
                    padding-bottom: 0.5rem; border-bottom: 1px solid #e2e8f0;'>
            <div>
                <h2 style='margin:0; color:#2563EB;'>{APP_ICON} {APP_NAME}</h2>
                <p style='margin:0; color:#475569; font-size:0.9rem;'>{APP_DESCRIPTION}</p>
            </div>
            <div style='text-align:right; color:#64748b; font-size:0.95rem;'>
                {greeting}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")
