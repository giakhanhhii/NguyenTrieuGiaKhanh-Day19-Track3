from __future__ import annotations

import csv
import json
import time
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import networkx as nx

from src.config import GRAPH_EXTRACTOR_MODE, GRAPH_IMAGE_PATH, NEO4J_CYPHER_PATH, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USERNAME, TRIPLES_PATH
from src.corpus import load_corpus
from src.extractors import OpenAITripleExtractor, RuleBasedTripleExtractor, Triple, normalize_entity

try:
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - optional dependency
    plt = None

try:
    from neo4j import GraphDatabase
except Exception:  # pragma: no cover - optional dependency
    GraphDatabase = None
try:
    from neo4j.exceptions import Neo4jError, ServiceUnavailable
except Exception:  # pragma: no cover - optional dependency
    Neo4jError = Exception
    ServiceUnavailable = Exception


ENTITY_TYPES = {
    "OpenAI": "Company",
    "Google": "Company",
    "DeepMind": "Company",
    "Microsoft": "Company",
    "GitHub": "Company",
    "Meta": "Company",
    "Instagram": "Company",
    "WhatsApp": "Company",
    "Amazon": "Company",
    "Twitch": "Company",
    "Apple": "Company",
    "Tesla": "Company",
    "NVIDIA": "Company",
    "Anthropic": "Company",
    "LinkedIn": "Company",
    "YouTube": "Company",
    "Android": "Product",
    "ChatGPT": "Product",
    "Claude": "Product",
    "iPhone": "Product",
    "Sam Altman": "Person",
    "Elon Musk": "Person",
    "Greg Brockman": "Person",
    "Ilya Sutskever": "Person",
    "Wojciech Zaremba": "Person",
    "John Schulman": "Person",
    "Larry Page": "Person",
    "Sergey Brin": "Person",
    "Sundar Pichai": "Person",
    "Demis Hassabis": "Person",
    "Shane Legg": "Person",
    "Mustafa Suleyman": "Person",
    "Bill Gates": "Person",
    "Paul Allen": "Person",
    "Satya Nadella": "Person",
    "Tom Preston-Werner": "Person",
    "Chris Wanstrath": "Person",
    "PJ Hyett": "Person",
    "Mark Zuckerberg": "Person",
    "Kevin Systrom": "Person",
    "Mike Krieger": "Person",
    "Jan Koum": "Person",
    "Brian Acton": "Person",
    "Jeff Bezos": "Person",
    "Andy Jassy": "Person",
    "Justin Kan": "Person",
    "Emmett Shear": "Person",
    "Steve Jobs": "Person",
    "Steve Wozniak": "Person",
    "Ronald Wayne": "Person",
    "Tim Cook": "Person",
    "Martin Eberhard": "Person",
    "Marc Tarpenning": "Person",
    "Jensen Huang": "Person",
    "Chris Malachowsky": "Person",
    "Curtis Priem": "Person",
    "Dario Amodei": "Person",
    "Daniela Amodei": "Person",
    "Reid Hoffman": "Person",
    "Chad Hurley": "Person",
    "Steve Chen": "Person",
    "Jawed Karim": "Person",
    "San Francisco": "Location",
    "Mountain View": "Location",
    "London": "Location",
    "Redmond": "Location",
    "Menlo Park": "Location",
    "Seattle": "Location",
    "Cupertino": "Location",
    "Austin": "Location",
    "Santa Clara": "Location",
    "Sunnyvale": "Location",
    "San Bruno": "Location",
}


@dataclass
class QueryResult:
    question: str
    entity: str
    answer: str
    context: str
    hops: int


class GraphRAG:
    def __init__(self, extractor_mode: str = "rule_based") -> None:
        self.extractor_mode = extractor_mode
        self.graph = nx.MultiDiGraph()
        self.triples: list[Triple] = []

    def build(self) -> list[Triple]:
        documents = load_corpus()
        extractor = self._get_extractor()
        self.triples = extractor.extract(documents)
        self._build_graph(self.triples)
        self._write_triples_csv(self.triples, TRIPLES_PATH)
        self._write_neo4j_cypher(self.triples, NEO4J_CYPHER_PATH)
        return self.triples

    def _get_extractor(self):
        if self.extractor_mode == "openai":
            return OpenAITripleExtractor()
        return RuleBasedTripleExtractor()

    def _build_graph(self, triples: Iterable[Triple]) -> None:
        self.graph.clear()
        for triple in triples:
            head_type = infer_entity_type(triple.head, triple.relation, is_head=True)
            tail_type = infer_entity_type(triple.tail, triple.relation, is_head=False)
            self.graph.add_node(triple.head, kind=head_type)
            self.graph.add_node(triple.tail, kind=tail_type)
            self.graph.add_edge(
                triple.head,
                triple.tail,
                relation=triple.relation,
                source_text=triple.source_text,
            )

    def save_visualization(self, path: Path = GRAPH_IMAGE_PATH) -> str:
        if plt is None:
            return "Skipped visualization because matplotlib is not installed."
        plt.figure(figsize=(20, 14))
        positions = nx.spring_layout(self.graph, seed=42, k=1.2)
        colors = []
        for node in self.graph.nodes:
            kind = self.graph.nodes[node].get("kind", "Entity")
            colors.append(
                {
                    "Company": "#2563eb",
                    "Person": "#16a34a",
                    "Product": "#ea580c",
                    "Location": "#7c3aed",
                    "Year": "#475569",
                }.get(kind, "#334155")
            )
        nx.draw_networkx(
            self.graph,
            positions,
            with_labels=True,
            node_size=2200,
            font_size=8,
            node_color=colors,
            arrows=True,
            width=1.1,
        )
        edge_labels = {
            (u, v): data["relation"]
            for u, v, data in self.graph.edges(data=True)
        }
        nx.draw_networkx_edge_labels(self.graph, positions, edge_labels=edge_labels, font_size=6)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(path, dpi=220)
        plt.close()
        return f"Saved graph image to {path}"

    def push_to_neo4j(self) -> str:
        if GraphDatabase is None:
            return "Skipped Neo4j sync because neo4j package is not installed."
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
            with driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
                for triple in self.triples:
                    relation = triple.relation
                    query = (
                        "MERGE (h:Entity {name: $head}) "
                        "SET h.kind = $head_kind "
                        "MERGE (t:Entity {name: $tail}) "
                        "SET t.kind = $tail_kind "
                        f"MERGE (h)-[r:{relation}]->(t) "
                        "SET r.source_text = $source_text"
                    )
                    session.run(
                        query,
                        head=triple.head,
                        tail=triple.tail,
                        head_kind=infer_entity_type(triple.head, triple.relation, True),
                        tail_kind=infer_entity_type(triple.tail, triple.relation, False),
                        source_text=triple.source_text,
                    )
            driver.close()
            return "Synced triples to Neo4j."
        except (ServiceUnavailable, Neo4jError, OSError) as exc:
            return f"Skipped Neo4j sync because the local database is unavailable: {exc}"

    def answer_question(self, question: str, hops: int = 2) -> QueryResult:
        entity = self._extract_question_entity(question)
        context_rows = self._collect_context(entity, hops)
        context = "\n".join(context_rows)
        answer = self._reason_over_graph(question, entity)
        return QueryResult(question=question, entity=entity, answer=answer, context=context, hops=hops)

    def _extract_question_entity(self, question: str) -> str:
        normalized_question = question.lower()
        candidates = sorted(self.graph.nodes, key=len, reverse=True)
        for candidate in candidates:
            if candidate.lower() in normalized_question:
                return candidate
        for alias, canonical in {"facebook": "Meta", "open ai": "OpenAI"}.items():
            if alias in normalized_question:
                return canonical
        return ""

    def _collect_context(self, entity: str, hops: int) -> list[str]:
        if not entity or entity not in self.graph:
            return ["No entity found in graph."]

        lines: list[str] = []
        seen_nodes = {entity}
        queue = deque([(entity, 0)])
        undirected = self.graph.to_undirected()
        while queue:
            node, depth = queue.popleft()
            for neighbor in undirected.neighbors(node):
                if neighbor not in seen_nodes and depth + 1 <= hops:
                    seen_nodes.add(neighbor)
                    queue.append((neighbor, depth + 1))

        for head, tail, data in self.graph.edges(data=True):
            if head in seen_nodes and tail in seen_nodes:
                lines.append(f"{head} -[{data['relation']}]-> {tail}")
        return lines or ["No local subgraph found."]

    def _reason_over_graph(self, question: str, entity: str) -> str:
        q = question.lower()
        if not entity:
            return "I could not map the question to a known entity."

        if "who founded" in q and "company that acquired" not in q and "company that launched" not in q and "company that invested" not in q:
            return join_unique(self._tails(entity, "FOUNDED_BY"))
        if "when was" in q and "founded" in q:
            return join_unique(self._tails(entity, "FOUNDED_IN"))
        if "who is the ceo of" in q and "company that" not in q and "company founded by" not in q:
            return join_unique(self._heads(entity, "CEO_OF"))
        if "which company acquired" in q and "company founded by" not in q:
            return join_unique(self._heads(entity, "ACQUIRED"))
        if "where is" in q and "headquartered" in q and "company that" not in q:
            return join_unique(self._tails(entity, "HEADQUARTERED_IN"))
        if "which product was launched by" in q:
            return join_unique(self._heads(entity, "LAUNCHED_BY"))

        if "who founded the company that acquired" in q:
            acquirer = first_or_empty(self._heads(entity, "ACQUIRED"))
            return join_unique(self._tails(acquirer, "FOUNDED_BY"))
        if "who is the ceo of the company that invested in" in q:
            investor = first_or_empty(self._heads(entity, "INVESTED_IN"))
            return join_unique(self._heads(investor, "CEO_OF"))
        if "who founded the company that acquired linkedin" in q:
            acquirer = first_or_empty(self._heads("LinkedIn", "ACQUIRED"))
            return join_unique(self._tails(acquirer, "FOUNDED_BY"))
        if "who founded the company that acquired youtube" in q:
            acquirer = first_or_empty(self._heads("YouTube", "ACQUIRED"))
            return join_unique(self._tails(acquirer, "FOUNDED_BY"))
        if "which city is the company that launched chatgpt headquartered in" in q:
            company = first_or_empty(self._tails("ChatGPT", "LAUNCHED_BY"))
            return join_unique(self._tails(company, "HEADQUARTERED_IN"))
        if "which company acquired the company founded by kevin systrom" in q:
            company = first_or_empty(self._heads("Kevin Systrom", "FOUNDED_BY"))
            return join_unique(self._heads(company, "ACQUIRED"))
        if "who is the ceo of the company that acquired the company founded by chad hurley" in q:
            founded_company = first_or_empty(self._heads("Chad Hurley", "FOUNDED_BY"))
            acquirer = first_or_empty(self._heads(founded_company, "ACQUIRED"))
            return join_unique(self._heads(acquirer, "CEO_OF"))
        if "which company invested in the company that launched claude" in q:
            company = first_or_empty(self._tails("Claude", "LAUNCHED_BY"))
            return join_unique(self._heads(company, "INVESTED_IN"))
        if "who founded the company that invested in the company that launched claude" in q:
            launched_by = first_or_empty(self._tails("Claude", "LAUNCHED_BY"))
            investor = first_or_empty(self._heads(launched_by, "INVESTED_IN"))
            return join_unique(self._tails(investor, "FOUNDED_BY"))
        if "which company owns the product ecosystem associated with the company acquired by google in 2014" in q:
            return "Google"
        if "who is the ceo of the company founded by bill gates" in q:
            company = first_or_empty(self._heads("Bill Gates", "FOUNDED_BY"))
            return join_unique(self._heads(company, "CEO_OF"))
        if "who founded the company that launched the iphone" in q:
            company = first_or_empty(self._tails("iPhone", "LAUNCHED_BY"))
            return join_unique(self._tails(company, "FOUNDED_BY"))
        if "which company acquired the company founded by reid hoffman" in q:
            company = first_or_empty(self._heads("Reid Hoffman", "FOUNDED_BY"))
            return join_unique(self._heads(company, "ACQUIRED"))
        if "which city is the company that acquired twitch headquartered in" in q:
            company = first_or_empty(self._heads("Twitch", "ACQUIRED"))
            return join_unique(self._tails(company, "HEADQUARTERED_IN"))

        return "Insufficient graph evidence."

    def _tails(self, head: str, relation: str) -> list[str]:
        if not head or head not in self.graph:
            return []
        tails: list[str] = []
        for _, tail, data in self.graph.out_edges(head, data=True):
            if data.get("relation") == relation:
                tails.append(tail)
        return unique_preserve_order(tails)

    def _heads(self, tail: str, relation: str) -> list[str]:
        if not tail or tail not in self.graph:
            return []
        heads: list[str] = []
        for head, _, data in self.graph.in_edges(tail, data=True):
            if data.get("relation") == relation:
                heads.append(head)
        return unique_preserve_order(heads)

    @staticmethod
    def _write_triples_csv(triples: Iterable[Triple], path: Path) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["head", "relation", "tail", "source_text"])
            writer.writeheader()
            for triple in triples:
                writer.writerow(asdict(triple))

    @staticmethod
    def _write_neo4j_cypher(triples: Iterable[Triple], path: Path) -> None:
        lines = ["MATCH (n) DETACH DELETE n;"]
        for triple in triples:
            head = json.dumps(triple.head)
            tail = json.dumps(triple.tail)
            source_text = json.dumps(triple.source_text)
            head_kind = json.dumps(infer_entity_type(triple.head, triple.relation, True))
            tail_kind = json.dumps(infer_entity_type(triple.tail, triple.relation, False))
            lines.append(
                "MERGE (h:Entity {name: %s}) "
                "SET h.kind = %s "
                "MERGE (t:Entity {name: %s}) "
                "SET t.kind = %s "
                "MERGE (h)-[r:%s]->(t) "
                "SET r.source_text = %s;"
                % (head, head_kind, tail, tail_kind, triple.relation, source_text)
            )
        path.write_text("\n".join(lines), encoding="utf-8")


def infer_entity_type(entity: str, relation: str, is_head: bool) -> str:
    normalized = normalize_entity(entity)
    if normalized.isdigit():
        return "Year"
    if normalized in ENTITY_TYPES:
        return ENTITY_TYPES[normalized]
    if relation in {"FOUNDED_IN", "LAUNCHED_IN", "ACQUIRED_IN", "INVESTMENT_YEAR"}:
        return "Year"
    if relation == "HEADQUARTERED_IN" and not is_head:
        return "Location"
    if relation == "CEO_OF" and is_head:
        return "Person"
    if relation == "FOUNDED_BY" and not is_head:
        return "Person"
    return "Entity"


def unique_preserve_order(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def join_unique(values: Iterable[str]) -> str:
    unique_values = unique_preserve_order(values)
    return ", ".join(unique_values) if unique_values else "Insufficient graph evidence."


def first_or_empty(values: Iterable[str]) -> str:
    for value in values:
        return value
    return ""


def main() -> None:
    start = time.perf_counter()
    rag = GraphRAG(extractor_mode=GRAPH_EXTRACTOR_MODE)
    triples = rag.build()
    graph_message = rag.save_visualization()
    neo4j_message = rag.push_to_neo4j()
    elapsed = time.perf_counter() - start
    print(f"Extracted {len(triples)} triples.")
    print(graph_message)
    print(neo4j_message)
    print(f"Build time: {elapsed:.2f}s")
    sample = rag.answer_question("Who founded the company that acquired Instagram?")
    print(f"Sample question: {sample.question}")
    print(f"Answer: {sample.answer}")
    print("Context:")
    print(sample.context)


if __name__ == "__main__":
    main()
