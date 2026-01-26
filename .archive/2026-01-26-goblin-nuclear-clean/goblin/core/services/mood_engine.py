"""
uDOS Mood Engine - Unified Mood Factor System v3.0.0
Alpha v1.0.0.65

Main engine that coordinates all mood factor calculations:
- Celestial (25%): lunar, solar, zodiac
- Temporal (25%): circadian, day of week, numerology
- Behavioral (30%): typing patterns, session activity
- Biological (20%): self-reported energy, activity inference

Usage:
    from dev.goblin.core.services.mood_engine import MoodEngine

    engine = MoodEngine()
    composite = engine.calculate()

    print(f"Mood: {composite.summary()}")
    print(f"Score: {composite.score:.2f}")
"""

from datetime import datetime, date, time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from dev.goblin.core.services.mood_factors import (
    MoodFactorEngine,
    MoodComposite,
    FactorCategory,
    CategoryScore,
)
from dev.goblin.core.services.celestial_factors import CelestialCategoryCalculator
from dev.goblin.core.services.temporal_factors import TemporalCategoryCalculator
from dev.goblin.core.services.behavioral_factors import (
    BehavioralCategoryCalculator,
    get_metrics_collector,
    BehavioralMetricsCollector,
)
from dev.goblin.core.services.biological_factors import (
    BiologicalCategoryCalculator,
    get_biological_state,
    BiologicalState,
)
from dev.goblin.core.services.identity_service import (
    IdentityService,
    DerivedIdentity,
    hash_for_log,
)
from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("mood-engine")


class MoodEngine:
    """
    Unified mood calculation engine.

    Coordinates all factor categories and provides a simple API
    for calculating and tracking mood over time.
    """

    def __init__(
        self,
        identity_service: Optional[IdentityService] = None,
    ):
        """
        Initialize the mood engine.

        Args:
            identity_service: Optional identity service for zodiac/numerology.
                              If not provided, a default one is created.
        """
        # Core engine
        self._engine = MoodFactorEngine()

        # Identity service for user data
        self._identity = identity_service or IdentityService()

        # Register all category calculators
        self._engine.register_calculator(CelestialCategoryCalculator())
        self._engine.register_calculator(TemporalCategoryCalculator())
        self._engine.register_calculator(BehavioralCategoryCalculator())
        self._engine.register_calculator(BiologicalCategoryCalculator())

        # History tracking
        self._history: List[MoodComposite] = []
        self._max_history = 100

        logger.info("[LOCAL] Mood Engine v3.0.0 initialized")

    def calculate(
        self,
        behavioral_metrics: Optional[BehavioralMetricsCollector] = None,
        biological_state: Optional[BiologicalState] = None,
    ) -> MoodComposite:
        """
        Calculate the composite mood score.

        Args:
            behavioral_metrics: Optional behavioral metrics collector.
                               If not provided, uses global collector.
            biological_state: Optional biological state tracker.
                             If not provided, uses global state.

        Returns:
            MoodComposite with full breakdown
        """
        # Build context
        context = self._build_context(behavioral_metrics, biological_state)

        # Calculate composite
        composite = self._engine.calculate_composite(context)

        # Add to history
        self._add_to_history(composite)

        # Log summary (with hashed identity)
        id_hash = (
            self._identity._get_identity_hash()
            if self._identity.has_identity()
            else "anon"
        )
        logger.info(f"[LOCAL] Mood [{id_hash}]: {composite.summary()}")

        return composite

    def _build_context(
        self,
        behavioral_metrics: Optional[BehavioralMetricsCollector],
        biological_state: Optional[BiologicalState],
    ) -> Dict[str, Any]:
        """Build the context dictionary for factor calculations."""
        now = datetime.now()

        context = {
            "datetime": now,
            "date": now.date(),
            "time": now.time(),
            "identity": self._identity.get_derived_identity(),
            "behavioral_metrics": behavioral_metrics or get_metrics_collector(),
            "biological_state": biological_state or get_biological_state(),
        }

        return context

    def _add_to_history(self, composite: MoodComposite) -> None:
        """Add composite to history, pruning old entries."""
        self._history.append(composite)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

    # =========================================================================
    # Behavioral API
    # =========================================================================

    def record_keystroke(self, is_backspace: bool = False) -> None:
        """Record a keystroke event."""
        collector = get_metrics_collector()
        collector.record_keystroke(is_backspace)

    def record_prompt(self, text: str) -> None:
        """Record a prompt submission."""
        collector = get_metrics_collector()
        collector.record_prompt(text)

    # =========================================================================
    # Biological API
    # =========================================================================

    def update_energy(self, level: float) -> None:
        """
        Update energy level (0-1).

        Args:
            level: 0.0 (exhausted) to 1.0 (energized)
        """
        state = get_biological_state()
        state.update_energy(level)
        logger.info(f"[LOCAL] Energy updated: {level:.2f}")

    def update_mood(self, level: float) -> None:
        """
        Update mood level (0-1).

        Args:
            level: 0.0 (very low) to 1.0 (excellent)
        """
        state = get_biological_state()
        state.update_mood(level)
        logger.info(f"[LOCAL] Mood updated: {level:.2f}")

    def record_sleep(self, quality: float) -> None:
        """
        Record sleep quality (0-1).

        Args:
            quality: 0.0 (very poor) to 1.0 (excellent)
        """
        state = get_biological_state()
        state.last_sleep_quality = max(0.0, min(1.0, quality))
        logger.info(f"[LOCAL] Sleep quality: {quality:.2f}")

    def record_meal(self) -> None:
        """Record that user just ate."""
        state = get_biological_state()
        state.record_meal()
        logger.info("[LOCAL] Meal recorded")

    # =========================================================================
    # Identity API
    # =========================================================================

    def set_birth_date(self, birth_date: date) -> None:
        """Set user's birth date for zodiac/numerology calculations."""
        self._identity.set_birth_date(birth_date)

    def set_birth_time(self, birth_time: time) -> None:
        """Set user's birth time."""
        self._identity.set_birth_time(birth_time)

    def set_chronotype(self, chronotype: str) -> None:
        """Set user's chronotype (early/intermediate/late)."""
        self._identity.set_chronotype(chronotype)

    def has_identity(self) -> bool:
        """Check if user has set birth date."""
        return self._identity.has_identity()

    def get_identity_summary(self) -> Dict[str, Any]:
        """Get summary of user's identity data (non-sensitive)."""
        return self._identity.get_summary()

    # =========================================================================
    # History API
    # =========================================================================

    def get_trend(self, hours: float = 4.0) -> Optional[float]:
        """
        Get mood trend over specified hours.

        Returns:
            Positive = improving, Negative = declining, None = insufficient data
        """
        if len(self._history) < 2:
            return None

        cutoff = datetime.now().timestamp() - (hours * 3600)
        recent = [c for c in self._history if c.timestamp.timestamp() > cutoff]

        if len(recent) < 2:
            return None

        # Calculate trend (simple linear)
        first_avg = sum(c.score for c in recent[: len(recent) // 2]) / (
            len(recent) // 2
        )
        last_avg = sum(c.score for c in recent[len(recent) // 2 :]) / (
            len(recent) - len(recent) // 2
        )

        return last_avg - first_avg

    def get_average(self, hours: float = 4.0) -> Optional[float]:
        """Get average mood over specified hours."""
        if not self._history:
            return None

        cutoff = datetime.now().timestamp() - (hours * 3600)
        recent = [c for c in self._history if c.timestamp.timestamp() > cutoff]

        if not recent:
            return None

        return sum(c.score for c in recent) / len(recent)

    def get_history_count(self) -> int:
        """Get number of historical calculations."""
        return len(self._history)

    # =========================================================================
    # Display API
    # =========================================================================

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive data for dashboard display.

        Returns a dictionary with:
        - current: Latest mood composite
        - trend: Mood trend
        - categories: Individual category breakdowns
        - factors: All individual factors
        """
        composite = self.calculate()

        return {
            "current": {
                "score": round(composite.score, 3),
                "label": composite.mood_label(),
                "icon": composite.mood_icon(),
                "confidence": round(composite.confidence, 3),
                "summary": composite.summary(),
            },
            "trend": {
                "4h": self.get_trend(4.0),
                "1h": self.get_trend(1.0),
            },
            "categories": {
                cat.name_str: {
                    "weight": cat.weight,
                    "icon": cat.icon,
                    "score": (
                        round(composite.categories[cat.name_str].score, 3)
                        if cat.name_str in composite.categories
                        else 0.5
                    ),
                    "confidence": (
                        round(composite.categories[cat.name_str].confidence, 3)
                        if cat.name_str in composite.categories
                        else 0.0
                    ),
                }
                for cat in FactorCategory
            },
            "identity": self.get_identity_summary(),
            "history_count": self.get_history_count(),
        }

    def format_report(self, detailed: bool = False) -> str:
        """
        Format a text report of current mood state.

        Args:
            detailed: Include all individual factors

        Returns:
            Formatted string report
        """
        composite = self.calculate()

        lines = [
            f"╔══════════════════════════════════════════╗",
            f"║  MOOD FACTORS REPORT                     ║",
            f"╠══════════════════════════════════════════╣",
            f"║  {composite.summary():<38} ║",
            f"╠══════════════════════════════════════════╣",
        ]

        for cat in FactorCategory:
            cat_score = composite.categories.get(cat.name_str)
            if cat_score:
                pct = int(cat_score.score * 100)
                weight_pct = int(cat.weight * 100)
                lines.append(
                    f"║  {cat.icon} {cat.name_str.title():<12} {pct:>3}%  "
                    f"(weight: {weight_pct}%)     ║"
                )

        lines.extend(
            [
                f"╠══════════════════════════════════════════╣",
                f"║  Confidence: {int(composite.confidence * 100)}%                          ║",
            ]
        )

        # Trend
        trend = self.get_trend(1.0)
        if trend is not None:
            trend_icon = "📈" if trend > 0.05 else "📉" if trend < -0.05 else "➡️"
            lines.append(
                f"║  Trend (1h): {trend_icon} {trend:+.2f}                      ║"
            )

        lines.append(f"╚══════════════════════════════════════════╝")

        if detailed:
            lines.append("")
            lines.append("DETAILED FACTORS:")
            lines.append("─" * 44)

            for cat in FactorCategory:
                cat_score = composite.categories.get(cat.name_str)
                if cat_score and cat_score.factors:
                    lines.append(f"\n{cat.icon} {cat.name_str.upper()}")
                    for factor in cat_score.factors:
                        pct = int(factor.score * 100)
                        conf = factor.confidence.name_str[0].upper()
                        lines.append(f"  • {factor.description} [{pct}% {conf}]")

        return "\n".join(lines)


# =============================================================================
# Singleton Instance
# =============================================================================

_mood_engine: Optional[MoodEngine] = None


def get_mood_engine() -> MoodEngine:
    """Get or create the global mood engine instance."""
    global _mood_engine
    if _mood_engine is None:
        _mood_engine = MoodEngine()
    return _mood_engine


def reset_mood_engine() -> None:
    """Reset the mood engine (for testing or new session)."""
    global _mood_engine
    _mood_engine = MoodEngine()
