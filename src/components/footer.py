import streamlit as st


def show_footer():
    """Render a disclaimer footer at the bottom of the page."""
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align:center; color:#64748b; font-size:0.8rem; padding: 0.5rem;'>
            🩺 <strong>DOCUS AI</strong> &nbsp;|&nbsp;
            This tool is for informational purposes only and is <em>not</em> a substitute
            for professional medical advice, diagnosis, or treatment.
            Always consult a qualified healthcare provider.
        </div>
        """,
        unsafe_allow_html=True,
    )
