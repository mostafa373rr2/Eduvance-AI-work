"""
Eduvance AI - Domain Concept Extraction & Graph Linking Service
WBS 3.2 - Step 4: Concept Extractor

Extracts pedagogical concepts from source chunks, estimates difficulty levels,
establishes prerequisite dependencies, and maps each concept to its supporting
source chunk UUIDs for source traceability.

Owner: Member 2 (Content and RAG Engineer)
"""

import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple
from uuid import UUID

from .schemas import DifficultyLevel, ExtractedChunk, ExtractedConcept

# Keywords indicating difficulty grading
BEGINNER_KEYWORDS = {"overview", "introduction", "basics", "fundamentals", "core", "concept", "definition", "function"}
ADVANCED_KEYWORDS = {"governance", "audit", "adaptive", "optimization", "metrics", "continuous", "tier 4", "assurance"}

# Stopwords to filter out non-concept noun phrases
COMMON_STOPWORDS = {
    "the", "a", "an", "this", "that", "these", "those", "such", "all", "each", "every",
    "some", "any", "other", "many", "more", "most", "several", "figure", "table", "section",
    "chapter", "page", "note", "example", "document", "framework", "organization", "system",
}


class ConceptExtractor:
    """Extracts, categorizes, and links domain concepts from document chunks."""

    def __init__(self, min_concepts: int = 2, max_concepts: int = 15):
        self.min_concepts = min_concepts
        self.max_concepts = max_concepts

    def extract_concepts(self, chunks: List[ExtractedChunk]) -> List[ExtractedConcept]:
        """
        Analyzes chunks to discover domain concepts, infer difficulty,
        construct prerequisite relationships, and map source chunk IDs.
        """
        if not chunks:
            return []

        # 1. Discover raw candidate concepts from headings and definitional sentences
        candidates: Dict[str, Dict] = defaultdict(lambda: {
            "descriptions": [],
            "source_chunk_ids": set(),
            "first_chunk_index": float("inf"),
            "occurrences": 0,
        })

        for chunk in chunks:
            self._scan_chunk_for_concepts(chunk, candidates)

        # Fallback if no explicit definition patterns were matched
        if len(candidates) < self.min_concepts:
            self._fallback_extract_keyphrases(chunks, candidates)

        # 2. Structure and rank discovered concepts
        sorted_candidates = sorted(
            candidates.items(),
            key=lambda item: (item[1]["first_chunk_index"], -item[1]["occurrences"]),
        )[:self.max_concepts]

        # 3. Build concepts with difficulty and prerequisites
        total_chunks = max(1, len(chunks))
        concepts_list: List[ExtractedConcept] = []
        registered_names: List[str] = []

        for name, data in sorted_candidates:
            # Clean and combine descriptions
            description = self._synthesize_description(name, data["descriptions"])
            if len(description) < 10:
                description = f"Core domain concept concerning {name} and related operational practices."

            # Estimate difficulty based on relative position and keywords
            rel_pos = data["first_chunk_index"] / total_chunks
            difficulty = self._estimate_difficulty(name, description, rel_pos)

            # Determine prerequisites: earlier concepts that have lower difficulty
            prerequisites: List[str] = []
            for prev_name in registered_names:
                # Add up to 2 earlier concepts as prerequisites
                if len(prerequisites) < 2 and prev_name != name:
                    prerequisites.append(prev_name)

            concept = ExtractedConcept(
                name=name,
                description=description,
                difficulty=difficulty,
                prerequisite_names=prerequisites,
                source_chunk_ids=list(data["source_chunk_ids"]),
            )
            concepts_list.append(concept)
            registered_names.append(name)

        return concepts_list

    def _scan_chunk_for_concepts(self, chunk: ExtractedChunk, candidates: Dict[str, Dict]):
        """Scans a single chunk for headings, definition patterns, and capitalized terms."""
        text = chunk.text_content

        # A. Section Header inspection
        if chunk.section_header:
            clean_hdr = self._clean_concept_name(chunk.section_header)
            if self._is_valid_concept_name(clean_hdr):
                candidates[clean_hdr]["source_chunk_ids"].add(chunk.chunk_id)
                candidates[clean_hdr]["first_chunk_index"] = min(
                    candidates[clean_hdr]["first_chunk_index"], chunk.chunk_index
                )
                candidates[clean_hdr]["occurrences"] += 1
                # Grab the first sentence of the chunk as an initial description
                first_sent = text.split(".")[0].strip()
                if len(first_sent) > 15:
                    candidates[clean_hdr]["descriptions"].append(first_sent + ".")

        # B. Definitional sentence patterns (e.g. 'X is defined as Y', 'X refers to Y')
        def_pattern = (
            r"(?:(?:The\s+term|A|An)?\s*([A-Z][a-zA-Z0-9\s\-]{2,35}))\s+"
            r"(is defined as|refers to|consists of|is the process of|involves)\s+([^.\n]+)"
        )
        for match in re.finditer(def_pattern, text):
            raw_term = match.group(1).strip()
            connector = match.group(2).strip()
            rest = match.group(3).strip()
            clean_term = self._clean_concept_name(raw_term)

            if self._is_valid_concept_name(clean_term):
                desc = f"{clean_term} {connector} {rest}."
                candidates[clean_term]["source_chunk_ids"].add(chunk.chunk_id)
                candidates[clean_term]["descriptions"].append(desc)
                candidates[clean_term]["first_chunk_index"] = min(
                    candidates[clean_term]["first_chunk_index"], chunk.chunk_index
                )
                candidates[clean_term]["occurrences"] += 2

        # C. Core Functional enumeration patterns (e.g., 'Identify, Protect, Detect, Respond, Recover')
        function_pattern = r"\b(Identify|Protect|Detect|Respond|Recover|Risk Management|Asset Management|Access Control)\b"
        for match in re.finditer(function_pattern, text):
            term = match.group(1).strip()
            candidates[term]["source_chunk_ids"].add(chunk.chunk_id)
            candidates[term]["first_chunk_index"] = min(
                candidates[term]["first_chunk_index"], chunk.chunk_index
            )
            candidates[term]["occurrences"] += 1

    def _fallback_extract_keyphrases(self, chunks: List[ExtractedChunk], candidates: Dict[str, Dict]):
        """Extracts prominent capitalized noun phrases if formal definitions are scarce."""
        phrase_pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b"
        for chunk in chunks:
            for match in re.finditer(phrase_pattern, chunk.text_content):
                phrase = match.group(1).strip()
                clean = self._clean_concept_name(phrase)
                if self._is_valid_concept_name(clean):
                    candidates[clean]["source_chunk_ids"].add(chunk.chunk_id)
                    candidates[clean]["first_chunk_index"] = min(
                        candidates[clean]["first_chunk_index"], chunk.chunk_index
                    )
                    candidates[clean]["occurrences"] += 1
                    # Extract surrounding sentence
                    sent = self._extract_surrounding_sentence(chunk.text_content, match.start())
                    if sent:
                        candidates[clean]["descriptions"].append(sent)

    @staticmethod
    def _clean_concept_name(name: str) -> str:
        """Strips leading numbers, bullets, or labels like 'Section 1.1'."""
        cleaned = re.sub(r"^(?:Section|Chapter|Part)?\s*[0-9]+(?:\.[0-9]+)*[:.\s-]*", "", name, flags=re.IGNORECASE)
        cleaned = re.sub(r"^(?:Function|Category|Tier)[:\s-]*", "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    @staticmethod
    def _is_valid_concept_name(name: str) -> bool:
        """Filters out stopwords, very short strings, or purely numerical strings."""
        if not name or len(name) < 3 or len(name) > 50:
            return False
        words = name.lower().split()
        if len(words) == 1 and words[0] in COMMON_STOPWORDS:
            return False
        if all(w in COMMON_STOPWORDS for w in words):
            return False
        if name.isdigit():
            return False
        return True

    @staticmethod
    def _synthesize_description(name: str, descriptions: List[str]) -> str:
        """Combines and cleans collected descriptions into a concise definition."""
        if not descriptions:
            return f"Foundational cybersecurity and risk management concept: {name}."
        # Pick the most descriptive single sentence
        best = max(descriptions, key=len).strip()
        if not best.endswith("."):
            best += "."
        return best

    @staticmethod
    def _estimate_difficulty(name: str, description: str, relative_pos: float) -> DifficultyLevel:
        """Determines pedagogical difficulty level based on vocabulary and curriculum placement."""
        combined_text = f"{name} {description}".lower()

        if any(kw in combined_text for kw in ADVANCED_KEYWORDS) or relative_pos > 0.75:
            return DifficultyLevel.ADVANCED
        if any(kw in combined_text for kw in BEGINNER_KEYWORDS) or relative_pos < 0.35:
            return DifficultyLevel.BEGINNER
        return DifficultyLevel.INTERMEDIATE

    @staticmethod
    def _extract_surrounding_sentence(text: str, match_pos: int) -> str:
        """Extracts the sentence containing the matched term."""
        start = text.rfind(".", 0, match_pos)
        start = 0 if start == -1 else start + 1
        end = text.find(".", match_pos)
        end = len(text) if end == -1 else end + 1
        sent = text[start:end].strip()
        return sent if len(sent) > 20 else ""
