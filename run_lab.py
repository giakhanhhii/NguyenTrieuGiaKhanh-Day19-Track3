from __future__ import annotations

from src.evaluate import evaluate


def main() -> None:
    rows = evaluate()
    flat_correct = sum(row.flat_correct for row in rows)
    graph_correct = sum(row.graph_correct for row in rows)
    print("LAB pipeline finished.")
    print(f"Flat RAG accuracy: {flat_correct}/{len(rows)}")
    print(f"GraphRAG accuracy: {graph_correct}/{len(rows)}")


if __name__ == "__main__":
    main()
