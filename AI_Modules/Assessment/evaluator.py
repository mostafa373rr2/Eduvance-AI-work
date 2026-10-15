"""
Eduvance AI - Quiz Evaluation & Concept Mastery Scoring Engine
WBS 3.5 - Deterministic Assessment Grading & Diagnostic Feedback

Evaluates learner submissions, computes exact percentage scores, tracks concept
mastery signals, and generates explainable revision recommendations for scores < 70%.

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from typing import List, Set
from uuid import UUID

from .schemas import (
    QuestionEvaluation,
    QuizResult,
    QuizSpec,
    QuizSubmission,
)


class QuizEvaluator:
    """
    Evaluates learner quiz submissions and diagnoses concept mastery.
    """

    def evaluate_submission(
        self,
        quiz: QuizSpec,
        submission: QuizSubmission,
    ) -> QuizResult:
        """
        Grades learner answers against ground-truth correct options.

        Returns:
            QuizResult containing exact score, mastery signals, and revision guidance.
        """
        question_map = {q.question_number: q for q in quiz.questions}
        total_questions = len(quiz.questions)

        evaluations: List[QuestionEvaluation] = []
        correct_count = 0

        mastered_concepts: Set[UUID] = set()
        revision_concepts: Set[UUID] = set()

        for q_num, question in sorted(question_map.items()):
            selected_ans = submission.answers.get(q_num, "").strip()
            is_correct = (selected_ans == question.correct_answer.strip())

            if is_correct:
                correct_count += 1
                mastered_concepts.add(question.target_concept_id)
            else:
                revision_concepts.add(question.target_concept_id)

            evaluations.append(
                QuestionEvaluation(
                    question_number=q_num,
                    question_text=question.question_text,
                    selected_answer=selected_ans,
                    correct_answer=question.correct_answer,
                    is_correct=is_correct,
                    explanation=question.explanation,
                    target_concept_id=question.target_concept_id,
                    source_chunk_id=question.source_chunk_id,
                )
            )

        # Concepts where learner answered all corresponding questions correctly
        fully_mastered = list(mastered_concepts - revision_concepts)
        needs_revision = list(revision_concepts)

        score_percentage = round((correct_count / total_questions) * 100.0, 1)
        passed = score_percentage >= quiz.passing_score_percentage

        # Explainable recommendation messaging
        if passed:
            msg = (
                f"Congratulations! You passed the assessment with a score of {score_percentage}% "
                f"({correct_count}/{total_questions} correct). You have demonstrated solid comprehension "
                f"of the examined concepts."
            )
        else:
            msg = (
                f"Assessment score: {score_percentage}% ({correct_count}/{total_questions} correct). "
                f"This is below the required passing threshold of {quiz.passing_score_percentage}%. "
                f"Revision is recommended for {len(needs_revision)} identified concept(s). "
                f"Please review the corresponding lesson slides and ask the AI Tutor for clarification."
            )

        return QuizResult(
            lesson_id=submission.lesson_id,
            total_questions=total_questions,
            correct_count=correct_count,
            score_percentage=score_percentage,
            passed=passed,
            passing_score_percentage=quiz.passing_score_percentage,
            evaluations=evaluations,
            mastered_concept_ids=fully_mastered,
            revision_recommended_concept_ids=needs_revision,
            recommendation_message=msg,
        )
