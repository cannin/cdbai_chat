"""Prompt normalization utilities built on top of FlashText."""
from __future__ import annotations

import csv
from importlib import resources
from pathlib import Path
from typing import Dict

try:
    from flashtext import KeywordProcessor
except ImportError:  # pragma: no cover - fallback when FlashText is unavailable

    class KeywordProcessor:  # type: ignore[override]
        """Minimal case-insensitive keyword replacer used when FlashText is absent."""

        def __init__(self, case_sensitive: bool = False) -> None:
            self.case_sensitive = case_sensitive
            self._mapping: Dict[str, str] = {}

        def add_keyword(self, keyword: str, replacement: str) -> None:
            key = keyword if self.case_sensitive else keyword.lower()
            self._mapping[key] = replacement

        def replace_keywords(self, text: str) -> str:
            working = text if self.case_sensitive else text.lower()
            result = working
            for key, replacement in self._mapping.items():
                result = result.replace(key, replacement)
            if self.case_sensitive:
                return result
            # For case-insensitive mode, we already lowercased the input so this is fine.
            return result


def _load_map_from_path(csv_path: Path) -> Dict[str, str]:
    """Load synonym → standard-id mappings from an explicit path."""
    id_map: Dict[str, str] = {}
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if not row or len(row) < 2:
                continue
            synonym, standard_id = row[0].strip(), row[1].strip()
            if synonym:
                id_map[synonym.lower()] = standard_id
    return id_map


def load_id_map(csv_path: Path | str | None = None) -> Dict[str, str]:
    """Load synonym → standard-id mappings from the packaged CSV.

    Args:
        csv_path: Optional override pointing to a custom mapping file. When omitted,
            the bundled ``cdbai/data/id_mapping.csv`` file is used.

    Returns:
        Dictionary keyed by lowercase synonym mapping to the canonical identifier.
    """
    if csv_path is not None:
        return _load_map_from_path(Path(csv_path))

    resource = resources.files("cdbai.data") / "id_mapping.csv"
    with resources.as_file(resource) as resolved:
        return _load_map_from_path(resolved)


def build_processor(id_map: Dict[str, str]) -> KeywordProcessor:
    """Return a case-insensitive KeywordProcessor populated with the mapping."""
    processor = KeywordProcessor(case_sensitive=False)
    for synonym_lc, standard_id in id_map.items():
        processor.add_keyword(synonym_lc, standard_id)
    return processor


def normalize_for_matching(text: str) -> str:
    """Lowercase helper ensuring consistent matching semantics."""
    return text.lower()


def normalize_prompt(prompt: str, csv_path: Path | str | None = None) -> str:
    """Normalize a prompt by rewriting synonyms to canonical identifiers.

    Args:
        prompt: Original user prompt.
        csv_path: Optional mapping file containing ``synonym,standard_id`` rows.

    Returns:
        Normalized prompt string after applying keyword replacements.
    """
    id_map = load_id_map(csv_path)
    processor = build_processor(id_map)
    prompt_lc = normalize_for_matching(prompt)
    return processor.replace_keywords(prompt_lc)


__all__ = [
    "normalize_prompt",
    "load_id_map",
    "build_processor",
    "normalize_for_matching",
]
