#!/bin/bash
#
# Pre-release validation script for planmyday
#
# This script automates Phase 5 validation checks:
# 1. Build the package
# 2. Create fresh virtual environment
# 3. Install the wheel
# 4. Run all CLI smoke tests
# 5. Test error scenarios
#
# Usage: ./scripts/validate-release.sh
#
# Exit codes:
#   0 - All validations passed
#   1 - Validation failed

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TEST_VENV="/tmp/planmyday-validation-$$"
PASSED=0
FAILED=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_step() { echo -e "\n${BLUE}==>${NC} $1"; }
echo_pass() { echo -e "  ${GREEN}[PASS]${NC} $1"; PASSED=$((PASSED + 1)); }
echo_fail() { echo -e "  ${RED}[FAIL]${NC} $1"; FAILED=$((FAILED + 1)); }
echo_warn() { echo -e "  ${YELLOW}[WARN]${NC} $1"; }
echo_info() { echo -e "  ${NC}$1"; }

cleanup() {
    echo_step "Cleaning up..."
    if [ -d "$TEST_VENV" ]; then
        rm -rf "$TEST_VENV"
        echo_info "Removed test venv: $TEST_VENV"
    fi
}
trap cleanup EXIT

header() {
    echo ""
    echo -e "${GREEN}=============================================${NC}"
    echo -e "${GREEN}  planmyday Pre-Release Validation${NC}"
    echo -e "${GREEN}=============================================${NC}"
    echo ""
}

# ============================================
# Step 1: Build package
# ============================================
build_package() {
    echo_step "Building package..."
    cd "$PROJECT_DIR"
    
    # Clean previous builds
    rm -rf dist/
    
    # Build using uv
    if uv build > /tmp/build-output.txt 2>&1; then
        echo_pass "Package built successfully"
        
        # Show what was built (only .whl and .tar.gz files)
        for f in dist/*.whl dist/*.tar.gz; do
            if [ -f "$f" ]; then
                echo_info "  Built: $(basename "$f")"
            fi
        done
    else
        echo_fail "Package build failed"
        cat /tmp/build-output.txt
        exit 1
    fi
}

# ============================================
# Step 2: Create fresh virtual environment
# ============================================
create_venv() {
    echo_step "Creating fresh virtual environment..."
    
    # Check Python 3.12 is available
    if ! command -v python3.12 &> /dev/null; then
        echo_fail "Python 3.12 not found"
        exit 1
    fi
    
    # Create venv
    python3.12 -m venv "$TEST_VENV"
    echo_pass "Created venv at $TEST_VENV"
    
    # Activate
    source "$TEST_VENV/bin/activate"
    echo_pass "Activated venv"
    
    # Upgrade pip quietly
    pip install --quiet --upgrade pip
}

# ============================================
# Step 3: Install wheel
# ============================================
install_wheel() {
    echo_step "Installing wheel..."
    
    # Find the wheel file
    WHEEL_FILE=$(ls "$PROJECT_DIR"/dist/planmyday-*.whl 2>/dev/null | head -1)
    
    if [ -z "$WHEEL_FILE" ]; then
        echo_fail "No wheel file found in dist/"
        exit 1
    fi
    
    # Install
    if pip install --quiet "$WHEEL_FILE"; then
        echo_pass "Installed $(basename "$WHEEL_FILE")"
    else
        echo_fail "Failed to install wheel"
        exit 1
    fi
}

# ============================================
# Step 4: Verify CLI entry points
# ============================================
verify_entry_points() {
    echo_step "Verifying CLI entry points..."
    
    # Check pday
    if command -v pday &> /dev/null; then
        echo_pass "pday command available"
    else
        echo_fail "pday command not found"
    fi
    
    # Check planmyday
    if command -v planmyday &> /dev/null; then
        echo_pass "planmyday command available"
    else
        echo_fail "planmyday command not found"
    fi
}

# ============================================
# Step 5: Test --version
# ============================================
test_version() {
    echo_step "Testing version..."
    
    VERSION_OUTPUT=$(pday --version 2>&1)
    if [ $? -eq 0 ]; then
        echo_pass "pday --version: $VERSION_OUTPUT"
    else
        echo_fail "pday --version failed"
    fi
}

# ============================================
# Step 6: Test all --help commands
# ============================================
test_help_commands() {
    echo_step "Testing help commands..."
    
    # Main help
    if pday --help > /dev/null 2>&1; then
        echo_pass "pday --help"
    else
        echo_fail "pday --help"
    fi
    
    # All subcommands
    local commands=(
        "start"
        "list"
        "show"
        "checkin"
        "export"
        "profile"
        "stats"
        "template"
        "setup"
        "config"
        "quick"
        "revise"
        "delete"
        "info"
        "import"
        "summary"
        "export-all"
        "show-profile"
    )
    
    for cmd in "${commands[@]}"; do
        if pday "$cmd" --help > /dev/null 2>&1; then
            echo_pass "pday $cmd --help"
        else
            echo_fail "pday $cmd --help"
        fi
    done
    
    # Template subcommands
    local template_commands=("list" "save" "show" "apply" "delete")
    for cmd in "${template_commands[@]}"; do
        if pday template "$cmd" --help > /dev/null 2>&1; then
            echo_pass "pday template $cmd --help"
        else
            echo_fail "pday template $cmd --help"
        fi
    done
}

# ============================================
# Step 7: Test commands with mock config
# ============================================
test_commands_with_mock_config() {
    echo_step "Testing commands with mock configuration..."
    
    # Create a temporary directory with mock config
    local TEST_DIR="/tmp/planmyday-test-$$"
    mkdir -p "$TEST_DIR/sessions"
    mkdir -p "$TEST_DIR/profiles"
    mkdir -p "$TEST_DIR/data/templates"
    cd "$TEST_DIR"
    
    # Create a minimal .env with a dummy API key for testing
    # (API key format validated but not actually used for list/read operations)
    echo "OPENAI_API_KEY=sk-test-dummy-key-for-validation-only-1234567890" > .env
    
    # list should work (shows empty sessions)
    if pday --local list > /dev/null 2>&1; then
        echo_pass "pday --local list"
    else
        echo_fail "pday --local list"
    fi
    
    # template list should work
    if pday --local template list > /dev/null 2>&1; then
        echo_pass "pday --local template list"
    else
        echo_fail "pday --local template list"
    fi
    
    # config should show configuration
    if pday --local config > /dev/null 2>&1; then
        echo_pass "pday --local config"
    else
        echo_fail "pday --local config"
    fi
    
    # Clean up test directory
    rm -rf "$TEST_DIR"
    cd "$PROJECT_DIR"
}

# ============================================
# Step 8: Test error handling
# ============================================
test_error_handling() {
    echo_step "Testing error handling..."
    
    local TEST_DIR="/tmp/planmyday-test-$$"
    mkdir -p "$TEST_DIR/sessions"
    cd "$TEST_DIR"
    
    # Create mock config
    echo "OPENAI_API_KEY=sk-test-dummy-key-for-validation-only-1234567890" > .env
    
    # Test non-existent session - should fail gracefully with clear message
    local output
    output=$(pday --local show "2020-01-01" 2>&1) || true
    if echo "$output" | grep -qi "not found\|error\|no.*plan" > /dev/null; then
        echo_pass "Non-existent session shows error message"
    else
        echo_warn "Non-existent session message unclear: $output"
    fi
    
    # Test setup required when no config
    rm -f .env
    output=$(pday --local list 2>&1) || true
    if echo "$output" | grep -qi "setup\|api.key\|configure" > /dev/null; then
        echo_pass "Missing config shows setup message"
    else
        echo_warn "Missing config message unclear: $output"
    fi
    
    # Clean up
    rm -rf "$TEST_DIR"
    cd "$PROJECT_DIR"
}

# ============================================
# Step 9: Verify package metadata
# ============================================
verify_metadata() {
    echo_step "Verifying package metadata..."
    
    # Check pip show output
    local metadata
    metadata=$(pip show planmyday 2>&1)
    
    # Check name
    if echo "$metadata" | grep -q "Name: planmyday"; then
        echo_pass "Package name: planmyday"
    else
        echo_fail "Package name incorrect"
    fi
    
    # Check author
    if echo "$metadata" | grep -q "Author:"; then
        echo_pass "Author field present"
    else
        echo_warn "Author field missing"
    fi
    
    # Check license
    if echo "$metadata" | grep -q "License: MIT"; then
        echo_pass "License: MIT"
    else
        echo_warn "License field check"
    fi
    
    # Check required dependencies are installed
    local deps=("click" "rich" "openai" "pydantic")
    for dep in "${deps[@]}"; do
        if pip show "$dep" > /dev/null 2>&1; then
            echo_pass "Dependency installed: $dep"
        else
            echo_fail "Dependency missing: $dep"
        fi
    done
}

# ============================================
# Summary
# ============================================
summary() {
    echo ""
    echo -e "${BLUE}=============================================${NC}"
    echo -e "${BLUE}  Validation Summary${NC}"
    echo -e "${BLUE}=============================================${NC}"
    echo ""
    echo -e "  ${GREEN}Passed:${NC} $PASSED"
    echo -e "  ${RED}Failed:${NC} $FAILED"
    echo ""
    
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}All validations passed!${NC}"
        echo ""
        echo "Manual tests still required:"
        echo "  1. Test 'pday setup' with real API key"
        echo "  2. Test 'pday start' full planning flow"
        echo "  3. Test offline behavior (disconnect network)"
        echo ""
        return 0
    else
        echo -e "${RED}Some validations failed. Please fix before release.${NC}"
        echo ""
        return 1
    fi
}

# ============================================
# Main
# ============================================
main() {
    header
    build_package
    create_venv
    install_wheel
    verify_entry_points
    test_version
    test_help_commands
    test_commands_with_mock_config
    test_error_handling
    verify_metadata
    summary
}

main "$@"
