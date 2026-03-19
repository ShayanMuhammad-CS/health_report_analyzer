from datetime import datetime, timedelta
import streamlit as st
from agents.model_manager import ModelManager


class AnalysisAgent:
    """
    Agent responsible for managing report analysis, rate limiting,
    and implementing in-context learning from previous analyses.
    """

    def __init__(self):
        self.model_manager = ModelManager()
        self._init_state()

    def _init_state(self):
        """Initialize analysis-related session state variables."""
        if "analysis_count" not in st.session_state:
            st.session_state.analysis_count = 0
        if "last_analysis_reset" not in st.session_state:
            st.session_state.last_analysis_reset = datetime.now()
        if "analysis_limit" not in st.session_state:
            st.session_state.analysis_limit = 15
        if "models_used" not in st.session_state:
            st.session_state.models_used = {}
        if "knowledge_base" not in st.session_state:
            st.session_state.knowledge_base = {}

    def check_rate_limit(self) -> tuple:
        """Check if user has reached their analysis limit. Returns (can_analyze, error_msg)."""
        now = datetime.now()
        time_since_reset = now - st.session_state.last_analysis_reset
        time_until_reset = timedelta(days=1) - time_since_reset

        # Reset counter after 24 hours
        if time_until_reset.days < 0 or time_until_reset.total_seconds() <= 0:
            st.session_state.analysis_count = 0
            st.session_state.last_analysis_reset = now
            return True, None

        hours, remainder = divmod(int(time_until_reset.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)

        if st.session_state.analysis_count >= st.session_state.analysis_limit:
            error_msg = f"Daily analysis limit reached. Resets in {hours}h {minutes}m."
            return False, error_msg

        return True, None

    def get_remaining_analyses(self) -> int:
        """Get remaining analyses for today."""
        return max(0, st.session_state.analysis_limit - st.session_state.analysis_count)

    def analyze_report(self, data: dict, system_prompt: str, chat_history: list = None) -> dict:
        """
        Analyze report data using in-context learning from previous analyses.

        Args:
            data: dict with keys 'report', 'age', 'gender', 'medical_history'
            system_prompt: Base system prompt from SPECIALIST_PROMPTS
            chat_history: Previous messages in the current session (optional)
        """
        can_analyze, error_msg = self.check_rate_limit()
        if not can_analyze:
            return {"success": False, "error": error_msg}

        # Preprocess inputs
        processed_data = self._preprocess_data(data)

        # Enhance prompt with in-context learning
        enhanced_prompt = (
            self._build_enhanced_prompt(system_prompt, processed_data, chat_history)
            if chat_history
            else system_prompt
        )

        # Generate analysis using ModelManager
        result = self.model_manager.generate_analysis(processed_data, enhanced_prompt)

        if result["success"]:
            self._update_analytics(result)
            self._update_knowledge_base(processed_data, result["content"])

        return result

    def _preprocess_data(self, data: dict) -> dict:
        """Clean and structure report data before sending to the model."""
        processed = {}
        if isinstance(data, dict):
            processed["report"] = str(data.get("report", "")).strip()
            processed["age"] = str(data.get("age", "Not specified"))
            processed["gender"] = str(data.get("gender", "Not specified"))
            processed["medical_history"] = str(data.get("medical_history", "None"))
        else:
            processed["report"] = str(data).strip()
        return processed

    def _update_analytics(self, result: dict):
        """Update analytics after a successful analysis."""
        st.session_state.analysis_count += 1

        model_used = result.get("model_used", "unknown")
        if model_used in st.session_state.models_used:
            st.session_state.models_used[model_used] += 1
        else:
            st.session_state.models_used[model_used] = 1

    def _update_knowledge_base(self, data: dict, analysis: str):
        """
        Update knowledge base with new analysis results for in-context learning.
        Maps key health indicators to analysis patterns.
        """
        if not isinstance(data, dict) or "report" not in data:
            return

        report_text = data["report"].lower()
        patient_profile = f"{data.get('age', 'unknown')}-{data.get('gender', 'unknown')}"

        key_indicators = [
            "hemoglobin", "glucose", "cholesterol", "triglycerides",
            "hdl", "ldl", "wbc", "rbc", "platelet", "creatinine",
            "tsh", "ferritin", "bilirubin", "alt", "ast",
        ]

        for indicator in key_indicators:
            if indicator in report_text and indicator in analysis.lower():
                if indicator not in st.session_state.knowledge_base:
                    st.session_state.knowledge_base[indicator] = {}

                if patient_profile not in st.session_state.knowledge_base[indicator]:
                    st.session_state.knowledge_base[indicator][patient_profile] = []

                lines = analysis.split("\n")
                relevant_lines = [l for l in lines if indicator in l.lower()]
                if relevant_lines:
                    kb_list = st.session_state.knowledge_base[indicator][patient_profile]
                    if len(kb_list) >= 3:
                        kb_list.pop(0)
                    kb_list.append(relevant_lines[0])

    def _build_enhanced_prompt(self, system_prompt: str, data: dict, chat_history: list) -> str:
        """
        Build an enhanced prompt using in-context learning from:
        1. Knowledge base of previous analyses
        2. Current session chat history
        """
        enhanced_prompt = system_prompt

        if isinstance(data, dict) and "report" in data:
            kb_context = self._get_knowledge_base_context(data)
            if kb_context:
                enhanced_prompt += "\n\n## Relevant Learning From Previous Analyses\n" + kb_context

        if chat_history:
            session_context = self._get_session_context(chat_history)
            if session_context:
                enhanced_prompt += "\n\n## Current Session History\n" + session_context

        return enhanced_prompt

    def _get_knowledge_base_context(self, data: dict) -> str:
        """Extract relevant context from the knowledge base."""
        if not st.session_state.knowledge_base:
            return ""

        report_text = data.get("report", "").lower()
        patient_profile = f"{data.get('age', 'unknown')}-{data.get('gender', 'unknown')}"
        context_items = []

        for indicator, profiles in st.session_state.knowledge_base.items():
            if indicator in report_text:
                if patient_profile in profiles:
                    for insight in profiles[patient_profile]:
                        context_items.append(f"- {indicator} (similar profile): {insight}")
                for profile, insights in profiles.items():
                    if profile != patient_profile:
                        for insight in insights:
                            context_items.append(f"- {indicator} (other profile): {insight}")

        return "\n".join(context_items[:5])

    def _get_session_context(self, chat_history: list) -> str:
        """Extract relevant context from the current session."""
        if not chat_history or len(chat_history) < 2:
            return ""

        context_items = []
        for i in range(len(chat_history) - 1, 0, -2):
            if i >= 1 and chat_history[i - 1]["role"] == "user" and chat_history[i]["role"] == "assistant":
                user_msg = chat_history[i - 1]["content"]
                ai_msg = chat_history[i]["content"]
                if len(user_msg) > 200:
                    user_msg = user_msg[:197] + "..."
                if len(ai_msg) > 200:
                    ai_msg = ai_msg[:197] + "..."
                context_items.append(f"User: {user_msg}\nAssistant: {ai_msg}")
                if len(context_items) >= 2:
                    break

        return "\n\n".join(context_items)
