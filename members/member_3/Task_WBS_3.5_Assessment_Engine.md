# Task WBS 3.5: Assessment Engine (Quizzes, Exercises & Rubrics)

### Member Information
- **Member Name:** Member 3
- **Role:** Generative Media and Assessment Engineer
- **Assigned Work Package (WBS):** WBS 3.5 (Assessment Engine & Evaluator)
- **Task Name:** Assessment Synthesis & Deterministic Grading Engine
- **Week:** Weeks 7–8
- **Status:** COMPLETED (All Steps Finished & Verified - 15 Passing Tests, 151 Project-Wide)

---

## 1. Executive Summary & Objective

WBS 3.5 delivers the **Assessment Engine** for **Eduvance AI**. Operating as the evaluation pillar of the platform, this subsystem transforms structured lesson concepts and source chunks into comprehensive assessment packages. It features automated quiz generation, applied practical challenge authoring, and a deterministic grading engine with concept mastery diagnostics and remedial revision recommendations.

### Core Deliverables Achieved:
1. **Contract 5 Interface Adherence:** Formulates strict Pydantic v2 validation models (`AssessmentPackageOutput`, `QuizSpec`, `QuizQuestionSpec`, `PracticalExerciseSpec`, `RubricCriterionSpec`) conforming precisely to **Agent Contract 5** established in WBS 2.1.
2. **Grounded Quiz Synthesis:** Generates 4 to 8 questions per lesson with balanced question types (MCQ with 4 choices, TRUE_FALSE with 2 choices), plausible educational distractors, and pedagogically sound explanations.
3. **100% Provenance Traceability:** Every question strictly records `target_concept_id` and `source_chunk_id` UUID anchors, ensuring that every assessment item is defensibly backed by the uploaded training document.
4. **Applied Practical Challenges & Rubrics:** Synthesizes scenario-based challenges with detailed problem prompts, deliverable descriptions, starter code/configuration scaffolding, and multi-criteria rubrics summing to 100 points.
5. **Deterministic Scoring & Diagnostic Mastery:** Provides an automated evaluation service (`QuizEvaluator`) that grades learner submissions, computes exact percentage scores, and triggers explainable revision recommendations for scores $< 70\%$ as specified in WBS 1.2 and the WBS 2.1 state machine.
6. **Relational Persistence:** Persists assessment entities into the database tables `quizzes`, `quiz_questions`, and `practical_exercises` (`Database/models/all_models.py`) with full cascade lifecycle support.

---

## 2. Requirements & Acceptance Criteria Conformance

| Criterion | Contract Requirement | Implementation Mechanism | Verification Result |
| :--- | :--- | :--- | :---: |
| **AC-3.5.1** | Question count bounded between 4 and 8 | Bounded in `quiz_generator.py` and validated by `schemas.py` | ✅ PASSED |
| **AC-3.5.2** | Options count bounded between 2 and 4 | Validated in `QuizQuestionSpec.options` validator | ✅ PASSED |
| **AC-3.5.3** | `correct_answer` must be present in `options` | Pydantic model validator ensures exact membership | ✅ PASSED |
| **AC-3.5.4** | TRUE_FALSE questions must contain exactly 2 options | Model validator enforces `['True', 'False']` format | ✅ PASSED |
| **AC-3.5.5** | Every question links to concept and chunk | Mandatory UUID fields `target_concept_id` & `source_chunk_id` | ✅ PASSED |
| **AC-3.5.6** | Practical exercise rubric has $\ge 2$ criteria | Validated by `PracticalExerciseSpec.rubric_criteria` | ✅ PASSED |
| **AC-3.5.7** | Rubric points total 100 points | Verified across generated criteria (40/30/30 distribution) | ✅ PASSED |
| **AC-3.5.8** | Deterministic grading & $< 70\%$ revision trigger | `QuizEvaluator` emits mastery and remedial recommendations | ✅ PASSED |
| **AC-3.5.9** | Database persistence into relational schema | `AssessmentPersistenceService` commits Quiz, Questions, Exercise | ✅ PASSED |

---

## 3. Technology Stack & Approach

| Component | Selected Technology | Technical Justification | Operating Cost |
| :--- | :--- | :--- | :--- |
| **Data Contracts** | Pydantic v2 (`pydantic.BaseModel`) | Enforces schema validation, choice membership, and strict compatibility with FastAPI and SQLAlchemy. | **$0.00** |
| **Assessment Generator** | Rule-Guided Heuristic & Prompt Templates | Generates grounded questions and applied challenges with zero external API dependencies in local/CI runs. | **$0.00** |
| **Evaluation Engine** | Deterministic Scoring Algorithm | Constant-time answer matching, mastery set difference, and threshold-based revision triggers. | **$0.00** |
| **Relational Storage** | SQLAlchemy 2.0 ORM | Maps quizzes, questions, and exercises directly to relational tables with foreign keys and cascade rules. | **$0.00** |

---

## 4. Implementation Structure (`AI_Modules/Assessment/`)

```
AI_Modules/Assessment/
├── __init__.py               # Public package exports
├── schemas.py                # Pydantic v2 schemas strictly fulfilling Contract 5 & scoring models
├── quiz_generator.py         # Grounded quiz question synthesizer (MCQ, True/False, distractors)
├── exercise_generator.py     # Applied challenge generator with code scaffolding and rubrics
├── evaluator.py              # Deterministic scoring engine with concept mastery & revision triggers
├── persistence.py            # Relational database persistence (Quiz, QuizQuestion, PracticalExercise)
├── pipeline.py               # Master AssessmentGenerationPipeline orchestrator
└── tests/
    ├── __init__.py
    ├── conftest.py           # Synthetic lesson & chunk fixtures, in-memory SQLite DB
    ├── test_schemas.py       # Contract 5 validation & boundary tests
    ├── test_quiz_generator.py # Question counts, types, distractors, and provenance tests
    ├── test_exercise_generator.py # Scenario prompt, template, and rubric point tests
    ├── test_evaluator.py     # Deterministic grading & revision recommendation tests
    └── test_assessment_pipeline.py # End-to-end integration & persistence tests
```

---

## 5. Architectural Detail & Core Algorithms

### 5.1 Contract 5 Pydantic Schemas (`schemas.py`)
- `QuizQuestionSpec`:
  - `question_number`: Integer $\ge 1$.
  - `question_type`: Enum (`MCQ` or `TRUE_FALSE`).
  - `question_text`: String ($\ge 10$ characters).
  - `options`: Array of strings ($2 \le \text{options} \le 4$).
  - `correct_answer`: Must match one of the items in `options`.
  - `explanation`: String ($\ge 10$ characters).
  - `target_concept_id`: UUID reference to assessed concept.
  - `source_chunk_id`: UUID reference to grounding source chunk.
- `QuizSpec`:
  - `passing_score_percentage`: Integer in $[50, 100]$ (default: 70%).
  - `questions`: Array of `QuizQuestionSpec` ($4 \le \text{questions} \le 8$).
- `PracticalExerciseSpec`:
  - `prompt`: Problem statement ($\ge 20$ characters).
  - `deliverable_description`: Submission specification ($\ge 15$ characters).
  - `starter_template`: Code/configuration boilerplate.
  - `rubric_criteria`: Array of `RubricCriterionSpec` ($\ge 2$ criteria).
- `AssessmentPackageOutput`:
  - `lesson_id`: UUID.
  - `quiz`: `QuizSpec`.
  - `practical_exercise`: `PracticalExerciseSpec`.

### 5.2 Deterministic Evaluation & Remedial Triggers (`evaluator.py`)
- **Scoring Formula:**
  $$\text{score\_percentage} = \frac{\text{correct\_count}}{\text{total\_questions}} \times 100$$
- **Mastery Tracking:**
  - Identifies which concepts were answered correctly versus incorrectly.
  - `mastered_concept_ids`: Concepts where all corresponding questions were answered correctly.
  - `revision_recommended_concept_ids`: Concepts where the learner missed one or more questions.
- **Pass/Fail Threshold:**
  - Evaluates `score_percentage >= quiz.passing_score_percentage` (70%).
  - If score $< 70\%$, generates explainable guidance directing the learner to review specific lesson slides and consult the AI Tutor.

### 5.3 Database Persistence (`persistence.py`)
- Maps `AssessmentPackageOutput` to the relational tables:
  - `quizzes`: `lesson_id`, `passing_score`.
  - `quiz_questions`: `quiz_id`, `question_text`, `question_type`, `options`, `correct_answer`, `explanation`, `target_concept_id`, `source_chunk_id`, `sequence_order`.
  - `practical_exercises`: `lesson_id`, `prompt`, `deliverable_description`, `starter_template`, `rubric_criteria`.
- Supports idempotent re-generation: cleans up obsolete questions before inserting fresh assessments.

---

## 6. Automated Test Suite & Empirical Evidence

### Assessment Engine Test Suite (15 Tests, 100% Passing in 0.21s):
```
AI_Modules/Assessment/tests/test_assessment_pipeline.py::test_assessment_pipeline_end_to_end_persists_to_database PASSED [  6%]
AI_Modules/Assessment/tests/test_assessment_pipeline.py::test_idempotent_regeneration_clears_old_records PASSED [ 13%]
AI_Modules/Assessment/tests/test_evaluator.py::test_evaluator_perfect_score PASSED [ 20%]
AI_Modules/Assessment/tests/test_evaluator.py::test_evaluator_failing_score_triggers_revision PASSED [ 26%]
AI_Modules/Assessment/tests/test_evaluator.py::test_evaluator_missing_answers_treated_as_incorrect PASSED [ 33%]
AI_Modules/Assessment/tests/test_exercise_generator.py::test_generate_practical_exercise_satisfies_contract_5 PASSED [ 40%]
AI_Modules/Assessment/tests/test_quiz_generator.py::test_generate_quiz_satisfies_contract_5 PASSED [ 46%]
AI_Modules/Assessment/tests/test_quiz_generator.py::test_custom_question_count_clamping PASSED [ 53%]
AI_Modules/Assessment/tests/test_quiz_generator.py::test_quiz_generator_rejects_empty_chunks PASSED [ 60%]
AI_Modules/Assessment/tests/test_schemas.py::test_quiz_question_spec_valid PASSED [ 66%]
AI_Modules/Assessment/tests/test_schemas.py::test_quiz_question_correct_answer_must_be_in_options PASSED [ 73%]
AI_Modules/Assessment/tests/test_schemas.py::test_true_false_must_have_exactly_two_options PASSED [ 80%]
AI_Modules/Assessment/tests/test_schemas.py::test_quiz_spec_questions_bounds PASSED [ 86%]
AI_Modules/Assessment/tests/test_schemas.py::test_practical_exercise_rubric_bounds PASSED [ 93%]
AI_Modules/Assessment/tests/test_schemas.py::test_assessment_package_output_valid PASSED [100%]

============================= 15 passed in 0.21s ==============================
```

### Cumulative Repository Regression Status:
- Backend & Database Foundation (WBS 3.1): **71 tests passed**
- Content Extraction & Ingestion (WBS 3.2): **27 tests passed**
- Course Designer Agent (WBS 3.3): **18 tests passed**
- Video Generation Pipeline (WBS 3.4): **20 tests passed**
- Assessment Engine (WBS 3.5): **15 tests passed**
- **Cumulative Total:** **151 passed, 1 skipped (live GCS credentials), 0 failures**

---

## 7. Downstream Dependencies Enabled

* **Member 1 (WBS 4.1 - Central Workflow Controller & Progress Engine):** Ingests quiz attempt events, stores scores, and updates `concept_mastery` and `lesson_progress` tables.
* **Member 4 (WBS 3.6 - Frontend UI):** Quiz and Assessment UI component can render interactive MCQ/True-False forms, submit answers, and display detailed feedback and rubrics.
* **Member 2 (WBS 4.2 - Tutor RAG):** Grounded Q&A tutor can provide targeted clarification on concepts identified by the evaluator as needing revision.
