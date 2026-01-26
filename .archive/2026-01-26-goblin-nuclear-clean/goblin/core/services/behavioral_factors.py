"""
uDOS Behavioral Factors - User Activity-Based Mood Indicators
Alpha v1.0.0.65

Calculates mood factors based on observable behavioral patterns:
- Typing speed and rhythm
- Prompt frequency and complexity
- Error rate and corrections
- Session duration and patterns
- Break patterns

These factors have the highest weight (30%) because they're
direct observations of user state, not predictions.

Privacy: All metrics are calculated locally and stored with daily hashing.
"""

import math
import time as time_module
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Deque
from collections import deque
from dataclasses import dataclass, field

from dev.goblin.core.services.mood_factors import (
    BaseFactor,
    BaseCategoryCalculator,
    MoodFactorResult,
    FactorCategory,
    FactorConfidence,
    normalize_score,
    gaussian_peak,
    sigmoid_score,
)
from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("behavioral-factors")


# =============================================================================
# Behavioral Metrics Collector
# =============================================================================


@dataclass
class KeystrokeEvent:
    """Single keystroke event."""

    timestamp: float  # Unix timestamp
    is_backspace: bool = False


@dataclass
class PromptEvent:
    """Single prompt submission event."""

    timestamp: float
    length: int  # Character count
    word_count: int
    complexity_score: float  # 0-1, based on vocabulary, etc.


@dataclass
class SessionMetrics:
    """Aggregated session metrics."""

    session_start: float = field(default_factory=time_module.time)
    total_keystrokes: int = 0
    total_backspaces: int = 0
    total_prompts: int = 0
    total_prompt_chars: int = 0

    # Rolling windows for recent activity
    recent_keystroke_intervals: Deque[float] = field(
        default_factory=lambda: deque(maxlen=100)
    )
    recent_prompts: Deque[PromptEvent] = field(default_factory=lambda: deque(maxlen=20))

    # Break tracking
    last_activity: float = field(default_factory=time_module.time)
    breaks_taken: int = 0
    total_break_time: float = 0.0


class BehavioralMetricsCollector:
    """
    Collects and aggregates behavioral metrics during a session.

    This class should be instantiated once per session and updated
    in real-time as the user interacts with the system.
    """

    # Thresholds
    BREAK_THRESHOLD = 300.0  # 5 minutes of no activity = break
    RAPID_TYPING_WPM = 60  # Words per minute threshold
    SLOW_TYPING_WPM = 20

    def __init__(self):
        self.metrics = SessionMetrics()
        self._last_keystroke_time: Optional[float] = None
        self._in_break = False
        self._break_start: Optional[float] = None

    def record_keystroke(self, is_backspace: bool = False) -> None:
        """Record a keystroke event."""
        now = time_module.time()

        # Check for break
        self._check_break(now)

        # Record interval if we have a previous keystroke
        if self._last_keystroke_time is not None:
            interval = now - self._last_keystroke_time
            if interval < 10.0:  # Ignore gaps > 10 seconds
                self.metrics.recent_keystroke_intervals.append(interval)

        self._last_keystroke_time = now
        self.metrics.last_activity = now
        self.metrics.total_keystrokes += 1

        if is_backspace:
            self.metrics.total_backspaces += 1

    def record_prompt(
        self,
        text: str,
        complexity_score: Optional[float] = None,
    ) -> None:
        """Record a prompt submission."""
        now = time_module.time()

        # Check for break
        self._check_break(now)

        # Calculate complexity if not provided
        if complexity_score is None:
            complexity_score = self._calculate_complexity(text)

        words = len(text.split())

        event = PromptEvent(
            timestamp=now,
            length=len(text),
            word_count=words,
            complexity_score=complexity_score,
        )

        self.metrics.recent_prompts.append(event)
        self.metrics.total_prompts += 1
        self.metrics.total_prompt_chars += len(text)
        self.metrics.last_activity = now

    def _check_break(self, now: float) -> None:
        """Check if user has been on a break."""
        if self.metrics.last_activity is None:
            return

        gap = now - self.metrics.last_activity

        if gap >= self.BREAK_THRESHOLD:
            if not self._in_break:
                # Just returned from a break
                self.metrics.breaks_taken += 1
                self.metrics.total_break_time += gap
                logger.debug(f"[LOCAL] Break detected: {gap/60:.1f} min")

        self._in_break = gap >= self.BREAK_THRESHOLD

    def _calculate_complexity(self, text: str) -> float:
        """Calculate text complexity score (0-1)."""
        if not text:
            return 0.0

        words = text.split()
        if not words:
            return 0.0

        # Factors contributing to complexity
        factors = []

        # Average word length (longer = more complex)
        avg_word_len = sum(len(w) for w in words) / len(words)
        factors.append(normalize_score(avg_word_len, 3.0, 8.0))

        # Vocabulary diversity (unique words / total words)
        unique_ratio = len(set(words)) / len(words)
        factors.append(unique_ratio)

        # Sentence count (more sentences = more structured)
        sentences = text.count(".") + text.count("!") + text.count("?")
        sentence_factor = normalize_score(sentences, 0, 5)
        factors.append(sentence_factor)

        # Technical indicators (code-like content)
        tech_chars = sum(1 for c in text if c in "{}[]()<>=+-*/;:")
        tech_ratio = tech_chars / len(text)
        factors.append(min(1.0, tech_ratio * 10))

        return sum(factors) / len(factors)

    def get_typing_speed_wpm(self) -> Optional[float]:
        """Calculate recent typing speed in words per minute."""
        if len(self.metrics.recent_keystroke_intervals) < 10:
            return None

        # Average interval between keystrokes
        avg_interval = sum(self.metrics.recent_keystroke_intervals) / len(
            self.metrics.recent_keystroke_intervals
        )

        if avg_interval == 0:
            return None

        # Characters per minute
        cpm = 60.0 / avg_interval

        # Words per minute (assuming 5 chars per word)
        wpm = cpm / 5.0

        return wpm

    def get_error_rate(self) -> float:
        """Calculate backspace/error rate."""
        if self.metrics.total_keystrokes == 0:
            return 0.0

        return self.metrics.total_backspaces / self.metrics.total_keystrokes

    def get_prompt_frequency(self) -> Optional[float]:
        """Calculate prompts per hour."""
        if len(self.metrics.recent_prompts) < 2:
            return None

        # Time span of recent prompts
        first = self.metrics.recent_prompts[0].timestamp
        last = self.metrics.recent_prompts[-1].timestamp

        span_hours = (last - first) / 3600.0
        if span_hours < 0.01:  # Less than 36 seconds
            return None

        return len(self.metrics.recent_prompts) / span_hours

    def get_average_complexity(self) -> float:
        """Get average prompt complexity."""
        if not self.metrics.recent_prompts:
            return 0.5

        return sum(p.complexity_score for p in self.metrics.recent_prompts) / len(
            self.metrics.recent_prompts
        )

    def get_session_duration_hours(self) -> float:
        """Get session duration in hours."""
        return (time_module.time() - self.metrics.session_start) / 3600.0

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics."""
        return {
            "session_duration_hours": round(self.get_session_duration_hours(), 2),
            "total_keystrokes": self.metrics.total_keystrokes,
            "total_prompts": self.metrics.total_prompts,
            "typing_speed_wpm": round(self.get_typing_speed_wpm() or 0, 1),
            "error_rate": round(self.get_error_rate(), 3),
            "prompt_frequency": round(self.get_prompt_frequency() or 0, 1),
            "average_complexity": round(self.get_average_complexity(), 2),
            "breaks_taken": self.metrics.breaks_taken,
        }


# Global metrics collector (instantiated per session)
_metrics_collector: Optional[BehavioralMetricsCollector] = None


def get_metrics_collector() -> BehavioralMetricsCollector:
    """Get or create the session metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = BehavioralMetricsCollector()
    return _metrics_collector


def reset_metrics_collector() -> None:
    """Reset the metrics collector (new session)."""
    global _metrics_collector
    _metrics_collector = BehavioralMetricsCollector()


# =============================================================================
# Behavioral Factor Implementations
# =============================================================================


class TypingSpeedFactor(BaseFactor):
    """
    Factor based on typing speed.

    Typing speed can indicate:
    - Fast + steady = engaged, focused
    - Fast + erratic = rushed, stressed
    - Slow + steady = thoughtful, tired
    - Slow + erratic = distracted, uncertain
    """

    name = "typing_speed"
    category = FactorCategory.BEHAVIORAL
    weight = 1.0

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        collector = context.get("behavioral_metrics") or get_metrics_collector()

        wpm = collector.get_typing_speed_wpm()
        if wpm is None:
            return self.default_result("Insufficient typing data")

        # Optimal typing speed: 40-60 WPM (comfortable, engaged)
        # Too fast (>80) might indicate stress
        # Too slow (<20) might indicate fatigue

        # Use gaussian for optimal range
        score = gaussian_peak(wpm, 50.0, 25.0)

        # Penalty for extreme speeds
        if wpm > 90:
            score *= 0.8  # Might be stressed
        elif wpm < 15:
            score *= 0.7  # Might be fatigued

        if wpm > 70:
            desc = "⚡ Fast typing"
        elif wpm > 40:
            desc = "✨ Optimal pace"
        elif wpm > 25:
            desc = "🐢 Measured pace"
        else:
            desc = "💭 Thoughtful pace"

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.HIGH,
            weight=self.weight,
            raw_value=wpm,
            description=f"{desc} ({wpm:.0f} WPM)",
            metadata={"wpm": round(wpm, 1)},
        )


class TypingRhythmFactor(BaseFactor):
    """
    Factor based on typing rhythm consistency.

    Consistent rhythm suggests focused, calm state.
    Erratic rhythm suggests distraction or stress.
    """

    name = "typing_rhythm"
    category = FactorCategory.BEHAVIORAL
    weight = 0.75

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        collector = context.get("behavioral_metrics") or get_metrics_collector()

        intervals = list(collector.metrics.recent_keystroke_intervals)
        if len(intervals) < 20:
            return self.default_result("Insufficient rhythm data")

        # Calculate coefficient of variation (CV = std/mean)
        # Lower CV = more consistent rhythm
        mean = sum(intervals) / len(intervals)
        if mean == 0:
            return self.default_result("Invalid interval data")

        variance = sum((x - mean) ** 2 for x in intervals) / len(intervals)
        std = math.sqrt(variance)
        cv = std / mean

        # CV < 0.3 = very consistent
        # CV 0.3-0.6 = normal
        # CV > 0.6 = erratic

        # Convert to score (lower CV = higher score)
        score = normalize_score(cv, 0.8, 0.2)  # Inverted: 0.2 CV = 1.0, 0.8 CV = 0.0

        if cv < 0.3:
            desc = "🎯 Very consistent"
        elif cv < 0.5:
            desc = "👍 Normal rhythm"
        elif cv < 0.7:
            desc = "⚡ Variable rhythm"
        else:
            desc = "🌊 Erratic rhythm"

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.HIGH,
            weight=self.weight,
            raw_value=cv,
            description=desc,
            metadata={"coefficient_of_variation": round(cv, 3)},
        )


class ErrorRateFactor(BaseFactor):
    """
    Factor based on typing error rate (backspaces).

    Higher error rates can indicate:
    - Rushing (stress)
    - Fatigue (coordination decline)
    - Distraction
    """

    name = "error_rate"
    category = FactorCategory.BEHAVIORAL
    weight = 0.75

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        collector = context.get("behavioral_metrics") or get_metrics_collector()

        if collector.metrics.total_keystrokes < 50:
            return self.default_result("Insufficient keystroke data")

        error_rate = collector.get_error_rate()

        # Normal error rate: 5-10%
        # High: > 15%
        # Low: < 5%

        # Score inversely related to error rate
        score = normalize_score(error_rate, 0.20, 0.02)  # 2% = 1.0, 20% = 0.0

        pct = error_rate * 100
        if pct < 5:
            desc = "✨ Very accurate"
        elif pct < 10:
            desc = "👍 Normal accuracy"
        elif pct < 15:
            desc = "📝 Some corrections"
        else:
            desc = "🔄 High corrections"

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.HIGH,
            weight=self.weight,
            raw_value=error_rate,
            description=f"{desc} ({pct:.1f}%)",
            metadata={"error_rate_percent": round(pct, 1)},
        )


class PromptFrequencyFactor(BaseFactor):
    """
    Factor based on prompt submission frequency.

    - Very high frequency: might indicate frustration or rapid iteration
    - Moderate: engaged, productive
    - Low: deep thinking or disengaged
    """

    name = "prompt_frequency"
    category = FactorCategory.BEHAVIORAL
    weight = 0.5

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        collector = context.get("behavioral_metrics") or get_metrics_collector()

        freq = collector.get_prompt_frequency()
        if freq is None:
            return self.default_result("Insufficient prompt data")

        # Optimal: 10-30 prompts per hour
        # Very high (>60): possibly frustrated
        # Low (<5): deep work or disengaged

        score = gaussian_peak(freq, 20.0, 15.0)

        if freq > 50:
            desc = "⚡ Rapid iteration"
        elif freq > 25:
            desc = "🔥 High engagement"
        elif freq > 10:
            desc = "✨ Optimal pace"
        elif freq > 5:
            desc = "💭 Thoughtful pace"
        else:
            desc = "🧘 Deep focus"

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.MEDIUM,
            weight=self.weight,
            raw_value=freq,
            description=f"{desc} ({freq:.0f}/hr)",
            metadata={"prompts_per_hour": round(freq, 1)},
        )


class PromptComplexityFactor(BaseFactor):
    """
    Factor based on prompt complexity.

    Complexity indicates cognitive load and engagement level.
    - High complexity: engaged, working on challenging tasks
    - Low complexity: possibly fatigued, doing simple tasks
    """

    name = "prompt_complexity"
    category = FactorCategory.BEHAVIORAL
    weight = 0.5

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        collector = context.get("behavioral_metrics") or get_metrics_collector()

        complexity = collector.get_average_complexity()

        if not collector.metrics.recent_prompts:
            return self.default_result("No prompts recorded")

        # Complexity 0.3-0.6 is typical
        # Very high might indicate overload
        # Very low might indicate fatigue or simple tasks

        score = gaussian_peak(complexity, 0.5, 0.25)

        if complexity > 0.7:
            desc = "🧠 High complexity"
        elif complexity > 0.5:
            desc = "✨ Engaged"
        elif complexity > 0.3:
            desc = "📝 Standard"
        else:
            desc = "💬 Simple"

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.MEDIUM,
            weight=self.weight,
            raw_value=complexity,
            description=f"{desc}",
            metadata={"complexity_score": round(complexity, 2)},
        )


class SessionDurationFactor(BaseFactor):
    """
    Factor based on session duration.

    Long sessions without breaks can indicate:
    - Hyperfocus (can be positive or exhausting)
    - Forgetting to take breaks (fatigue building)
    """

    name = "session_duration"
    category = FactorCategory.BEHAVIORAL
    weight = 0.5

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        collector = context.get("behavioral_metrics") or get_metrics_collector()

        hours = collector.get_session_duration_hours()
        breaks = collector.metrics.breaks_taken

        # Optimal: 2-4 hours with regular breaks
        # Short (<1h): warming up
        # Long (>4h) without breaks: fatigue risk

        # Base score from duration
        score = gaussian_peak(hours, 2.5, 1.5)

        # Adjust for breaks in long sessions
        if hours > 2 and breaks == 0:
            score *= 0.8  # Penalty for no breaks
        elif hours > 4 and breaks < 2:
            score *= 0.7  # Bigger penalty

        if hours < 0.5:
            desc = "🌅 Just starting"
        elif hours < 2:
            desc = "✨ Warming up"
        elif hours < 4:
            desc = "🔥 In the zone"
        elif hours < 6:
            desc = "⏰ Extended session"
        else:
            desc = "🌙 Marathon session"

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.HIGH,
            weight=self.weight,
            raw_value=hours,
            description=f"{desc} ({hours:.1f}h, {breaks} breaks)",
            metadata={
                "hours": round(hours, 2),
                "breaks": breaks,
            },
        )


class BreakPatternFactor(BaseFactor):
    """
    Factor based on break-taking patterns.

    Regular breaks improve sustained performance.
    """

    name = "break_pattern"
    category = FactorCategory.BEHAVIORAL
    weight = 0.5

    def calculate(self, context: Dict[str, Any]) -> MoodFactorResult:
        collector = context.get("behavioral_metrics") or get_metrics_collector()

        hours = collector.get_session_duration_hours()
        breaks = collector.metrics.breaks_taken

        if hours < 0.5:
            return self.default_result("Session too short")

        # Expected breaks: roughly 1 per hour after first hour
        expected_breaks = max(0, hours - 1)

        if expected_breaks == 0:
            score = 0.6  # Early in session, breaks not needed yet
            desc = "🌱 Early session"
        else:
            # Break ratio
            ratio = breaks / expected_breaks
            score = gaussian_peak(ratio, 1.0, 0.5)

            if ratio >= 1.0:
                desc = "✨ Good break habits"
            elif ratio >= 0.5:
                desc = "👍 Some breaks"
            else:
                desc = "⚠️ Consider a break"

        return MoodFactorResult(
            name=self.name,
            category=self.category,
            score=score,
            confidence=FactorConfidence.MEDIUM,
            weight=self.weight,
            raw_value=breaks,
            description=desc,
            metadata={
                "breaks_taken": breaks,
                "session_hours": round(hours, 2),
            },
        )


# =============================================================================
# Behavioral Category Calculator
# =============================================================================


class BehavioralCategoryCalculator(BaseCategoryCalculator):
    """Calculator for all behavioral factors."""

    category = FactorCategory.BEHAVIORAL

    def __init__(self):
        super().__init__()

        # Register all behavioral factors
        self.register_factor(TypingSpeedFactor())
        self.register_factor(TypingRhythmFactor())
        self.register_factor(ErrorRateFactor())
        self.register_factor(PromptFrequencyFactor())
        self.register_factor(PromptComplexityFactor())
        self.register_factor(SessionDurationFactor())
        self.register_factor(BreakPatternFactor())

        logger.debug(f"[LOCAL] Registered {len(self.factors)} behavioral factors")
