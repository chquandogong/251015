"""Utilities to generate `car_labels.csv` for the Streamlit quiz app.

The dataset is expected to live inside the repository at `../dataset`.
Filenames follow the pattern observed in the original GitHub repository, e.g.:
`Acura_ILX_2013_28_16_110_15_4_70_55_179_39_FWD_5_4_4dr_aWg.jpg`.

Running this script will scan all images, extract basic metadata, and write a
CSV with the schema required by the quiz application:

    image_path, make_ko, make_en, model_ko, model_en, year,
    variant, source_url, notes

Translations default to their English counterparts, but you can supply an
external JSON file to override them with proper Korean labels.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

# Default location of the dataset relative to this script.
DEFAULT_DATASET_DIR = Path(__file__).resolve().parents[1] / "dataset"
# Default location for the generated CSV.
DEFAULT_OUTPUT_CSV = Path(__file__).resolve().parent / "car_labels.csv"
# Original data attribution.
SOURCE_URL = (
    "https://github.com/nicolas-gervais/"
    "predicting-car-price-from-scraped-data/tree/master/picture-scraper"
)

# Common manufacturer translations (extend as needed).
DEFAULT_MAKE_TRANSLATIONS = {
    "Acura": "아큐라",
    "Audi": "아우디",
    "BMW": "BMW",
    "Buick": "뷰익",
    "Chevrolet": "쉐보레",
    "Chrysler": "크라이슬러",
    "Dodge": "닷지",
    "Ford": "포드",
    "GMC": "GMC",
    "Honda": "혼다",
    "Hyundai": "현대",
    "Infiniti": "인피니티",
    "Jeep": "지프",
    "Kia": "기아",
    "Lexus": "렉서스",
    "Mazda": "마쯔다",
    "Mercedes-Benz": "메르세데스-벤츠",
    "Nissan": "닛산",
    "Porsche": "포르쉐",
    "Subaru": "스바루",
    "Toyota": "토요타",
    "Volkswagen": "폭스바겐",
    "Volvo": "볼보",
}

# A minimal example for models; by default models fall back to English.
DEFAULT_MODEL_TRANSLATIONS: Dict[str, str] = {
    "Sonata": "쏘나타",
    "Elantra": "엘란트라",
    "Sorento": "쏘렌토",
}

# CSV column order used across the app.
CSV_COLUMNS = [
    "image_path",
    "make_ko",
    "make_en",
    "model_ko",
    "model_en",
    "year",
    "variant",
    "source_url",
    "notes",
]


@dataclass
class LabelRow:
    image_path: str
    make_ko: str
    make_en: str
    model_ko: str
    model_en: str
    year: str
    variant: str
    source_url: str
    notes: str

    def to_csv_row(self) -> Dict[str, str]:
        return {
            "image_path": self.image_path,
            "make_ko": self.make_ko,
            "make_en": self.make_en,
            "model_ko": self.model_ko,
            "model_en": self.model_en,
            "year": self.year,
            "variant": self.variant,
            "source_url": self.source_url,
            "notes": self.notes,
        }


def load_translations(path: Optional[Path]) -> tuple[Dict[str, str], Dict[str, str]]:
    """Load translation overrides from a JSON file if provided.

    The JSON file should contain:
        {
            "make": {"Ford": "포드", ...},
            "model": {"Mustang": "머스탱", ...}
        }
    """
    make_translations = dict(DEFAULT_MAKE_TRANSLATIONS)
    model_translations = dict(DEFAULT_MODEL_TRANSLATIONS)

    if not path:
        return make_translations, model_translations

    if not path.exists():
        raise FileNotFoundError(f"Translation file not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        overrides = json.load(fh)

    make_translations.update(overrides.get("make", {}))
    model_translations.update(overrides.get("model", {}))
    return make_translations, model_translations


def iter_image_files(root: Path) -> Iterable[Path]:
    """Yield image files recursively from the dataset directory."""
    if not root.exists():
        raise FileNotFoundError(f"Dataset directory does not exist: {root}")

    for suffix in (".jpg", ".jpeg", ".png"):
        yield from root.rglob(f"*{suffix}")


def parse_metadata_from_filename(path: Path) -> tuple[str, str, str]:
    """Extract make, model, year from the dataset filename."""
    name = path.stem
    # Filenames are under-scored, make sure we have enough tokens.
    parts = name.split("_")
    if len(parts) < 3:
        raise ValueError(f"Unexpected filename format: {path.name}")

    make = parts[0]
    model = parts[1]
    year_token = parts[2]

    # Attempt to extract a 4-digit year.
    year = ""
    for token in (year_token, year_token[:4]):
        if len(token) >= 4 and token[:4].isdigit():
            year = token[:4]
            break

    if not year:
        raise ValueError(f"Could not parse year from: {path.name}")

    return make, model, year


def build_row(
    path: Path,
    dataset_root: Path,
    make_trans: Dict[str, str],
    model_trans: Dict[str, str],
) -> LabelRow:
    relative_path = path.relative_to(dataset_root).as_posix()
    make_en, model_en, year = parse_metadata_from_filename(path)

    make_ko = make_trans.get(make_en, make_en)
    model_ko = model_trans.get(model_en, model_en)

    return LabelRow(
        image_path=relative_path,
        make_ko=make_ko,
        make_en=make_en,
        model_ko=model_ko,
        model_en=model_en,
        year=year,
        variant="",
        source_url=SOURCE_URL,
        notes="",
    )


def write_csv(rows: Iterable[LabelRow], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_csv_row())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate car_labels.csv from the car image dataset."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_DIR,
        help="Path to the car image dataset root (default: ../dataset)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_CSV,
        help="Path to the output CSV file (default: data/car_labels.csv)",
    )
    parser.add_argument(
        "--translations",
        type=Path,
        help="Optional JSON file with make/model translation overrides",
    )
    args = parser.parse_args()

    make_trans, model_trans = load_translations(args.translations)
    dataset_root = args.dataset.resolve()

    rows = []
    for idx, image_path in enumerate(iter_image_files(dataset_root), start=1):
        try:
            row = build_row(image_path, dataset_root, make_trans, model_trans)
            rows.append(row)
        except ValueError as exc:
            # Include the reason in the notes column to preserve the record.
            relative = image_path.relative_to(dataset_root).as_posix()
            rows.append(
                LabelRow(
                    image_path=relative,
                    make_ko="",
                    make_en="",
                    model_ko="",
                    model_en="",
                    year="",
                    variant="",
                    source_url=SOURCE_URL,
                    notes=f"parse_error: {exc}",
                )
            )

        if idx % 500 == 0:
            print(f"Processed {idx} images...", flush=True)

    write_csv(rows, args.output)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
