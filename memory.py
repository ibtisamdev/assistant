import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from models import (
    Memory,
    SessionMetadata,
    AgentState,
    ConversationHistory,
    UserProfile,
    State,
)
from prompt import SYSTEM_PROMPT

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AgentMemory:
    """
    Memory manager with persistence support.
    Handles loading/saving sessions and user profile.
    """

    SESSIONS_DIR = "sessions"
    USER_PROFILE_PATH = "user_profile.json"

    def __init__(self, session_date: Optional[str] = None, force_new: bool = False):
        """
        Initialize memory, loading from disk if available.

        Args:
            session_date: Date in YYYY-MM-DD format (defaults to today)
            force_new: If True, ignore existing session and start fresh
        """
        # Determine session date
        self.session_date = session_date or datetime.now().strftime("%Y-%m-%d")
        self.session_path = self._get_session_path()
        self.is_resuming = False

        # Load or create memory
        if not force_new and os.path.exists(self.session_path):
            logger.info(f"Resuming session from {self.session_path}")
            self.memory = self._load_session()
            self.is_resuming = True
        else:
            logger.info(f"Creating new session for {self.session_date}")
            self.memory = self._create_fresh_memory()
            self._save()  # Save immediately

        # Load user profile (separate from session)
        self.user_profile = self._load_user_profile()

    # === Session Path Management ===

    def _get_session_path(self) -> str:
        """Generate file path for session"""
        return os.path.join(self.SESSIONS_DIR, f"{self.session_date}.json")

    # === Memory CRUD Operations ===

    def get(self, key: str):
        """
        Get value from memory with dotted path support.

        Supports legacy keys for backward compatibility:
            get("state") -> memory.agent_state.state
            get("plan") -> memory.agent_state.plan
            get("questions") -> memory.agent_state.questions
            get("history") -> conversation in OpenAI format

        Also supports new dotted paths:
            get("agent_state.state")
            get("metadata.session_id")
        """
        # Map legacy keys to new structure
        key_mapping = {
            "state": "agent_state.state",
            "plan": "agent_state.plan",
            "questions": "agent_state.questions",
            "history": "conversation",
        }

        actual_key = key_mapping.get(key, key)
        parts = actual_key.split(".")

        value = self.memory
        for part in parts:
            value = getattr(value, part)

        # Special case: convert conversation to OpenAI format for backwards compat
        if key == "history":
            return value.to_openai_format()

        return value

    def set(self, key: str, value):
        """
        Set value in memory and auto-save.

        Examples:
            set("state", State.questions)
            set("plan", plan_object)
            set("questions", questions_list)
        """
        # Map legacy keys to new structure
        key_mapping = {
            "state": "agent_state.state",
            "plan": "agent_state.plan",
            "questions": "agent_state.questions",
        }

        actual_key = key_mapping.get(key, key)
        parts = actual_key.split(".")

        # Navigate to parent object
        obj = self.memory
        for part in parts[:-1]:
            obj = getattr(obj, part)

        # Set the value
        setattr(obj, parts[-1], value)

        # Update timestamp and save
        self.memory.update_timestamp()
        self._save()

    # === Conversation Helpers ===

    def add_user_message(self, content: str):
        """Add user message to conversation and save"""
        self.memory.conversation.add_user(content)
        self.memory.increment_user_messages()
        self._save()

    def add_assistant_summary(self, summary: str):
        """Add concise assistant response to conversation and save"""
        self.memory.conversation.add_assistant(summary)
        self._save()

    def add_system_prompt(self, prompt: str):
        """Add system prompt (typically only at initialization)"""
        self.memory.conversation.add_system(prompt)
        self._save()

    # === Persistence ===

    def _create_fresh_memory(self) -> Memory:
        """Create new memory instance"""
        metadata = SessionMetadata(session_id=self.session_date)
        agent_state = AgentState()
        conversation = ConversationHistory()

        # Add system prompt
        conversation.add_system(SYSTEM_PROMPT)

        return Memory(
            metadata=metadata, agent_state=agent_state, conversation=conversation
        )

    def _save(self):
        """Save session to disk (atomic write)"""
        try:
            # Ensure directory exists
            os.makedirs(self.SESSIONS_DIR, exist_ok=True)

            # Prepare data - use model_dump with mode='json' for datetime serialization
            data = self.memory.model_dump(mode="json")

            # Atomic write: write to temp file, then rename
            temp_path = self.session_path + ".tmp"
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2)

            os.replace(temp_path, self.session_path)
            logger.debug(f"Saved session to {self.session_path}")

        except IOError as e:
            logger.error(f"Failed to save session: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving session: {e}")

    def _load_session(self) -> Memory:
        """Load session from disk"""
        try:
            with open(self.session_path, "r") as f:
                data = json.load(f)

            memory = Memory.model_validate(data)
            logger.info(f"Loaded session from {self.session_path}")
            return memory

        except json.JSONDecodeError as e:
            logger.error(f"Corrupted session file: {e}")
            self._handle_corrupted_session()
            return self._create_fresh_memory()

        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return self._create_fresh_memory()

    def _handle_corrupted_session(self):
        """Rename corrupted session file"""
        corrupted_path = self.session_path + ".corrupted"
        try:
            os.rename(self.session_path, corrupted_path)
            logger.warning(f"Renamed corrupted session to {corrupted_path}")
        except Exception as e:
            logger.error(f"Failed to rename corrupted session: {e}")

    # === User Profile Management ===

    def _load_user_profile(self) -> UserProfile:
        """Load user profile from disk, or create default"""
        if os.path.exists(self.USER_PROFILE_PATH):
            try:
                with open(self.USER_PROFILE_PATH, "r") as f:
                    data = json.load(f)
                logger.info(f"Loaded user profile from {self.USER_PROFILE_PATH}")
                return UserProfile.model_validate(data)
            except Exception as e:
                logger.error(f"Failed to load user profile: {e}")
                return UserProfile()
        else:
            # Create default profile
            logger.info("Creating default user profile")
            profile = UserProfile()
            self._save_user_profile(profile)
            return profile

    def _save_user_profile(self, profile: UserProfile):
        """Save user profile to disk"""
        try:
            profile.last_updated = datetime.now()
            data = profile.model_dump(mode="json")
            with open(self.USER_PROFILE_PATH, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved user profile to {self.USER_PROFILE_PATH}")
        except Exception as e:
            logger.error(f"Failed to save user profile: {e}")

    def update_user_profile(self, **kwargs):
        """Update user profile fields"""
        for key, value in kwargs.items():
            if hasattr(self.user_profile, key):
                setattr(self.user_profile, key, value)
        self._save_user_profile(self.user_profile)

    # === Utility Methods ===

    def get_session_info(self) -> dict:
        """Get session metadata for display"""
        return {
            "session_id": self.memory.metadata.session_id,
            "created_at": self.memory.metadata.created_at,
            "last_updated": self.memory.metadata.last_updated,
            "state": self.memory.agent_state.state.value,
            "num_llm_calls": self.memory.metadata.num_llm_calls,
            "num_messages": len(self.memory.conversation.messages),
        }

    @staticmethod
    def list_sessions() -> list[dict]:
        """List all available sessions"""
        sessions = []
        sessions_dir = AgentMemory.SESSIONS_DIR

        if not os.path.exists(sessions_dir):
            return sessions

        for filename in os.listdir(sessions_dir):
            if filename.endswith(".json") and not filename.endswith(".corrupted"):
                filepath = os.path.join(sessions_dir, filename)
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)

                    sessions.append(
                        {
                            "session_id": data["metadata"]["session_id"],
                            "created_at": data["metadata"]["created_at"],
                            "last_updated": data["metadata"]["last_updated"],
                            "state": data["agent_state"]["state"],
                            "has_plan": data["agent_state"]["plan"] is not None,
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to read session {filename}: {e}")

        # Sort by session_id (date) descending
        sessions.sort(key=lambda x: x["session_id"], reverse=True)
        return sessions
