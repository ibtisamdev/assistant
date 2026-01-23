"""Tests for JSONStorage - async JSON file storage."""


import pytest

from src.application.config import StorageConfig
from src.domain.models.planning import ScheduleItem
from src.domain.models.state import State
from src.domain.models.template import DayTemplate
from src.infrastructure.storage.json_storage import JSONStorage
from tests.conftest import MemoryFactory, PlanFactory, UserProfileFactory


class TestJSONStorageInitialization:
    """Test JSONStorage initialization."""

    def test_init_creates_directories(self, temp_dir):
        """Test that init creates required directories."""
        config = StorageConfig(
            sessions_dir=temp_dir / "sessions",
            profiles_dir=temp_dir / "profiles",
            templates_dir=temp_dir / "templates",
        )

        storage = JSONStorage(config)

        assert storage.sessions_dir.exists()
        assert storage.profiles_dir.exists()
        assert storage.templates_dir.exists()

    def test_init_with_existing_directories(self, temp_dir):
        """Test init with existing directories doesn't raise."""
        sessions_dir = temp_dir / "sessions"
        sessions_dir.mkdir()

        config = StorageConfig(
            sessions_dir=sessions_dir,
            profiles_dir=temp_dir / "profiles",
            templates_dir=temp_dir / "templates",
        )

        storage = JSONStorage(config)

        assert storage.sessions_dir == sessions_dir


class TestSessionOperations:
    """Tests for session CRUD operations."""

    @pytest.fixture
    def storage(self, temp_dir):
        """Create storage instance."""
        config = StorageConfig(
            sessions_dir=temp_dir / "sessions",
            profiles_dir=temp_dir / "profiles",
            templates_dir=temp_dir / "templates",
        )
        return JSONStorage(config)

    @pytest.mark.asyncio
    async def test_save_session(self, storage):
        """Test saving a session."""
        memory = MemoryFactory.create(session_id="2026-01-23")

        await storage.save_session("2026-01-23", memory)

        # Verify file exists
        path = storage.sessions_dir / "2026-01-23.json"
        assert path.exists()

    @pytest.mark.asyncio
    async def test_save_and_load_session(self, storage):
        """Test saving and loading a session."""
        memory = MemoryFactory.create(session_id="2026-01-23")
        memory.agent_state.plan = PlanFactory.create()

        await storage.save_session("2026-01-23", memory)
        loaded = await storage.load_session("2026-01-23")

        assert loaded is not None
        assert loaded.metadata.session_id == "2026-01-23"
        assert loaded.agent_state.plan is not None

    @pytest.mark.asyncio
    async def test_load_nonexistent_session(self, storage):
        """Test loading a session that doesn't exist."""
        result = await storage.load_session("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_save_overwrites_existing(self, storage):
        """Test that saving overwrites existing session."""
        memory1 = MemoryFactory.create(session_id="2026-01-23")
        memory2 = MemoryFactory.create(session_id="2026-01-23")
        memory2.agent_state.state = State.done
        memory2.agent_state.plan = PlanFactory.create()

        await storage.save_session("2026-01-23", memory1)
        await storage.save_session("2026-01-23", memory2)

        loaded = await storage.load_session("2026-01-23")
        assert loaded.agent_state.state == State.done

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, storage):
        """Test listing sessions when none exist."""
        result = await storage.list_sessions()

        assert result == []

    @pytest.mark.asyncio
    async def test_list_sessions(self, storage):
        """Test listing multiple sessions."""
        for date in ["2026-01-20", "2026-01-21", "2026-01-22"]:
            memory = MemoryFactory.create(session_id=date)
            await storage.save_session(date, memory)

        result = await storage.list_sessions()

        assert len(result) == 3
        session_ids = [s["session_id"] for s in result]
        assert "2026-01-20" in session_ids
        assert "2026-01-21" in session_ids
        assert "2026-01-22" in session_ids

    @pytest.mark.asyncio
    async def test_list_sessions_sorted_descending(self, storage):
        """Test that sessions are sorted by date descending."""
        for date in ["2026-01-20", "2026-01-22", "2026-01-21"]:
            memory = MemoryFactory.create(session_id=date)
            await storage.save_session(date, memory)

        result = await storage.list_sessions()

        session_ids = [s["session_id"] for s in result]
        assert session_ids == ["2026-01-22", "2026-01-21", "2026-01-20"]

    @pytest.mark.asyncio
    async def test_delete_session(self, storage):
        """Test deleting a session."""
        memory = MemoryFactory.create(session_id="2026-01-23")
        await storage.save_session("2026-01-23", memory)

        result = await storage.delete_session("2026-01-23")

        assert result is True
        assert await storage.load_session("2026-01-23") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, storage):
        """Test deleting a session that doesn't exist."""
        result = await storage.delete_session("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_atomic_save(self, storage):
        """Test that saves are atomic (uses temp file)."""
        memory = MemoryFactory.create(session_id="2026-01-23")
        memory.agent_state.plan = PlanFactory.create()

        await storage.save_session("2026-01-23", memory)

        # No temp file should remain
        temp_path = storage.sessions_dir / "2026-01-23.tmp"
        assert not temp_path.exists()

        # Main file should exist
        main_path = storage.sessions_dir / "2026-01-23.json"
        assert main_path.exists()


class TestCorruptionRecovery:
    """Tests for corruption handling."""

    @pytest.fixture
    def storage(self, temp_dir):
        """Create storage instance."""
        config = StorageConfig(
            sessions_dir=temp_dir / "sessions",
            profiles_dir=temp_dir / "profiles",
            templates_dir=temp_dir / "templates",
        )
        return JSONStorage(config)

    @pytest.mark.asyncio
    async def test_load_corrupted_json(self, storage):
        """Test loading a corrupted JSON file."""
        # Create a corrupted file
        path = storage.sessions_dir / "corrupted.json"
        path.write_text("{ invalid json")

        result = await storage.load_session("corrupted")

        assert result is None

    @pytest.mark.asyncio
    async def test_corrupted_file_renamed(self, storage):
        """Test that corrupted files are renamed."""
        # Create a corrupted file
        path = storage.sessions_dir / "corrupted.json"
        path.write_text("{ invalid json")

        await storage.load_session("corrupted")

        # Original file should be renamed
        corrupted_files = list(storage.sessions_dir.glob("*.corrupted.*.json"))
        assert len(corrupted_files) == 1


class TestProfileOperations:
    """Tests for profile CRUD operations."""

    @pytest.fixture
    def storage(self, temp_dir):
        """Create storage instance."""
        config = StorageConfig(
            sessions_dir=temp_dir / "sessions",
            profiles_dir=temp_dir / "profiles",
            templates_dir=temp_dir / "templates",
        )
        return JSONStorage(config)

    @pytest.mark.asyncio
    async def test_save_and_load_profile(self, storage):
        """Test saving and loading a profile."""
        profile = UserProfileFactory.create()

        await storage.save_profile("test_user", profile)
        loaded = await storage.load_profile("test_user")

        assert loaded is not None
        assert loaded.user_id == profile.user_id

    @pytest.mark.asyncio
    async def test_load_nonexistent_profile_creates_default(self, storage):
        """Test loading nonexistent profile creates default."""
        result = await storage.load_profile("new_user")

        assert result is not None
        assert result.user_id == "new_user"

        # Verify it was saved
        loaded_again = await storage.load_profile("new_user")
        assert loaded_again is not None


class TestTemplateOperations:
    """Tests for template CRUD operations."""

    @pytest.fixture
    def storage(self, temp_dir):
        """Create storage instance."""
        config = StorageConfig(
            sessions_dir=temp_dir / "sessions",
            profiles_dir=temp_dir / "profiles",
            templates_dir=temp_dir / "templates",
        )
        return JSONStorage(config)

    @pytest.fixture
    def sample_template(self):
        """Create a sample template."""
        return DayTemplate(
            name="Workday",
            description="Standard workday template",
            schedule=[
                ScheduleItem(time="09:00-12:00", task="Deep work"),
                ScheduleItem(time="14:00-17:00", task="Meetings"),
            ],
            priorities=["Complete project", "Review PRs"],
        )

    @pytest.mark.asyncio
    async def test_save_and_load_template(self, storage, sample_template):
        """Test saving and loading a template."""
        await storage.save_template("workday", sample_template)
        loaded = await storage.load_template("workday")

        assert loaded is not None
        assert loaded.name == "Workday"
        assert len(loaded.schedule) == 2

    @pytest.mark.asyncio
    async def test_load_nonexistent_template(self, storage):
        """Test loading nonexistent template."""
        result = await storage.load_template("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_templates(self, storage, sample_template):
        """Test listing templates."""
        await storage.save_template("workday", sample_template)

        template2 = DayTemplate(
            name="Weekend",
            description="Weekend template",
            schedule=[],
            priorities=[],
        )
        await storage.save_template("weekend", template2)

        result = await storage.list_templates()

        assert len(result) == 2
        names = [t.name for t in result]
        assert "Workday" in names or "workday" in [t.name.lower() for t in result]

    @pytest.mark.asyncio
    async def test_delete_template(self, storage, sample_template):
        """Test deleting a template."""
        await storage.save_template("workday", sample_template)

        result = await storage.delete_template("workday")

        assert result is True
        assert await storage.load_template("workday") is None

    @pytest.mark.asyncio
    async def test_template_exists(self, storage, sample_template):
        """Test checking if template exists."""
        assert await storage.template_exists("workday") is False

        await storage.save_template("workday", sample_template)

        assert await storage.template_exists("workday") is True

    @pytest.mark.asyncio
    async def test_template_name_sanitization(self, storage, sample_template):
        """Test that template names are sanitized for filenames."""
        sample_template.name = "My Special Template!"
        await storage.save_template("My Special Template!", sample_template)

        # Should be able to load with sanitized name
        loaded = await storage.load_template("My Special Template!")
        assert loaded is not None

        # Check the actual filename
        files = list(storage.templates_dir.glob("*.json"))
        assert len(files) == 1
        # Should not contain special characters
        assert "!" not in files[0].name


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture
    def storage(self, temp_dir):
        """Create storage instance."""
        config = StorageConfig(
            sessions_dir=temp_dir / "sessions",
            profiles_dir=temp_dir / "profiles",
            templates_dir=temp_dir / "templates",
        )
        return JSONStorage(config)

    @pytest.mark.asyncio
    async def test_list_sessions_ignores_tmp_files(self, storage):
        """Test that tmp files are ignored in listing."""
        # Create a valid session
        memory = MemoryFactory.create(session_id="2026-01-23")
        await storage.save_session("2026-01-23", memory)

        # Create a tmp file
        tmp_path = storage.sessions_dir / "2026-01-24.tmp"
        tmp_path.write_text("{}")

        result = await storage.list_sessions()

        assert len(result) == 1
        assert result[0]["session_id"] == "2026-01-23"

    @pytest.mark.asyncio
    async def test_list_sessions_ignores_corrupted_files(self, storage):
        """Test that corrupted files are ignored in listing."""
        # Create a valid session
        memory = MemoryFactory.create(session_id="2026-01-23")
        await storage.save_session("2026-01-23", memory)

        # Create a corrupted backup file
        corrupted_path = storage.sessions_dir / "corrupted.corrupted.20260124.json"
        corrupted_path.write_text("{}")

        result = await storage.list_sessions()

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_delete_template_nonexistent(self, storage):
        """Test deleting a template that doesn't exist."""
        result = await storage.delete_template("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_load_profile_handles_corrupted_json(self, storage):
        """Test loading a profile with corrupted JSON returns None."""
        path = storage.profiles_dir / "corrupted.json"
        path.write_text("{ invalid json")

        result = await storage.load_profile("corrupted")

        # Should return None for corrupted profile
        assert result is None

    @pytest.mark.asyncio
    async def test_load_template_handles_corrupted_json(self, storage):
        """Test loading a template with corrupted JSON."""
        path = storage.templates_dir / "corrupted.json"
        path.write_text("{ invalid json")

        result = await storage.load_template("corrupted")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_templates_empty(self, storage):
        """Test listing templates when none exist."""
        result = await storage.list_templates()

        assert result == []

    @pytest.mark.asyncio
    async def test_list_templates_ignores_corrupted_files(self, storage):
        """Test that corrupted templates are skipped in listing."""
        # Create a valid template
        template = DayTemplate(
            name="Valid",
            description="Valid template",
            schedule=[],
            priorities=[],
        )
        await storage.save_template("valid", template)

        # Create a corrupted template file
        corrupted_path = storage.templates_dir / "corrupted.json"
        corrupted_path.write_text("{ invalid")

        result = await storage.list_templates()

        # Should only have the valid template
        assert len(result) == 1
        assert result[0].name == "Valid"
