import os
import re
import json
import time
import shutil
import logging
from datetime import datetime
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

        # Clean up stale temp files
        self._cleanup_temp_files()

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
        """Save session to disk (atomic write) with comprehensive error handling"""
        try:
            # Ensure directory exists
            os.makedirs(self.SESSIONS_DIR, exist_ok=True)

            # Check disk space (basic heuristic - at least 1MB free)
            try:
                stat = shutil.disk_usage(self.SESSIONS_DIR)
                if stat.free < 1024 * 1024:  # Less than 1MB free
                    logger.error("Low disk space! Cannot save session.")
                    print("\n  WARNING: Low disk space - session may not be saved!")
                    return
            except Exception as e:
                logger.warning(f"Could not check disk space: {e}")

            # Prepare data - use model_dump with mode='json' for datetime serialization
            data = self.memory.model_dump(mode="json")

            # Atomic write: write to temp file, then rename
            temp_path = self.session_path + ".tmp"
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2)

            os.replace(temp_path, self.session_path)
            logger.debug(f"Saved session to {self.session_path}")

        except PermissionError:
            logger.error(f"Permission denied writing to {self.session_path}")
            print(f"\n  WARNING: Cannot save session - permission denied")
            print(f"   Check file permissions: {self.session_path}")

        except OSError as e:
            if e.errno == 28:  # ENOSPC - No space left on device
                logger.error("Disk full! Cannot save session.")
                print("\n  WARNING: Disk full - session cannot be saved!")
            else:
                logger.error(f"OS error saving session: {e}")
                print(f"\n  WARNING: Failed to save session: {e}")

        except IOError as e:
            logger.error(f"I/O error saving session: {e}")
            print(f"\n  WARNING: Failed to save session: {e}")

        except Exception as e:
            logger.error(f"Unexpected error saving session: {e}")
            print(f"\n  WARNING: Failed to save session: {e}")

    def _load_session(self) -> Memory:
        """Load session from disk with validation and recovery"""
        try:
            with open(self.session_path, "r") as f:
                data = json.load(f)

            memory = Memory.model_validate(data)

            # Validate timestamp consistency
            if not memory.validate_timestamps():
                # Timestamps were corrected, save the fix
                self.memory = memory
                self._save()
                logger.info("Fixed corrupted timestamps during load")

            logger.info(f"Loaded session from {self.session_path}")
            return memory

        except json.JSONDecodeError as e:
            logger.error(f"Corrupted session file (invalid JSON): {e}")
            return self._handle_corrupted_session_with_recovery()

        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return self._handle_corrupted_session_with_recovery()

    def _handle_corrupted_session_with_recovery(self) -> Memory:
        """
        Handle corrupted session with user notification and recovery attempt.
        Returns either recovered partial data or fresh memory.
        """
        print("\n  WARNING: Session file is corrupted!")
        print(f"   File: {self.session_path}")

        # Try to read raw content for partial recovery
        partial_data = self._attempt_partial_recovery()

        if partial_data:
            print("   Recovered some data from corrupted file")

            # Create fresh memory but preserve conversation history if possible
            memory = self._create_fresh_memory()

            if "conversation" in partial_data:
                try:
                    # Restore conversation if possible
                    memory.conversation = ConversationHistory.model_validate(
                        partial_data["conversation"]
                    )
                    logger.info("Recovered conversation history")
                    print("     - Conversation history was preserved")
                except Exception as e:
                    logger.error(f"Could not recover conversation history: {e}")
                    print("     - Could not recover conversation history")

            # Try to recover plan
            if "agent_state" in partial_data and partial_data["agent_state"].get(
                "plan"
            ):
                try:
                    from models import Plan

                    memory.agent_state.plan = Plan.model_validate(
                        partial_data["agent_state"]["plan"]
                    )
                    logger.info("Recovered plan")
                    print("     - Plan was preserved")
                except Exception as e:
                    logger.error(f"Could not recover plan: {e}")

            print("     - Starting with fresh state machine\n")

            # Rename corrupted file
            self._rename_corrupted_session()
            return memory
        else:
            print("   Could not recover any data")
            print("     - Creating fresh session\n")
            self._rename_corrupted_session()
            return self._create_fresh_memory()

    def _attempt_partial_recovery(self) -> Optional[dict]:
        """
        Attempt to extract partial data from corrupted JSON.
        Returns dict with any recoverable data, or None.
        """
        try:
            with open(self.session_path, "r") as f:
                content = f.read()

            # Strategy 1: Try to parse even with trailing commas (common JSON corruption)
            content_fixed = re.sub(r",\s*}", "}", content)
            content_fixed = re.sub(r",\s*]", "]", content_fixed)

            try:
                return json.loads(content_fixed)
            except json.JSONDecodeError:
                pass

            # Strategy 2: Try to find and extract just the conversation
            conversation_match = re.search(
                r'"conversation"\s*:\s*(\{[^}]*"messages"\s*:\s*\[[^\]]*\][^}]*\})',
                content,
                re.DOTALL,
            )

            if conversation_match:
                try:
                    conv_json = conversation_match.group(1)
                    return {"conversation": json.loads(conv_json)}
                except Exception:
                    pass

            # Strategy 3: Try to extract any valid JSON objects
            try:
                # Find the outermost braces
                start = content.find("{")
                end = content.rfind("}")
                if start != -1 and end != -1 and end > start:
                    potential_json = content[start : end + 1]
                    return json.loads(potential_json)
            except Exception:
                pass

            return None

        except Exception as e:
            logger.error(f"Partial recovery failed: {e}")
            return None

    def _rename_corrupted_session(self):
        """Rename corrupted session with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        corrupted_path = f"{self.session_path}.corrupted.{timestamp}"

        try:
            os.rename(self.session_path, corrupted_path)
            logger.warning(f"Renamed corrupted session to {corrupted_path}")
            print(f"   Corrupted file saved as: {os.path.basename(corrupted_path)}")
        except Exception as e:
            logger.error(f"Failed to rename corrupted session: {e}")

    def _cleanup_temp_files(self):
        """Remove any stale .tmp files from sessions directory"""
        try:
            if not os.path.exists(self.SESSIONS_DIR):
                return

            for filename in os.listdir(self.SESSIONS_DIR):
                if filename.endswith(".tmp"):
                    tmp_path = os.path.join(self.SESSIONS_DIR, filename)
                    try:
                        # Check file age - only delete if > 1 hour old
                        file_age = time.time() - os.path.getmtime(tmp_path)
                        if file_age > 3600:  # 1 hour
                            os.remove(tmp_path)
                            logger.info(f"Cleaned up stale temp file: {filename}")
                    except Exception as e:
                        logger.error(f"Failed to cleanup {filename}: {e}")

        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")

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
                print(
                    f"\n  Warning: Could not load user profile ({e}). Using defaults."
                )
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
                # Skip .tmp files too
                if filename.endswith(".tmp"):
                    continue

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
