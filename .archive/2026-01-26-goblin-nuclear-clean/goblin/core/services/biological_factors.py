"""
uDOS Biological Factors - Self-Reported and Inferred Biological State
Alpha v1.0.0.65

Calculates mood factors based on biological indicators:
- Self-reported energy level
- Self-reported mood (if provided)
- Activity level inference
- Break recency (affects recovery)

These factors have 20% weight - they combine self-reports with
inferred states from other behavioral data.
"""

import time as time_module
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

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

logger = get_logger("biological-factors")


# =============================================================================
# Biological State Tracker
# =============================================================================


@dataclass
class BiologicalState:
    """
    User's self-reported biological state.

    Updated periodically through WELLBEING check-ins.
    """

    energy_level: Optional[float] = None  # 0-1
    mood_level: Optional[float] = None  # 0-1
    last_sleep_quality: Optional[float] = None  # 0-1
    last_meal_hours: Optional[float] = None
    hydration_status: Optional[str] = None  # "good", "fair", "poor"
    last_checkin: Optional[float] = None  # Unix timestamp

    def is_stale(self, max_age_hours: float = 2.0) -> bool:
        """Check if data is stale (needs refresh)."""
        if self.last_checkin is None:
            return True
        age_hours = (time_module.time() - self.last_checkin) / 3600
        return age_hours > max_age_hours

    def update_energy(self, level: float) -> None:
        """Update energy level (0-1)."""
        self.energy_level = max(0.0, min(1.0, level))
        self.last_checkin = time_module.time()

    def update_mood(self, level: float) -> None:
        """Update mood level (0-1)."""
        self.mood_level = max(0.0, min(1.0, level))
        self.last_checkin = time_module.time()

    def record_meal(self) -> None:
        """Record that user just ate."""
        self.last_meal_hours = 0.0
        self.last_checkin = time_module.time()


# Global biological state (persists across factor calculations)
_biological_state: Optional[BiologicalState] = None


def get_biological_state() -> BiologicalState:
    """Get or create the biological state tracker."""
    global _biological_state
    if _biological_state is None:
        _biological_state = BiologicalState()
    return _biological_state


def reset_biological_state() -> None:
    """Reset biological state (new session)."""
    global _biological_state
    _biological_state = BiologicalState()


# =============================================================================
# Biological Factor Implementations
# =============================================================================


class EnergyLevelFactor(BaseFactor):
    """
    Factor based on self-reported energy level.

    This is the most direct biological indicator and highly
    correlated with mood and productivity.
    """

    name = "energy_level"
    category = FactorCategory.BIOLOGICAL
    weight = 2.0  # Higher weight - direct self-report

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        state = context.get("biological_state") or get_biological_state()

        if state.energy_level is None:
            return MoodFactorResult(
                name=self.name,
                category=self.category,
                score=0.5,
                confidence=FactorConfidence.NONE,
                weight=self.weight,
                description="No energy data - try WELLBEING CHECKIN",
            )

        score = state.energy_level

        # Reduce confidence if data is stale
        if state.is_stale(2.0):
            confidence = FactorConfidence.LOW
            stale_note = " (stale)"
        elif state.is_stale(1.0):
            confidence = FactorConfidence.MEDIUM
            stale_note = ""
        else:
            confidence = FactorConfidence.HIGH
            stale_note = ""

        if score >= 0.8:
            desc = f"⚡ High energy{stale_note}"
        elif score >= 0.6:
            desc = f"✨ Good energy{stale_note}"
        elif score >= 0.4:
            desc = f"👍 Moderate energy{stale_note}"
        elif score >= 0.2:
            desc = f"🔋 Low energy{stale_note}"
        else:
            desc = f"😴 Very low energy{stale_note}"

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=confidence,
            weight=self.weight,
            raw_value=state.energy_level,
            description=desc,
            metadata={
                "energy_level": round(score, 2),
                "is_stale": state.is_stale(2.0),
            },
        )


class MoodLevelFactor(BaseFactor):
    """
    Factor based on self-reported mood level.

    Direct mood input from user check-ins.
    """

    name = "mood_level"
    category = FactorCategory.BIOLOGICAL
    weight = 2.0  # Higher weight - direct self-report

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        state = context.get("biological_state") or get_biological_state()

        if state.mood_level is None:
            return MoodFactorResult(
                name=self.name,
                category=self.category,
                score=0.5,
                confidence=FactorConfidence.NONE,
                weight=self.weight,
                description="No mood data - try WELLBEING CHECKIN",
            )

        score = state.mood_level

        # Reduce confidence if data is stale
        if state.is_stale(2.0):
            confidence = FactorConfidence.LOW
            stale_note = " (stale)"
        elif state.is_stale(1.0):
            confidence = FactorConfidence.MEDIUM
            stale_note = ""
        else:
            confidence = FactorConfidence.HIGH
            stale_note = ""

        if score >= 0.8:
            desc = f"😊 Feeling great{stale_note}"
        elif score >= 0.6:
            desc = f"🙂 Feeling good{stale_note}"
        elif score >= 0.4:
            desc = f"😐 Neutral{stale_note}"
        elif score >= 0.2:
            desc = f"😕 Feeling low{stale_note}"
        else:
            desc = f"😔 Struggling{stale_note}"

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=confidence,
            weight=self.weight,
            raw_value=state.mood_level,
            description=desc,
            metadata={
                "mood_level": round(score, 2),
                "is_stale": state.is_stale(2.0),
            },
        )


class ActivityLevelFactor(BaseFactor):
    """
    Factor inferring activity level from behavioral patterns.

    Uses keystroke and prompt activity to infer engagement level,
    which correlates with biological state.
    """

    name = "activity_level"
    category = FactorCategory.BIOLOGICAL
    weight = 0.75

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        from dev.goblin.core.services.behavioral_factors import get_metrics_collector

        collector = context.get("behavioral_metrics") or get_metrics_collector()

        hours = collector.get_session_duration_hours()
        if hours < 0.1:  # Less than 6 minutes
            return self.default_result("Session too short")

        # Activity indicators
        keystrokes = collector.metrics.total_keystrokes
        prompts = collector.metrics.total_prompts

        # Calculate activity rate
        keystrokes_per_hour = keystrokes / hours if hours > 0 else 0
        prompts_per_hour = prompts / hours if hours > 0 else 0

        # Normalize activity level
        # Expected: 2000-5000 keystrokes/hour for active typing
        keystroke_factor = normalize_score(keystrokes_per_hour, 500, 4000)

        # Expected: 5-30 prompts/hour for active use
        prompt_factor = normalize_score(prompts_per_hour, 2, 25)

        # Combined activity score
        score = (keystroke_factor * 0.6) + (prompt_factor * 0.4)

        if score >= 0.7:
            desc = "🔥 Highly active"
        elif score >= 0.5:
            desc = "✨ Active"
        elif score >= 0.3:
            desc = "👍 Moderate activity"
        elif score >= 0.1:
            desc = "🐢 Low activity"
        else:
            desc = "💤 Minimal activity"

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.MEDIUM,
            weight=self.weight,
            raw_value=keystrokes_per_hour,
            description=desc,
            metadata={
                "keystrokes_per_hour": round(keystrokes_per_hour, 0),
                "prompts_per_hour": round(prompts_per_hour, 1),
            },
        )


class BreakRecencyFactor(BaseFactor):
    """
    Factor based on time since last break.

    Regular breaks are essential for maintaining biological state.
    Working too long without breaks leads to fatigue.
    """

    name = "break_recency"
    category = FactorCategory.BIOLOGICAL
    weight = 0.75

    # Optimal break frequency: every 50-90 minutes
    OPTIMAL_BREAK_INTERVAL = 60.0  # minutes
    MAX_BREAK_INTERVAL = 120.0  # minutes before penalty

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        from dev.goblin.core.services.behavioral_factors import get_metrics_collector

        collector = context.get("behavioral_metrics") or get_metrics_collector()

        # Time since last activity (potential micro-break)
        last_activity = collector.metrics.last_activity
        now = time_module.time()

        # Time since session start or last substantial break
        minutes_active = (now - collector.metrics.session_start) / 60.0

        # Account for breaks taken
        if collector.metrics.breaks_taken > 0:
            # Estimate time since last break
            avg_interval = minutes_active / (collector.metrics.breaks_taken + 1)
            minutes_since_break = avg_interval  # Approximation
        else:
            minutes_since_break = minutes_active

        # Score based on time since break
        if minutes_since_break < 30:
            score = 0.8  # Recently took a break
        elif minutes_since_break < 60:
            score = 0.7  # Normal range
        elif minutes_since_break < 90:
            score = 0.5  # Getting long
        elif minutes_since_break < 120:
            score = 0.35  # Break recommended
        else:
            score = 0.2  # Overdue for break

        if minutes_since_break < 30:
            desc = "✨ Recently refreshed"
        elif minutes_since_break < 60:
            desc = "👍 Good break timing"
        elif minutes_since_break < 90:
            desc = "⏰ Break soon"
        else:
            desc = "🔴 Break overdue"

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.MEDIUM,
            weight=self.weight,
            raw_value=minutes_since_break,
            description=f"{desc} ({minutes_since_break:.0f}min)",
            metadata={
                "minutes_since_break": round(minutes_since_break, 0),
                "total_breaks": collector.metrics.breaks_taken,
            },
        )


class SleepQualityFactor(BaseFactor):
    """
    Factor based on self-reported sleep quality.

    Sleep quality is a major determinant of daily mood and energy.
    """

    name = "sleep_quality"
    category = FactorCategory.BIOLOGICAL
    weight = 1.0

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        state = context.get("biological_state") or get_biological_state()

        if state.last_sleep_quality is None:
            return MoodFactorResult(
                name=self.name,
                category=self.category,
                score=0.5,
                confidence=FactorConfidence.NONE,
                weight=self.weight,
                description="No sleep data",
            )

        score = state.last_sleep_quality

        if score >= 0.8:
            desc = "😴 Well rested"
        elif score >= 0.6:
            desc = "🙂 Decent sleep"
        elif score >= 0.4:
            desc = "😐 Fair sleep"
        elif score >= 0.2:
            desc = "😕 Poor sleep"
        else:
            desc = "😫 Very poor sleep"

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.HIGH,
            weight=self.weight,
            raw_value=state.last_sleep_quality,
            description=desc,
            metadata={"sleep_quality": round(score, 2)},
        )


class NutritionFactor(BaseFactor):
    """
    Factor based on time since last meal.

    Blood sugar affects mood and cognitive performance.
    """

    name = "nutrition"
    category = FactorCategory.BIOLOGICAL
    weight = 0.5

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        state = context.get("biological_state") or get_biological_state()

        if state.last_meal_hours is None:
            return MoodFactorResult(
                name=self.name,
                category=self.category,
                score=0.5,
                confidence=FactorConfidence.NONE,
                weight=self.weight,
                description="No meal data",
            )

        hours = state.last_meal_hours

        # Optimal: 1-3 hours since meal
        # Too soon (<0.5h): digesting
        # Too long (>5h): possible blood sugar dip

        if hours < 0.5:
            score = 0.5  # Just ate, digesting
            desc = "🍽️ Just ate"
        elif hours < 3:
            score = 0.7  # Optimal range
            desc = "✨ Well fueled"
        elif hours < 5:
            score = 0.5  # Getting hungry
            desc = "⏰ Consider a snack"
        else:
            score = 0.3  # Blood sugar likely low
            desc = "🍎 Time to eat"

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.MEDIUM,
            weight=self.weight,
            raw_value=hours,
            description=f"{desc} ({hours:.1f}h ago)",
            metadata={"hours_since_meal": round(hours, 1)},
        )


# =============================================================================
# Biological Category Calculator
# =============================================================================


class BiologicalCategoryCalculator(BaseCategoryCalculator):
    """Calculator for all biological factors."""

    category = FactorCategory.BIOLOGICAL

    def __init__(self):
        super().__init__()

        # Register all biological factors
        self.register_factor(EnergyLevelFactor())
        self.register_factor(MoodLevelFactor())
        self.register_factor(ActivityLevelFactor())
        self.register_factor(BreakRecencyFactor())
        self.register_factor(SleepQualityFactor())
        self.register_factor(NutritionFactor())

        logger.debug(f"[LOCAL] Registered {len(self.factors)} biological factors")
