import streamlit as st
from supabase import create_client
from datetime import datetime
import re


class AuthService:
    """
    Handles Supabase authentication (sign up, sign in, sign out),
    session management, and database operations for users, chat sessions,
    and chat messages.
    """

    def __init__(self):
        try:
            self.supabase = create_client(
                st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
            )
        except Exception as e:
            st.error(f"Failed to initialize Supabase: {str(e)}")
            raise e

        self.try_restore_session()

        if "auth_token" in st.session_state:
            self.validate_session_token()

    # ── Session Restoration ──────────────────────────────────────────────────

    def try_restore_session(self):
        """Try to restore a persisted Supabase session from Streamlit session state."""
        try:
            if "auth_token" in st.session_state and "refresh_token" in st.session_state:
                try:
                    self.supabase.auth.set_session(
                        st.session_state.auth_token, st.session_state.refresh_token
                    )
                except Exception:
                    pass

            session = self.supabase.auth.get_session()
            if session and session.access_token:
                current_token = st.session_state.get("auth_token")
                if not current_token or current_token != session.access_token:
                    user = self.supabase.auth.get_user()
                    if user and user.user:
                        user_data = self.get_user_data(user.user.id)
                        if user_data:
                            st.session_state.auth_token = session.access_token
                            st.session_state.refresh_token = session.refresh_token
                            st.session_state.user = user_data
        except Exception:
            pass

    def validate_session_token(self) -> bool:
        """Validate the current session token."""
        try:
            user = self.supabase.auth.get_user()
            return user is not None and user.user is not None
        except Exception:
            return False

    # ── Auth Operations ──────────────────────────────────────────────────────

    def sign_up(self, email: str, password: str, name: str) -> tuple:
        """Register a new user with Supabase Auth and create a users table row."""
        try:
            auth_response = self.supabase.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {"data": {"name": name}},
                }
            )

            if not auth_response.user:
                return False, "Failed to create user account."

            user_data = {
                "id": auth_response.user.id,
                "email": email,
                "name": name,
                "created_at": datetime.now().isoformat(),
            }

            self.supabase.table("users").insert(user_data).execute()

            if auth_response.session:
                st.session_state.auth_token = auth_response.session.access_token
                st.session_state.refresh_token = auth_response.session.refresh_token
                st.session_state.user = user_data

            return True, user_data

        except Exception as e:
            error_msg = str(e).lower()
            if "duplicate" in error_msg or "already registered" in error_msg:
                return False, "Email already registered. Please sign in."
            return False, f"Sign up failed: {str(e)}"

    def sign_in(self, email: str, password: str) -> tuple:
        """Sign in an existing user with Supabase Auth."""
        try:
            # Clear stale state
            for key in ["auth_token", "refresh_token", "user"]:
                st.session_state.pop(key, None)

            auth_response = self.supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            if not auth_response.user or not auth_response.session:
                return False, "Invalid email or password."

            user_data = self.get_user_data(auth_response.user.id)
            if not user_data:
                # Fallback: build from auth data
                user_data = {
                    "id": auth_response.user.id,
                    "email": email,
                    "name": auth_response.user.user_metadata.get("name", email.split("@")[0]),
                }

            st.session_state.auth_token = auth_response.session.access_token
            st.session_state.refresh_token = auth_response.session.refresh_token
            st.session_state.user = user_data

            return True, user_data

        except Exception as e:
            error_msg = str(e).lower()
            if "invalid" in error_msg or "credentials" in error_msg:
                return False, "Invalid email or password."
            return False, f"Sign in failed: {str(e)}"

    def sign_out(self):
        """Sign out the current user and clear session state."""
        try:
            self.supabase.auth.sign_out()
        except Exception:
            pass
        for key in ["auth_token", "refresh_token", "user", "current_session_id",
                    "chat_history", "report_text", "analysis_result",
                    "vector_store_cache", "last_active"]:
            st.session_state.pop(key, None)

    # ── User Data ────────────────────────────────────────────────────────────

    def get_user_data(self, user_id: str) -> dict | None:
        """Fetch user row from the users table by ID."""
        try:
            result = self.supabase.table("users").select("*").eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None

    # ── Chat Sessions ────────────────────────────────────────────────────────

    def get_chat_sessions(self, user_id: str) -> list:
        """Fetch all chat sessions for the given user, newest first."""
        try:
            result = (
                self.supabase.table("chat_sessions")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception:
            return []

    def create_chat_session(self, user_id: str, title: str = None) -> dict | None:
        """Create a new chat session row in Supabase."""
        try:
            if not title:
                title = f"Session {datetime.now().strftime('%b %d, %H:%M')}"
            result = (
                self.supabase.table("chat_sessions")
                .insert({"user_id": user_id, "title": title})
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception:
            return None

    def update_session_data(self, session_id: str, report_text: str = None, analysis_result: str = None):
        """Persist report text and/or analysis result for a session."""
        try:
            updates = {}
            if report_text is not None:
                updates["report_text"] = report_text
            if analysis_result is not None:
                updates["analysis_result"] = analysis_result
            if updates:
                self.supabase.table("chat_sessions").update(updates).eq("id", session_id).execute()
        except Exception:
            pass

    def delete_chat_session(self, session_id: str) -> bool:
        """Delete a chat session and all its messages."""
        try:
            self.supabase.table("chat_sessions").delete().eq("id", session_id).execute()
            return True
        except Exception:
            return False

    # ── Chat Messages ────────────────────────────────────────────────────────

    def save_message(self, session_id: str, role: str, content: str) -> bool:
        """Persist a single chat message to Supabase."""
        try:
            self.supabase.table("chat_messages").insert(
                {
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "created_at": datetime.now().isoformat(),
                }
            ).execute()
            return True
        except Exception:
            return False

    def get_messages(self, session_id: str) -> list:
        """Fetch all messages for a session, oldest first."""
        try:
            result = (
                self.supabase.table("chat_messages")
                .select("*")
                .eq("session_id", session_id)
                .order("created_at", desc=False)
                .execute()
            )
            return result.data or []
        except Exception:
            return []
