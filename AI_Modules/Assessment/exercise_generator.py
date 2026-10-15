"""
Eduvance AI - Practical Exercise Generation Engine
WBS 3.5 - Hands-on Challenge & Rubric Synthesis

Generates realistic, applied practical assignments complete with problem prompts,
deliverable specifications, starter code scaffolding, and multi-criteria rubrics.

Fulfills WBS 2.1 Contract 5 (AssessmentPackageOutput.practical_exercise).

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from AI_Modules.Extraction.schemas import ExtractedChunk, ExtractedConcept
from .schemas import PracticalExerciseSpec, RubricCriterionSpec


class PracticalExerciseGenerator:
    """
    Generates applied hands-on exercises and grading rubrics for a lesson.
    """

    def generate_exercise(
        self,
        lesson_id: UUID,
        lesson_title: str,
        learning_objectives: List[str],
        concepts: List[Union[ExtractedConcept, Dict[str, Any]]],
        chunks: List[Union[ExtractedChunk, Dict[str, Any]]],
    ) -> PracticalExerciseSpec:
        """
        Synthesizes a complete PracticalExerciseSpec aligned with lesson concepts and Bloom's objectives.
        """
        norm_concepts = [c if isinstance(c, ExtractedConcept) else ExtractedConcept.model_validate(c) for c in concepts]
        top_concept = norm_concepts[0].name if norm_concepts else "Core Architecture"
        second_concept = norm_concepts[1].name if len(norm_concepts) > 1 else "Operational Governance"

        # 1. Synthesize scenario-based problem prompt
        prompt = (
            f"You are tasked with designing and implementing an enterprise solution for {lesson_title}. "
            f"An organization requires a robust operational framework incorporating {top_concept} and {second_concept}. "
            f"Develop a complete implementation plan and configuration artifact demonstrating compliance with "
            f"the architectural principles and verification standards taught in this lesson."
        )

        # 2. Define clear deliverable expectations
        deliverable_description = (
            f"A documented technical submission including a working configuration script or code implementation, "
            f"an architectural diagram outline, and a brief verification report addressing potential failure modes."
        )

        # 3. Build code / configuration starter boilerplate
        starter_template = (
            f"# =============================================================================\n"
            f"# Eduvance AI Practical Exercise: {lesson_title}\n"
            f"# Challenge: Implement {top_concept} with {second_concept} integration\n"
            f"# =============================================================================\n\n"
            f"def configure_environment():\n"
            f"    \"\"\"Initializes baseline operational parameters.\"\"\"\n"
            f"    # TODO: Define core identity, resource access, and logging configuration\n"
            f"    config = {{\n"
            f"        'service_name': '{lesson_title.replace(' ', '_').lower()}',\n"
            f"        'enforce_strict_validation': True,\n"
            f"        'audit_logging_enabled': True,\n"
            f"    }}\n"
            f"    return config\n\n"
            f"def execute_validation_pipeline(config: dict) -> bool:\n"
            f"    \"\"\"Validates that all architectural constraints are satisfied.\"\"\"\n"
            f"    # TODO: Implement verification checks for {top_concept}\n"
            f"    # TODO: Verify fallback and error handling routines\n"
            f"    return True\n\n"
            f"if __name__ == '__main__':\n"
            f"    env_config = configure_environment()\n"
            f"    status = execute_validation_pipeline(env_config)\n"
            f"    print(f'Pipeline execution status: {{status}}')\n"
        )

        # 4. Formulate multi-criteria rubric (summing to 100 points)
        rubric_criteria = [
            RubricCriterionSpec(
                criterion="Core Architectural Implementation",
                points=40,
                description=(
                    f"Submission accurately models {top_concept} and incorporates necessary operational constraints "
                    f"without syntax or conceptual errors."
                ),
            ),
            RubricCriterionSpec(
                criterion="Verification & Error Handling",
                points=30,
                description=(
                    f"Implementation includes robust exception handling, validation checks for {second_concept}, "
                    f"and defensive operational safeguards."
                ),
            ),
            RubricCriterionSpec(
                criterion="Documentation & Provenance Traceability",
                points=30,
                description=(
                    "Code is thoroughly annotated with explanatory comments explicitly linking implemented features "
                    "back to the foundational course guidelines and learning objectives."
                ),
            ),
        ]

        return PracticalExerciseSpec(
            prompt=prompt,
            deliverable_description=deliverable_description,
            starter_template=starter_template,
            rubric_criteria=rubric_criteria,
        )
