from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class EscalationEvent:
    reason: str
    turn: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConversationState:
    """Holds all mutable state for a single customer conversation session."""

    # Current workflow stage
    stage: str = "faq"  # faq | qualifying | escalated | closing

    # Lead qualification answers (keyed by question label)
    qual_answers: dict[str, str] = field(default_factory=dict)

    # Questions asked so far in qualification (list of question labels)
    qual_questions_asked: list[str] = field(default_factory=list)

    # All escalation events logged this session
    escalation_log: list[EscalationEvent] = field(default_factory=list)

    # Count of consecutive SOP misses (resets on a successful lookup)
    unanswered_count: int = 0

    # Total conversation turns
    turn_count: int = 0

    # Anthropic message history (list of {"role": ..., "content": ...})
    messages: list[dict[str, Any]] = field(default_factory=list)

    # Raw transcript for summary generation
    transcript_lines: list[str] = field(default_factory=list)

    def log_escalation(self, reason: str) -> None:
        self.escalation_log.append(
            EscalationEvent(reason=reason, turn=self.turn_count)
        )
        self.stage = "escalated"

    def record_qual_answer(self, question_label: str, answer: str) -> None:
        self.qual_answers[question_label] = answer

    def is_escalated(self) -> bool:
        return len(self.escalation_log) > 0

    def escalated_this_turn(self) -> bool:
        """Returns True if an escalation was logged on the current turn."""
        return any(e.turn == self.turn_count for e in self.escalation_log)
