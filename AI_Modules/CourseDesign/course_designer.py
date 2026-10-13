"""
Eduvance AI - Course Designer Agent Engine
WBS 3.3 - Course Curriculum & Syllabus Synthesis

Synthesizes structured modules, lessons, measurable Bloom's taxonomy learning
objectives, and citation references from extracted domain concepts and chunks.

Strictly fulfills WBS 2.1 Contract 2 (CourseDesignOutput).

Owner: Member 2 (Content and RAG Engineer)
"""

import json
import math
import re
from typing import Any, Dict, List, Optional, Sequence, Set
from uuid import UUID

from AI_Modules.Extraction.schemas import ContentExtractionOutput, DifficultyLevel, ExtractedChunk, ExtractedConcept
from .schemas import CourseDesignOutput, LessonDesign, ModuleDesign


# Bloom's Taxonomy cognitive action verbs categorized by pedagogical stage
BLOOM_VERBS = {
    DifficultyLevel.BEGINNER: [
        "Identify",
        "Define",
        "Explain",
        "Describe",
        "Recognize",
        "Summarize",
        "Differentiate",
        "Clarify",
    ],
    DifficultyLevel.INTERMEDIATE: [
        "Apply",
        "Implement",
        "Analyze",
        "Execute",
        "Construct",
        "Examine",
        "Integrate",
        "Demonstrate",
    ],
    DifficultyLevel.ADVANCED: [
        "Evaluate",
        "Optimize",
        "Formulate",
        "Design",
        "Assess",
        "Synthesize",
        "Standardize",
        "Govern",
    ],
}


class CourseDesigner:
    """
    Core curriculum generation engine that translates extracted concepts and
    text chunks into pedagogically sequenced modules and lessons.
    """

    def __init__(
        self,
        min_modules: int = 2,
        max_modules: int = 4,
        min_lessons_per_module: int = 1,
        max_lessons_per_module: int = 3,
    ):
        self.min_modules = max(2, min_modules)
        self.max_modules = min(4, max_modules)
        self.min_lessons = max(1, min_lessons_per_module)
        self.max_lessons = min(3, max_lessons_per_module)

    def generate_curriculum(
        self,
        extraction_output: ContentExtractionOutput,
        course_title_override: Optional[str] = None,
        course_description_override: Optional[str] = None,
    ) -> CourseDesignOutput:
        """
        Generates a validated CourseDesignOutput conforming strictly to Contract 2
        using extracted concepts, their prerequisite topology, and supporting chunks.
        """
        concepts = extraction_output.concepts
        chunks = extraction_output.chunks

        if not concepts:
            raise ValueError("Cannot generate curriculum: No extracted concepts provided.")

        if not chunks:
            raise ValueError("Cannot generate curriculum: No extracted chunks provided.")

        # 1. Order concepts pedagogically (Prerequisite topology & Difficulty levels)
        ordered_concepts = self._order_concepts_pedagogically(concepts)

        # 2. Determine module count (strictly bounded between min_modules and max_modules)
        num_modules = self._calculate_module_count(len(ordered_concepts))

        # 3. Partition concepts into module cohorts
        module_concept_groups = self._partition_concepts(ordered_concepts, num_modules)

        # 4. Generate structured modules and lessons
        modules: List[ModuleDesign] = []
        for mod_idx, mod_concepts in enumerate(module_concept_groups, start=1):
            module_design = self._build_module(
                module_sequence=mod_idx,
                total_modules=num_modules,
                concepts=mod_concepts,
                all_chunks=chunks,
            )
            modules.append(module_design)

        # 5. Synthesize course title and description
        course_title = course_title_override or self._synthesize_course_title(ordered_concepts, chunks)
        if len(course_title) < 5:
            course_title = f"{course_title} Fundamentals & Applications"

        course_description = course_description_override or self._synthesize_course_description(
            course_title=course_title,
            modules=modules,
            concepts=ordered_concepts,
        )
        if len(course_description) < 20:
            course_description = (
                f"Comprehensive training course exploring core methodologies, operational "
                f"frameworks, and applied implementation practices for {course_title}."
            )

        # 6. Validate and return root Contract 2 schema
        return CourseDesignOutput(
            course_title=course_title,
            description=course_description,
            modules=modules,
        )

    def _order_concepts_pedagogically(self, concepts: List[ExtractedConcept]) -> List[ExtractedConcept]:
        """
        Sorts concepts such that prerequisites and beginner foundations come first,
        followed by intermediate applications, and advanced governance/optimization.
        """
        difficulty_weight = {
            DifficultyLevel.BEGINNER: 1,
            DifficultyLevel.INTERMEDIATE: 2,
            DifficultyLevel.ADVANCED: 3,
        }

        # Build name to concept mapping
        concept_by_name = {c.name.lower(): c for c in concepts}
        concept_by_id = {c.concept_id: c for c in concepts}

        # Topological in-degree calculation based on prerequisites
        in_degree: Dict[UUID, int] = {c.concept_id: 0 for c in concepts}
        dependents: Dict[UUID, List[UUID]] = {c.concept_id: [] for c in concepts}

        for c in concepts:
            for prereq_name in c.prerequisite_names:
                prereq_concept = concept_by_name.get(prereq_name.lower())
                if prereq_concept and prereq_concept.concept_id != c.concept_id:
                    in_degree[c.concept_id] += 1
                    dependents[prereq_concept.concept_id].append(c.concept_id)

        # Stable sort prioritizing in-degree, then difficulty, preserving original discovery order
        return sorted(
            concepts,
            key=lambda c: (
                in_degree[c.concept_id],
                difficulty_weight.get(c.difficulty, 2),
            ),
        )

    def _calculate_module_count(self, num_concepts: int) -> int:
        """Determines the number of modules to construct within Contract 2 limits [2, 4]."""
        if num_concepts <= 3:
            return 2
        elif num_concepts <= 6:
            return 3
        else:
            return 4

    def _partition_concepts(
        self,
        concepts: List[ExtractedConcept],
        num_modules: int,
    ) -> List[List[ExtractedConcept]]:
        """Splits an ordered list of concepts across the target module count."""
        n = len(concepts)
        num_modules = min(num_modules, n)
        k, m = divmod(n, num_modules)

        groups: List[List[ExtractedConcept]] = []
        start = 0
        for i in range(num_modules):
            end = start + k + (1 if i < m else 0)
            groups.append(concepts[start:end])
            start = end

        # Ensure all groups have at least 1 concept
        while len(groups) < num_modules:
            groups.append([concepts[-1]])

        return groups

    def _build_module(
        self,
        module_sequence: int,
        total_modules: int,
        concepts: List[ExtractedConcept],
        all_chunks: List[ExtractedChunk],
    ) -> ModuleDesign:
        """Constructs a single ModuleDesign containing 1 to 3 lessons."""
        # 1. Determine lesson count (bounded between min_lessons=1 and max_lessons=3)
        num_lessons = min(self.max_lessons, max(self.min_lessons, math.ceil(len(concepts) / 2)))

        # 2. Partition module concepts into lessons
        k, m = divmod(len(concepts), num_lessons)
        lesson_concept_groups: List[List[ExtractedConcept]] = []
        start = 0
        for i in range(num_lessons):
            end = start + k + (1 if i < m else 0)
            group = concepts[start:end]
            if not group:
                group = [concepts[0]]  # Fallback to ensure target concepts exist
            lesson_concept_groups.append(group)
            start = end

        # 3. Construct individual lessons
        lessons: List[LessonDesign] = []
        for les_idx, les_concepts in enumerate(lesson_concept_groups, start=1):
            lesson = self._build_lesson(
                lesson_sequence=les_idx,
                module_sequence=module_sequence,
                concepts=les_concepts,
                all_chunks=all_chunks,
            )
            lessons.append(lesson)

        # 4. Generate thematic module title & description
        mod_title = self._synthesize_module_title(module_sequence, total_modules, concepts)
        mod_desc = self._synthesize_module_description(mod_title, concepts, lessons)

        return ModuleDesign(
            module_sequence=module_sequence,
            title=mod_title,
            description=mod_desc,
            lessons=lessons,
        )

    def _build_lesson(
        self,
        lesson_sequence: int,
        module_sequence: int,
        concepts: List[ExtractedConcept],
        all_chunks: List[ExtractedChunk],
    ) -> LessonDesign:
        """Constructs a single LessonDesign with verified Contract 2 attributes."""
        target_concept_ids = [c.concept_id for c in concepts]

        # Gather supporting chunk UUIDs directly mapped to concepts
        source_chunk_ids: List[UUID] = []
        for c in concepts:
            for cid in c.source_chunk_ids:
                if cid not in source_chunk_ids:
                    source_chunk_ids.append(cid)

        # Fallback grounding: if concepts lacked explicit chunks, link nearest document chunks
        if not source_chunk_ids and all_chunks:
            source_chunk_ids = [all_chunks[0].chunk_id]
            if len(all_chunks) > 1:
                source_chunk_ids.append(all_chunks[1].chunk_id)

        # Generate actionable Bloom's taxonomy learning objectives
        learning_objectives = self._generate_learning_objectives(concepts)

        # Estimated duration in minutes: 10 mins baseline + 5 mins per concept, clamped to [5, 30]
        estimated_minutes = max(5, min(30, 8 + len(concepts) * 5 + len(source_chunk_ids) * 2))

        # Synthesize clear, engaging lesson title
        lesson_title = self._synthesize_lesson_title(lesson_sequence, concepts)

        return LessonDesign(
            lesson_sequence=lesson_sequence,
            title=lesson_title,
            estimated_minutes=estimated_minutes,
            learning_objectives=learning_objectives,
            target_concept_ids=target_concept_ids,
            source_chunk_ids=source_chunk_ids,
        )

    def _generate_learning_objectives(self, concepts: List[ExtractedConcept]) -> List[str]:
        """
        Generates at least 2 measurable learning objectives phrased using
        Bloom's taxonomy action verbs matching concept difficulty.
        """
        objectives: List[str] = []

        for idx, concept in enumerate(concepts):
            verbs = BLOOM_VERBS.get(concept.difficulty, BLOOM_VERBS[DifficultyLevel.BEGINNER])
            verb1 = verbs[idx % len(verbs)]
            verb2 = verbs[(idx + 2) % len(verbs)]

            # Clean name for phrasing
            clean_name = concept.name.strip()

            obj1 = f"{verb1} the fundamental mechanisms, definitions, and operational principles of {clean_name}."
            if obj1 not in objectives:
                objectives.append(obj1)

            if len(objectives) < 2:
                obj2 = f"{verb2} how {clean_name} is implemented within standard practical workflows and environments."
                if obj2 not in objectives:
                    objectives.append(obj2)

        # Ensure we always meet Contract 2 requirement: min_length=2
        if len(objectives) < 2:
            lead_concept = concepts[0].name.strip()
            objectives.append(
                f"Analyze common operational challenges and evaluation metrics associated with {lead_concept}."
            )

        return objectives

    def _synthesize_lesson_title(self, sequence: int, concepts: List[ExtractedConcept]) -> str:
        """Synthesizes a descriptive lesson title."""
        names = [c.name.strip() for c in concepts]
        if len(names) == 1:
            diff = concepts[0].difficulty
            if diff == DifficultyLevel.BEGINNER:
                return f"Fundamentals of {names[0]}"
            elif diff == DifficultyLevel.ADVANCED:
                return f"Advanced Implementation & Optimization of {names[0]}"
            return f"Practical Application of {names[0]}"
        elif len(names) == 2:
            return f"{names[0]} and {names[1]}: Core Principles & Workflows"
        else:
            return f"{names[0]} and Related Methodologies"

    def _synthesize_module_title(
        self,
        module_sequence: int,
        total_modules: int,
        concepts: List[ExtractedConcept],
    ) -> str:
        """Synthesizes a coherent module title aligned with curriculum stage."""
        top_name = concepts[0].name.strip() if concepts else "Core Principles"

        if module_sequence == 1:
            return f"Module 1: Foundations and Architectural Core of {top_name}"
        elif module_sequence == total_modules:
            return f"Module {module_sequence}: Advanced Synthesis, Governance & Optimization"
        else:
            return f"Module {module_sequence}: Practical Workflows and Implementation of {top_name}"

    def _synthesize_module_description(
        self,
        title: str,
        concepts: List[ExtractedConcept],
        lessons: List[LessonDesign],
    ) -> str:
        """Synthesizes an informative module overview."""
        concept_names = ", ".join(c.name.strip() for c in concepts)
        return (
            f"This module investigates {title.lower()}, covering {len(lessons)} focused lessons. "
            f"Learners will master essential concepts including: {concept_names}."
        )

    def _synthesize_course_title(
        self,
        concepts: List[ExtractedConcept],
        chunks: List[ExtractedChunk],
    ) -> str:
        """Synthesizes an overarching course title from extracted content."""
        # Check if chunks contain prominent section headers
        for chunk in chunks:
            if chunk.section_header and len(chunk.section_header.strip()) >= 5:
                header = chunk.section_header.strip()
                # Remove markdown hash tags
                header = re.sub(r"^#+\s*", "", header).strip()
                if len(header) >= 5 and len(header) <= 60:
                    return f"{header} Comprehensive Masterclass"

        # Fallback to top concept
        top_concept = concepts[0].name.strip()
        return f"{top_concept}: End-to-End Principles and Practices"

    def _synthesize_course_description(
        self,
        course_title: str,
        modules: List[ModuleDesign],
        concepts: List[ExtractedConcept],
    ) -> str:
        """Synthesizes a comprehensive course description satisfying Contract 2 length constraints."""
        total_lessons = sum(len(m.lessons) for m in modules)
        core_topics = ", ".join(c.name.strip() for c in concepts[:4])
        return (
            f"An intensive, source-grounded curriculum designed to equip learners with mastery "
            f"in {course_title}. Spanning {len(modules)} progressive modules and {total_lessons} "
            f"structured lessons, this course establishes comprehensive competency across: {core_topics}."
        )

    def generate_llm_prompt(self, extraction_output: ContentExtractionOutput) -> Dict[str, Any]:
        """
        Generates structured prompt specifications for optional LLM-assisted curriculum design
        (e.g., via Gemini 1.5 Pro / Flash).
        """
        system_instruction = (
            "You are an expert Educational Curriculum Designer for Eduvance AI. "
            "You receive validated extracted document chunks and domain concepts. "
            "Your task is to design a pedagogically sequenced curriculum conforming strictly to Contract 2 JSON schema. "
            "Ensure: exactly 2 to 4 modules, 1 to 3 lessons per module, at least 2 Bloom's taxonomy objectives per lesson, "
            "and all target_concept_ids and source_chunk_ids are valid UUIDs from the input."
        )

        user_payload = {
            "course_id": str(extraction_output.course_id),
            "concepts": [
                {
                    "concept_id": str(c.concept_id),
                    "name": c.name,
                    "description": c.description,
                    "difficulty": c.difficulty.value,
                    "prerequisites": c.prerequisite_names,
                    "source_chunk_ids": [str(cid) for cid in c.source_chunk_ids],
                }
                for c in extraction_output.concepts
            ],
            "chunks_sample": [
                {
                    "chunk_id": str(chunk.chunk_id),
                    "page_number": chunk.page_number,
                    "section_header": chunk.section_header,
                    "excerpt": chunk.text_content[:200] + "...",
                }
                for chunk in extraction_output.chunks[:10]
            ],
        }

        return {
            "system_instruction": system_instruction,
            "user_prompt": f"Generate CourseDesignOutput JSON based on the following extracted knowledge:\n{json.dumps(user_payload, indent=2)}",
        }

    def parse_llm_response(
        self,
        raw_response: str,
        fallback_output: ContentExtractionOutput,
    ) -> CourseDesignOutput:
        """
        Parses and validates an LLM-generated JSON response into a validated CourseDesignOutput.
        Gracefully falls back to deterministic curriculum generation if response is malformed.
        """
        try:
            # Strip markdown code blocks if wrapped
            cleaned = re.sub(r"^```json\s*", "", raw_response.strip(), flags=re.IGNORECASE)
            cleaned = re.sub(r"```$", "", cleaned.strip())
            data = json.loads(cleaned)
            return CourseDesignOutput.model_validate(data)
        except Exception:
            # Fallback to robust deterministic generation
            return self.generate_curriculum(fallback_output)
