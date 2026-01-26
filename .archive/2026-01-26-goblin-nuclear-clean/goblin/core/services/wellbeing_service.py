"""
uDOS WELLBEING System - Holistic User Wellness
Alpha v1.0.0.65

A mindful, astrological, and resource-aware wellness system that:
- Tracks MOOD influenced by celestial alignments, weather, and user feedback
- Manages ENERGY balance between user enthusiasm, system load, and workflow
- Monitors MIND for mindfulness, encouraging breaks and rest
- Provides RUOK? system checks on user wellbeing

Philosophy:
- Conservation over performance - uDOS seeks to conserve energy and resources
- Variety over intensity - diverse tasks serve user wellness
- Mindfulness over productivity - rest is more important than high output
- Balance over optimization - harmony between user and system

Influences on Mood:
- User star sign (from birth date)
- Current celestial alignments (moon phase, planetary hours)
- Weather conditions (future: Home Assistant integration)
- User feedback and history
- Time of day and season

Energy Balance:
- User enthusiasm (self-reported)
- System load (CPU, memory, tasks)
- Workflow load (pending tasks, deadlines)
- Affects task execution pace and priority ordering

Mind States:
- FOCUSED: Deep work mode
- FLOWING: Creative, open state
- RESTING: Recovery mode
- SCATTERED: Needs grounding
- DRIFTING: Mindfulness prompt needed
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import json
import math

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("wellbeing")


# =============================================================================
# Zodiac and Celestial Definitions
# =============================================================================


class ZodiacSign(Enum):
    """Western zodiac signs with associated traits."""

    ARIES = ("aries", "♈", "🔥", "fire", "cardinal", (3, 21), (4, 19))
    TAURUS = ("taurus", "♉", "🌍", "earth", "fixed", (4, 20), (5, 20))
    GEMINI = ("gemini", "♊", "💨", "air", "mutable", (5, 21), (6, 20))
    CANCER = ("cancer", "♋", "💧", "water", "cardinal", (6, 21), (7, 22))
    LEO = ("leo", "♌", "🔥", "fire", "fixed", (7, 23), (8, 22))
    VIRGO = ("virgo", "♍", "🌍", "earth", "mutable", (8, 23), (9, 22))
    LIBRA = ("libra", "♎", "💨", "air", "cardinal", (9, 23), (10, 22))
    SCORPIO = ("scorpio", "♏", "💧", "water", "fixed", (10, 23), (11, 21))
    SAGITTARIUS = ("sagittarius", "♐", "🔥", "fire", "mutable", (11, 22), (12, 21))
    CAPRICORN = ("capricorn", "♑", "🌍", "earth", "cardinal", (12, 22), (1, 19))
    AQUARIUS = ("aquarius", "♒", "💨", "air", "fixed", (1, 20), (2, 18))
    PISCES = ("pisces", "♓", "💧", "water", "mutable", (2, 19), (3, 20))

    @property
    def name_str(self) -> str:
        return self.value[0]

    @property
    def symbol(self) -> str:
        return self.value[1]

    @property
    def element_emoji(self) -> str:
        return self.value[2]

    @property
    def element(self) -> str:
        return self.value[3]

    @property
    def modality(self) -> str:
        return self.value[4]

    @classmethod
    def from_date(cls, birth_date: date) -> "ZodiacSign":
        """Get zodiac sign from birth date."""
        month, day = birth_date.month, birth_date.day
        for sign in cls:
            start_month, start_day = sign.value[5]
            end_month, end_day = sign.value[6]

            # Handle Capricorn spanning year boundary
            if start_month > end_month:  # Capricorn
                if (month == start_month and day >= start_day) or (
                    month == end_month and day <= end_day
                ):
                    return sign
            else:
                if (
                    (month == start_month and day >= start_day)
                    or (month == end_month and day <= end_day)
                    or (start_month < month < end_month)
                ):
                    return sign
        return cls.ARIES  # Fallback


class MoonPhase(Enum):
    """Moon phases with energy associations."""

    NEW_MOON = ("new", "🌑", "introspection", -0.2)
    WAXING_CRESCENT = ("waxing_crescent", "🌒", "initiation", 0.0)
    FIRST_QUARTER = ("first_quarter", "🌓", "action", 0.1)
    WAXING_GIBBOUS = ("waxing_gibbous", "🌔", "refinement", 0.15)
    FULL_MOON = ("full", "🌕", "culmination", 0.2)
    WANING_GIBBOUS = ("waning_gibbous", "🌖", "gratitude", 0.1)
    LAST_QUARTER = ("last_quarter", "🌗", "release", 0.0)
    WANING_CRESCENT = ("waning_crescent", "🌘", "rest", -0.15)

    @property
    def name_str(self) -> str:
        return self.value[0]

    @property
    def icon(self) -> str:
        return self.value[1]

    @property
    def theme(self) -> str:
        return self.value[2]

    @property
    def mood_modifier(self) -> float:
        """Mood influence (-0.2 to +0.2)."""
        return self.value[3]

    @classmethod
    def current(cls) -> "MoonPhase":
        """Calculate current moon phase (simplified)."""
        # Synodic month is ~29.53 days
        # Known new moon: Jan 6, 2000
        known_new_moon = datetime(2000, 1, 6, 18, 14)
        now = datetime.now()
        days_since = (now - known_new_moon).total_seconds() / 86400
        lunation = days_since % 29.53

        if lunation < 1.85:
            return cls.NEW_MOON
        elif lunation < 7.38:
            return cls.WAXING_CRESCENT
        elif lunation < 9.23:
            return cls.FIRST_QUARTER
        elif lunation < 14.77:
            return cls.WAXING_GIBBOUS
        elif lunation < 16.61:
            return cls.FULL_MOON
        elif lunation < 22.15:
            return cls.WANING_GIBBOUS
        elif lunation < 24.0:
            return cls.LAST_QUARTER
        else:
            return cls.WANING_CRESCENT


class PlanetaryHour(Enum):
    """Planetary hours for timing activities."""

    SUN = ("sun", "☉", "creativity, leadership")
    MOON = ("moon", "☽", "intuition, emotions")
    MARS = ("mars", "♂", "action, courage")
    MERCURY = ("mercury", "☿", "communication, learning")
    JUPITER = ("jupiter", "♃", "expansion, luck")
    VENUS = ("venus", "♀", "harmony, beauty")
    SATURN = ("saturn", "♄", "discipline, structure")

    @property
    def name_str(self) -> str:
        return self.value[0]

    @property
    def symbol(self) -> str:
        return self.value[1]

    @property
    def theme(self) -> str:
        return self.value[2]


# =============================================================================
# Mind States
# =============================================================================


class MindState(Enum):
    """Mental states for mindfulness tracking."""

    FOCUSED = ("focused", "🎯", "Deep concentration mode", 1.0)
    FLOWING = ("flowing", "🌊", "Creative, open state", 0.8)
    STEADY = ("steady", "⚖️", "Balanced, stable", 0.6)
    WANDERING = ("wandering", "🦋", "Mind drifting, needs grounding", 0.4)
    SCATTERED = ("scattered", "💫", "Fragmented attention", 0.3)
    RESTING = ("resting", "🌙", "Recovery mode", 0.2)
    DRIFTING = ("drifting", "☁️", "Mindfulness prompt needed", 0.1)

    @property
    def name_str(self) -> str:
        return self.value[0]

    @property
    def icon(self) -> str:
        return self.value[1]

    @property
    def description(self) -> str:
        return self.value[2]

    @property
    def productivity_factor(self) -> float:
        """Factor for task pacing (0.1 to 1.0)."""
        return self.value[3]


# =============================================================================
# Mood System (Astrological)
# =============================================================================


@dataclass
class MoodInfluence:
    """A factor influencing mood."""

    source: str  # "zodiac", "moon", "weather", "user", "time", "sensor"
    name: str  # Human-readable name
    value: float  # Influence value (-1.0 to +1.0)
    weight: float = 1.0  # How much this matters
    icon: str = ""
    note: str = ""


@dataclass
class MoodState:
    """Current mood with all influences."""

    base_value: float = 3.0  # User-reported (1-5 scale)
    influences: List[MoodInfluence] = field(default_factory=list)
    calculated_value: float = 3.0  # After all influences
    theme: str = "neutral"
    icon: str = "😐"

    def calculate(self) -> float:
        """Calculate final mood from base + influences."""
        total_influence = 0.0
        total_weight = 0.0

        for inf in self.influences:
            total_influence += inf.value * inf.weight
            total_weight += inf.weight

        if total_weight > 0:
            avg_influence = total_influence / total_weight
        else:
            avg_influence = 0.0

        # Apply influence to base (capped at 1-5)
        self.calculated_value = max(1.0, min(5.0, self.base_value + avg_influence))

        # Set theme and icon
        if self.calculated_value >= 4.5:
            self.theme = "radiant"
            self.icon = "✨"
        elif self.calculated_value >= 3.5:
            self.theme = "bright"
            self.icon = "😊"
        elif self.calculated_value >= 2.5:
            self.theme = "neutral"
            self.icon = "😐"
        elif self.calculated_value >= 1.5:
            self.theme = "dim"
            self.icon = "😔"
        else:
            self.theme = "dark"
            self.icon = "😢"

        return self.calculated_value


# =============================================================================
# Energy System (Resource Balance)
# =============================================================================


@dataclass
class EnergyBalance:
    """Balance between user, system, and workflow energy."""

    user_enthusiasm: float = 0.5  # User's reported energy (0-1)
    system_load: float = 0.2  # CPU/memory usage (0-1)
    workflow_load: float = 0.3  # Pending tasks weight (0-1)
    calculated_pace: float = 0.5  # Resulting task pace (0-1)

    def calculate_pace(self) -> float:
        """
        Calculate task execution pace based on energy balance.

        uDOS philosophy: conserve energy, avoid pressure-cooker situations.
        """
        # User has priority - if low enthusiasm, slow down regardless
        if self.user_enthusiasm < 0.3:
            # Low user energy = slow pace
            self.calculated_pace = 0.2
        elif self.system_load > 0.8:
            # High system load = slow pace to conserve
            self.calculated_pace = 0.3
        elif self.workflow_load > 0.8 and self.user_enthusiasm < 0.5:
            # Heavy workload + moderate user = gentle pace
            self.calculated_pace = 0.4
        else:
            # Balance: user enthusiasm modified by loads
            base_pace = self.user_enthusiasm
            load_penalty = (self.system_load + self.workflow_load) / 4
            self.calculated_pace = max(0.2, min(1.0, base_pace - load_penalty))

        return self.calculated_pace

    def get_pace_description(self) -> Tuple[str, str]:
        """Get human-readable pace description."""
        if self.calculated_pace >= 0.8:
            return ("🚀 Energized", "Full speed - tackle complex tasks")
        elif self.calculated_pace >= 0.6:
            return ("🏃 Active", "Good pace - balanced workload")
        elif self.calculated_pace >= 0.4:
            return ("🚶 Steady", "Moderate pace - focus on essentials")
        elif self.calculated_pace >= 0.2:
            return ("🐢 Gentle", "Slow pace - light tasks only")
        else:
            return ("🌙 Resting", "Rest mode - recovery time")


# =============================================================================
# RUOK System (Mutual Wellbeing Check)
# =============================================================================


@dataclass
class RUOKCheck:
    """A wellbeing check result."""

    timestamp: datetime
    initiator: str  # "system" or "user"
    target: str  # "user" or "system"
    status: str  # "ok", "concern", "alert"
    concerns: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    pathways: List[str] = field(default_factory=list)  # Commands to offer


class RUOKChecker:
    """Mutual wellbeing checker - system checks user, user checks system."""

    # Thresholds for concern
    LOW_MOOD_THRESHOLD = 2.5
    LOW_ENERGY_THRESHOLD = 0.3
    SCATTERED_MIND_STATES = ["scattered", "drifting"]
    LONG_SESSION_MINUTES = 90

    @classmethod
    def check_user(
        cls,
        mood: MoodState,
        energy: EnergyBalance,
        mind: MindState,
        session_minutes: int = 0,
        last_break_minutes: int = 0,
    ) -> RUOKCheck:
        """System checks on user wellbeing."""
        check = RUOKCheck(
            timestamp=datetime.now(), initiator="system", target="user", status="ok"
        )

        # Check mood
        if mood.calculated_value < cls.LOW_MOOD_THRESHOLD:
            check.concerns.append(f"Mood seems low ({mood.icon} {mood.theme})")
            check.suggestions.append("Consider a break or change of activity")
            check.pathways.append("WELLBEING BREAK")
            check.pathways.append("WELLBEING SUGGEST")

        # Check energy
        if energy.user_enthusiasm < cls.LOW_ENERGY_THRESHOLD:
            check.concerns.append("Energy running low")
            check.suggestions.append("Rest is more productive than pushing through")
            check.pathways.append("WELLBEING REST")

        # Check mind state
        if mind.name_str in cls.SCATTERED_MIND_STATES:
            check.concerns.append(f"Mind seems {mind.name_str}")
            check.suggestions.append("Try a grounding exercise or short meditation")
            check.pathways.append("WELLBEING MIND ground")

        # Check session length
        if session_minutes > cls.LONG_SESSION_MINUTES:
            check.concerns.append(f"Long session ({session_minutes}m without break)")
            check.suggestions.append(
                "Take a proper break - stretch, hydrate, rest eyes"
            )
            check.pathways.append("WELLBEING BREAK")

        # Check break frequency
        if last_break_minutes > 60:
            check.concerns.append(f"No break in {last_break_minutes} minutes")
            check.suggestions.append("Regular breaks improve focus and creativity")
            check.pathways.append("WELLBEING BREAK")

        # Set overall status
        if len(check.concerns) >= 3:
            check.status = "alert"
        elif len(check.concerns) >= 1:
            check.status = "concern"

        return check

    @classmethod
    def check_system(
        cls,
        cpu_percent: float = 0.0,
        memory_percent: float = 0.0,
        pending_tasks: int = 0,
        error_count: int = 0,
    ) -> RUOKCheck:
        """User checks on system wellbeing."""
        check = RUOKCheck(
            timestamp=datetime.now(), initiator="user", target="system", status="ok"
        )

        # Check CPU
        if cpu_percent > 80:
            check.concerns.append(f"High CPU usage ({cpu_percent:.0f}%)")
            check.suggestions.append("Consider pausing background tasks")
            check.pathways.append("STATUS TASKS")

        # Check memory
        if memory_percent > 85:
            check.concerns.append(f"High memory usage ({memory_percent:.0f}%)")
            check.suggestions.append("Close unused applications")
            check.pathways.append("STATUS MEMORY")

        # Check task queue
        if pending_tasks > 20:
            check.concerns.append(f"Large task queue ({pending_tasks} pending)")
            check.suggestions.append("Review and prioritize tasks")
            check.pathways.append("TASK LIST")

        # Check errors
        if error_count > 5:
            check.concerns.append(f"Recent errors detected ({error_count})")
            check.suggestions.append("Review error log")
            check.pathways.append("DEV ERRORS")

        # Set overall status
        if len(check.concerns) >= 2:
            check.status = "alert"
        elif len(check.concerns) >= 1:
            check.status = "concern"

        return check


# =============================================================================
# Wellbeing Service
# =============================================================================


class WellbeingService:
    """
    Holistic wellbeing service integrating mood, energy, mind, and RUOK.

    This service is designed to:
    1. Calculate mood from multiple sources (astrological, environmental, user)
    2. Balance energy between user, system, and workflow demands
    3. Track mind state for mindfulness prompts
    4. Provide mutual RUOK checks
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path("memory/private/wellbeing")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.state_file = self.data_dir / "state.json"
        self.history_file = self.data_dir / "history.json"

        # Current state
        self.mood = MoodState()
        self.energy = EnergyBalance()
        self.mind_state = MindState.STEADY
        self.user_zodiac: Optional[ZodiacSign] = None

        # Session tracking
        self.session_start = datetime.now()
        self.last_break = datetime.now()
        self.last_ruok_check: Optional[RUOKCheck] = None

        # Load saved state
        self._load_state()

    def _load_state(self):
        """Load persisted state."""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self.mood.base_value = data.get("mood_base", 3.0)
                self.energy.user_enthusiasm = data.get("user_enthusiasm", 0.5)

                mind_str = data.get("mind_state", "steady")
                for ms in MindState:
                    if ms.name_str == mind_str:
                        self.mind_state = ms
                        break

                if data.get("birth_date"):
                    try:
                        bd = datetime.fromisoformat(data["birth_date"]).date()
                        self.user_zodiac = ZodiacSign.from_date(bd)
                    except:
                        pass

                if data.get("last_break"):
                    try:
                        self.last_break = datetime.fromisoformat(data["last_break"])
                    except:
                        pass

            except Exception as e:
                logger.warning(f"Could not load wellbeing state: {e}")

    def _save_state(self):
        """Persist current state."""
        data = {
            "mood_base": self.mood.base_value,
            "user_enthusiasm": self.energy.user_enthusiasm,
            "mind_state": self.mind_state.name_str,
            "last_break": self.last_break.isoformat(),
            "updated": datetime.now().isoformat(),
        }

        if self.user_zodiac:
            # We don't store birth_date, only zodiac sign
            data["zodiac_sign"] = self.user_zodiac.name_str

        self.state_file.write_text(json.dumps(data, indent=2))

    def set_birth_date(self, birth_date: date):
        """Set user's birth date for zodiac calculation."""
        self.user_zodiac = ZodiacSign.from_date(birth_date)
        logger.info(
            f"[LOCAL] Set zodiac sign: {self.user_zodiac.symbol} {self.user_zodiac.name_str}"
        )

    def calculate_mood(self, user_input: Optional[float] = None) -> MoodState:
        """
        Calculate mood from all influences.

        Influences:
        - User input (if provided)
        - Zodiac sign compatibility with current day
        - Moon phase
        - Time of day
        - Weather (future)
        - Sensors (future: Home Assistant)
        """
        if user_input is not None:
            self.mood.base_value = max(1.0, min(5.0, user_input))

        self.mood.influences.clear()

        # Moon phase influence
        moon = MoonPhase.current()
        self.mood.influences.append(
            MoodInfluence(
                source="moon",
                name=f"Moon Phase: {moon.name_str.replace('_', ' ').title()}",
                value=moon.mood_modifier,
                weight=0.8,
                icon=moon.icon,
                note=f"Theme: {moon.theme}",
            )
        )

        # Zodiac influence (if set)
        if self.user_zodiac:
            # Element compatibility with current day
            # Fire/Air days (odd) vs Earth/Water days (even) - simplified
            day_of_year = datetime.now().timetuple().tm_yday
            is_active_day = day_of_year % 2 == 1

            if self.user_zodiac.element in ["fire", "air"]:
                zodiac_mod = 0.1 if is_active_day else -0.05
            else:
                zodiac_mod = 0.1 if not is_active_day else -0.05

            self.mood.influences.append(
                MoodInfluence(
                    source="zodiac",
                    name=f"Star Sign: {self.user_zodiac.symbol} {self.user_zodiac.name_str.title()}",
                    value=zodiac_mod,
                    weight=0.5,
                    icon=self.user_zodiac.element_emoji,
                    note=f"Element: {self.user_zodiac.element}",
                )
            )

        # Time of day influence
        hour = datetime.now().hour
        if 6 <= hour < 10:
            time_mod = 0.1  # Morning boost
            time_note = "Morning energy"
        elif 10 <= hour < 14:
            time_mod = 0.15  # Peak hours
            time_note = "Peak productivity"
        elif 14 <= hour < 17:
            time_mod = -0.1  # Afternoon dip
            time_note = "Afternoon lull"
        elif 17 <= hour < 21:
            time_mod = 0.05  # Evening
            time_note = "Evening wind-down"
        else:
            time_mod = -0.15  # Night
            time_note = "Rest time"

        self.mood.influences.append(
            MoodInfluence(
                source="time",
                name="Time of Day",
                value=time_mod,
                weight=0.6,
                icon="🕐",
                note=time_note,
            )
        )

        # TODO: Weather influence (future Home Assistant integration)
        # TODO: Sensor influences (future Home Assistant integration)

        self.mood.calculate()
        self._save_state()

        return self.mood

    def set_energy(self, user_enthusiasm: float):
        """Set user enthusiasm level (0-1)."""
        self.energy.user_enthusiasm = max(0.0, min(1.0, user_enthusiasm))
        self.energy.calculate_pace()
        self._save_state()

    def update_system_load(self, cpu: float = 0.0, memory: float = 0.0):
        """Update system load metrics."""
        self.energy.system_load = (cpu + memory) / 2
        self.energy.calculate_pace()

    def update_workflow_load(self, pending_tasks: int = 0, urgent_count: int = 0):
        """Update workflow load."""
        # Normalize: 0 tasks = 0.0, 20+ tasks = 1.0
        task_load = min(1.0, pending_tasks / 20)
        urgent_load = min(1.0, urgent_count / 5) * 0.3  # Urgent adds 30% max
        self.energy.workflow_load = min(1.0, task_load + urgent_load)
        self.energy.calculate_pace()

    def set_mind_state(self, state: str) -> dict:
        """Set current mind state."""
        for ms in MindState:
            if ms.name_str == state.lower():
                self.mind_state = ms
                self._save_state()
                return {"mind_state": ms}
        raise ValueError(f"Unknown mind state: {state}")

    def get_mind_state(self) -> MindState:
        """Get current mind state."""
        return self.mind_state

    def get_zodiac_sign(self) -> ZodiacSign:
        """Get user's zodiac sign (or default based on current date)."""
        if self.user_zodiac:
            return self.user_zodiac
        # Default to current date's sign if not set
        return ZodiacSign.from_date(date.today())

    def get_moon_phase(self) -> MoonPhase:
        """Get current moon phase."""
        return MoonPhase.current()

    def log_break(self):
        """Log that user took a break."""
        self.last_break = datetime.now()
        self._save_state()
        logger.info("[LOCAL] Break logged")

    def get_session_minutes(self) -> int:
        """Get minutes since session start."""
        return int((datetime.now() - self.session_start).total_seconds() / 60)

    def get_minutes_since_break(self) -> int:
        """Get minutes since last break."""
        return int((datetime.now() - self.last_break).total_seconds() / 60)

    def ruok_check(self) -> RUOKCheck:
        """Perform RUOK check on user."""
        self.calculate_mood()  # Update mood
        self.energy.calculate_pace()  # Update energy

        check = RUOKChecker.check_user(
            mood=self.mood,
            energy=self.energy,
            mind=self.mind_state,
            session_minutes=self.get_session_minutes(),
            last_break_minutes=self.get_minutes_since_break(),
        )

        self.last_ruok_check = check
        return check

    def get_task_suggestions(self) -> List[str]:
        """Get task suggestions based on current wellbeing state."""
        suggestions = []
        pace = self.energy.calculated_pace
        mood = self.mood.calculated_value
        mind = self.mind_state

        # Mind-state specific suggestions
        if mind == MindState.DRIFTING:
            suggestions.append("🧘 Take a mindful pause - WELLBEING MIND")
            suggestions.append("🚶 Step away for fresh air")
        elif mind == MindState.SCATTERED:
            suggestions.append("📋 Review your priorities - TASK LIST")
            suggestions.append("🎯 Pick ONE thing to focus on")
        elif mind == MindState.RESTING:
            suggestions.append("☕ Honor your rest time")
            suggestions.append("📖 Light reading from Knowledge Bank")

        # Energy-based suggestions
        if pace < 0.3:
            suggestions.append("💤 Rest mode - no complex tasks")
            suggestions.append("📚 Review knowledge (GUIDE)")
        elif pace < 0.5:
            suggestions.append("🚶 Gentle pace - small wins only")
            suggestions.append("📁 Organize or review (INBOX)")
        elif pace < 0.7:
            suggestions.append("⚖️ Balanced pace - steady progress")
            suggestions.append("📝 Work on current project")
        else:
            suggestions.append("🚀 Full energy - tackle challenges")
            suggestions.append("🎯 Complex tasks welcome (MISSION)")

        # Mood-based additions
        if mood < 2.5:
            suggestions.insert(0, "💚 Self-care first - WELLBEING BREAK")
        elif mood > 4.0:
            suggestions.append("✨ Positive energy - share with others!")

        return suggestions[:5]  # Limit to 5 suggestions

    def get_os_mood_theme(self) -> Dict[str, Any]:
        """
        Get mood theme for uDOS UI.

        The system mood affects:
        - Color palette hints
        - Animation speed
        - Sound/feedback intensity
        - Message tone
        """
        mood_val = self.mood.calculated_value

        if mood_val >= 4.0:
            return {
                "theme": "radiant",
                "palette": "warm",
                "animation_speed": 1.0,
                "feedback_intensity": "gentle",
                "message_tone": "encouraging",
                "ambient": "bright",
            }
        elif mood_val >= 3.0:
            return {
                "theme": "balanced",
                "palette": "neutral",
                "animation_speed": 0.8,
                "feedback_intensity": "moderate",
                "message_tone": "supportive",
                "ambient": "calm",
            }
        elif mood_val >= 2.0:
            return {
                "theme": "gentle",
                "palette": "cool",
                "animation_speed": 0.6,
                "feedback_intensity": "soft",
                "message_tone": "caring",
                "ambient": "quiet",
            }
        else:
            return {
                "theme": "restful",
                "palette": "muted",
                "animation_speed": 0.4,
                "feedback_intensity": "minimal",
                "message_tone": "nurturing",
                "ambient": "peaceful",
            }
