"""Utilities for generating quiz options."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List, Sequence

import pandas as pd


@dataclass(frozen=True)
class OptionItem:
    """Representation of a selectable quiz option."""

    row_idx: int
    label: str

    def __str__(self) -> str:
        return self.label


def build_option_label(row: pd.Series) -> str:
    """Format the display label for an option row."""
    make = f"{row['make_ko']}({row['make_en']})" if row["make_ko"] else row["make_en"]
    model = (
        f"{row['model_ko']}({row['model_en']})"
        if row["model_ko"]
        else row["model_en"]
    )
    year = row["year"]
    variant = row.get("variant", "")

    components = [make, model, year]
    if variant:
        components.append(variant)
    # Components already contain bilingual text where relevant.
    return " ".join(str(part) for part in components if part)


def _candidate_indices(
    df: pd.DataFrame, mask: pd.Series, exclude: Sequence[int]
) -> List[int]:
    indices: List[int] = []
    excluded = set(exclude)
    for idx in df[mask].index.tolist():
        if idx in excluded:
            continue
        indices.append(int(idx))
    return indices


def generate_options(
    df: pd.DataFrame,
    correct_idx: int,
    total_options: int = 10,
    difficulty: str = "medium",
    rng: random.Random | None = None,
) -> List[OptionItem]:
    """Return a randomized list of OptionItems including the correct answer."""
    if rng is None:
        rng = random.Random()

    available_count = len(df)
    if available_count == 0:
        raise ValueError("The dataframe is empty; cannot generate options.")

    total_options = max(2, min(total_options, available_count))

    if correct_idx not in df.index:
        raise KeyError(f"Index {correct_idx} not in dataframe")

    correct_row = df.loc[correct_idx]
    selected_set = {int(correct_idx)}

    difficulty = difficulty.lower()

    difficulty_plan = {
        "easy": {
            "same_make": 2,
            "same_model": 1,
            "same_year": 1,
        },
        "medium": {
            "same_make": 4,
            "same_model": 2,
            "same_year": 2,
        },
        "hard": {
            "same_make": 6,
            "same_model": 3,
            "same_year": 1,
        },
    }
    plan = difficulty_plan.get(
        difficulty,
        difficulty_plan["medium"],
    )

    def try_add(mask: pd.Series, target: int, *, different_make: bool = False) -> None:
        if len(selected_set) >= total_options or target <= 0:
            return
        candidates = _candidate_indices(df, mask, selected_set)
        if different_make:
            candidates = [
                idx
                for idx in candidates
                if df.loc[idx, "make_en"] != correct_row["make_en"]
            ]
        rng.shuffle(candidates)
        for candidate_idx in candidates[:target]:
            selected_set.add(candidate_idx)
            if len(selected_set) >= total_options:
                return

    # Strategy buckets based on the plan.
    try_add(
        df["make_en"].eq(correct_row["make_en"]) & (df.index != correct_idx),
        target=plan["same_make"],
    )

    try_add(
        df["model_en"].eq(correct_row["model_en"])
        & (df["year"] != correct_row["year"])
        & (df.index != correct_idx),
        target=plan["same_model"],
    )

    try_add(
        df["year"].eq(correct_row["year"]) & (df.index != correct_idx),
        target=plan["same_year"],
        different_make=(difficulty == "easy"),
    )

    # Fill the remaining slots. For easy mode, prefer different manufacturers.
    if len(selected_set) < total_options:
        remaining_indices = [
            int(idx) for idx in df.index.tolist() if int(idx) not in selected_set
        ]
        if difficulty == "easy":
            rng.shuffle(remaining_indices)
            different_make_indices = [
                idx
                for idx in remaining_indices
                if df.loc[idx, "make_en"] != correct_row["make_en"]
            ]
            same_make_indices = [
                idx
                for idx in remaining_indices
                if df.loc[idx, "make_en"] == correct_row["make_en"]
            ]
            ordered_indices = different_make_indices + same_make_indices
        elif difficulty == "hard":
            rng.shuffle(remaining_indices)
            same_make_indices = [
                idx
                for idx in remaining_indices
                if df.loc[idx, "make_en"] == correct_row["make_en"]
            ]
            different_make_indices = [
                idx
                for idx in remaining_indices
                if df.loc[idx, "make_en"] != correct_row["make_en"]
            ]
            ordered_indices = same_make_indices + different_make_indices
        else:
            rng.shuffle(remaining_indices)
            ordered_indices = remaining_indices

        for idx in ordered_indices:
            selected_set.add(idx)
            if len(selected_set) >= total_options:
                break

    selected_list = list(selected_set)
    if len(selected_list) < total_options:
        raise RuntimeError(
            f"Unable to collect {total_options} options from dataset "
            f"(only {len(selected_list)})"
        )

    # Shuffle before building OptionItems so the correct answer moves around.
    rng.shuffle(selected_list)

    return [
        OptionItem(row_idx=idx, label=build_option_label(df.loc[idx]))
        for idx in selected_list[:total_options]
    ]
