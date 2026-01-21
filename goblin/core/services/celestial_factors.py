"""
uDOS Celestial Factors - Moon, Sun, and Zodiac Mood Influences
Alpha v1.0.0.65

Calculates mood factors based on celestial mechanics:
- Lunar phase and distance (tidal influence)
- Solar position and day length
- Western zodiac alignment
- Chinese zodiac compatibility with current year

All calculations use astronomical formulas and don't require internet.
Based on algorithms from "Astronomical Algorithms" by Jean Meeus.
"""

import math
from datetime import datetime, date, time, timedelta
from typing import Dict, Any, Optional, Tuple

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

logger = get_logger("celestial-factors")


# =============================================================================
# Astronomical Constants and Calculations
# =============================================================================

# Lunar constants
SYNODIC_MONTH = 29.530588853  # Days - moon phase cycle
ANOMALISTIC_MONTH = 27.554549878  # Days - moon distance cycle

# Reference new moon (known date for calculation)
REFERENCE_NEW_MOON = datetime(2000, 1, 6, 18, 14, 0)  # J2000.0 epoch


def julian_day(dt: datetime) -> float:
    """Calculate Julian Day from datetime."""
    year = dt.year
    month = dt.month
    day = dt.day + (dt.hour + dt.minute / 60.0 + dt.second / 3600.0) / 24.0

    if month <= 2:
        year -= 1
        month += 12

    a = int(year / 100)
    b = 2 - a + int(a / 4)

    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5
    return jd


def lunar_phase(dt: datetime) -> Tuple[float, str, str]:
    """
    Calculate lunar phase.

    Returns:
        Tuple of (phase_fraction, phase_name, phase_icon)
        phase_fraction: 0.0 = new moon, 0.5 = full moon, 1.0 = new moon again
    """
    # Days since reference new moon
    days = (dt - REFERENCE_NEW_MOON).total_seconds() / 86400.0

    # Current position in cycle (0.0 to 1.0)
    phase = (days % SYNODIC_MONTH) / SYNODIC_MONTH

    # Phase name and icon
    if phase < 0.0625:
        name, icon = "new moon", "🌑"
    elif phase < 0.1875:
        name, icon = "waxing crescent", "🌒"
    elif phase < 0.3125:
        name, icon = "first quarter", "🌓"
    elif phase < 0.4375:
        name, icon = "waxing gibbous", "🌔"
    elif phase < 0.5625:
        name, icon = "full moon", "🌕"
    elif phase < 0.6875:
        name, icon = "waning gibbous", "🌖"
    elif phase < 0.8125:
        name, icon = "last quarter", "🌗"
    elif phase < 0.9375:
        name, icon = "waning crescent", "🌘"
    else:
        name, icon = "new moon", "🌑"

    return phase, name, icon


def lunar_distance_factor(dt: datetime) -> float:
    """
    Calculate relative lunar distance (for tidal influence).

    Returns:
        Factor from 0.0 (apogee/farthest) to 1.0 (perigee/closest)
    """
    days = (dt - REFERENCE_NEW_MOON).total_seconds() / 86400.0
    position = (days % ANOMALISTIC_MONTH) / ANOMALISTIC_MONTH

    # Distance varies sinusoidally - closest at position 0
    # Using cosine so perigee (closest) is at maximum
    distance_factor = (math.cos(2 * math.pi * position) + 1) / 2

    return distance_factor


def solar_declination(dt: datetime) -> float:
    """
    Calculate solar declination angle in degrees.

    This determines how high the sun gets and affects day length.
    """
    # Day of year (1-365)
    day_of_year = dt.timetuple().tm_yday

    # Approximate declination
    # Maximum at summer solstice (day ~172), minimum at winter solstice (day ~355)
    declination = 23.45 * math.sin(math.radians(360 / 365 * (day_of_year - 81)))

    return declination


def day_length_hours(dt: datetime, latitude: float = 40.0) -> float:
    """
    Calculate approximate day length in hours.

    Args:
        dt: Datetime to calculate for
        latitude: Observer's latitude (default 40°N)

    Returns:
        Day length in hours
    """
    declination = solar_declination(dt)
    lat_rad = math.radians(latitude)
    dec_rad = math.radians(declination)

    # Hour angle calculation
    cos_hour_angle = -math.tan(lat_rad) * math.tan(dec_rad)

    # Clamp for polar regions
    if cos_hour_angle > 1:
        return 0.0  # Polar night
    elif cos_hour_angle < -1:
        return 24.0  # Midnight sun

    hour_angle = math.acos(cos_hour_angle)
    day_length = (2 * hour_angle) / math.pi * 12

    return day_length


# =============================================================================
# Celestial Factor Implementations
# =============================================================================


class LunarPhaseFactor(BaseFactor):
    """
    Factor based on lunar phase.

    Research suggests subtle mood correlations with lunar cycle:
    - Full moon: heightened energy, possible sleep disruption
    - New moon: introspection, lower energy
    - Waxing: building energy
    - Waning: releasing energy
    """

    name = "lunar_phase"
    category = FactorCategory.CELESTIAL
    weight = 1.0

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        dt = context.get("datetime", datetime.now())
        phase, phase_name, icon = lunar_phase(dt)

        # Score based on phase
        # Full moon and new moon are "peak" states
        # Using a dual-peak model: energy at full, calm at new
        # Normalize to neutral baseline (0.5) with variations

        if phase < 0.5:
            # Waxing phase: energy building toward full
            score = 0.45 + 0.15 * (phase / 0.5)  # 0.45 to 0.60
        else:
            # Waning phase: energy releasing after full
            score = 0.60 - 0.15 * ((phase - 0.5) / 0.5)  # 0.60 to 0.45

        # Peak at full moon (good for some, disruptive for others)
        # We keep it slightly positive
        if 0.4 <= phase <= 0.6:
            score = 0.55 + gaussian_peak(phase, 0.5, 0.1) * 0.1

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.HIGH,
            weight=self.weight,
            raw_value=phase,
            description=f"{icon} {phase_name.title()} ({int(phase * 100)}%)",
            metadata={
                "phase_fraction": round(phase, 3),
                "phase_name": phase_name,
                "icon": icon,
            },
        )


class TidalInfluenceFactor(BaseFactor):
    """
    Factor based on tidal forces (lunar distance).

    Tidal forces are strongest at perigee (moon closest).
    Some research suggests subtle physiological effects.
    """

    name = "tidal_influence"
    category = FactorCategory.CELESTIAL
    weight = 0.5  # Lower weight - subtle effect

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        dt = context.get("datetime", datetime.now())
        distance_factor = lunar_distance_factor(dt)

        # Convert to mood score
        # Higher tidal force (perigee) = slightly more energy
        # Keep effect subtle: 0.45 to 0.55
        score = 0.45 + distance_factor * 0.10

        if distance_factor > 0.9:
            proximity = "perigee (closest)"
        elif distance_factor > 0.5:
            proximity = "approaching"
        elif distance_factor > 0.1:
            proximity = "receding"
        else:
            proximity = "apogee (farthest)"

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.HIGH,
            weight=self.weight,
            raw_value=distance_factor,
            description=f"Moon {proximity}",
            metadata={
                "distance_factor": round(distance_factor, 3),
            },
        )


class DayLengthFactor(BaseFactor):
    """
    Factor based on day length (photoperiod).

    Research clearly shows seasonal mood effects (SAD).
    Longer days generally correlate with better mood.
    """

    name = "day_length"
    category = FactorCategory.CELESTIAL
    weight = 1.5  # Higher weight - well-researched effect

    def __init__(self, latitude: float = 40.0):
        self.latitude = latitude

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        dt = context.get("datetime", datetime.now())

        # Get latitude from context if available
        latitude = context.get("latitude", self.latitude)

        hours = day_length_hours(dt, latitude)

        # Score: 8 hours (winter) = 0.3, 16 hours (summer) = 0.8
        # Optimal around 14-15 hours
        score = normalize_score(hours, 8.0, 16.0)

        # Apply slight gaussian for "optimal" day length (not too long/short)
        optimal_modifier = gaussian_peak(hours, 14.0, 4.0) * 0.1
        score = min(1.0, score + optimal_modifier)

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.HIGH,
            weight=self.weight,
            raw_value=hours,
            description=f"☀️ {hours:.1f}h daylight",
            metadata={
                "day_length_hours": round(hours, 2),
                "latitude": latitude,
                "solar_declination": round(solar_declination(dt), 2),
            },
        )


class ZodiacAlignmentFactor(BaseFactor):
    """
    Factor based on Western zodiac element compatibility.

    Uses traditional elemental affinities:
    - Fire + Air = energizing
    - Water + Earth = grounding
    - Same element = harmonious

    Note: This is pattern-based, not scientifically validated.
    Lower weight reflects this.
    """

    name = "zodiac_alignment"
    category = FactorCategory.CELESTIAL
    weight = 0.5  # Lower weight - pattern-based

    # Element compatibility matrix
    ELEMENT_COMPAT = {
        ("fire", "fire"): 0.7,
        ("fire", "air"): 0.8,
        ("fire", "earth"): 0.4,
        ("fire", "water"): 0.3,
        ("air", "air"): 0.7,
        ("air", "earth"): 0.4,
        ("air", "water"): 0.5,
        ("earth", "earth"): 0.7,
        ("earth", "water"): 0.8,
        ("water", "water"): 0.7,
    }

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        # Get user's zodiac from identity
        identity = context.get("identity")
        if not identity or not identity.western_element:
            return self.default_result("No zodiac data")

        user_element = identity.western_element

        # Current sun sign (what sign the sun is in today)
        dt = context.get("datetime", datetime.now())
        current_sign_element = self._current_sun_element(dt)

        # Look up compatibility
        key = tuple(sorted([user_element, current_sign_element]))
        compat = self.ELEMENT_COMPAT.get(key, 0.5)

        # Normalize to mood score
        score = 0.3 + compat * 0.4  # Range 0.3 to 0.7

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.MEDIUM,
            weight=self.weight,
            raw_value=compat,
            description=f"Your {user_element} + today's {current_sign_element}",
            metadata={
                "user_element": user_element,
                "current_element": current_sign_element,
                "compatibility": compat,
            },
        )

    def _current_sun_element(self, dt: datetime) -> str:
        """Determine current sun sign element."""
        from dev.goblin.core.services.identity_service import WesternZodiac

        zodiac = WesternZodiac.from_date(dt.date())
        return zodiac.element


class ChineseZodiacFactor(BaseFactor):
    """
    Factor based on Chinese zodiac year compatibility.

    Uses traditional animal compatibility (six harmonies, six conflicts).
    Current year is compared against user's birth year animal.
    """

    name = "chinese_zodiac"
    category = FactorCategory.CELESTIAL
    weight = 0.5  # Lower weight - pattern-based

    # Six harmonies (highly compatible)
    HARMONIES = [
        ("rat", "ox"),
        ("tiger", "pig"),
        ("rabbit", "dog"),
        ("dragon", "rooster"),
        ("snake", "monkey"),
        ("horse", "goat"),
    ]

    # Six conflicts (challenging)
    CONFLICTS = [
        ("rat", "horse"),
        ("ox", "goat"),
        ("tiger", "monkey"),
        ("rabbit", "rooster"),
        ("dragon", "dog"),
        ("snake", "pig"),
    ]

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        # Get user's Chinese zodiac from identity
        identity = context.get("identity")
        if not identity or not identity.chinese_animal:
            return self.default_result("No Chinese zodiac data")

        user_animal = identity.chinese_animal
        dt = context.get("datetime", datetime.now())

        # Current year's animal
        from dev.goblin.core.services.identity_service import chinese_zodiac_from_year

        current_animal, current_element = chinese_zodiac_from_year(dt.year)

        # Calculate compatibility
        pair = tuple(sorted([user_animal, current_animal]))

        if user_animal == current_animal:
            compat = 0.6  # Same animal - mixed (competition)
            relation = "same animal year"
        elif pair in self.HARMONIES or tuple(reversed(pair)) in self.HARMONIES:
            compat = 0.9  # Harmony
            relation = "harmonious"
        elif pair in self.CONFLICTS or tuple(reversed(pair)) in self.CONFLICTS:
            compat = 0.3  # Conflict
            relation = "challenging"
        else:
            compat = 0.5  # Neutral
            relation = "neutral"

        score = 0.3 + compat * 0.4  # Range 0.3 to 0.7

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.MEDIUM,
            weight=self.weight,
            raw_value=compat,
            description=f"Your {user_animal} + year of {current_animal} = {relation}",
            metadata={
                "user_animal": user_animal,
                "current_animal": current_animal,
                "current_element": current_element,
                "relation": relation,
            },
        )


# =============================================================================
# Celestial Category Calculator
# =============================================================================


class CelestialCategoryCalculator(BaseCategoryCalculator):
    """Calculator for all celestial factors."""

    category = FactorCategory.CELESTIAL

    def __init__(self):
        super().__init__()

        # Register all celestial factors
        self.register_factor(LunarPhaseFactor())
        self.register_factor(TidalInfluenceFactor())
        self.register_factor(DayLengthFactor())
        self.register_factor(ZodiacAlignmentFactor())
        self.register_factor(ChineseZodiacFactor())

        logger.debug(f"[LOCAL] Registered {len(self.factors)} celestial factors")
