"""Interactive profile setup wizard."""

from typing import Optional, List
from src.domain.models.profile import (
    UserProfile,
    PersonalInfo,
    ProductivityHabits,
    WellnessSchedule,
    WorkContext,
    LearningPreferences,
    WorkHours,
    EnergyPattern,
    RecurringTask,
)


class ProfileSetupWizard:
    """Interactive CLI wizard for setting up user profile."""

    def __init__(self):
        self.profile: Optional[UserProfile] = None

    def run_full_setup(self, existing_profile: Optional[UserProfile] = None) -> UserProfile:
        """Run complete profile setup wizard."""
        print("\n" + "=" * 60)
        print("Welcome to the Personal Planning Assistant Profile Setup")
        print("=" * 60)
        print("\nThis wizard will help you create a personalized profile")
        print("to improve your daily planning experience.\n")
        print("Press Enter to skip any optional question.\n")

        # Start with existing profile or create new
        if existing_profile:
            self.profile = existing_profile
            print("Updating existing profile...\n")
        else:
            self.profile = UserProfile()
            print("Creating new profile...\n")

        # Run through all sections
        self._setup_personal_info()
        self._setup_work_schedule()
        self._setup_productivity_habits()
        self._setup_wellness()
        self._setup_work_context()
        self._setup_learning_preferences()
        self._setup_priorities_and_goals()
        self._setup_recurring_tasks()
        self._setup_blocked_times()

        print("\n" + "=" * 60)
        print("Profile setup complete!")
        print("=" * 60)

        return self.profile

    def setup_section(self, section: str, existing_profile: UserProfile) -> UserProfile:
        """Setup a specific section of the profile."""
        self.profile = existing_profile

        sections = {
            "personal": self._setup_personal_info,
            "schedule": self._setup_work_schedule,
            "productivity": self._setup_productivity_habits,
            "wellness": self._setup_wellness,
            "work": self._setup_work_context,
            "learning": self._setup_learning_preferences,
            "priorities": self._setup_priorities_and_goals,
            "tasks": self._setup_recurring_tasks,
            "blocked": self._setup_blocked_times,
        }

        if section not in sections:
            print(f"Unknown section: {section}")
            print(f"Available sections: {', '.join(sections.keys())}")
            return existing_profile

        print(f"\n--- Setting up: {section.title()} ---\n")
        sections[section]()
        print(f"\n{section.title()} section updated!\n")

        return self.profile

    # Section setup methods

    def _setup_personal_info(self) -> None:
        """Setup personal information."""
        print("--- Personal Information ---")

        name = self._prompt("Your name (optional)", self.profile.personal_info.name)
        if name:
            self.profile.personal_info.name = name

        preferred_name = self._prompt(
            "Preferred name/nickname (optional)", self.profile.personal_info.preferred_name
        )
        if preferred_name:
            self.profile.personal_info.preferred_name = preferred_name

        style = self._prompt_choice(
            "Communication style",
            ["concise", "balanced", "detailed"],
            default=self.profile.personal_info.communication_style,
        )
        self.profile.personal_info.communication_style = style

        timezone = self._prompt("Timezone (e.g., America/New_York)", self.profile.timezone)
        if timezone:
            self.profile.timezone = timezone

        print()

    def _setup_work_schedule(self) -> None:
        """Setup work hours and energy patterns."""
        print("--- Work Schedule & Energy ---")

        start = self._prompt("Work start time (HH:MM)", self.profile.work_hours.start)
        if start:
            self.profile.work_hours.start = start

        end = self._prompt("Work end time (HH:MM)", self.profile.work_hours.end)
        if end:
            self.profile.work_hours.end = end

        days_input = self._prompt(
            "Work days (comma-separated, e.g., Monday,Tuesday,Wednesday)",
            ",".join(self.profile.work_hours.days),
        )
        if days_input:
            self.profile.work_hours.days = [d.strip() for d in days_input.split(",")]

        # Energy pattern
        morning = self._prompt_choice(
            "Morning energy level",
            ["low", "medium", "high"],
            default=self.profile.energy_pattern.morning,
        )
        self.profile.energy_pattern.morning = morning

        afternoon = self._prompt_choice(
            "Afternoon energy level",
            ["low", "medium", "high"],
            default=self.profile.energy_pattern.afternoon,
        )
        self.profile.energy_pattern.afternoon = afternoon

        evening = self._prompt_choice(
            "Evening energy level",
            ["low", "medium", "high"],
            default=self.profile.energy_pattern.evening,
        )
        self.profile.energy_pattern.evening = evening

        print()

    def _setup_productivity_habits(self) -> None:
        """Setup productivity preferences."""
        print("--- Productivity Habits ---")

        focus_length = self._prompt_int(
            "Focus session length (minutes)",
            self.profile.productivity_habits.focus_session_length,
        )
        if focus_length:
            self.profile.productivity_habits.focus_session_length = focus_length

        max_deep_work = self._prompt_int(
            "Max deep work hours per day",
            self.profile.productivity_habits.max_deep_work_hours,
        )
        if max_deep_work:
            self.profile.productivity_habits.max_deep_work_hours = max_deep_work

        peak_time = self._prompt_choice(
            "Peak productivity time",
            ["morning", "afternoon", "evening", "varies"],
            default=self.profile.productivity_habits.peak_productivity_time or "varies",
            allow_empty=True,
        )
        if peak_time and peak_time != "varies":
            self.profile.productivity_habits.peak_productivity_time = peak_time

        distractions = self._prompt_list(
            "Known distractions (comma-separated)",
            self.profile.productivity_habits.distraction_triggers,
        )
        if distractions is not None:
            self.profile.productivity_habits.distraction_triggers = distractions

        procrastination = self._prompt_list(
            "Procrastination patterns (comma-separated, e.g., 'large tasks', 'afternoons')",
            self.profile.productivity_habits.procrastination_patterns,
        )
        if procrastination is not None:
            self.profile.productivity_habits.procrastination_patterns = procrastination

        print()

    def _setup_wellness(self) -> None:
        """Setup wellness schedule."""
        print("--- Health & Wellness ---")

        wake_time = self._prompt("Wake time (HH:MM)", self.profile.wellness_schedule.wake_time)
        if wake_time:
            self.profile.wellness_schedule.wake_time = wake_time

        sleep_time = self._prompt("Sleep time (HH:MM)", self.profile.wellness_schedule.sleep_time)
        if sleep_time:
            self.profile.wellness_schedule.sleep_time = sleep_time

        # Meal times
        if self._prompt_yes_no("Add meal times?"):
            meals = []
            for meal_name in ["breakfast", "lunch", "dinner"]:
                time = self._prompt(f"{meal_name.title()} time (HH:MM, or skip)")
                if time:
                    duration = self._prompt_int(f"{meal_name.title()} duration (minutes)", 30)
                    meals.append(
                        {
                            "name": meal_name,
                            "time": time,
                            "duration": duration or 30,
                        }
                    )
            if meals:
                self.profile.wellness_schedule.meal_times = meals

        # Exercise times
        if self._prompt_yes_no("Add exercise schedule?"):
            exercises = []
            while True:
                day = self._prompt("Exercise day (or 'done' to finish)")
                if not day or day.lower() == "done":
                    break
                time = self._prompt("Exercise time (HH:MM)")
                duration = self._prompt_int("Duration (minutes)", 60)
                if time:
                    exercises.append(
                        {
                            "day": day,
                            "time": time,
                            "duration": duration or 60,
                        }
                    )
            if exercises:
                self.profile.wellness_schedule.exercise_times = exercises

        print()

    def _setup_work_context(self) -> None:
        """Setup work context."""
        print("--- Work Context ---")

        job_role = self._prompt("Job role/title", self.profile.work_context.job_role)
        if job_role:
            self.profile.work_context.job_role = job_role

        meeting_days = self._prompt_list(
            "Meeting-heavy days (comma-separated)",
            self.profile.work_context.meeting_heavy_days,
        )
        if meeting_days is not None:
            self.profile.work_context.meeting_heavy_days = meeting_days

        deadline_pattern = self._prompt(
            "Deadline pattern (e.g., 'end of sprint', 'monthly')",
            self.profile.work_context.deadline_patterns,
        )
        if deadline_pattern:
            self.profile.work_context.deadline_patterns = deadline_pattern

        collab_style = self._prompt_choice(
            "Collaboration preference",
            ["sync", "async", "mixed"],
            default=self.profile.work_context.collaboration_preference,
        )
        self.profile.work_context.collaboration_preference = collab_style

        meeting_duration = self._prompt_int(
            "Typical meeting duration (minutes)",
            self.profile.work_context.typical_meeting_duration,
        )
        if meeting_duration:
            self.profile.work_context.typical_meeting_duration = meeting_duration

        print()

    def _setup_learning_preferences(self) -> None:
        """Setup learning preferences."""
        print("--- Learning Preferences ---")

        learning_style = self._prompt_choice(
            "Learning style",
            ["visual", "auditory", "kinesthetic", "reading", "mixed"],
            default=self.profile.learning_preferences.learning_style,
        )
        self.profile.learning_preferences.learning_style = learning_style

        skill_goals = self._prompt_list(
            "Skill development goals (comma-separated)",
            self.profile.learning_preferences.skill_development_goals,
        )
        if skill_goals is not None:
            self.profile.learning_preferences.skill_development_goals = skill_goals

        interests = self._prompt_list(
            "Areas of interest (comma-separated)",
            self.profile.learning_preferences.areas_of_interest,
        )
        if interests is not None:
            self.profile.learning_preferences.areas_of_interest = interests

        learning_time = self._prompt_choice(
            "Best time for learning",
            ["morning", "afternoon", "evening", "varies"],
            default=self.profile.learning_preferences.preferred_learning_time or "varies",
            allow_empty=True,
        )
        if learning_time and learning_time != "varies":
            self.profile.learning_preferences.preferred_learning_time = learning_time

        print()

    def _setup_priorities_and_goals(self) -> None:
        """Setup priorities and long-term goals."""
        print("--- Priorities & Goals ---")

        priorities = self._prompt_list(
            "Top priorities (comma-separated, max 5)",
            self.profile.top_priorities,
        )
        if priorities is not None:
            self.profile.top_priorities = priorities[:5]  # Limit to 5

        goals = self._prompt_list(
            "Long-term goals (comma-separated)",
            self.profile.long_term_goals,
        )
        if goals is not None:
            self.profile.long_term_goals = goals

        print()

    def _setup_recurring_tasks(self) -> None:
        """Setup recurring tasks."""
        print("--- Recurring Tasks ---")

        if not self._prompt_yes_no("Add recurring tasks?"):
            return

        tasks = []
        while True:
            name = self._prompt("Task name (or 'done' to finish)")
            if not name or name.lower() == "done":
                break

            frequency = self._prompt_choice(
                "Frequency", ["daily", "weekly", "monthly"], default="daily"
            )
            duration = self._prompt_int("Duration (minutes)", 30)
            preferred_time = self._prompt("Preferred time (HH:MM, optional)")
            priority = self._prompt_choice("Priority", ["low", "medium", "high"], default="medium")

            tasks.append(
                RecurringTask(
                    name=name,
                    frequency=frequency,
                    duration=duration or 30,
                    preferred_time=preferred_time if preferred_time else None,
                    priority=priority,
                )
            )

        if tasks:
            self.profile.recurring_tasks = tasks

        print()

    def _setup_blocked_times(self) -> None:
        """Setup blocked times."""
        print("--- Blocked Times ---")

        if not self._prompt_yes_no("Add blocked times?"):
            return

        blocked = []
        while True:
            reason = self._prompt("Block reason (or 'done' to finish, e.g., 'lunch', 'commute')")
            if not reason or reason.lower() == "done":
                break

            start = self._prompt("Start time (HH:MM)")
            end = self._prompt("End time (HH:MM)")

            if start and end:
                blocked.append({"start": start, "end": end, "reason": reason})

        if blocked:
            self.profile.blocked_times = blocked

        print()

    # Helper methods

    def _prompt(self, question: str, default: Optional[str] = None) -> str:
        """Prompt user for input with optional default."""
        if default:
            user_input = input(f"{question} [{default}]: ").strip()
            return user_input if user_input else default
        else:
            return input(f"{question}: ").strip()

    def _prompt_int(self, question: str, default: Optional[int] = None) -> Optional[int]:
        """Prompt user for integer input."""
        default_str = str(default) if default is not None else None
        result = self._prompt(question, default_str)
        if not result:
            return None
        try:
            return int(result)
        except ValueError:
            print(f"Invalid number: {result}, keeping default")
            return default

    def _prompt_choice(
        self,
        question: str,
        choices: List[str],
        default: Optional[str] = None,
        allow_empty: bool = False,
    ) -> str:
        """Prompt user to choose from a list."""
        choices_str = "/".join(choices)
        while True:
            result = self._prompt(f"{question} ({choices_str})", default)
            if not result and allow_empty:
                return ""
            if not result and default:
                return default
            if result.lower() in [c.lower() for c in choices]:
                return result.lower()
            print(f"Invalid choice. Please choose from: {choices_str}")

    def _prompt_list(
        self, question: str, default: Optional[List[str]] = None
    ) -> Optional[List[str]]:
        """Prompt user for comma-separated list."""
        default_str = ", ".join(default) if default else None
        result = self._prompt(question, default_str)
        if not result:
            return None
        return [item.strip() for item in result.split(",") if item.strip()]

    def _prompt_yes_no(self, question: str) -> bool:
        """Prompt user for yes/no answer."""
        while True:
            result = input(f"{question} (y/n): ").strip().lower()
            if result in ["y", "yes"]:
                return True
            if result in ["n", "no"]:
                return False
            print("Please answer 'y' or 'n'")
