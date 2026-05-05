from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Iterable

from src.config import OPENAI_API_KEY, OPENAI_MODEL
from src.corpus import sentence_split

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency during local verification
    OpenAI = None


@dataclass(frozen=True)
class Triple:
    head: str
    relation: str
    tail: str
    source_text: str


ENTITY_ALIASES = {
    "facebook": "Meta",
    "meta platforms": "Meta",
    "open ai": "OpenAI",
    "openai": "OpenAI",
    "github": "GitHub",
    "linkedin": "LinkedIn",
    "youtube": "YouTube",
    "whatsapp": "WhatsApp",
    "iphone": "iPhone",
    "nvidia": "NVIDIA",
    "chatgpt": "ChatGPT",
    "claude": "Claude",
}

RELATION_ALIASES = {
    "IS_CEO_OF": "CEO_OF",
    "INVESTED_IN_YEAR": "INVESTMENT_YEAR",
}


def normalize_entity(entity: str) -> str:
    clean = entity.strip().strip(".").replace("_", " ")
    clean = re.sub(r"\s+", " ", clean)
    if clean.isupper() and any(char.isalpha() for char in clean):
        clean = clean.title()
    mapped = ENTITY_ALIASES.get(clean.lower())
    return mapped if mapped else clean


def normalize_relation(relation: str) -> str:
    clean = relation.strip().upper()
    return RELATION_ALIASES.get(clean, clean)


def split_people(text: str) -> list[str]:
    text = text.replace(", and ", ", ").replace(" and ", ", ")
    return [normalize_entity(item) for item in text.split(",") if item.strip()]


class RuleBasedTripleExtractor:
    def extract(self, documents: Iterable[dict]) -> list[Triple]:
        triples: list[Triple] = []
        for document in documents:
            for sentence in sentence_split(document["text"]):
                triples.extend(self._extract_from_sentence(sentence))
        return deduplicate_triples(triples)

    def _extract_from_sentence(self, sentence: str) -> list[Triple]:
        triples: list[Triple] = []

        founded_match = re.search(
            r"(?P<company>.+?) was founded by (?P<founders>.+?) in (?P<year>\d{4})\.",
            sentence,
        )
        if founded_match:
            company = normalize_entity(founded_match.group("company"))
            for founder in split_people(founded_match.group("founders")):
                triples.append(Triple(company, "FOUNDED_BY", founder, sentence))
            triples.append(Triple(company, "FOUNDED_IN", founded_match.group("year"), sentence))
            return triples

        ceo_match = re.search(r"(?P<person>.+?) is the CEO of (?P<company>.+?)\.", sentence)
        if ceo_match:
            triples.append(
                Triple(
                    normalize_entity(ceo_match.group("person")),
                    "CEO_OF",
                    normalize_entity(ceo_match.group("company")),
                    sentence,
                )
            )
            return triples

        acquired_match = re.search(
            r"(?P<company>.+?) acquired (?P<target>.+?) in (?P<year>\d{4})\.",
            sentence,
        )
        if acquired_match:
            company = normalize_entity(acquired_match.group("company"))
            target = normalize_entity(acquired_match.group("target"))
            triples.append(Triple(company, "ACQUIRED", target, sentence))
            triples.append(Triple(target, "ACQUIRED_IN", acquired_match.group("year"), sentence))
            return triples

        invested_match = re.search(
            r"(?P<company>.+?) invested in (?P<target>.+?) in (?P<year>\d{4})\.",
            sentence,
        )
        if invested_match:
            company = normalize_entity(invested_match.group("company"))
            target = normalize_entity(invested_match.group("target"))
            triples.append(Triple(company, "INVESTED_IN", target, sentence))
            triples.append(Triple(target, "INVESTMENT_YEAR", invested_match.group("year"), sentence))
            return triples

        launched_match = re.search(
            r"(?P<product>.+?) was launched by (?P<company>.+?) in (?P<year>\d{4})\.",
            sentence,
        )
        if launched_match:
            product = normalize_entity(launched_match.group("product"))
            company = normalize_entity(launched_match.group("company"))
            triples.append(Triple(product, "LAUNCHED_BY", company, sentence))
            triples.append(Triple(product, "LAUNCHED_IN", launched_match.group("year"), sentence))
            return triples

        hq_match = re.search(r"(?P<company>.+?) is headquartered in (?P<location>.+?)\.", sentence)
        if hq_match:
            triples.append(
                Triple(
                    normalize_entity(hq_match.group("company")),
                    "HEADQUARTERED_IN",
                    normalize_entity(hq_match.group("location")),
                    sentence,
                )
            )
            return triples

        owns_match = re.search(r"(?P<company>.+?) owns (?P<target>.+?)\.", sentence)
        if owns_match:
            triples.append(
                Triple(
                    normalize_entity(owns_match.group("company")),
                    "OWNS",
                    normalize_entity(owns_match.group("target")),
                    sentence,
                )
            )
            return triples

        return triples


class OpenAITripleExtractor:
    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set.")
        if OpenAI is None:
            raise ImportError("openai package is not available.")
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def extract(self, documents: Iterable[dict]) -> list[Triple]:
        triples: list[Triple] = []
        for document in documents:
            for sentence in sentence_split(document["text"]):
                triples.extend(self._extract_from_sentence(sentence))
        return deduplicate_triples(triples)

    def _extract_from_sentence(self, sentence: str) -> list[Triple]:
        prompt = (
            "Extract knowledge triples from the sentence. "
            "Return valid JSON with key 'triples'. "
            "Each triple must have head, relation, tail. "
            "Use uppercase snake_case for relations.\n"
            f"Sentence: {sentence}"
        )
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You extract clean knowledge graph triples from tech company text.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content or '{"triples": []}'
        payload = json.loads(_extract_json_block(content))
        triples = [
            Triple(
                normalize_entity(item["head"]),
                normalize_relation(item["relation"]),
                normalize_entity(str(item["tail"])),
                sentence,
            )
            for item in payload.get("triples", [])
        ]
        return triples


def _extract_json_block(content: str) -> str:
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        return '{"triples": []}'
    return match.group(0)


def deduplicate_triples(triples: Iterable[Triple]) -> list[Triple]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[Triple] = []
    for triple in triples:
        key = (normalize_entity(triple.head), triple.relation, normalize_entity(triple.tail))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(
            Triple(
                normalize_entity(triple.head),
                triple.relation,
                normalize_entity(triple.tail),
                triple.source_text,
            )
        )
    return deduped
