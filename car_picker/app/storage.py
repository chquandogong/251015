"""CSV persistence helpers for the quiz app."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

QUIZ_LOG_COLUMNS = [
    "session_id",
    "timestamp",
    "question_idx",
    "image_path",
    "selected_make_en",
    "selected_model_en",
    "selected_year",
    "selected_variant",
    "correct_make_en",
    "correct_model_en",
    "correct_year",
    "correct_variant",
    "is_correct",
    "score_after_question",
    "response_time_sec",
]

SUMMARY_COLUMNS = [
    "session_id",
    "timestamp",
    "total_questions",
    "correct_answers",
    "total_score",
    "total_time_sec",
    "average_response_time_sec",
    "difficulty",
    "ended_early",
]

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
QUIZ_LOG_PATH = RESULTS_DIR / "quiz_log.csv"
SUMMARY_PATH = RESULTS_DIR / "summary.csv"


def _append_row(path: Path, columns: list[str], row: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def log_response(row: Dict[str, object]) -> None:
    """Append a single question response to the quiz log CSV."""
    _append_row(QUIZ_LOG_PATH, QUIZ_LOG_COLUMNS, row)


def log_summary(row: Dict[str, object]) -> None:
    """Append a session summary to the summary CSV."""
    _append_row(SUMMARY_PATH, SUMMARY_COLUMNS, row)


def utc_timestamp() -> str:
    """Return an ISO formatted UTC timestamp."""
    return datetime.now(tz=timezone.utc).isoformat()
