"""
uDOS WELLBEING Handler - Holistic User Wellness
Alpha v1.0.0.65

A mindful, astrological, and resource-aware wellness system.

Commands:
- WELLBEING                     Show holistic status
- WELLBEING SETUP               Initial questionnaire (zodiac, preferences)
- WELLBEING STATUS              Current state summary
- WELLBEING FACTORS             Show all mood factors (v3.0.0)
- WELLBEING FACTORS DETAIL      Detailed factor breakdown
- WELLBEING ENERGY <0-100>      Set energy level (0-100% or low/medium/high)
- WELLBEING MOOD <1-5>          Set base mood score (influences calculated)
- WELLBEING MIND <state>        Set mind state (focused/flowing/steady/resting)
- WELLBEING BREAK               Log a break
- WELLBEING SLEEP <1-5>         Log sleep quality
- WELLBEING MEAL                Log that you just ate
- WELLBEING CHECKIN             Quick wellness check-in
- WELLBEING SUGGEST             Get task suggestions based on state
- WELLBEING HISTORY             View recent logs
- WELLBEING CELESTIAL           Show astrological influences
- WELLBEING IDENTITY            Set birth date for zodiac/numerology
- WELLBEING RESET               Reset tracking data

Philosophy:
- Conservation over performance
- Mindfulness over productivity
- Balance over optimization
- Variety for wellness

Version: 2.0.0
Created: 2026-01-07
"""

import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import psutil

from dev.goblin.core.commands.base_handler import BaseCommandHandler
from dev.goblin.core.services.logging_manager import get_logger
from dev.goblin.core.services.wellbeing_service import (
    WellbeingService,
    MoodState,
    EnergyBalance,
    MindState,
    ZodiacSign,
    MoonPhase,
    RUOKChecker,
    RUOKCheck,
)
from dev.goblin.core.services.mood_engine import MoodEngine, get_mood_engine
from dev.goblin.core.services.behavioral_factors import get_metrics_collector
from dev.goblin.core.services.biological_factors import get_biological_state

logger = get_logger("command-wellbeing")


# Legacy energy level mapping (for backward compatibility)
ENERGY_LEVELS = {
    "low": {
        "icon": "😴",
        "value": 0.25,
        "description": "Low energy - focus on light tasks",
        "task_types": ["review", "organize", "read"],
        "max_session_minutes": 15,
    },
    "medium": {
        "icon": "😊",
        "value": 0.5,
        "description": "Medium energy - good for most tasks",
        "task_types": ["write", "learn", "create"],
        "max_session_minutes": 25,
    },
    "high": {
        "icon": "⚡",
        "value": 0.85,
        "description": "High energy - tackle challenging work",
        "task_types": ["complex", "debug", "plan"],
        "max_session_minutes": 45,
    },
}

# Mood scale
MOOD_SCALE = {
    1: {"icon": "😞", "label": "Very Low"},
    2: {"icon": "😕", "label": "Low"},
    3: {"icon": "😐", "label": "Neutral"},
    4: {"icon": "🙂", "label": "Good"},
    5: {"icon": "😄", "label": "Great"},
}


class WellbeingHandler(BaseCommandHandler):
    """Handler for WELLBEING commands - holistic user wellness."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_path = Path(__file__).parent.parent.parent
        self.memory_path = self.root_path / "memory"
        self.wellbeing_dir = self.memory_path / "private" / "wellbeing"
        self.state_file = self.wellbeing_dir / "state.json"
        self.history_file = self.wellbeing_dir / "history.json"
        self.story_file = self.memory_path / "private" / "story.yaml"

        # Ensure directory exists
        self.wellbeing_dir.mkdir(parents=True, exist_ok=True)

        # Initialize the wellbeing service
        self.service = WellbeingService(data_dir=self.wellbeing_dir)

        # Initialize mood engine (v3.0.0)
        self.mood_engine = get_mood_engine()

    def handle(self, command: str, params: list, grid=None, parser=None) -> dict:
        """Route WELLBEING commands to appropriate handlers."""

        if not params:
            return self._handle_status([], grid)

        subcommand = params[0].upper()
        sub_params = params[1:] if len(params) > 1 else []

        handlers = {
            "SETUP": self._handle_setup,
            "STATUS": self._handle_status,
            "FACTORS": self._handle_factors,
            "ENERGY": self._handle_energy,
            "MOOD": self._handle_mood,
            "BREAK": self._handle_break,
            "SLEEP": self._handle_sleep,
            "MEAL": self._handle_meal,
            "CHECKIN": self._handle_checkin,
            "SUGGEST": self._handle_suggest,
            "HISTORY": self._handle_history,
            "RESET": self._handle_reset,
            "CHECK": self._handle_check,
            # Holistic handlers
            "MIND": self._handle_mind,
            "CELESTIAL": self._handle_celestial,
            "IDENTITY": self._handle_identity,
            "RUOK": self._handle_ruok,
            "RUOK?": self._handle_ruok,
        }

        handler = handlers.get(subcommand)
        if handler:
            return handler(sub_params, grid)

        # Check if first param is energy level
        if subcommand.lower() in ENERGY_LEVELS:
            return self._handle_energy([subcommand], grid)

        # Check if first param is mood number
        try:
            mood = int(subcommand)
            if 1 <= mood <= 5:
                return self._handle_mood([subcommand], grid)
        except ValueError:
            pass

        return {"status": "error", "message": f"Unknown subcommand: {subcommand}"}

    def _load_state(self) -> dict:
        """Load current wellbeing state."""
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except:
                pass
        return self._default_state()

    def _default_state(self) -> dict:
        """Return default state."""
        return {
            "energy": "medium",
            "mood": 3,
            "last_break": None,
            "session_start": None,
            "session_minutes": 0,
            "today_sessions": 0,
            "streak_days": 0,
            "updated": datetime.now().isoformat(),
        }

    def _save_state(self, state: dict) -> None:
        """Save wellbeing state."""
        state["updated"] = datetime.now().isoformat()
        self.state_file.write_text(json.dumps(state, indent=2))

    def _log_entry(self, entry_type: str, value: Any, notes: str = None) -> None:
        """Log an entry to history."""
        history = self._load_history()

        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": entry_type,
            "value": value,
        }
        if notes:
            entry["notes"] = notes

        history.append(entry)

        # Keep last 100 entries
        history = history[-100:]

        self.history_file.write_text(json.dumps(history, indent=2))

    def _load_history(self) -> list:
        """Load history entries."""
        if self.history_file.exists():
            try:
                return json.loads(self.history_file.read_text())
            except:
                pass
        return []

    def _handle_setup(self, params: list, grid=None) -> dict:
        """Interactive setup questionnaire."""
        lines = [
            "🧘 WELLBEING SETUP",
            "",
            "Let's set up your wellbeing preferences.",
            "",
            "Run these commands to configure:",
            "",
            "1. Set your current energy level:",
            "   WELLBEING ENERGY low|medium|high",
            "",
            "2. Log your mood (1-5):",
            "   WELLBEING MOOD 3",
            "",
            "3. Start a focused session:",
            "   WELLBEING CHECK",
            "",
            "Your preferences are stored in memory/private/",
            "and are never shared.",
        ]

        return {"status": "success", "message": "\n".join(lines)}

    def _handle_status(self, params: list, grid=None) -> dict:
        """Show current wellbeing status."""
        state = self._load_state()

        energy_level = state.get("energy", "medium")
        energy_info = ENERGY_LEVELS.get(energy_level, ENERGY_LEVELS["medium"])

        mood_val = state.get("mood", 3)
        mood_info = MOOD_SCALE.get(mood_val, MOOD_SCALE[3])

        lines = [
            "🧘 WELLBEING STATUS",
            "",
            f"Energy: {energy_info['icon']} {energy_level.title()}",
            f"        {energy_info['description']}",
            "",
            f"Mood:   {mood_info['icon']} {mood_info['label']} ({mood_val}/5)",
            "",
        ]

        # Break reminder
        last_break = state.get("last_break")
        if last_break:
            try:
                last_break_dt = datetime.fromisoformat(last_break)
                minutes_since = int(
                    (datetime.now() - last_break_dt).total_seconds() / 60
                )

                if minutes_since > energy_info["max_session_minutes"]:
                    lines.append(
                        f"⚠️ Break recommended! ({minutes_since}m since last break)"
                    )
                else:
                    lines.append(f"Last break: {minutes_since}m ago")
            except:
                pass
        else:
            lines.append("💡 Tip: Use WELLBEING BREAK after focused work")

        lines.extend(
            [
                "",
                f"Today's sessions: {state.get('today_sessions', 0)}",
                f"Streak: {state.get('streak_days', 0)} days",
            ]
        )

        # Suggest based on current state
        lines.extend(
            [
                "",
                "─" * 40,
                "",
                f"Suggested tasks for {energy_level} energy:",
            ]
        )

        for task_type in energy_info["task_types"]:
            lines.append(f"  • {task_type}")

        return {"status": "success", "message": "\n".join(lines), "data": state}

    def _handle_energy(self, params: list, grid=None) -> dict:
        """Log current energy level."""
        if not params:
            return {
                "status": "error",
                "message": "Usage: WELLBEING ENERGY low|medium|high",
            }

        level = params[0].lower()

        if level not in ENERGY_LEVELS:
            return {
                "status": "error",
                "message": f"Invalid energy level: {level}\nUse: low, medium, or high",
            }

        state = self._load_state()
        old_level = state.get("energy")
        state["energy"] = level
        self._save_state(state)

        self._log_entry("energy", level)

        # Update mood engine with normalized value
        energy_value = ENERGY_LEVELS[level]["value"]
        self.mood_engine.update_energy(energy_value)

        info = ENERGY_LEVELS[level]

        logger.info(f"[LOCAL] Energy logged: {level}")

        return {
            "status": "success",
            "message": f"{info['icon']} Energy set to: {level.title()}\n\n"
            f"{info['description']}\n\n"
            f"Recommended session length: {info['max_session_minutes']}m",
        }

    def _handle_mood(self, params: list, grid=None) -> dict:
        """Log mood score."""
        if not params:
            return {"status": "error", "message": "Usage: WELLBEING MOOD <1-5>"}

        try:
            mood = int(params[0])
        except ValueError:
            return {"status": "error", "message": "Mood must be a number 1-5"}

        if mood < 1 or mood > 5:
            return {"status": "error", "message": "Mood must be between 1 and 5"}

        state = self._load_state()
        old_mood = state.get("mood")
        state["mood"] = mood
        self._save_state(state)

        self._log_entry("mood", mood)

        # Update mood engine with normalized value (1-5 to 0-1)
        self.mood_engine.update_mood((mood - 1) / 4.0)

        info = MOOD_SCALE[mood]

        logger.info(f"[LOCAL] Mood logged: {mood}")

        message = f"{info['icon']} Mood logged: {info['label']}"

        # Add encouragement for low moods
        if mood <= 2:
            message += "\n\n💡 Consider a short break or light activity."
        elif mood >= 4:
            message += "\n\n✨ Great to hear! Make the most of this positive energy."

        return {"status": "success", "message": message}

    def _handle_break(self, params: list, grid=None) -> dict:
        """Start or log a break."""
        state = self._load_state()

        # Log break time
        state["last_break"] = datetime.now().isoformat()

        # Update session count
        state["today_sessions"] = state.get("today_sessions", 0) + 1

        self._save_state(state)
        self._log_entry("break", True)

        # Reset behavioral metrics for break tracking
        from dev.goblin.core.services.behavioral_factors import reset_metrics_collector

        reset_metrics_collector()

        energy_level = state.get("energy", "medium")
        energy_info = ENERGY_LEVELS.get(energy_level, ENERGY_LEVELS["medium"])

        lines = [
            "☕ BREAK TIME",
            "",
            "Take a moment to:",
            "  • Stretch and move",
            "  • Look away from screen",
            "  • Hydrate",
            "  • Breathe deeply",
            "",
            f"Next session: {energy_info['max_session_minutes']}m recommended",
            "",
            "Return refreshed! 🌟",
        ]

        return {"status": "success", "message": "\n".join(lines)}

    def _handle_suggest(self, params: list, grid=None) -> dict:
        """Suggest tasks based on current state."""
        state = self._load_state()

        energy = state.get("energy", "medium")
        mood = state.get("mood", 3)

        energy_info = ENERGY_LEVELS.get(energy, ENERGY_LEVELS["medium"])

        # Build suggestions
        suggestions = []

        if energy == "low":
            suggestions = [
                "📚 Review a knowledge article (GUIDE)",
                "📁 Organize files in inbox (INBOX)",
                "📖 Read bundle content (BUNDLE NEXT)",
                "🔍 Light research (CAPTURE urls for later)",
            ]
        elif energy == "medium":
            suggestions = [
                "📝 Work on a bundle (BUNDLE NEXT)",
                "✍️ Write or edit content",
                "🎓 Learn something new (GUIDE)",
                "🔧 Small fixes or improvements",
            ]
        else:  # high
            suggestions = [
                "🎯 Tackle complex tasks (MISSION)",
                "💡 Creative work (MAKE)",
                "🏗️ Build or plan new features",
                "🐛 Debug challenging issues",
            ]

        # Adjust for mood
        if mood <= 2:
            suggestions.insert(0, "🧘 Consider a wellbeing break first")

        lines = [
            f"💡 SUGGESTIONS for {energy.title()} Energy",
            "",
        ]

        for suggestion in suggestions:
            lines.append(f"  {suggestion}")

        lines.extend(
            [
                "",
                f"Session length: {energy_info['max_session_minutes']}m",
                "",
                "Update your state:",
                "  WELLBEING ENERGY <level>",
                "  WELLBEING MOOD <1-5>",
            ]
        )

        return {"status": "success", "message": "\n".join(lines)}

    def _handle_history(self, params: list, grid=None) -> dict:
        """View recent wellbeing history."""
        history = self._load_history()

        if not history:
            return {
                "status": "info",
                "message": "No history yet. Start logging with WELLBEING ENERGY or MOOD.",
            }

        # Get last 20 entries
        recent = history[-20:]

        lines = ["📊 WELLBEING HISTORY", ""]

        current_date = None
        for entry in reversed(recent):
            try:
                dt = datetime.fromisoformat(entry["timestamp"])
                date_str = dt.strftime("%Y-%m-%d")

                if date_str != current_date:
                    current_date = date_str
                    lines.append(f"\n📅 {date_str}")

                time_str = dt.strftime("%H:%M")
                entry_type = entry["type"]
                value = entry["value"]

                if entry_type == "energy":
                    info = ENERGY_LEVELS.get(value, {})
                    icon = info.get("icon", "")
                    lines.append(f"  {time_str} {icon} Energy: {value}")
                elif entry_type == "mood":
                    info = MOOD_SCALE.get(value, {})
                    icon = info.get("icon", "")
                    lines.append(f"  {time_str} {icon} Mood: {value}/5")
                elif entry_type == "break":
                    lines.append(f"  {time_str} ☕ Break taken")

            except Exception as e:
                continue

        return {"status": "success", "message": "\n".join(lines)}

    def _handle_check(self, params: list, grid=None) -> dict:
        """Quick check-in prompt."""
        lines = [
            "🧘 WELLBEING CHECK-IN",
            "",
            "How are you feeling right now?",
            "",
            "Energy:",
            "  WELLBEING low    - 😴 Need rest",
            "  WELLBEING medium - 😊 Doing okay",
            "  WELLBEING high   - ⚡ Energized!",
            "",
            "Mood (1-5):",
            "  WELLBEING 1-5",
            "",
            "Then get suggestions:",
            "  WELLBEING SUGGEST",
        ]

        return {"status": "success", "message": "\n".join(lines)}

    def _handle_reset(self, params: list, grid=None) -> dict:
        """Reset wellbeing data."""
        state = self._default_state()
        self._save_state(state)

        # Clear history
        self.history_file.write_text("[]")

        return {
            "status": "success",
            "message": "🔄 Wellbeing data reset.\n\nRun WELLBEING SETUP to reconfigure.",
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # MOOD FACTORS v3.0.0 - Multi-Factor Scientific Mood System
    # ═══════════════════════════════════════════════════════════════════════════

    def _handle_factors(self, params: list, grid=None) -> dict:
        """Show all mood factors breakdown.

        Usage:
            WELLBEING FACTORS           - Show summary
            WELLBEING FACTORS DETAIL    - Show detailed breakdown
            WELLBEING FACTORS REPORT    - Full formatted report
        """
        detailed = False
        if params:
            sub = params[0].upper()
            if sub in ("DETAIL", "DETAILED", "ALL"):
                detailed = True
            elif sub == "REPORT":
                # Return full report
                report = self.mood_engine.format_report(detailed=True)
                return {"status": "success", "message": report}

        # Calculate current composite
        composite = self.mood_engine.calculate()

        if detailed:
            return {
                "status": "success",
                "message": self.mood_engine.format_report(detailed=True),
            }

        # Summary view
        lines = [
            "📊 MOOD FACTORS v3.0.0",
            "",
            f"  {composite.summary()}",
            "",
            "─" * 44,
        ]

        # Category breakdown
        from dev.goblin.core.services.mood_factors import FactorCategory

        for cat in FactorCategory:
            cat_score = composite.categories.get(cat.name_str)
            if cat_score:
                pct = int(cat_score.score * 100)
                conf = int(cat_score.confidence * 100)
                bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
                lines.append(f"  {cat.icon} {cat.name_str.title():<12} [{bar}] {pct}%")

        lines.extend(
            [
                "",
                "─" * 44,
                "",
            ]
        )

        # Show identity info if available
        if self.mood_engine.has_identity():
            identity = self.mood_engine.get_identity_summary()
            lines.extend(
                [
                    f"  ☀️ {identity.get('western_zodiac', 'Not set')}",
                    f"  🐉 {identity.get('chinese_zodiac', 'Not set')}",
                    f"  🔢 Life Path: {identity.get('life_path_number', 'Not set')}",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "  💡 Set your birth date for zodiac/numerology:",
                    "     WELLBEING IDENTITY 1990-03-15",
                    "",
                ]
            )

        # Trend
        trend = self.mood_engine.get_trend(1.0)
        if trend is not None:
            trend_icon = "📈" if trend > 0.02 else "📉" if trend < -0.02 else "➡️"
            lines.append(f"  Trend (1h): {trend_icon} {trend:+.1%}")

        lines.extend(
            [
                "",
                "For details: WELLBEING FACTORS DETAIL",
            ]
        )

        return {
            "status": "success",
            "message": "\n".join(lines),
            "data": composite.to_dict(),
        }

    def _handle_sleep(self, params: list, grid=None) -> dict:
        """Log sleep quality.

        Usage:
            WELLBEING SLEEP 4           - Good sleep (1-5 scale)
            WELLBEING SLEEP good        - Descriptive
        """
        if not params:
            return {
                "status": "error",
                "message": "Usage: WELLBEING SLEEP <1-5> or <poor|fair|good|great|excellent>",
            }

        # Parse input
        quality_map = {
            "poor": 0.2,
            "bad": 0.2,
            "terrible": 0.1,
            "fair": 0.4,
            "ok": 0.4,
            "okay": 0.4,
            "good": 0.6,
            "decent": 0.6,
            "great": 0.8,
            "well": 0.8,
            "excellent": 1.0,
            "amazing": 1.0,
            "perfect": 1.0,
        }

        value = params[0].lower()
        if value in quality_map:
            quality = quality_map[value]
        else:
            try:
                num = float(value)
                if 1 <= num <= 5:
                    quality = (num - 1) / 4  # Convert 1-5 to 0-1
                elif 0 <= num <= 100:
                    quality = num / 100  # Percentage
                else:
                    return {
                        "status": "error",
                        "message": "Sleep quality must be 1-5 or 0-100",
                    }
            except ValueError:
                return {"status": "error", "message": f"Unknown sleep quality: {value}"}

        # Update mood engine
        self.mood_engine.record_sleep(quality)
        self._log_entry("sleep", quality)

        # Feedback
        if quality >= 0.8:
            msg = "😴 Excellent rest! You're well-equipped for the day."
        elif quality >= 0.6:
            msg = "🙂 Good sleep. Should be a productive day."
        elif quality >= 0.4:
            msg = "😐 Fair sleep. Consider lighter tasks today."
        else:
            msg = "😓 Poor sleep noted. Be gentle with yourself today."

        return {
            "status": "success",
            "message": f"💤 Sleep quality logged: {int(quality * 100)}%\n\n{msg}",
        }

    def _handle_meal(self, params: list, grid=None) -> dict:
        """Log that the user just ate.

        Usage:
            WELLBEING MEAL              - Log a meal now
        """
        self.mood_engine.record_meal()
        self._log_entry("meal", datetime.now().isoformat())

        return {
            "status": "success",
            "message": "🍽️ Meal logged!\n\nEnergy should be good for the next few hours.",
        }

    def _handle_checkin(self, params: list, grid=None) -> dict:
        """Quick wellness check-in with energy and mood.

        Usage:
            WELLBEING CHECKIN           - Interactive prompt
            WELLBEING CHECKIN 70 4      - Set energy (%) and mood (1-5)
        """
        if len(params) >= 2:
            # Quick set both
            try:
                energy = float(params[0])
                mood = int(params[1])

                # Normalize energy to 0-1
                if energy > 1:
                    energy = energy / 100

                self.mood_engine.update_energy(energy)
                self.mood_engine.update_mood((mood - 1) / 4)  # 1-5 to 0-1

                self._log_entry("energy", energy)
                self._log_entry("mood", mood)

                # Get updated composite
                composite = self.mood_engine.calculate()

                return {
                    "status": "success",
                    "message": f"✅ Check-in logged!\n\n"
                    f"Energy: {int(energy * 100)}%\n"
                    f"Mood: {mood}/5\n\n"
                    f"Current: {composite.summary()}",
                }
            except ValueError:
                pass

        # Interactive prompt
        lines = [
            "🧘 QUICK CHECK-IN",
            "",
            "Log your current state:",
            "",
            "  WELLBEING CHECKIN <energy%> <mood1-5>",
            "  Example: WELLBEING CHECKIN 75 4",
            "",
            "Or set individually:",
            "  WELLBEING ENERGY <0-100>",
            "  WELLBEING MOOD <1-5>",
            "  WELLBEING SLEEP <1-5>",
            "  WELLBEING MEAL",
            "",
            "Then view your mood factors:",
            "  WELLBEING FACTORS",
        ]

        return {"status": "success", "message": "\n".join(lines)}

    def _handle_identity(self, params: list, grid=None) -> dict:
        """Set birth date for zodiac and numerology calculations.

        Usage:
            WELLBEING IDENTITY                      - Show current
            WELLBEING IDENTITY 1990-03-15           - Set birth date
            WELLBEING IDENTITY 1990-03-15 14:30     - Set birth date and time
            WELLBEING IDENTITY CHRONOTYPE early     - Set chronotype
        """
        if not params:
            # Show current identity
            if self.mood_engine.has_identity():
                summary = self.mood_engine.get_identity_summary()
                lines = [
                    "🆔 YOUR IDENTITY (for mood factors)",
                    "",
                    f"  ☀️ Western: {summary.get('western_zodiac', 'Not set')}",
                    f"  🐉 Chinese: {summary.get('chinese_zodiac', 'Not set')}",
                    f"  🔢 Life Path: {summary.get('life_path_number', 'Not set')}",
                    f"  ⏰ Chronotype: {summary.get('chronotype', 'intermediate').title()}",
                    "",
                    "To update: WELLBEING IDENTITY YYYY-MM-DD",
                    "To set chronotype: WELLBEING IDENTITY CHRONOTYPE early|intermediate|late",
                ]
            else:
                lines = [
                    "🆔 IDENTITY SETUP",
                    "",
                    "Set your birth date for zodiac and numerology:",
                    "",
                    "  WELLBEING IDENTITY 1990-03-15",
                    "",
                    "Optionally add birth time:",
                    "  WELLBEING IDENTITY 1990-03-15 14:30",
                    "",
                    "Set your chronotype (sleep pattern):",
                    "  WELLBEING IDENTITY CHRONOTYPE early       - Morning person",
                    "  WELLBEING IDENTITY CHRONOTYPE intermediate - Average",
                    "  WELLBEING IDENTITY CHRONOTYPE late        - Night owl",
                    "",
                    "Your data is encrypted and stored locally only.",
                ]

            return {"status": "success", "message": "\n".join(lines)}

        # Handle chronotype
        if params[0].upper() == "CHRONOTYPE":
            if len(params) < 2:
                return {
                    "status": "error",
                    "message": "Usage: WELLBEING IDENTITY CHRONOTYPE early|intermediate|late",
                }

            chronotype = params[1].lower()
            if chronotype not in ("early", "intermediate", "late"):
                return {
                    "status": "error",
                    "message": "Chronotype must be: early, intermediate, or late",
                }

            self.mood_engine.set_chronotype(chronotype)
            labels = {
                "early": "🐦 Early Bird",
                "intermediate": "⚖️ Intermediate",
                "late": "🦉 Night Owl",
            }

            return {
                "status": "success",
                "message": f"✅ Chronotype set to: {labels[chronotype]}\n\n"
                f"Circadian rhythm calculations will be adjusted accordingly.",
            }

        # Parse birth date
        try:
            date_str = params[0]
            birth_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            self.mood_engine.set_birth_date(birth_date)

            # Also update old service for compatibility
            self.service.set_birth_date(birth_date)

            # Optional birth time
            if len(params) >= 2:
                try:
                    time_str = params[1]
                    birth_time = datetime.strptime(time_str, "%H:%M").time()
                    self.mood_engine.set_birth_time(birth_time)
                except ValueError:
                    pass  # Ignore invalid time

            # Get derived info
            summary = self.mood_engine.get_identity_summary()

            lines = [
                "✅ Identity set!",
                "",
                f"  ☀️ Western Zodiac: {summary.get('western_zodiac', '')}",
                f"  🐉 Chinese Zodiac: {summary.get('chinese_zodiac', '')}",
                f"  🔢 Life Path Number: {summary.get('life_path_number', '')}",
                "",
                "Mood factors will now include zodiac and numerology influences.",
                "",
                "View your factors: WELLBEING FACTORS",
            ]

            return {"status": "success", "message": "\n".join(lines)}

        except ValueError:
            return {
                "status": "error",
                "message": "Invalid date format. Use: YYYY-MM-DD (e.g., 1990-03-15)",
            }

    # ═══════════════════════════════════════════════════════════════════════════
    # HOLISTIC WELLBEING - Astrological Mood, Energy Balance, Mindfulness
    # ═══════════════════════════════════════════════════════════════════════════

    def _handle_mind(self, params: list, grid=None) -> dict:
        """Set or query mind state - encouraging mindfulness, breaks, rest.

        Usage:
            WELLBEING MIND              - Show current mind state
            WELLBEING MIND focused      - Set to focused mode
            WELLBEING MIND resting      - Set to resting mode
            WELLBEING MIND wandering    - Acknowledge wandering (get suggestion)
        """
        if not params:
            # Show current mind state
            mind_state = self.service.get_mind_state()

            lines = [
                "🧠 MIND STATE",
                "",
                f"{mind_state.icon} {mind_state.name}: {mind_state.description}",
                f"Mindfulness Level: {mind_state.mindfulness_level:.0%}",
                "",
                "Set your mind state:",
            ]

            for state in MindState:
                lines.append(
                    f"  WELLBEING MIND {state.name.lower():<10} {state.icon} {state.description}"
                )

            return {"status": "success", "message": "\n".join(lines)}

        # Set mind state
        state_name = params[0].lower()

        try:
            result = self.service.set_mind_state(state_name)
            mind_state = result["mind_state"]

            self._log_entry("mind", state_name)
            logger.info(f"[LOCAL] Mind state set: {state_name}")

            message = [
                f"{mind_state.icon} Mind state: {mind_state.name}",
                "",
                f"{mind_state.description}",
                "",
            ]

            # Add mindfulness suggestions based on state
            if mind_state == MindState.WANDERING or mind_state == MindState.SCATTERED:
                message.extend(
                    [
                        "💡 Mindfulness suggestions:",
                        "  • Take 3 deep breaths",
                        "  • Stand and stretch for 30 seconds",
                        "  • Ground yourself - name 5 things you can see",
                        "",
                        "When ready: WELLBEING MIND focused",
                    ]
                )
            elif mind_state == MindState.DRIFTING:
                message.extend(
                    [
                        "💤 Rest suggestions:",
                        "  • Consider a 10-minute power nap",
                        "  • Step outside for fresh air",
                        "  • Make a warm drink",
                        "",
                        "uDOS will conserve energy and simplify tasks.",
                    ]
                )
            elif mind_state == MindState.FOCUSED:
                message.extend(
                    [
                        "🎯 Focus mode active",
                        "  • Notifications minimized",
                        "  • Tasks prioritized for deep work",
                        "  • Break reminder in 45 minutes",
                    ]
                )

            return {"status": "success", "message": "\n".join(message)}

        except ValueError as e:
            valid_states = ", ".join(s.name.lower() for s in MindState)
            return {
                "status": "error",
                "message": f"Unknown mind state: {state_name}\nValid states: {valid_states}",
            }

    def _handle_celestial(self, params: list, grid=None) -> dict:
        """Show astrological influences on mood and energy.

        Usage:
            WELLBEING CELESTIAL         - Show all celestial influences
            WELLBEING CELESTIAL sign    - Show your zodiac sign details
            WELLBEING CELESTIAL moon    - Show current moon phase
        """
        if params and params[0].lower() == "sign":
            return self._show_zodiac_sign(grid)
        elif params and params[0].lower() == "moon":
            return self._show_moon_phase(grid)

        # Show full celestial overview
        zodiac = self.service.get_zodiac_sign()
        moon = self.service.get_moon_phase()
        mood = self.service.calculate_mood()

        lines = [
            "✨ CELESTIAL INFLUENCES",
            "",
            "─" * 40,
            "",
            f"☀️ Sun Sign: {zodiac.symbol} {zodiac.name_str.title()}",
            f"   Element: {zodiac.element_emoji} {zodiac.element.title()}",
            f"   Quality: {zodiac.modality.title()}",
            "",
            f"🌙 Moon Phase: {moon.icon} {moon.name_str.replace('_', ' ').title()}",
            f"   Theme: {moon.theme.title()}",
            f"   Mood Influence: {moon.mood_modifier:+.0%}",
            "",
        ]

        # Show all mood influences
        lines.extend(
            [
                "─" * 40,
                "",
                "📊 Current Mood Influences:",
                "",
            ]
        )

        for influence in mood.influences:
            weight_bar = "█" * int(influence.weight * 10) + "░" * (
                10 - int(influence.weight * 10)
            )
            lines.append(
                f"  {influence.icon} {influence.source:<12} [{weight_bar}] {influence.value:+.0%}"
            )

        lines.extend(
            [
                "",
                f"🎭 Combined Mood: {mood.theme.title()}",
                f"   Base: {mood.base_value:.1f}/5 → Final: {mood.calculated_value:.1f}/5",
                "",
                "─" * 40,
                "",
                "💡 Celestial Tip:",
                f"   Moon in {moon.theme} phase - {self._get_moon_advice(moon)}",
            ]
        )

        return {
            "status": "success",
            "message": "\n".join(lines),
            "data": {
                "zodiac": zodiac.name_str,
                "moon_phase": moon.name_str,
                "mood": mood.calculated_value,
            },
        }

    def _get_moon_advice(self, moon: MoonPhase) -> str:
        """Get advice based on moon phase."""
        advice = {
            MoonPhase.NEW_MOON: "Good for setting intentions and new beginnings",
            MoonPhase.WAXING_CRESCENT: "Build momentum with small steps",
            MoonPhase.FIRST_QUARTER: "Time for action and decisions",
            MoonPhase.WAXING_GIBBOUS: "Refine and prepare for completion",
            MoonPhase.FULL_MOON: "Celebrate achievements, culminate efforts",
            MoonPhase.WANING_GIBBOUS: "Share knowledge and express gratitude",
            MoonPhase.LAST_QUARTER: "Release what no longer serves you",
            MoonPhase.WANING_CRESCENT: "Rest and recuperate",
        }
        return advice.get(moon, "Follow your natural rhythm")

    def _show_zodiac_sign(self, grid=None) -> dict:
        """Show detailed zodiac sign information."""
        zodiac = self.service.get_zodiac_sign()

        # Get date range from enum value
        start_month, start_day = zodiac.value[5]
        end_month, end_day = zodiac.value[6]

        lines = [
            f"☀️ YOUR ZODIAC SIGN: {zodiac.symbol} {zodiac.name_str.upper()}",
            "",
            f"Element: {zodiac.element_emoji} {zodiac.element.title()}",
            f"Quality: {zodiac.modality.title()}",
            f"Date Range: {start_month}/{start_day} - {end_month}/{end_day}",
            "",
        ]

        # Add element-based traits
        element_traits = {
            "fire": ["Passionate", "Dynamic", "Action-oriented", "Enthusiastic"],
            "earth": ["Practical", "Grounded", "Patient", "Reliable"],
            "air": ["Intellectual", "Communicative", "Social", "Adaptable"],
            "water": ["Intuitive", "Emotional", "Empathetic", "Creative"],
        }

        traits = element_traits.get(zodiac.element, [])
        if traits:
            lines.extend(["Traits:", *[f"  • {t}" for t in traits], ""])

        # Workflow suggestions based on element
        element_workflows = {
            "fire": "Best for creative bursts, starting projects, bold decisions",
            "earth": "Best for systematic work, detailed tasks, long-term planning",
            "air": "Best for collaboration, communication, brainstorming",
            "water": "Best for intuitive work, reflection, emotional intelligence tasks",
        }

        workflow = element_workflows.get(zodiac.element, "")
        if workflow:
            lines.extend(
                [
                    "🔧 Workflow Affinity:",
                    f"   {workflow}",
                ]
            )

        return {"status": "success", "message": "\n".join(lines)}

    def _show_moon_phase(self, grid=None) -> dict:
        """Show current moon phase and its influence."""
        moon = self.service.get_moon_phase()

        phase_advice = {
            MoonPhase.NEW_MOON: "Good for: New beginnings, setting intentions, quiet reflection",
            MoonPhase.WAXING_CRESCENT: "Good for: Building momentum, initial planning, small steps",
            MoonPhase.FIRST_QUARTER: "Good for: Taking action, making decisions, problem-solving",
            MoonPhase.WAXING_GIBBOUS: "Good for: Refinement, details, preparation",
            MoonPhase.FULL_MOON: "Good for: Completion, celebration, culmination of efforts",
            MoonPhase.WANING_GIBBOUS: "Good for: Sharing knowledge, gratitude, teaching",
            MoonPhase.LAST_QUARTER: "Good for: Release, letting go, clearing space",
            MoonPhase.WANING_CRESCENT: "Good for: Rest, surrender, recuperation",
        }

        lines = [
            f"🌙 MOON PHASE: {moon.icon} {moon.name_str.replace('_', ' ').upper()}",
            "",
            f"Theme: {moon.theme.title()}",
            f"Mood Influence: {moon.mood_modifier:+.0%}",
            "",
            phase_advice.get(moon, ""),
            "",
            "uDOS task suggestions adapt to lunar rhythms,",
            "balancing productivity with natural cycles.",
        ]

        return {"status": "success", "message": "\n".join(lines)}

    def _handle_ruok(self, params: list, grid=None) -> dict:
        """RUOK? - Are You OK? Mutual wellbeing check.

        The system checks on the user (or user checks on system).
        Provides pathways and options to benefit the recipient.

        Usage:
            WELLBEING RUOK      - System checks on you
            WELLBEING RUOK? ME  - You reflect on your own state
            WELLBEING RUOK SYS  - You check on the system
        """
        target = params[0].lower() if params else "user"

        if target in ["sys", "system"]:
            return self._ruok_check_system(grid)

        # Default: system checks on user
        return self._ruok_check_user(grid)

    def _ruok_check_user(self, grid=None) -> dict:
        """System checks on user wellbeing."""
        check = self.service.ruok_check()

        # Calculate wellness score based on concerns
        concern_count = len(check.concerns)
        wellness_score = max(0.0, 1.0 - (concern_count * 0.25))

        lines = [
            "💚 R U OK?",
            "",
            "uDOS is checking in on you.",
            "",
            "─" * 40,
            "",
        ]

        # Show status
        status_icons = {"ok": "✅", "concern": "⚠️", "alert": "🚨"}
        lines.append(
            f"Status: {status_icons.get(check.status, '❓')} {check.status.upper()}"
        )
        lines.append("")

        # Show concerns
        if check.concerns:
            lines.extend(
                [
                    "📊 Observations:",
                    "",
                ]
            )
            for concern in check.concerns:
                lines.append(f"  ⚠️ {concern}")
        else:
            lines.append("✨ No concerns detected!")

        lines.extend(
            [
                "",
                "─" * 40,
                "",
                f"Overall Wellness: {wellness_score:.0%}",
                "",
            ]
        )

        # Show suggestions
        if check.suggestions:
            lines.extend(
                [
                    "💡 Suggestions for You:",
                    "",
                ]
            )
            for sug in check.suggestions:
                lines.append(f"  • {sug}")

        # Show command pathways
        if check.pathways:
            lines.extend(
                [
                    "",
                    "🛤️ Quick Actions:",
                    "",
                ]
            )
            for path in check.pathways:
                lines.append(f"  → {path}")

        lines.extend(
            [
                "",
                "─" * 40,
                "",
            ]
        )

        # Closing message based on wellness
        if wellness_score < 0.5:
            lines.extend(
                [
                    "🤝 How can uDOS help?",
                    "",
                    "Remember: Conservation > Performance",
                    "Variety supports wellness.",
                ]
            )
        else:
            lines.extend(
                [
                    "✨ You seem to be doing well!",
                    "",
                    "Keep up the good balance. uDOS is here",
                    "whenever you need support.",
                ]
            )

        # Log the check
        self._log_entry("ruok_user", wellness_score)
        logger.info(f"[LOCAL] RUOK user check: {wellness_score:.0%}")

        return {
            "status": "success",
            "message": "\n".join(lines),
            "data": {
                "wellness_score": wellness_score,
                "status": check.status,
                "concerns": check.concerns,
                "suggestions": check.suggestions,
            },
        }

    def _ruok_check_system(self, grid=None) -> dict:
        """User checks on system wellbeing."""
        # Get system health metrics (psutil imported at module level)
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()

        # Calculate system wellness
        cpu_wellness = max(0, 1 - (cpu / 100))
        mem_wellness = memory.available / memory.total
        overall = (cpu_wellness + mem_wellness) / 2

        lines = [
            "🖥️ SYSTEM WELLNESS CHECK",
            "",
            "You asked: Is uDOS okay?",
            "",
            "─" * 40,
            "",
            f"💾 Memory: {memory.available / (1024**3):.1f}GB free of {memory.total / (1024**3):.1f}GB",
            f"   Health: {'█' * int(mem_wellness * 10)}{'░' * (10 - int(mem_wellness * 10))} {mem_wellness:.0%}",
            "",
            f"⚡ CPU: {cpu:.1f}% utilization",
            f"   Health: {'█' * int(cpu_wellness * 10)}{'░' * (10 - int(cpu_wellness * 10))} {cpu_wellness:.0%}",
            "",
            "─" * 40,
            "",
        ]

        if overall > 0.7:
            lines.extend(
                [
                    "✨ uDOS is feeling good!",
                    "",
                    "Resources are healthy and available.",
                    "Ready to support your work.",
                ]
            )
        elif overall > 0.4:
            lines.extend(
                [
                    "😐 uDOS is managing okay.",
                    "",
                    "Consider closing unused applications",
                    "to free up resources.",
                ]
            )
        else:
            lines.extend(
                [
                    "😓 uDOS is under pressure.",
                    "",
                    "Suggestions:",
                    "  • Close unused apps",
                    "  • TIDY to clean temp files",
                    "  • Consider a break",
                ]
            )

        lines.extend(
            [
                "",
                f"Overall System Wellness: {overall:.0%}",
                "",
                "Thank you for checking on me! 💚",
            ]
        )

        self._log_entry("ruok_system", overall)
        logger.info(f"[LOCAL] RUOK system check: {overall:.0%}")

        return {
            "status": "success",
            "message": "\n".join(lines),
            "data": {
                "cpu_percent": cpu,
                "memory_available_gb": memory.available / (1024**3),
                "wellness_score": overall,
            },
        }
