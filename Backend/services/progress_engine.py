"""
Eduvance AI - Progress & Recommendation Engine
WBS 4.1 - Contract 6 Implementation

Computes overall course completion percentage, summarizes concept mastery scores,
and generates deterministic, explainable remedial revision recommendations for
concepts scoring below the 70% passing threshold.

Fulfills WBS 2.1 Contract 6 (ProgressEvaluationOutput).

Owner: Member 1 (Project Manager and Backend/Deployment Engineer)
"""

from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from Backend.core.progress_schemas import (
    ConceptMasteryItem,
    ProgressEvaluationOutput,
    RecommendationItem,
)
from Database.models.all_models import (
    Concept,
    ConceptMastery,
    Course,
    Lesson,
    LessonProgress,
    Module,
    User,
)


class ProgressEngine:
    """
    Evaluates learner course progression and generates remedial recommendations.
    """

    PASSING_THRESHOLD = 70.0

    def evaluate_course_progress(
        self,
        session: Session,
        user_id: UUID,
        course_id: UUID,
    ) -> ProgressEvaluationOutput:
        """
        Evaluates a learner's overall progress across a course and its concepts.

        Returns:
            ProgressEvaluationOutput conforming to Contract 6.
        """
        str_user_id = str(user_id)
        str_course_id = str(course_id)

        # 1. Verify Course and User exist
        course = session.query(Course).filter(Course.id == str_course_id).first()
        if not course:
            raise ValueError(f"Course with ID '{course_id}' not found.")

        user = session.query(User).filter(User.id == str_user_id).first()
        if not user:
            raise ValueError(f"User with ID '{user_id}' not found.")

        # 2. Fetch all modules and lessons for the course
        modules = session.query(Module).filter(Module.course_id == str_course_id).all()
        module_ids = [m.id for m in modules]

        lessons: List[Lesson] = []
        if module_ids:
            lessons = session.query(Lesson).filter(Lesson.module_id.in_(module_ids)).all()

        total_lessons = len(lessons)
        lesson_map = {les.id: les for les in lessons}

        # 3. Compute overall completion percentage
        completed_lessons_count = 0
        if total_lessons > 0:
            lesson_ids = list(lesson_map.keys())
            progress_records = (
                session.query(LessonProgress)
                .filter(
                    LessonProgress.user_id == str_user_id,
                    LessonProgress.lesson_id.in_(lesson_ids),
                )
                .all()
            )
            for pr in progress_records:
                if pr.status == "COMPLETED" or (pr.video_completed and pr.quiz_completed):
                    completed_lessons_count += 1

            completion_percentage = round((completed_lessons_count / total_lessons) * 100.0, 1)
        else:
            completion_percentage = 0.0

        # 4. Evaluate concept mastery summary
        concepts = session.query(Concept).filter(Concept.course_id == str_course_id).all()
        concept_ids = [c.id for c in concepts]

        mastery_records = {}
        if concept_ids:
            records = (
                session.query(ConceptMastery)
                .filter(
                    ConceptMastery.user_id == str_user_id,
                    ConceptMastery.concept_id.in_(concept_ids),
                )
                .all()
            )
            mastery_records = {r.concept_id: r for r in records}

        concept_mastery_summary: List[ConceptMasteryItem] = []
        recommendations: List[RecommendationItem] = []

        for concept in concepts:
            cm = mastery_records.get(concept.id)
            if cm:
                score = round(float(cm.mastery_score), 1)
                needs_rev = cm.needs_revision or (score < self.PASSING_THRESHOLD)
            else:
                score = 0.0
                needs_rev = False  # Not attempted yet

            concept_mastery_summary.append(
                ConceptMasteryItem(
                    concept_id=UUID(concept.id),
                    concept_name=concept.name,
                    score_percentage=score,
                    needs_revision=needs_rev,
                )
            )

            # 5. Formulate explainable recommendation if revision is required
            if needs_rev:
                # Find the primary lesson teaching this concept
                target_lesson = None
                for les in lessons:
                    concept_ids_in_lesson = les.target_concept_ids or []
                    if concept.id in concept_ids_in_lesson or any(concept.name.lower() in str(cid).lower() for cid in concept_ids_in_lesson):
                        target_lesson = les
                        break

                if not target_lesson and lessons:
                    target_lesson = lessons[0]

                if target_lesson:
                    reason = (
                        f"Remedial revision recommended: Your latest assessment score for '{concept.name}' was {score}%, "
                        f"which is below the {int(self.PASSING_THRESHOLD)}% proficiency threshold. Reviewing '{target_lesson.title}' "
                        f"will reinforce core mechanisms, definitions, and operational workflows."
                    )
                    recommendations.append(
                        RecommendationItem(
                            lesson_id=UUID(target_lesson.id),
                            lesson_title=target_lesson.title,
                            trigger_concept=concept.name,
                            trigger_quiz_score=score,
                            reason=reason,
                        )
                    )

        return ProgressEvaluationOutput(
            user_id=user_id,
            course_id=course_id,
            overall_completion_percentage=completion_percentage,
            concept_mastery_summary=concept_mastery_summary,
            recommendations=recommendations,
        )

