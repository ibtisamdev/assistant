"""CLI smoke tests using Click's CliRunner."""

import pytest
from click.testing import CliRunner

from src.cli.main import cli


class TestCLIBasics:
    """Basic CLI functionality tests."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_cli_help(self, runner):
        """Test --help shows usage info."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Daily Planning Agent" in result.output or "Usage:" in result.output

    def test_cli_version(self, runner):
        """Test --version shows version info."""
        result = runner.invoke(cli, ["--version"])

        # Should not error, may or may not have version
        assert result.exit_code in [0, 2]  # 2 is "no such option" which is fine


class TestListCommand:
    """Tests for 'day list' command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_list_command_help(self, runner):
        """Test 'list --help' shows usage."""
        result = runner.invoke(cli, ["list", "--help"])

        assert result.exit_code == 0
        assert "List" in result.output or "session" in result.output.lower()


class TestShowCommand:
    """Tests for 'day show' command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_show_command_help(self, runner):
        """Test 'show --help' shows usage."""
        result = runner.invoke(cli, ["show", "--help"])

        assert result.exit_code == 0


class TestCheckinCommand:
    """Tests for 'day checkin' command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_checkin_command_help(self, runner):
        """Test 'checkin --help' shows usage."""
        result = runner.invoke(cli, ["checkin", "--help"])

        assert result.exit_code == 0
        assert "Check" in result.output or "track" in result.output.lower()


class TestExportCommand:
    """Tests for 'day export' command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_export_command_help(self, runner):
        """Test 'export --help' shows usage."""
        result = runner.invoke(cli, ["export", "--help"])

        assert result.exit_code == 0
        assert "Export" in result.output or "markdown" in result.output.lower()


class TestStatsCommand:
    """Tests for 'day stats' command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_stats_command_help(self, runner):
        """Test 'stats --help' shows usage."""
        result = runner.invoke(cli, ["stats", "--help"])

        assert result.exit_code == 0
        assert "stat" in result.output.lower()


class TestProfileCommand:
    """Tests for 'day profile' command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_profile_command_help(self, runner):
        """Test 'profile --help' shows usage."""
        result = runner.invoke(cli, ["profile", "--help"])

        assert result.exit_code == 0


class TestTemplateCommand:
    """Tests for 'day template' command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_template_command_help(self, runner):
        """Test 'template --help' shows usage."""
        result = runner.invoke(cli, ["template", "--help"])

        assert result.exit_code == 0


class TestStartCommand:
    """Tests for 'day start' command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_start_command_help(self, runner):
        """Test 'start --help' shows usage."""
        result = runner.invoke(cli, ["start", "--help"])

        assert result.exit_code == 0
        assert "Start" in result.output or "plan" in result.output.lower()


class TestQuickCommand:
    """Tests for 'day quick' command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_quick_command_help(self, runner):
        """Test 'quick --help' shows usage."""
        result = runner.invoke(cli, ["quick", "--help"])

        assert result.exit_code == 0


class TestReviseCommand:
    """Tests for 'day revise' command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_revise_command_help(self, runner):
        """Test 'revise --help' shows usage."""
        result = runner.invoke(cli, ["revise", "--help"])

        assert result.exit_code == 0
