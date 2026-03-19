import streamlit as st
from agents.analysis_agent import AnalysisAgent
from agents.chat_agent import ChatAgent
from config.prompts import SPECIALIST_PROMPTS


class AIService:
    """
    Central service layer that mediates between the UI components
    and the underlying AI agents.
    - analyze_report: delegates to AnalysisAgent
    - get_chat_response: manages vector store cache and delegates to ChatAgent
    """

    def __init__(self):
        self.analysis_agent = AnalysisAgent()
        self.chat_agent = ChatAgent()

    def analyze_report(
        self,
        report_text: str,
        patient_data: dict,
        chat_history: list = None,
    ) -> dict:
        """
        Run the full analysis pipeline on a blood report.

        Args:
            report_text: Extracted text from the blood report PDF or sample.
            patient_data: dict with 'age', 'gender', 'medical_history'.
            chat_history: Current session chat history for in-context learning.

        Returns:
            dict with 'success' bool, 'content' str (or 'error' str), 'model_used'.
        """
        data = {
            "report": report_text,
            "age": patient_data.get("age", "Not specified"),
            "gender": patient_data.get("gender", "Not specified"),
            "medical_history": patient_data.get("medical_history", "None"),
        }
        system_prompt = SPECIALIST_PROMPTS["comprehensive_analyst"]
        return self.analysis_agent.analyze_report(data, system_prompt, chat_history)

    def get_chat_response(
        self,
        query: str,
        report_text: str,
        session_id: str,
        chat_history: list = None,
    ) -> str:
        """
        Get a RAG-powered response for a follow-up question about the report.
        Vector stores are cached per session to avoid re-embedding on every message.

        Args:
            query: The user's follow-up question.
            report_text: The original report text (used to build/reuse vector store).
            session_id: Current chat session ID (used as cache key).
            chat_history: Current session chat history.

        Returns:
            str: The AI assistant's response.
        """
        if "vector_store_cache" not in st.session_state:
            st.session_state.vector_store_cache = {}

        # Build or retrieve cached vector store for this session
        if session_id not in st.session_state.vector_store_cache:
            with st.spinner("🔍 Indexing report for retrieval..."):
                vectorstore = self.chat_agent.initialize_vector_store(report_text or "")
                st.session_state.vector_store_cache[session_id] = vectorstore
        else:
            vectorstore = st.session_state.vector_store_cache[session_id]

        return self.chat_agent.get_response(query, vectorstore, chat_history)

    def get_remaining_analyses(self) -> int:
        """Return the number of analyses remaining today."""
        return self.analysis_agent.get_remaining_analyses()
