import argparse
import json
import os
from datetime import datetime
from agent import Agent
from dotenv import load_dotenv
from memory import AgentMemory


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

    print("\n📚 Available Sessions:")
    print("=" * 80)

    today = datetime.now().strftime("%Y-%m-%d")

    for session in sessions:
        is_today = session["session_id"] == today
        today_marker = " (TODAY)" if is_today else ""
        plan_marker = "✓" if session["has_plan"] else "○"

        print(f"{plan_marker} {session['session_id']}{today_marker}")
        print(f"   State: {session['state']}")
        print(f"   Last updated: {session['last_updated']}")
        print()


def main():
    # Load environment variables
    load_dotenv()

    # Parse CLI arguments
    args = parse_arguments()

    # Handle --list command
    if args.list:
        list_sessions()
        return

    # Handle --revise flag validation
    if args.revise:
        # Error: Can't use with --new
        if args.new:
            print("❌ Error: Cannot use --revise with --new")
            return

        # Error: Can't use with --date
        if args.date:
            print("❌ Error: --revise only works for today's session")
            print("   Tip: Run without --date to revise today's plan")
            return

        # Check if today's session exists
        today = datetime.now().strftime("%Y-%m-%d")
        session_path = os.path.join(AgentMemory.SESSIONS_DIR, f"{today}.json")

        if not os.path.exists(session_path):
            print(f"❌ Error: No session found for today ({today})")
            print("   Tip: Create a plan first, then use --revise to modify it")
            return

        # Check if session is in 'done' state
        try:
            with open(session_path, "r") as f:
                data = json.load(f)
            current_state = data["agent_state"]["state"]

            if current_state != "done":
                print(
                    f"⚠️  Warning: Today's session isn't finalized (state: {current_state})"
                )
                print("   Resuming session normally...")
                # Don't return - just continue with normal resume
        except Exception as e:
            print(f"❌ Error: Failed to read session: {e}")
            return

    # Determine session date
    session_date = args.date if args.date else None

    # Validate date format if provided
    if args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(
                f"Error: Invalid date format '{args.date}'. Please use YYYY-MM-DD format."
            )
            return

    # Display header
    print("\n" + "=" * 60)
    print("🤖 Daily Planning AI Agent")
    print("=" * 60)

    # Initialize agent (will auto-resume if session exists, unless --new)
    agent = Agent(session_date=session_date, force_new=args.new, revise=args.revise)

    # Run the agent
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n\n👋 Session interrupted. Your progress has been saved.")
        print(
            f"   Resume anytime by running: python main.py --date {agent.memory.session_date}"
        )
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        print("Your progress has been saved. Please try again.")
        raise

    print("\n" + "=" * 60)
    print("✨ Session complete! Have a great day!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
