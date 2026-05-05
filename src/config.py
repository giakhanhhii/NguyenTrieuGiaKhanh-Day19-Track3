from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "outputs"
ARTIFACT_DIR = ROOT_DIR / "screenshots"


def load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv(ROOT_DIR / ".env")

CORPUS_PATH = DATA_DIR / "tech_company_corpus.json"
BENCHMARK_PATH = DATA_DIR / "benchmark_questions.json"
TRIPLES_PATH = OUTPUT_DIR / "triples.csv"
EVALUATION_PATH = OUTPUT_DIR / "evaluation_results.csv"
SUMMARY_PATH = OUTPUT_DIR / "evaluation_summary.md"
GRAPH_IMAGE_PATH = ARTIFACT_DIR / "knowledge_graph.png"
NEO4J_CYPHER_PATH = OUTPUT_DIR / "neo4j_import.cypher"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GRAPH_EXTRACTOR_MODE = os.getenv("GRAPH_EXTRACTOR_MODE", "rule_based")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

for folder in (OUTPUT_DIR, ARTIFACT_DIR):
    folder.mkdir(parents=True, exist_ok=True)
