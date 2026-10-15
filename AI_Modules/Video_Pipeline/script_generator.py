"""
Eduvance AI - Video Script & Slide Outline Generator
WBS 3.4 - Narration Scripting & Instructional Storyboarding

Generates structured slide decks, visual composition cues, and conversational
voiceover scripts from lesson objectives, target concepts, and source chunks.

Fulfills WBS 2.1 Contract 3 (LessonVideoAssetOutput).

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

import math
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from AI_Modules.Extraction.schemas import ExtractedChunk, ExtractedConcept
from .schemas import LessonVideoAssetOutput, SlideSpec


class VideoScriptGenerator:
    """
    Synthesizes slide specifications, visual directives, and spoken voiceover
    scripts for a lesson, strictly conforming to Contract 3.
    """

    def __init__(
        self,
        min_slides: int = 3,
        max_slides: int = 8,
        default_slide_count: int = 4,
        words_per_minute: int = 140,
    ):
        self.min_slides = max(3, min_slides)
        self.max_slides = min(8, max_slides)
        self.default_slide_count = max(self.min_slides, min(self.max_slides, default_slide_count))
        self.wpm = words_per_minute

    def generate_lesson_script(
        self,
        lesson_id: UUID,
        lesson_title: str,
        learning_objectives: List[str],
        concepts: List[Union[ExtractedConcept, Dict[str, Any]]],
        chunks: List[Union[ExtractedChunk, Dict[str, Any]]],
        num_slides: Optional[int] = None,
    ) -> LessonVideoAssetOutput:
        """
        Synthesizes a complete LessonVideoAssetOutput adhering strictly to Contract 3.
        """
        if not chunks:
            raise ValueError("Cannot generate video script without source chunks for provenance grounding.")

        # Normalize concept and chunk objects
        norm_chunks = [c if isinstance(c, ExtractedChunk) else ExtractedChunk.model_validate(c) for c in chunks]
        norm_concepts = [c if isinstance(c, ExtractedConcept) else ExtractedConcept.model_validate(c) for c in concepts]

        # Determine target slide count within [min_slides, max_slides]
        target_slides = num_slides or self.default_slide_count
        target_slides = max(self.min_slides, min(self.max_slides, target_slides))

        slides: List[SlideSpec] = []

        # ---------------------------------------------------------
        # Slide 1: Introduction, Context & Learning Objectives
        # ---------------------------------------------------------
        intro_bullets = [
            f"Core Focus: {lesson_title}",
            f"Objective: {learning_objectives[0] if learning_objectives else 'Understand foundational principles'}",
        ]
        if len(learning_objectives) > 1:
            intro_bullets.append(f"Application: {learning_objectives[1]}")

        intro_script = (
            f"Welcome to this instructional session on {lesson_title}. In this video, we will explore the core "
            f"mechanisms and operational frameworks that govern this domain. By the conclusion of this lesson, "
            f"you will be equipped to {learning_objectives[0].lower() if learning_objectives else 'apply these principles'}."
        )

        slides.append(
            SlideSpec(
                slide_number=1,
                header=f"Overview: {lesson_title}",
                bullet_points=intro_bullets[:4],
                visual_cue="Thematic Agenda Card with Learning Outcomes Checklist",
                narration_script=intro_script,
                source_chunk_id=norm_chunks[0].chunk_id,
            )
        )

        # ---------------------------------------------------------
        # Intermediate Concept Deep-Dive Slides (Slides 2 to N-1)
        # ---------------------------------------------------------
        concept_idx = 0
        chunk_idx = 1 if len(norm_chunks) > 1 else 0

        for slide_no in range(2, target_slides):
            # Select concept and chunk for grounding
            concept = norm_concepts[concept_idx % len(norm_concepts)] if norm_concepts else None
            chunk = norm_chunks[chunk_idx % len(norm_chunks)]

            c_name = concept.name if concept else f"Core Topic {slide_no}"
            c_desc = concept.description if concept else chunk.text_content[:150]

            # Generate slide bullet points from concept and chunk
            bullets = [
                f"Principle: {c_name} defines critical operational standards.",
                f"Mechanism: {c_desc[:90].strip()}...",
                "Key Benefit: Establishes predictable and verifiable system behavior.",
            ]

            # Generate engaging narration script
            script = (
                f"Let us focus on {c_name}. {c_desc} Understanding this foundational component is essential "
                f"because it directly dictates how related processes behave in production environments. "
                f"Notice how each operational element integrates into the broader system architecture."
            )

            visual_cue = (
                f"Architectural Flow Diagram illustrating {c_name} components"
                if slide_no % 2 == 0
                else f"Comparative Functional Table highlighting {c_name} characteristics"
            )

            slides.append(
                SlideSpec(
                    slide_number=slide_no,
                    header=f"{c_name}: Principles & Architecture",
                    bullet_points=bullets,
                    visual_cue=visual_cue,
                    narration_script=script,
                    source_chunk_id=chunk.chunk_id,
                )
            )

            concept_idx += 1
            chunk_idx += 1

        # ---------------------------------------------------------
        # Final Slide: Synthesis, Best Practices & Summary
        # ---------------------------------------------------------
        final_chunk = norm_chunks[-1]
        summary_bullets = [
            "Synthesis: Cohesive integration of all examined components.",
            "Best Practice: Continuous validation and iterative review.",
            "Next Steps: Apply concepts in the upcoming practice exercises and quiz.",
        ]

        summary_script = (
            f"To summarize our study of {lesson_title}: remember that reliable implementations depend on "
            f"thorough validation, adherence to established standards, and continuous evaluation. "
            f"Review the accompanying source materials and proceed to the interactive assessment to reinforce your mastery."
        )

        slides.append(
            SlideSpec(
                slide_number=target_slides,
                header=f"Summary & Best Practices: {lesson_title}",
                bullet_points=summary_bullets,
                visual_cue="Summary Synthesis Card with Implementation Best Practices",
                narration_script=summary_script,
                source_chunk_id=final_chunk.chunk_id,
            )
        )

        # ---------------------------------------------------------
        # Estimate Total Duration (words spoken + transition padding)
        # ---------------------------------------------------------
        total_words = sum(len(s.narration_script.split()) for s in slides)
        # Speaking time in seconds = (words / WPM) * 60 + 2 seconds buffer per slide
        estimated_seconds = int((total_words / self.wpm) * 60) + (len(slides) * 2)
        total_estimated_seconds = max(15, min(420, estimated_seconds))

        return LessonVideoAssetOutput(
            lesson_id=lesson_id,
            total_estimated_seconds=total_estimated_seconds,
            slides=slides,
        )
