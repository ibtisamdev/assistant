# V1.0.0 Release Checklist

This document tracks everything needed to release v1.0.0 to production.

## Release Decisions

| Decision | Choice |
|----------|--------|
| Distribution | PyPI + GitHub Releases |
| Package name | `planmyday` |
| CLI commands | `pday` (primary) + `planmyday` (alias) |
| LLM support | OpenAI only for v1.0 |
| Setup UX | Interactive `pday setup` wizard |
| Data storage | Global (`~/.local/share/planmyday/`) |
| Config location | Global (`~/.config/planmyday/`) |
| License | MIT |

---

## Phase 1: Testing & Quality Gates ✅ COMPLETE

**Goal:** Achieve production-quality test coverage and pass all quality checks.

**Status:** Completed 2026-01-23

### Test Infrastructure
- [x] Create `tests/conftest.py` with shared fixtures (MockLLMProvider, MockStorage, factories)
- [x] Configure coverage omit for presentation-layer code (CLI, formatters, interactive use cases)
- [x] Configure ruff and mypy in `pyproject.toml`
- [x] Add pre-commit hooks (ruff lint + format with auto-fix)

### Unit Tests - Completed (381 tests total)

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_agent_service.py` | 29 | 95% |
| `test_planning_service.py` | 31 | 96% |
| `test_models.py` | 21 | 93% |
| `test_create_plan.py` | 12 | Use case init |
| `test_checkin.py` | 17 | Use case logic |
| `test_use_cases.py` | 14 | Various |
| `test_json_storage.py` | 29 | 83% |
| `test_openai_provider.py` | 14 | 87% |
| `test_retry.py` | 22 | 100% |
| `test_cache.py` | 14 | 100% |
| `test_container.py` | 14 | 88% |
| `test_session_orchestrator.py` | 10 | 100% |

### Integration Tests
- [x] Full planning workflow (goal → questions → plan → feedback → done)
- [x] Session persistence (create, save, reload, continue)
- [x] Time tracking workflow (checkin → progress → summary)
- [x] Export workflow (session → markdown file)

### CLI Smoke Tests
- [x] `pday --help` - main help
- [x] `pday start --help` - start help
- [x] `pday list --help` - list help
- [x] `pday show --help` - show help
- [x] `pday checkin --help` - checkin help
- [x] `pday export --help` - export help
- [x] `pday profile --help` - profile help
- [x] `pday stats --help` - stats help
- [x] `pday template --help` - template help
- [x] `pday setup --help` - configuration wizard

### Quality Gates (All Passing)
- [x] Unit test coverage ≥ 80% → **89% achieved**
- [x] All tests pass (100%) → **381 passed**
- [x] No ruff lint errors (`ruff check .`) → **All checks passed**
- [x] No mypy type errors (`mypy .`) → **Success: no issues in 64 source files**

---

## Phase 2: CI/CD Pipeline ✅ COMPLETE

**Goal:** Automated testing and release process.

**Status:** Completed 2026-01-23

### GitHub Actions Workflows
- [x] `.github/workflows/test.yml` - Run tests on every PR/push
  - Python 3.12
  - Run pytest with coverage
  - Run ruff lint
  - Run mypy type check
  - Codecov deferred (not needed for v1.0)
- [x] `.github/workflows/release.yml` - Publish to PyPI on release
  - Triggered by GitHub release creation
  - Build wheel and sdist using uv
  - Publish to PyPI using trusted publishing

### Badges for README
- [x] CI status badge
- [ ] Coverage badge (deferred - no Codecov)
- [ ] PyPI version badge (after first release)
- [x] Python version badge (already existed)

---

## Phase 3: Distribution Preparation ✅ COMPLETE

**Goal:** Package ready for PyPI and user-friendly installation.

**Status:** Completed 2026-01-23

### Package Naming
- [x] Decide final package name: `planmyday`
- [x] Update `pyproject.toml` with new name
- [x] Update CLI entry points: `pday` + `planmyday`
- [x] Update all documentation references

### Package Metadata (`pyproject.toml`)
- [x] Add `authors` field
- [x] Add `license` field
- [x] Add `keywords` for discoverability
- [x] Add `classifiers` (Development Status, License, OS, Python version)
- [x] Add `urls` (Homepage, Repository, Documentation, Bug Tracker)
- [x] Update `description` for PyPI listing
- [x] Verify `readme = "README.md"` renders correctly

### License
- [x] Create `LICENSE` file with MIT license text
- [ ] Add license header to key source files (optional - deferred)

### First-Time Setup Experience
- [x] Implement `pday setup` command
  - Prompt for OpenAI API key
  - Validate API key format
  - Save to `~/.config/planmyday/.env`
  - Create data directories
  - Show success message with next steps
- [x] Auto-detect missing config and prompt to run setup
- [x] Add `pday config` command to view configuration

### Global Data Storage
- [x] Default sessions directory: `~/.local/share/planmyday/sessions/`
- [x] Default profiles directory: `~/.local/share/planmyday/profiles/`
- [x] Default templates directory: `~/.local/share/planmyday/templates/`
- [x] Default exports directory: `~/.local/share/planmyday/exports/`
- [x] Config location: `~/.config/planmyday/`
- [x] Support `--local` flag to use current directory (dev mode)
- [x] Follow XDG Base Directory spec

---

## Phase 4: Documentation ✅ COMPLETE

**Goal:** Production-ready documentation for users.

**Status:** Completed 2026-01-23

### README Updates
- [x] Update title and branding to planmyday
- [x] Add installation instructions (`pip install planmyday`)
- [x] Add quick start guide (setup → first plan)
- [x] Update all command examples to use `pday`
- [x] Add badges (CI, Python version, License)

### Other Documentation
- [x] Update `AGENTS.md` with new global paths
- [x] Update `docs/configuration.md` with new config location
- [x] Update `docs/user-profiles.md` with new commands
- [x] Update `CHANGELOG.md` with rename entry
- [x] Update `ROADMAP.md` with new commands

---

## Phase 5: Pre-Release Validation ✅ COMPLETE

**Goal:** Verify everything works before public release.

**Status:** Completed 2026-01-23

### Automated Validation Script
- [x] Created `scripts/validate-release.sh` for repeatable testing
- [x] Builds package, creates fresh venv, installs wheel
- [x] Tests all CLI entry points and help commands
- [x] Verifies error handling and package metadata
- [x] All 43 automated checks pass

### Local Wheel Testing (Test PyPI skipped)
- [x] Build package: `uv build`
- [x] Install wheel in fresh Python 3.12 venv
- [x] Verify both `pday` and `planmyday` commands work
- [x] Verify all dependencies installed correctly

### Fresh Environment Testing
- [x] Test on fresh Python 3.12 virtual environment
- [x] Test on macOS (primary development platform)
- [x] Test on Linux via GitHub Actions CI (ubuntu-latest)

### User Experience Review
- [x] Verify error messages are user-friendly
- [x] Verify `--help` output is clear and complete
- [x] Verify `pday setup` wizard works smoothly
- [x] Missing config shows clear "Setup Required" message

---

## Pre-Release Setup (One-Time)

Before the first release, these manual setup steps must be completed:

### PyPI Trusted Publishing

Configure PyPI to accept releases from GitHub Actions (no API token needed):

1. Go to https://pypi.org/manage/account/publishing/
2. Click "Add a new pending publisher"
3. Fill in:
   - **PyPI Project Name:** `planmyday`
   - **Owner:** `ibtisamdev`
   - **Repository:** `planmyday`
   - **Workflow name:** `release.yml`
   - **Environment name:** (leave blank)
4. Click "Add"

**Note:** This must be done before creating the first GitHub release, otherwise the publish step will fail.

### GitHub Repository Settings

1. Rename repository from `assistant` to `planmyday`
2. Update repository description
3. Optionally create `pypi` environment for deployment protection

---

## Phase 6: Release

**Goal:** Ship v1.0.0!

### Version Bump
- [ ] Update version in `pyproject.toml` to `1.0.0`
- [ ] Update version in `src/cli/main.py` to `1.0.0`
- [ ] Update CHANGELOG.md with v1.0.0 release notes

### GitHub Release
- [ ] Create git tag: `git tag v1.0.0`
- [ ] Push tag: `git push origin v1.0.0`
- [ ] Create GitHub Release with:
  - Release title: `v1.0.0 - Initial Production Release`
  - Release notes from CHANGELOG.md
  - Auto-generated contributor list

### PyPI Release
- [ ] Verify GitHub Actions publishes to PyPI automatically
- [ ] Or manually: `twine upload dist/*`
- [ ] Verify package page on pypi.org
- [ ] Test `pip install planmyday` from PyPI

### Post-Release
- [ ] Announce release (Twitter, Reddit, Hacker News, etc.)
- [ ] Monitor for issues/feedback
- [ ] Update ROADMAP.md with post-v1.0 plans

---

## Estimated Timeline

| Phase | Effort | Estimate | Status |
|-------|--------|----------|--------|
| Phase 1: Testing & Quality | High | 3-5 days | ✅ Complete |
| Phase 2: CI/CD Pipeline | Low | 1 day | ✅ Complete |
| Phase 3: Distribution Prep | Medium | 2-3 days | ✅ Complete |
| Phase 4: Documentation | Low | 0.5 day | ✅ Complete |
| Phase 5: Pre-Release Validation | Low | 0.5 day | ✅ Complete |
| Phase 6: Release | Low | 0.5 day | ⏳ Next |
| **Total** | | **7-10 days** | ~95% done |

---

## Quick Reference: Commands

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src --cov-report=html

# Check linting
ruff check .

# Check types
mypy .

# Build package
uv build

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*

# Test the CLI
pday --help
pday setup
pday start
```

---

## Notes

- **Repository rename:** GitHub repo should be renamed from `assistant` to `planmyday` before release.
- **Python version:** Requires Python 3.12+ (uses modern typing features).
- **macOS/Linux only:** Windows support deferred to post-v1.0.
