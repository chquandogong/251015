from __future__ import annotations

import random
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app import options, scoring, storage  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATASET_DIR = Path(__file__).resolve().parents[1] / "dataset"
LABELS_CSV = DATA_DIR / "car_labels.csv"

DIFFICULTY_LABELS = {
    "easy": "하 / Easy",
    "medium": "중 / Medium",
    "hard": "상 / Hard",
}
DIFFICULTY_ORDER = ["easy", "medium", "hard"]


def configure_page() -> None:
    st.set_page_config(
        page_title="Car Picker Quiz",
        page_icon="🚗",
        layout="wide",
    )


@st.cache_data(show_spinner=False)
def load_metadata(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    # Drop rows with missing essentials.
    valid = df[
        df["image_path"].notna()
        & df["make_en"].notna()
        & df["model_en"].notna()
        & df["year"].notna()
    ].copy()
    valid["image_path"] = valid["image_path"].astype(str)
    valid["make_en"] = valid["make_en"].astype(str)
    valid["model_en"] = valid["model_en"].astype(str)
    valid["year"] = valid["year"].astype(str)
    valid["variant"] = valid.get("variant", "").fillna("")
    valid["make_ko"] = valid.get("make_ko", valid["make_en"]).fillna(valid["make_en"])
    valid["model_ko"] = valid.get("model_ko", valid["model_en"]).fillna(
        valid["model_en"]
    )
    # Preserve original index for deterministic lookups.
    return valid.reset_index(drop=True)


def init_session_state(df: pd.DataFrame, difficulty: str) -> None:
    if st.session_state.get("quiz_initialized"):
        return

    total_available = len(df)
    if total_available == 0:
        st.error("No labeled images found. Please generate `car_labels.csv`.")
        st.stop()

    total_questions = min(scoring.TOTAL_QUESTIONS, total_available)
    question_order = random.sample(range(total_available), total_questions)

    st.session_state.update(
        {
            "quiz_initialized": True,
            "session_id": uuid.uuid4().hex[:8],
            "question_order": question_order,
            "current_question_idx": 0,
            "total_questions": total_questions,
            "score": 0,
            "history": [],
            "question_start_ts": time.time(),
            "current_options": None,
            "summary_logged": False,
            "ended_early": False,
            "difficulty": difficulty,
        }
    )


def reset_session(*, difficulty: Optional[str] = None) -> None:
    selected_difficulty = (difficulty or st.session_state.get("difficulty", "medium")).lower()
    load_metadata.clear()  # type: ignore[attr-defined]
    st.session_state.clear()
    st.session_state["difficulty"] = selected_difficulty


def difficulty_label(value: str) -> str:
    return DIFFICULTY_LABELS.get(value.lower(), value.title())


def select_difficulty() -> str:
    current = st.session_state.get("difficulty", "medium")
    if current not in DIFFICULTY_ORDER:
        current = "medium"
    default_idx = DIFFICULTY_ORDER.index(current)
    selected = st.sidebar.radio(
        "난이도 / Difficulty",
        DIFFICULTY_ORDER,
        index=default_idx,
        format_func=difficulty_label,
    )
    if selected != current:
        reset_session(difficulty=selected)
        st.rerun()
    return selected


def get_current_dataframe_row(df: pd.DataFrame) -> pd.Series:
    idx = st.session_state["question_order"][st.session_state["current_question_idx"]]
    return df.loc[idx]


def ensure_current_options(df: pd.DataFrame) -> list[options.OptionItem]:
    if st.session_state.get("current_options") is None:
        correct_idx = st.session_state["question_order"][st.session_state["current_question_idx"]]
        rng = random.Random()
        st.session_state["current_options"] = options.generate_options(
            df,
            correct_idx,
            total_options=min(10, len(df)),
            difficulty=st.session_state.get("difficulty", "medium"),
            rng=rng,
        )
        if len(st.session_state["current_options"]) != min(10, len(df)):
            raise RuntimeError("Failed to generate the expected number of options.")
    return st.session_state["current_options"]


def load_image_path(image_path: str) -> Path:
    absolute_path = DATASET_DIR / image_path
    if not absolute_path.exists():
        raise FileNotFoundError(f"Image not found: {absolute_path}")
    return absolute_path


def display_status() -> None:
    current = st.session_state["current_question_idx"] + 1
    total = st.session_state["total_questions"]
    score = st.session_state["score"]
    difficulty = st.session_state.get("difficulty", "medium")
    st.markdown(f"**진행 상황 / Progress:** {current} / {total}")
    st.markdown(f"**점수 / Score:** {score} / {scoring.max_score()}")
    st.markdown(f"**난이도 / Difficulty:** {difficulty_label(difficulty)}")
    if st.session_state["history"]:
        last = st.session_state["history"][-1]
        message = (
            "✅ 정답! / Correct!"
            if last["is_correct"]
            else f"❌ 오답 / Incorrect: 정답은 {last['correct_label']}"
        )
        st.info(message)


def display_image(correct_row: pd.Series) -> None:
    try:
        image_path = load_image_path(correct_row["image_path"])
        st.image(str(image_path), use_column_width=True)
    except FileNotFoundError as exc:
        st.error(str(exc))


def log_response(
    correct_row: pd.Series,
    selected_row: pd.Series,
    is_correct: bool,
    response_time: float,
) -> None:
    storage.log_response(
        {
            "session_id": st.session_state["session_id"],
            "timestamp": storage.utc_timestamp(),
            "question_idx": st.session_state["current_question_idx"] + 1,
            "image_path": correct_row["image_path"],
            "selected_make_en": selected_row.get("make_en", ""),
            "selected_model_en": selected_row.get("model_en", ""),
            "selected_year": selected_row.get("year", ""),
            "selected_variant": selected_row.get("variant", ""),
            "correct_make_en": correct_row.get("make_en", ""),
            "correct_model_en": correct_row.get("model_en", ""),
            "correct_year": correct_row.get("year", ""),
            "correct_variant": correct_row.get("variant", ""),
            "is_correct": int(is_correct),
            "score_after_question": st.session_state["score"],
            "response_time_sec": round(response_time, 2),
        }
    )


def log_summary(total_time: float) -> None:
    if st.session_state.get("summary_logged"):
        return

    history = st.session_state["history"]
    correct_answers = sum(1 for item in history if item["is_correct"])
    average_time = total_time / len(history) if history else 0.0

    storage.log_summary(
        {
            "session_id": st.session_state["session_id"],
            "timestamp": storage.utc_timestamp(),
            "total_questions": st.session_state["total_questions"],
            "correct_answers": correct_answers,
            "total_score": st.session_state["score"],
            "total_time_sec": round(total_time, 2),
            "average_response_time_sec": round(average_time, 2),
            "difficulty": st.session_state.get("difficulty", "medium"),
            "ended_early": int(st.session_state["ended_early"]),
        }
    )
    st.session_state["summary_logged"] = True


def handle_submission(
    df: pd.DataFrame,
    correct_row: pd.Series,
    selected_option: Optional[options.OptionItem],
) -> None:
    if selected_option is None:
        st.warning("보기를 선택해 주세요. Please choose an option.")
        return

    response_time = time.time() - st.session_state["question_start_ts"]
    selected_row = df.loc[selected_option.row_idx]
    is_correct = selected_option.row_idx == correct_row.name

    st.session_state["score"] += scoring.score_answer(is_correct)

    log_response(correct_row, selected_row, is_correct, response_time)

    st.session_state["history"].append(
        {
            "question": st.session_state["current_question_idx"] + 1,
            "selected_label": selected_option.label,
            "correct_label": options.build_option_label(correct_row),
            "is_correct": is_correct,
            "response_time_sec": round(response_time, 2),
        }
    )

    st.session_state["current_question_idx"] += 1
    st.session_state["current_options"] = None
    st.session_state["question_start_ts"] = time.time()
    st.session_state.pop("selected_option", None)


def has_finished() -> bool:
    reached_end = st.session_state["current_question_idx"] >= st.session_state["total_questions"]
    return reached_end or st.session_state.get("ended_early", False)


def display_summary() -> None:
    total_time = (
        sum(entry["response_time_sec"] for entry in st.session_state["history"])
        if st.session_state["history"]
        else 0.0
    )
    log_summary(total_time)

    st.success("퀴즈가 종료되었습니다! / Quiz complete!")
    st.metric(
        label="최종 점수 / Final Score",
        value=f"{st.session_state['score']} / {scoring.max_score()}",
    )
    st.write(
        f"선택 난이도 / Difficulty: {difficulty_label(st.session_state.get('difficulty', 'medium'))}"
    )

    correct_answers = sum(1 for entry in st.session_state["history"] if entry["is_correct"])
    st.write(f"정답 수 / Correct answers: {correct_answers}")
    st.write(f"총 소요 시간 / Total time: {total_time:.2f}s")

    if st.session_state["history"]:
        st.subheader("문항별 기록 / Question Review")
        for entry in st.session_state["history"]:
            st.write(
                f"Q{entry['question']}: {'✅' if entry['is_correct'] else '❌'} "
                f"{entry['selected_label']} "
                f"(정답 / Correct: {entry['correct_label']}, "
                f"응답 시간 / Response time: {entry['response_time_sec']}s)"
            )

    if st.button("다시 시작 / Restart Quiz"):
        reset_session(difficulty=st.session_state.get("difficulty", "medium"))
        st.rerun()


def main() -> None:
    configure_page()
    difficulty = select_difficulty()
    df = load_metadata(LABELS_CSV)
    init_session_state(df, difficulty)

    display_header()

    if has_finished():
        display_summary()
        return

    correct_row = get_current_dataframe_row(df)
    display_status()

    col_image, col_options = st.columns([3, 2])
    with col_image:
        display_image(correct_row)

    possible_options = ensure_current_options(df)
    with col_options:
        st.subheader("정답 선택 / Select the correct car")
        selected = st.radio(
            "보기 / Options",
            options=possible_options,
            format_func=str,
            index=None,
            key="selected_option",
        )

        submit_clicked = st.button("제출 / Submit", type="primary")
        if submit_clicked:
            handle_submission(df, correct_row, selected)
            if st.session_state["score"] >= 60 and not st.session_state["ended_early"]:
                st.session_state["ended_early_allowed"] = True
            st.rerun()

        can_end = (
            st.session_state["score"] >= 60
            or st.session_state["current_question_idx"] + 1
            > st.session_state["total_questions"]
        )
        end_now = st.button(
            "종료 / End Quiz",
            disabled=not can_end,
        )
        if end_now and can_end:
            st.session_state["ended_early"] = True
            st.rerun()


if __name__ == "__main__":
    main()
