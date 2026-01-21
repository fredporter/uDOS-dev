"""
uDOS Mood Factors Framework - Factor Calculation Infrastructure
Alpha v1.0.0.65

Defines the base classes and interfaces for the four-category mood factor system:
- Celestial (25%): lunar phase, solar position, zodiac alignment
- Temporal (25%): circadian rhythm, day of week, numerology
- Behavioral (30%): typing patterns, session activity, prompt complexity
- Biological (20%): self-reported energy, activity inference

Usage:
    from dev.goblin.core.services.mood_factors import MoodFactorEngine

    engine = MoodFactorEngine()
    composite = engine.calculate_composite()
    print(f"Mood score: {composite.score:.2f}")
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, date, time
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import math

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("mood-factors")


# =============================================================================
# Enums and Constants
# =============================================================================


class FactorCategory(Enum):
    """The four mood factor categories with their weights."""

    CELESTIAL = ("celestial", 0.25, "🌙")
    TEMPORAL = ("temporal", 0.25, "⏰")
    BEHAVIORAL = ("behavioral", 0.30, "⌨️")
    BIOLOGICAL = ("biological", 0.20, "🧬")

    @property
    def name_str(self) -> str:
        return self.value[0]

    @property
    def weight(self) -> float:
        return self.value[1]

    @property
    def icon(self) -> str:
        return self.value[2]


class FactorConfidence(Enum):
    """Confidence level of a factor calculation."""

    HIGH = ("high", 1.0)  # Direct measurement or calculation
    MEDIUM = ("medium", 0.7)  # Inferred or estimated
    LOW = ("low", 0.4)  # Fallback or default
    NONE = ("none", 0.0)  # No data available

    @property
    def name_str(self) -> str:
        return self.value[0]

    @property
    def multiplier(self) -> float:
        return self.value[1]


# =============================================================================
# Factor Result Data Classes
# =============================================================================


@dataclass
class MoodFactorResult:
    """
    Result of a single mood factor calculation.

    Attributes:
        name: Factor name (e.g., "lunar_phase", "typing_speed")
        category: Which of the four categories this belongs to
        score: Normalized score from 0.0 to 1.0
        confidence: How reliable this calculation is
        weight: Factor's weight within its category
        raw_value: The raw calculated value before normalization
        description: Human-readable description of what this means
        metadata: Additional data about the calculation
    """

    name: str
    category: FactorCategory
    score: float  # 0.0 to 1.0
    confidence: FactorConfidence
    weight: float = 1.0  # Weight within category
    raw_value: Optional[Any] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def effective_score(self) -> float:
        """Score adjusted by confidence."""
        return self.score * self.confidence.multiplier

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category.name_str,
            "score": round(self.score, 3),
            "confidence": self.confidence.name_str,
            "weight": self.weight,
            "description": self.description,
            "raw_value": self.raw_value,
        }


@dataclass
class CategoryScore:
    """Aggregated score for a factor category."""

    category: FactorCategory
    score: float  # Weighted average of factors
    confidence: float  # Average confidence
    factors: List[MoodFactorResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.name_str,
            "icon": self.category.icon,
            "weight": self.category.weight,
            "score": round(self.score, 3),
            "confidence": round(self.confidence, 3),
            "factor_count": len(self.factors),
            "factors": [f.to_dict() for f in self.factors],
        }


@dataclass
class MoodComposite:
    """
    Composite mood score combining all categories.

    The final score is a weighted average of category scores,
    further adjusted by overall confidence.
    """

    score: float  # 0.0 to 1.0, the final mood composite
    confidence: float  # Overall confidence
    categories: Dict[str, CategoryScore]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_category(self, category: FactorCategory) -> Optional[CategoryScore]:
        return self.categories.get(category.name_str)

    def mood_label(self) -> str:
        """Get a human-readable mood label."""
        if self.score >= 0.8:
            return "excellent"
        elif self.score >= 0.6:
            return "good"
        elif self.score >= 0.4:
            return "moderate"
        elif self.score >= 0.2:
            return "low"
        else:
            return "challenging"

    def mood_icon(self) -> str:
        """Get an icon representing the mood."""
        if self.score >= 0.8:
            return "🌟"
        elif self.score >= 0.6:
            return "☀️"
        elif self.score >= 0.4:
            return "⛅"
        elif self.score >= 0.2:
            return "🌥️"
        else:
            return "🌧️"

    def summary(self) -> str:
        """Get a summary string."""
        label = self.mood_label()
        icon = self.mood_icon()
        pct = int(self.score * 100)
        conf = int(self.confidence * 100)
        return f"{icon} {label.title()} ({pct}% mood, {conf}% confidence)"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 3),
            "confidence": round(self.confidence, 3),
            "label": self.mood_label(),
            "icon": self.mood_icon(),
            "timestamp": self.timestamp.isoformat(),
            "categories": {k: v.to_dict() for k, v in self.categories.items()},
            "metadata": self.metadata,
        }


# =============================================================================
# Base Factor Calculator
# =============================================================================


class BaseFactor(ABC):
    """
    Abstract base class for individual mood factors.

    Implement calculate() to return a MoodFactorResult.
    """

    name: str = "base_factor"
    category: FactorCategory = FactorCategory.BIOLOGICAL
    weight: float = 1.0

    @abstractmethod
    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        """
        Calculate the factor value.

        Args:
            context: Dictionary containing relevant data like:
                - datetime: Current datetime
                - identity: User's DerivedIdentity
                - session: Current session data
                - behavioral: Behavioral metrics

        Returns:
            MoodFactorResult with normalized score
        """
        pass

    def default_result(self, reason: str = "No data") -> MoodFactorResult:
        """Return a default/fallback result."""
        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=0.5,  # Neutral
            confidence=FactorConfidence.NONE,
            weight=self.weight,
            description=reason,
        )


class BaseCategoryCalculator(ABC):
    """
    Abstract base class for category calculators.

    Each category (Celestial, Temporal, etc.) has a calculator
    that aggregates multiple factors.
    """

    category: FactorCategory = FactorCategory.BIOLOGICAL

    def __init__(self):
        self.factors: List[BaseFactor] = []

    def register_factor(self, factor: BaseFactor) -> None:
        """Register a factor calculator."""
        if factor.category != self.category:
            logger.warning(f"Factor {factor.name} category mismatch")
        self.factors.append(factor)

    def calculate(self, context: Dict[str, Any]) -> CategoryScore:
        """Calculate all factors and aggregate into category score."""
        results: List[MoodFactorResult] = []

        for factor in self.factors:
            try:
                result = factor.calculate(context)
                results.append(result)
            except Exception as e:
                logger.warning(f"[LOCAL] Factor {factor.name} failed: {e}")
                results.append(factor.default_result(f"Error: {e}"))

        if not results:
            return CategoryScore(
                category=self.category,
                score=0.5,
                confidence=0.0,
                factors=[],
            )

        # Weighted average of factor scores
        total_weight = sum(r.weight for r in results)
        if total_weight == 0:
            total_weight = 1.0

        weighted_score = (
            sum(r.effective_score() * r.weight for r in results) / total_weight
        )
        avg_confidence = sum(r.confidence.multiplier for r in results) / len(results)

        return CategoryScore(
            category=self.category,
            score=weighted_score,
            confidence=avg_confidence,
            factors=results,
        )


# =============================================================================
# Mood Factor Engine
# =============================================================================


class MoodFactorEngine:
    """
    Main engine for calculating composite mood scores.

    Coordinates all category calculators and produces the final MoodComposite.
    """

    def __init__(self):
        self.category_calculators: Dict[FactorCategory, BaseCategoryCalculator] = {}
        self._last_composite: Optional[MoodComposite] = None

        # Initialize with default calculators
        self._init_default_calculators()

    def _init_default_calculators(self) -> None:
        """Initialize default category calculators (to be extended)."""
        # These will be populated by specific implementations
        pass

    def register_calculator(self, calculator: BaseCategoryCalculator) -> None:
        """Register a category calculator."""
        self.category_calculators[calculator.category] = calculator
        logger.debug(
            f"[LOCAL] Registered calculator for {calculator.category.name_str}"
        )

    def calculate_composite(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> MoodComposite:
        """
        Calculate the full composite mood score.

        Args:
            context: Optional context data. If not provided, default context is built.

        Returns:
            MoodComposite with all category scores and final composite
        """
        if context is None:
            context = self._build_context()

        # Calculate each category
        category_scores: Dict[str, CategoryScore] = {}

        for category in FactorCategory:
            calculator = self.category_calculators.get(category)
            if calculator:
                try:
                    score = calculator.calculate(context)
                    category_scores[category.name_str] = score
                except Exception as e:
                    logger.warning(f"[LOCAL] Category {category.name_str} failed: {e}")
                    category_scores[category.name_str] = CategoryScore(
                        category=category,
                        score=0.5,
                        confidence=0.0,
                        factors=[],
                    )
            else:
                # No calculator for this category - use neutral score
                category_scores[category.name_str] = CategoryScore(
                    category=category,
                    score=0.5,
                    confidence=0.0,
                    factors=[],
                )

        # Calculate weighted composite
        total_weight = 0.0
        weighted_sum = 0.0
        confidence_sum = 0.0

        for cat_name, cat_score in category_scores.items():
            category = next(c for c in FactorCategory if c.name_str == cat_name)
            weighted_sum += cat_score.score * category.weight
            total_weight += category.weight
            confidence_sum += cat_score.confidence

        final_score = weighted_sum / total_weight if total_weight > 0 else 0.5
        avg_confidence = (
            confidence_sum / len(category_scores) if category_scores else 0.0
        )

        composite = MoodComposite(
            score=final_score,
            confidence=avg_confidence,
            categories=category_scores,
            timestamp=datetime.now(),
            metadata={
                "categories_counted": len(
                    [c for c in category_scores.values() if c.confidence > 0]
                ),
                "total_factors": sum(len(c.factors) for c in category_scores.values()),
            },
        )

        self._last_composite = composite
        logger.info(f"[LOCAL] Mood composite: {composite.summary()}")

        return composite

    def _build_context(self) -> Dict[str, Any]:
        """Build default context for factor calculations."""
        return {
            "datetime": datetime.now(),
            "date": date.today(),
            "time": datetime.now().time(),
        }

    def get_last_composite(self) -> Optional[MoodComposite]:
        """Get the most recently calculated composite."""
        return self._last_composite


# =============================================================================
# Utility Functions
# =============================================================================


def normalize_score(
    value: float,
    min_val: float,
    max_val: float,
    invert: bool = False,
) -> float:
    """
    Normalize a value to 0.0-1.0 range.

    Args:
        value: The value to normalize
        min_val: Minimum expected value
        max_val: Maximum expected value
        invert: If True, higher values produce lower scores

    Returns:
        Normalized score between 0.0 and 1.0
    """
    if max_val == min_val:
        return 0.5

    normalized = (value - min_val) / (max_val - min_val)
    normalized = max(0.0, min(1.0, normalized))  # Clamp to 0-1

    if invert:
        normalized = 1.0 - normalized

    return normalized


def gaussian_peak(
    value: float,
    peak: float,
    width: float,
) -> float:
    """
    Calculate a Gaussian curve score centered on peak.

    Useful for factors where there's an optimal value (like circadian rhythm).

    Args:
        value: Current value
        peak: Optimal value (score = 1.0)
        width: Standard deviation of the curve

    Returns:
        Score from 0.0 to 1.0, highest at peak
    """
    if width == 0:
        return 1.0 if value == peak else 0.0

    return math.exp(-((value - peak) ** 2) / (2 * width**2))


def sigmoid_score(
    value: float,
    midpoint: float,
    steepness: float = 1.0,
) -> float:
    """
    Calculate a sigmoid score.

    Useful for factors with a gradual transition.

    Args:
        value: Current value
        midpoint: Value where score is 0.5
        steepness: How quickly the transition happens

    Returns:
        Score from 0.0 to 1.0
    """
    try:
        return 1.0 / (1.0 + math.exp(-steepness * (value - midpoint)))
    except OverflowError:
        return 0.0 if value < midpoint else 1.0
