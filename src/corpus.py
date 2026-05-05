from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from src.config import BENCHMARK_PATH, CORPUS_PATH


def load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_corpus() -> list[dict]:
    return load_json(CORPUS_PATH)


def load_benchmarks() -> list[dict]:
    return load_json(BENCHMARK_PATH)


def sentence_split(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def iter_sentences(documents: Iterable[dict]) -> list[dict]:
    rows: list[dict] = []
    for document in documents:
        for index, sentence in enumerate(sentence_split(document["text"]), start=1):
            rows.append(
                {
                    "doc_id": document["id"],
                    "title": document["title"],
                    "chunk_id": f"{document['id']}_sent_{index}",
                    "text": sentence,
                }
            )
    return rows
