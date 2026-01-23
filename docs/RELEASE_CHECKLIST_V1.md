# V1.0.0 Release Checklist

This document tracks everything needed to release v1.0.0 to production.

## Release Decisions

| Decision | Choice |
|----------|--------|
| Distribution | PyPI + GitHub Releases |
| Package name | TBD (avoiding `day` conflict on PyPI) |
| CLI command | TBD (same as package name) |
| LLM support | OpenAI only for v1.0 |
| Setup UX | Interactive `day setup` wizard |
| Data storage | Global (`~/.local/share/day/`) |
| Config location | Global (`~/.config/day/`) |
| License | MIT |

---

## Phase 1: Testing & Quality Gates ✅ COMPLETE

**Goal:** Achieve production-quality test coverage and pass all quality checks.

**Status:** Completed 2026-01-23

### Test Infrastructure
- [x] Create `tests/conftest.py` with shared fixtures (MockLLMProvider, MockStorage, factories)
- [x] Configure coverage omit for presentation-layer code (CLI, formatters, interactive use cases)
- [x] Configure ruff and mypy in `pyproject.toml`
- [ ] Add pre-commit hook for fast tests (optional - deferred to Phase 2)

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
- [x] `day --help` - main help
- [x] `day start --help` - start help
- [x] `day list --help` - list help
- [x] `day show --help` - show help
- [x] `day checkin --help` - checkin help
- [x] `day export --help` - export help
- [x] `day profile --help` - profile help
- [x] `day stats --help` - stats help
- [x] `day template --help` - template help
- [ ] `day setup --help` - configuration wizard (after implemented)

### Quality Gates (All Passing)
- [x] Unit test coverage ≥ 80% → **89% achieved**
- [x] All tests pass (100%) → **381 passed**
- [x] No ruff lint errors (`ruff check .`) → **All checks passed**
- [x] No mypy type errors (`mypy .`) → **Success: no issues in 64 source files**

---

## Phase 2: CI/CD Pipeline

**Goal:** Automated testing and release process.

### GitHub Actions Workflows
- [ ] `.github/workflows/test.yml` - Run tests on every PR/push
  - Python 3.12 matrix
  - Run pytest with coverage
  - Run ruff lint
  - Run mypy type check
  - Upload coverage to Codecov (optional)
- [ ] `.github/workflows/release.yml` - Publish to PyPI on release
  - Triggered by GitHub release creation
  - Build wheel and sdist
  - Publish to PyPI using trusted publishing

### Badges for README
- [ ] CI status badge
- [ ] Coverage badge (Codecov or shields.io)
- [ ] PyPI version badge
- [ ] Python version badge

---

## Phase 3: Distribution Preparation

**Goal:** Package ready for PyPI and user-friendly installation.

### Package Naming
- [ ] Decide final package name (check availability on PyPI)
- [ ] Update `pyproject.toml` with new name
- [ ] Update CLI entry point in `[project.scripts]`
- [ ] Update all documentation references

### Package Metadata (`pyproject.toml`)
- [ ] Add `authors` field
- [ ] Add `license` field
- [ ] Add `keywords` for discoverability
- [ ] Add `classifiers` (Development Status, License, OS, Python version)
- [ ] Add `urls` (Homepage, Repository, Documentation, Bug Tracker)
- [ ] Update `description` for PyPI listing
- [ ] Verify `readme = "README.md"` renders correctly

### License
- [ ] Create `LICENSE` file with MIT license text
- [ ] Add license header to key source files (optional)

### First-Time Setup Experience
- [ ] Implement `day setup` command
  - Prompt for OpenAI API key
  - Validate API key format and connectivity
  - Save to `~/.config/day/config.yaml`
  - Create data directories
  - Show success message with next steps
- [ ] Auto-detect missing config and prompt to run setup
- [ ] Add `day config` command to view/edit configuration

### Global Data Storage Migration
- [ ] Move default sessions directory to `~/.local/share/day/sessions/`
- [ ] Move default profiles directory to `~/.local/share/day/profiles/`
- [ ] Move default templates directory to `~/.local/share/day/templates/`
- [ ] Move default exports directory to `~/.local/share/day/exports/`
- [ ] Move config to `~/.config/day/config.yaml`
- [ ] Support `--local` flag to use current directory (backward compat)
- [ ] Add migration path for existing local data (optional)
- [ ] Follow XDG Base Directory spec for cross-platform support

---

## Phase 4: Documentation

**Goal:** Production-ready documentation for users.

### README Updates
- [ ] Remove development version warnings
- [ ] Add installation instructions (`pip install <package>`)
- [ ] Add quick start guide (setup → first plan)
- [ ] Update feature list (remove "Coming Soon" for shipped features)
- [ ] Add badges (CI, coverage, PyPI, Python version)
- [ ] Add GIF/screenshot of CLI in action (optional)

### Other Documentation
- [ ] Update `AGENTS.md` with new global paths
- [ ] Update `docs/configuration.md` with new config location
- [ ] Create `CONTRIBUTING.md` (optional for v1.0)
- [ ] Prepare release notes for CHANGELOG.md

---

## Phase 5: Pre-Release Validation

**Goal:** Verify everything works before public release.

### Test PyPI
- [ ] Build package: `uv build` or `python -m build`
- [ ] Upload to test.pypi.org: `twine upload --repository testpypi dist/*`
- [ ] Test installation: `pip install -i https://test.pypi.org/simple/ <package>`
- [ ] Verify CLI commands work

### Fresh Environment Testing
- [ ] Test on fresh Python 3.12 virtual environment
- [ ] Test on macOS
- [ ] Test on Linux (Ubuntu/Debian)
- [ ] Test on Windows (optional for v1.0)

### User Experience Review
- [ ] Verify error messages are user-friendly
- [ ] Verify `--help` output is clear and complete
- [ ] Verify `day setup` wizard works smoothly
- [ ] Test offline behavior (graceful error when no internet)

---

## Phase 6: Release

**Goal:** Ship v1.0.0!

### Version Bump
- [ ] Update version in `pyproject.toml` to `1.0.0`
- [ ] Update version badge in README
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
- [ ] Test `pip install <package>` from PyPI

### Post-Release
- [ ] Announce release (Twitter, Reddit, Hacker News, etc.)
- [ ] Monitor for issues/feedback
- [ ] Update ROADMAP.md with post-v1.0 plans

---

## Estimated Timeline

| Phase | Effort | Estimate | Status |
|-------|--------|----------|--------|
| Phase 1: Testing & Quality | High | 3-5 days | ✅ Complete |
| Phase 2: CI/CD Pipeline | Low | 1 day | ⏳ Next |
| Phase 3: Distribution Prep | Medium | 2-3 days | Pending |
| Phase 4: Documentation | Low | 0.5 day | Pending |
| Phase 5: Pre-Release Validation | Low | 0.5 day | Pending |
| Phase 6: Release | Low | 0.5 day | Pending |
| **Total** | | **7-10 days** | ~15% done |

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
# or
python -m build

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

---

## Notes

- **Package name conflict:** The name `day` is taken on PyPI. Must choose alternative before release.
- **Breaking change:** Moving to global storage is a breaking change for existing users with local data.
- **Python version:** Requires Python 3.12+ (uses modern typing features).
