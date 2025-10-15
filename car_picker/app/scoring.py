"""Scoring logic for the car quiz."""

POINTS_PER_QUESTION = 10
TOTAL_QUESTIONS = 10


def score_answer(is_correct: bool) -> int:
    """Return the points earned for a single question."""
    return POINTS_PER_QUESTION if is_correct else 0


def max_score() -> int:
    """Return the maximum attainable score for a session."""
    return POINTS_PER_QUESTION * TOTAL_QUESTIONS
