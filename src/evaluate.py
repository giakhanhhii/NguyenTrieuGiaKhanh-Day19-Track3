from __future__ import annotations

import csv
import time
from dataclasses import asdict, dataclass

from src.config import EVALUATION_PATH, GRAPH_EXTRACTOR_MODE, SUMMARY_PATH
from src.corpus import load_benchmarks
from src.flat_rag import FlatRAG
from src.graph_rag import GraphRAG


@dataclass
class EvaluationRow:
    question_id: int
    category: str
    question: str
    ground_truth: str
    flat_rag_answer: str
    graph_rag_answer: str
    flat_correct: bool
    graph_correct: bool
    flat_failure_note: str


def evaluate() -> list[EvaluationRow]:
    benchmarks = load_benchmarks()

    graph_rag = GraphRAG(extractor_mode=GRAPH_EXTRACTOR_MODE)
    build_start = time.perf_counter()
    graph_rag.build()
    graph_build_time = time.perf_counter() - build_start
    graph_rag.save_visualization()

    flat_rag = FlatRAG()
    flat_start = time.perf_counter()
    flat_rag.build()
    flat_build_time = time.perf_counter() - flat_start

    rows: list[EvaluationRow] = []
    for item in benchmarks:
        question = item["question"]
        ground_truth = normalize_for_compare(item["ground_truth"])
        flat_answer, _ = flat_rag.answer_question(question)
        graph_result = graph_rag.answer_question(question)

        flat_correct = normalize_for_compare(flat_answer) == ground_truth
        graph_correct = normalize_for_compare(graph_result.answer) == ground_truth
        rows.append(
            EvaluationRow(
                question_id=item["id"],
                category=item["category"],
                question=question,
                ground_truth=item["ground_truth"],
                flat_rag_answer=flat_answer,
                graph_rag_answer=graph_result.answer,
                flat_correct=flat_correct,
                graph_correct=graph_correct,
                flat_failure_note=explain_flat_failure(item["category"], flat_correct, flat_answer),
            )
        )

    write_csv(rows)
    write_summary(rows, graph_build_time, flat_build_time)
    return rows


def normalize_for_compare(text: str) -> str:
    return (
        text.lower()
        .replace(" and ", ", ")
        .replace(", and ", ", ")
        .replace(".", "")
        .strip()
    )


def explain_flat_failure(category: str, flat_correct: bool, flat_answer: str) -> str:
    if flat_correct:
        return ""
    if "Insufficient" in flat_answer:
        return f"Flat RAG khong lay duoc bang chung truc tiep cho cau {category}."
    return "Flat RAG lay duoc van ban lien quan nhung khong noi dung quan he dung."


def write_csv(rows: list[EvaluationRow]) -> None:
    with EVALUATION_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_summary(rows: list[EvaluationRow], graph_build_time: float, flat_build_time: float) -> None:
    flat_correct = sum(row.flat_correct for row in rows)
    graph_correct = sum(row.graph_correct for row in rows)

    graph_token_estimate = 0
    flat_token_estimate = 0
    for row in rows:
        graph_token_estimate += estimate_tokens(row.graph_rag_answer) + estimate_tokens(row.question)
        flat_token_estimate += estimate_tokens(row.flat_rag_answer) + estimate_tokens(row.question)

    summary = f"""# Evaluation Summary

## Accuracy

- Flat RAG: {flat_correct}/20
- GraphRAG: {graph_correct}/20

## Build time

- Flat RAG build time: {flat_build_time:.2f}s
- GraphRAG build time: {graph_build_time:.2f}s

## Token usage estimate

- Flat RAG answer tokens (rough): {flat_token_estimate}
- GraphRAG answer tokens (rough): {graph_token_estimate}

## Cost analysis

- Flat RAG re index nhanh hon nhung de nham khi cau hoi can noi quan he qua nhieu chunk.
- GraphRAG ton cong hon o buoc indexing va graph construction.
- Doi lai, GraphRAG dat loi the ro o cau hoi two-hop va multi-hop.

## Cases where GraphRAG beats Flat RAG

"""
    for row in rows:
        if row.graph_correct and not row.flat_correct:
            summary += (
                f"- Q{row.question_id}: {row.question}\n"
                f"  Flat RAG: {row.flat_rag_answer}\n"
                f"  GraphRAG: {row.graph_rag_answer}\n"
            )
    SUMMARY_PATH.write_text(summary, encoding="utf-8")


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text.split()) * 1.3))


def main() -> None:
    rows = evaluate()
    print(f"Saved evaluation for {len(rows)} questions to {EVALUATION_PATH}")
    print(f"Saved summary to {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
