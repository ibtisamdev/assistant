import argparse
import json
import logging
import os
from datetime import datetime

from dotenv import load_dotenv

from agent import Agent
from llm import LLMError
from memory import AgentMemory

# Configure logging
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Daily Planning AI Agent - Your personalized planning assistant"
    )

    parser.add_argument(
        "--new",
        action="store_true",
        help="Start a new session (ignore existing session for today)",
    )

    parser.add_argument(
        "--date", type=str, help="Session date in YYYY-MM-DD format (defaults to today)"
    )

    parser.add_argument(
        "--list", action="store_true", help="List all saved sessions and exit"
    )

    parser.add_argument(
        "--revise",
        action="store_true",
        help="Revise today's finalized plan (re-enter feedback state)",
    )

    return parser.parse_args()


def list_sessions():
    """List all available sessions"""
    sessions = AgentMemory.list_sessions()

    if not sessions:
        print("No saved sessions found.")
        return

    print("\nAvailable Sessions:")
    print("=" * 80)

    today = datetime.now().strftime("%Y-%m-%d")

    for session in sessions:
        is_today = session["session_id"] == today
        today_marker = " (TODAY)" if is_today else ""
        plan_marker = "[x]" if session["has_plan"] else "[ ]"

        print(f"{plan_marker} {session['session_id']}{today_marker}")
        print(f"    State: {session['state']}")
        print(f"    Last updated: {session['last_updated']}")
        print()


def validate_api_key() -> bool:
    """
    Validate that OPENAI_API_KEY is configured properly.
    Returns True if valid, False otherwise.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("\nError: OPENAI_API_KEY not configured")
        print("   Please add your OpenAI API key to the .env file:")
        print("   OPENAI_API_KEY=your_key_here")
        return False

    if not api_key.startswith("sk-"):
        print("\nError: OPENAI_API_KEY appears to be invalid")
        print("   API key should start with 'sk-'")
        print("   Please check your .env file.")
        return False

    return True


def main():
    # Load environment variables
    load_dotenv()

    # Parse CLI arguments
    args = parse_arguments()

    # Handle --list command (doesn't need API key)
    if args.list:
        list_sessions()
        return

    # Validate API key before proceeding
    if not validate_api_key():
        return

    # Handle --revise flag validation
    if args.revise:
        # Error: Can't use with --new
        if args.new:
            print("\nError: Cannot use --revise with --new")
            return

        # Error: Can't use with --date
        if args.date:
            print("\nError: --revise only works for today's session")
            print("   Tip: Run without --date to revise today's plan")
            return

        # Check if today's session exists
        today = datetime.now().strftime("%Y-%m-%d")
        session_path = os.path.join(AgentMemory.SESSIONS_DIR, f"{today}.json")

        if not os.path.exists(session_path):
            print(f"\nError: No session found for today ({today})")
            print("   Tip: Create a plan first, then use --revise to modify it")
            return

        # Check if session is in 'done' state
        try:
            with open(session_path, "r") as f:
                data = json.load(f)
            current_state = data["agent_state"]["state"]

            if current_state != "done":
                print(
                    f"\n  Warning: Today's session isn't finalized (state: {current_state})"
                )
                print("   Resuming session normally...")
                # Don't return - just continue with normal resume
        except Exception as e:
            print(f"\nError: Failed to read session: {e}")
            return

    # Determine session date
    session_date = args.date if args.date else None

    # Validate date format if provided
    if args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(
                f"\nError: Invalid date format '{args.date}'. Please use YYYY-MM-DD format."
            )
            return

    # Display header
    print("\n" + "=" * 60)
    print("Daily Planning AI Agent")
    print("=" * 60)

    # Initialize agent
    try:
        agent = Agent(session_date=session_date, force_new=args.new, revise=args.revise)
    except ValueError as e:
        # API key or configuration errors
        print(f"\nConfiguration Error: {e}")
        return
    except PermissionError as e:
        print(f"\nPermission Error: Cannot access session files")
        print(f"   Details: {e}")
        return
    except Exception as e:
        print(f"\nFailed to initialize agent: {e}")
        logger.error(f"Agent initialization failed: {e}", exc_info=True)
        return

    # Run the agent
    try:
        agent.run()

    except KeyboardInterrupt:
        print("\n\nSession interrupted by user.")
        session_info = agent.memory.get_session_info()
        if session_info["state"] != "done":
            print("   Progress saved automatically")
            print(f"   Resume: python main.py --date {agent.memory.session_date}")
        print()
        return

    except LLMError as e:
        # LLM-specific errors (from our custom exception)
        print(f"\nAI Service Error: {e}")
        print("   Your progress has been saved.")
        print("   Possible causes:")
        print("   - Network connectivity issues")
        print("   - OpenAI API is down or overloaded")
        print("   - Rate limit reached")
        print("\n   Please try again in a few minutes.")
        logger.error(f"LLM error: {e}", exc_info=True)
        return

    except FileNotFoundError as e:
        print(f"\nFile Error: {e}")
        print("   Please check file paths and permissions.")
        logger.error(f"File not found: {e}", exc_info=True)
        return

    except PermissionError as e:
        print(f"\nPermission Error: {e}")
        print("   Please check file permissions in the sessions directory.")
        logger.error(f"Permission error: {e}", exc_info=True)
        return

    except json.JSONDecodeError as e:
        print(f"\nData Error: Session file is corrupted")
        print("   The session file contains invalid JSON.")
        print("   Try running with --new to start a fresh session.")
        logger.error(f"JSON decode error: {e}", exc_info=True)
        return

    except Exception as e:
        # Catch-all for unexpected errors
        print(f"\nUnexpected error: {e}")
        print("   Your progress may have been saved.")
        print("   Please report this issue if it persists.")
        logger.error(f"Unexpected error in agent.run(): {e}", exc_info=True)
        # DO NOT re-raise - just log and exit gracefully
        return

    # Normal completion
    print("\n" + "=" * 60)
    print("Session complete! Have a great day!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
