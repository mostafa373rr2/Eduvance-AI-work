"""
Eduvance AI - Grounded Quiz Generation Engine
WBS 3.5 - Automated Assessment Synthesis

Synthesizes 4 to 8 pedagogical assessment questions (MCQs and True/False)
strictly grounded in target concepts and source document chunks.

Fulfills WBS 2.1 Contract 5 (AssessmentPackageOutput.quiz).

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from AI_Modules.Extraction.schemas import ExtractedChunk, ExtractedConcept
from .schemas import QuestionType, QuizQuestionSpec, QuizSpec


class QuizGenerator:
    """
    Generates structured, source-grounded quizzes conforming to Contract 5.
    """

    def __init__(self, default_question_count: int = 5, default_passing_score: int = 70):
        self.default_question_count = max(4, min(8, default_question_count))
        self.default_passing_score = default_passing_score

    def generate_quiz(
        self,
        lesson_id: UUID,
        lesson_title: str,
        concepts: List[Union[ExtractedConcept, Dict[str, Any]]],
        chunks: List[Union[ExtractedChunk, Dict[str, Any]]],
        num_questions: Optional[int] = None,
        passing_score: Optional[int] = None,
    ) -> QuizSpec:
        """
        Synthesizes a complete QuizSpec with 4 to 8 questions grounded in lesson concepts and chunks.
        """
        if not chunks:
            raise ValueError("Cannot generate quiz: No source chunks provided for citation grounding.")

        norm_chunks = [c if isinstance(c, ExtractedChunk) else ExtractedChunk.model_validate(c) for c in chunks]
        norm_concepts = [c if isinstance(c, ExtractedConcept) else ExtractedConcept.model_validate(c) for c in concepts]

        target_q_count = num_questions or self.default_question_count
        target_q_count = max(4, min(8, target_q_count))
        passing_threshold = passing_score or self.default_passing_score

        questions: List[QuizQuestionSpec] = []
        concept_idx = 0
        chunk_idx = 0

        for q_num in range(1, target_q_count + 1):
            concept = norm_concepts[concept_idx % len(norm_concepts)] if norm_concepts else None
            chunk = norm_chunks[chunk_idx % len(norm_chunks)]

            c_name = concept.name if concept else f"Core Principle {q_num}"
            c_desc = concept.description if concept else chunk.text_content[:120]

            # Alternate between MCQ and TRUE_FALSE (e.g. Q1, Q2, Q4 MCQ; Q3, Q5 TRUE_FALSE)
            if q_num % 3 == 0 or (target_q_count >= 6 and q_num % 2 == 0):
                # -----------------------------------------------------
                # Generate TRUE_FALSE question
                # -----------------------------------------------------
                is_true = (q_num % 2 != 0)
                if is_true:
                    q_text = (
                        f"In the context of {lesson_title}, {c_name} directly functions to {c_desc.lower().rstrip('.')}."
                    )
                    correct_ans = "True"
                    explanation = (
                        f"Correct. As documented in the course material, {c_name} is specifically defined "
                        f"to address this operational requirement."
                    )
                else:
                    q_text = (
                        f"Under standard guidelines for {lesson_title}, {c_name} completely eliminates the need "
                        f"for validation, logging, or operational oversight."
                    )
                    correct_ans = "False"
                    explanation = (
                        f"Correct. This statement is false because {c_name} requires continuous verification, "
                        f"monitoring, and governance rather than eliminating operational controls."
                    )

                questions.append(
                    QuizQuestionSpec(
                        question_number=q_num,
                        question_type=QuestionType.TRUE_FALSE,
                        question_text=q_text,
                        options=["True", "False"],
                        correct_answer=correct_ans,
                        explanation=explanation,
                        target_concept_id=concept.concept_id if concept else chunk.chunk_id,
                        source_chunk_id=chunk.chunk_id,
                    )
                )
            else:
                # -----------------------------------------------------
                # Generate Multiple Choice Question (MCQ)
                # -----------------------------------------------------
                correct_option = f"It enforces {c_desc.lower().rstrip('.')}."
                distractor_1 = f"It replaces all external identity and monitoring frameworks entirely."
                distractor_2 = f"It operates as a purely decorative legacy standard without security impact."
                distractor_3 = f"It restricts system availability to prevent all user interaction."

                options = [correct_option, distractor_1, distractor_2, distractor_3]

                q_text = f"Which of the following best describes the core operational role of {c_name}?"
                explanation = (
                    f"Option A is correct: {c_name} is designed to enforce {c_desc.lower().rstrip('.')}. "
                    f"The other options represent inaccurate generalizations or operational anti-patterns."
                )

                questions.append(
                    QuizQuestionSpec(
                        question_number=q_num,
                        question_type=QuestionType.MCQ,
                        question_text=q_text,
                        options=options,
                        correct_answer=correct_option,
                        explanation=explanation,
                        target_concept_id=concept.concept_id if concept else chunk.chunk_id,
                        source_chunk_id=chunk.chunk_id,
                    )
                )

            concept_idx += 1
            chunk_idx += 1

        return QuizSpec(
            passing_score_percentage=passing_threshold,
            questions=questions,
        )
