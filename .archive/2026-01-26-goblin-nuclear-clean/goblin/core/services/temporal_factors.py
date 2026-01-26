"""
uDOS Temporal Factors - Time-Based Mood Influences
Alpha v1.0.0.65

Calculates mood factors based on temporal patterns:
- Circadian rhythm (alertness curve based on chronotype)
- Ultradian rhythm (90-minute cycles)
- Day of week effect
- Seasonal patterns
- Numerology (daily number resonance with life path)

All calculations run locally without internet access.
"""

import math
from datetime import datetime, date, time, timedelta
from typing import Dict, Any, Optional

from dev.goblin.core.services.mood_factors import (
    BaseFactor,
    BaseCategoryCalculator,
    MoodFactorResult,
    FactorCategory,
    FactorConfidence,
    normalize_score,
    gaussian_peak,
)
from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("temporal-factors")


# =============================================================================
# Circadian Constants
# =============================================================================

# Chronotype profiles: (wake_time, morning_peak, afternoon_dip, evening_peak, sleep_time)
# Times in hours from midnight
CHRONOTYPES = {
    "early": {
        "wake": 5.5,
        "morning_peak": 9.0,
        "afternoon_dip": 14.0,
        "evening_peak": 18.0,
        "sleep": 21.5,
        "label": "Early Bird 🐦",
    },
    "intermediate": {
        "wake": 7.0,
        "morning_peak": 10.5,
        "afternoon_dip": 15.0,
        "evening_peak": 19.5,
        "sleep": 23.0,
        "label": "Intermediate ⚖️",
    },
    "late": {
        "wake": 9.0,
        "morning_peak": 12.0,
        "afternoon_dip": 16.0,
        "evening_peak": 21.0,
        "sleep": 1.0,  # 1 AM next day
        "label": "Night Owl 🦉",
    },
}


def time_to_hours(t: time) -> float:
    """Convert time to hours from midnight."""
    return t.hour + t.minute / 60.0 + t.second / 3600.0


def hours_to_time(hours: float) -> time:
    """Convert hours from midnight to time."""
    hours = hours % 24
    h = int(hours)
    m = int((hours - h) * 60)
    return time(h, m)


# =============================================================================
# Temporal Factor Implementations
# =============================================================================


class CircadianFactor(BaseFactor):
    """
    Factor based on circadian rhythm alertness curve.

    Uses chronotype-adjusted model with:
    - Morning rise to peak
    - Post-lunch dip
    - Second peak in late afternoon/evening
    - Evening decline

    This is one of the most scientifically validated factors.
    """

    name = "circadian_rhythm"
    category = FactorCategory.TEMPORAL
    weight = 2.0  # Higher weight - well-researched

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        dt = context.get("datetime", datetime.now())
        current_hour = time_to_hours(dt.time())

        # Get chronotype from identity
        identity = context.get("identity")
        chronotype = identity.chronotype if identity else "intermediate"

        profile = CHRONOTYPES.get(chronotype, CHRONOTYPES["intermediate"])

        # Calculate alertness based on time position in circadian cycle
        score = self._calculate_alertness(current_hour, profile)

        # Determine current phase
        phase = self._get_phase(current_hour, profile)

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.HIGH,
            weight=self.weight,
            raw_value=current_hour,
            description=f"{profile['label']}: {phase}",
            metadata={
                "chronotype": chronotype,
                "current_hour": round(current_hour, 2),
                "phase": phase,
                "alertness": round(score, 2),
            },
        )

    def _calculate_alertness(self, hour: float, profile: Dict) -> float:
        """Calculate alertness score based on circadian curve."""
        wake = profile["wake"]
        morning_peak = profile["morning_peak"]
        dip = profile["afternoon_dip"]
        evening_peak = profile["evening_peak"]
        sleep = profile["sleep"]

        # Handle late chronotype sleep time (past midnight)
        if sleep < wake:
            sleep += 24
            if hour < wake:
                hour += 24

        # Before wake time - low alertness
        if hour < wake:
            return 0.2

        # After sleep time - declining alertness
        if hour > sleep:
            return 0.3

        # Rising to morning peak
        if hour < morning_peak:
            progress = (hour - wake) / (morning_peak - wake)
            return 0.3 + progress * 0.5  # 0.3 to 0.8

        # Morning peak to dip
        if hour < dip:
            progress = (hour - morning_peak) / (dip - morning_peak)
            return 0.8 - progress * 0.3  # 0.8 to 0.5

        # Dip to evening peak
        if hour < evening_peak:
            progress = (hour - dip) / (evening_peak - dip)
            return 0.5 + progress * 0.25  # 0.5 to 0.75

        # Evening peak to sleep
        progress = (hour - evening_peak) / (sleep - evening_peak)
        return 0.75 - progress * 0.45  # 0.75 to 0.3

    def _get_phase(self, hour: float, profile: Dict) -> str:
        """Get human-readable phase description."""
        wake = profile["wake"]
        morning_peak = profile["morning_peak"]
        dip = profile["afternoon_dip"]
        evening_peak = profile["evening_peak"]
        sleep = profile["sleep"]

        if sleep < wake:
            sleep += 24
            if hour < wake:
                hour += 24

        if hour < wake:
            return "🌙 Sleep cycle"
        elif hour < morning_peak:
            return "🌅 Rising alertness"
        elif hour < dip - 1:
            return "⭐ Peak performance"
        elif hour < dip + 1:
            return "😴 Post-lunch dip"
        elif hour < evening_peak:
            return "📈 Second wind"
        elif hour < sleep:
            return "🌆 Winding down"
        else:
            return "🌙 Sleep cycle"


class UltradianFactor(BaseFactor):
    """
    Factor based on ultradian rhythm (~90-minute cycles).

    Research shows attention and focus fluctuate in ~90-120 minute cycles.
    This factor encourages breaks at natural low points.
    """

    name = "ultradian_rhythm"
    category = FactorCategory.TEMPORAL
    weight = 0.5  # Lower weight - subtle effect

    CYCLE_LENGTH = 90.0  # minutes

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        dt = context.get("datetime", datetime.now())

        # Session start time (default to hour start if not available)
        session_start = context.get("session_start", dt.replace(minute=0, second=0))

        # Minutes since session start
        minutes = (dt - session_start).total_seconds() / 60.0

        # Position in cycle (0 to 1)
        cycle_position = (minutes % self.CYCLE_LENGTH) / self.CYCLE_LENGTH

        # Alertness follows sinusoidal pattern
        # Peak at 0.25 (about 22 min into cycle)
        # Low at 0.75 (about 67 min into cycle)
        score = 0.5 + 0.25 * math.sin(2 * math.pi * (cycle_position - 0.25))

        # Determine phase
        if cycle_position < 0.15:
            phase = "🚀 Cycle starting"
        elif cycle_position < 0.35:
            phase = "⭐ Peak focus"
        elif cycle_position < 0.55:
            phase = "📉 Declining"
        elif cycle_position < 0.85:
            phase = "💤 Break time"
        else:
            phase = "🔄 Cycle ending"

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.MEDIUM,
            weight=self.weight,
            raw_value=cycle_position,
            description=f"{phase} (cycle {int(minutes // self.CYCLE_LENGTH) + 1})",
            metadata={
                "cycle_position": round(cycle_position, 2),
                "minutes_in_session": round(minutes, 1),
                "cycles_completed": int(minutes // self.CYCLE_LENGTH),
            },
        )


class DayOfWeekFactor(BaseFactor):
    """
    Factor based on day of week patterns.

    Research shows mood patterns by day:
    - Monday: Lower (start of work week)
    - Friday: Higher (anticipation)
    - Weekend: Variable (depends on activities)
    """

    name = "day_of_week"
    category = FactorCategory.TEMPORAL
    weight = 0.75

    # Day scores (0=Monday, 6=Sunday)
    DAY_SCORES = {
        0: 0.40,  # Monday - "Blue Monday"
        1: 0.45,  # Tuesday - recovery
        2: 0.55,  # Wednesday - midweek
        3: 0.60,  # Thursday - anticipation building
        4: 0.75,  # Friday - peak weekday
        5: 0.65,  # Saturday - weekend high
        6: 0.50,  # Sunday - weekend wind-down
    }

    DAY_NAMES = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    DAY_ICONS = ["😐", "🙂", "😊", "😃", "🎉", "🌟", "☕"]

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        dt = context.get("datetime", datetime.now())
        day = dt.weekday()  # 0 = Monday

        score = self.DAY_SCORES.get(day, 0.5)
        name = self.DAY_NAMES[day]
        icon = self.DAY_ICONS[day]

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.MEDIUM,
            weight=self.weight,
            raw_value=day,
            description=f"{icon} {name}",
            metadata={
                "day_number": day,
                "day_name": name,
                "is_weekend": day >= 5,
            },
        )


class SeasonalFactor(BaseFactor):
    """
    Factor based on seasonal patterns.

    Research shows mood variations by season:
    - Spring: Rising (renewal)
    - Summer: Peak (light, warmth)
    - Autumn: Declining (preparation)
    - Winter: Lowest (less light)

    Note: This is Northern Hemisphere biased.
    """

    name = "seasonal"
    category = FactorCategory.TEMPORAL
    weight = 0.75

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        dt = context.get("datetime", datetime.now())

        # Day of year (1-365)
        day_of_year = dt.timetuple().tm_yday

        # Season determination (Northern Hemisphere)
        # Spring equinox ~day 80, Summer solstice ~172, Autumn ~266, Winter ~355

        if day_of_year < 80 or day_of_year >= 355:
            season = "winter"
            icon = "❄️"
            base_score = 0.40
        elif day_of_year < 172:
            season = "spring"
            icon = "🌸"
            base_score = 0.60
        elif day_of_year < 266:
            season = "summer"
            icon = "☀️"
            base_score = 0.70
        else:
            season = "autumn"
            icon = "🍂"
            base_score = 0.50

        # Smooth transitions using day position within season
        # Peak at mid-season
        if season == "winter":
            if day_of_year >= 355:
                days_in = day_of_year - 355
            else:
                days_in = day_of_year + 10
            season_progress = days_in / 90
        elif season == "spring":
            days_in = day_of_year - 80
            season_progress = days_in / 92
        elif season == "summer":
            days_in = day_of_year - 172
            season_progress = days_in / 94
        else:  # autumn
            days_in = day_of_year - 266
            season_progress = days_in / 89

        # Bell curve within season (peak at middle)
        modifier = gaussian_peak(season_progress, 0.5, 0.3) * 0.1
        score = base_score + modifier

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.HIGH,
            weight=self.weight,
            raw_value=day_of_year,
            description=f"{icon} {season.title()}",
            metadata={
                "season": season,
                "day_of_year": day_of_year,
                "season_progress": round(season_progress, 2),
            },
        )


class NumerologyFactor(BaseFactor):
    """
    Factor based on numerology daily number resonance.

    Compares today's universal number with user's life path number.
    Compatible numbers theoretically indicate harmonious days.

    Note: This is pattern-based, not scientifically validated.
    """

    name = "numerology"
    category = FactorCategory.TEMPORAL
    weight = 0.25  # Low weight - pattern-based

    # Compatibility matrix (simplified)
    # Numbers 1-9 plus master numbers 11, 22, 33
    COMPATIBLE = {
        1: [1, 2, 3, 5, 9],
        2: [1, 2, 4, 6, 8],
        3: [1, 3, 5, 6, 9],
        4: [2, 4, 6, 8],
        5: [1, 3, 5, 7, 9],
        6: [2, 3, 6, 8, 9],
        7: [5, 7],
        8: [2, 4, 6, 8],
        9: [1, 3, 5, 6, 9],
        11: [2, 4, 6, 11, 22],
        22: [4, 8, 11, 22, 33],
        33: [6, 9, 22, 33],
    }

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        # Get user's life path from identity
        identity = context.get("identity")
        if not identity or not identity.life_path_number:
            return self.default_result("No life path number")

        life_path = identity.life_path_number
        dt = context.get("datetime", datetime.now())

        # Calculate today's universal number
        from dev.goblin.core.services.identity_service import calculate_daily_number

        daily_number = calculate_daily_number(dt.date())

        # Check compatibility
        compatible_list = self.COMPATIBLE.get(life_path, [life_path])
        is_compatible = daily_number in compatible_list

        # Same number = perfect resonance
        if daily_number == life_path:
            score = 0.75
            resonance = "perfect resonance"
        elif is_compatible:
            score = 0.65
            resonance = "harmonious"
        else:
            score = 0.45
            resonance = "neutral"

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.LOW,  # Pattern-based
            weight=self.weight,
            raw_value=daily_number,
            description=f"Life path {life_path} + day {daily_number} = {resonance}",
            metadata={
                "life_path": life_path,
                "daily_number": daily_number,
                "resonance": resonance,
                "is_compatible": is_compatible,
            },
        )


# =============================================================================
# Temporal Category Calculator
# =============================================================================


class TemporalCategoryCalculator(BaseCategoryCalculator):
    """Calculator for all temporal factors."""

    category = FactorCategory.TEMPORAL

    def __init__(self):
        super().__init__()

        # Register all temporal factors
        self.register_factor(CircadianFactor())
        self.register_factor(UltradianFactor())
        self.register_factor(DayOfWeekFactor())
        self.register_factor(SeasonalFactor())
        self.register_factor(NumerologyFactor())

        logger.debug(f"[LOCAL] Registered {len(self.factors)} temporal factors")
