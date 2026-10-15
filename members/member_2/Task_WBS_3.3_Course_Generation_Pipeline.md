# Task WBS 3.3: Course Designer Agent & Curriculum Generation

### Member Information
- **Member Name:** Member 2
- **Role:** Content and RAG Engineer
- **Assigned Work Package (WBS):** WBS 3.3 (Course Designer Agent & Curriculum Generation)
- **Task Name:** Course Curriculum & Syllabus Synthesis
- **Week:** Weeks 5–6
- **Status:** COMPLETED (All Steps Finished & Verified - 18 Passing Tests, 116 Project-Wide)

---

## 1. Executive Summary & Objective

WBS 3.3 delivers the **Course Designer Agent** for the **Eduvance AI** platform. Operating as the direct downstream consumer of WBS 3.2's content extraction output, this module translates atomic source-anchored chunks and domain concepts into a pedagogically sequenced, structured syllabus consisting of thematic modules, focused lessons, and measurable learning objectives.

### Core Deliverables Achieved:
1. **Contract 2 Interface Adherence:** Formulates strict Pydantic v2 validation models (`CourseDesignOutput`, `ModuleDesign`, `LessonDesign`) conforming precisely to **Agent Contract 2** established in WBS 2.1.
2. **Pedagogical Concept Sequencing:** Orders concepts using prerequisite topology and difficulty tiers (`BEGINNER` $\rightarrow$ `INTERMEDIATE` $\rightarrow$ `ADVANCED`) ensuring foundational ideas precede complex operational practices.
3. **Bloom's Taxonomy Objective Formulation:** Generates at least 2 actionable, measurable learning objectives per lesson using recognized cognitive action verbs (`Identify`, `Explain`, `Apply`, `Analyze`, `Evaluate`, `Design`).
4. **End-to-End Citation Provenance:** Directly binds each lesson to its originating `target_concept_ids` and supporting `source_chunk_ids`, preserving citation provenance back to physical PDF pages.
5. **Relational Persistence & Workflow State Machine:** Maps curriculum entities into `modules` and `lessons` database tables, manages course lifecycle transitions (`EXTRACTED` $\rightarrow$ `DESIGNING_COURSE` $\rightarrow$ `PENDING_APPROVAL` $\rightarrow$ `GENERATING_ASSETS`), and provides instructor review and reordering APIs.
6. **Dual-Mode Architecture (LLM + Deterministic Fallback):** Supplies prompt templates for live LLM generation (e.g., Gemini API) alongside a robust, offline deterministic heuristic engine for reproducible, cost-free testing.

---

## 2. Requirements & Acceptance Criteria Conformance

| Criterion | Contract Requirement | Implementation Mechanism | Verification Result |
| :--- | :--- | :--- | :---: |
| **AC-3.3.1** | Course title $\ge 5$ chars, description $\ge 20$ chars | Pydantic v2 `min_length` validators in `schemas.py` | ✅ PASSED |
| **AC-3.3.2** | Course must contain 2 to 4 modules | Bounded in `course_designer.py` and validated by `schemas.py` | ✅ PASSED |
| **AC-3.3.3** | Each module must contain 1 to 3 lessons | Module partitioner strictly bounds lesson cohort sizes | ✅ PASSED |
| **AC-3.3.4** | Lesson duration bounded to 5–30 minutes | `estimated_minutes` computed and clamped to $[5, 30]$ | ✅ PASSED |
| **AC-3.3.5** | At least 2 Bloom's learning objectives per lesson | `_generate_learning_objectives()` with categorized verbs | ✅ PASSED |
| **AC-3.3.6** | Full target concept & source chunk provenance | Lessons retain valid UUID arrays matching extraction inputs | ✅ PASSED |
| **AC-3.3.7** | Database persistence & status transition | `CourseDesignPersistenceService` commits to `modules`/`lessons` | ✅ PASSED |
| **AC-3.3.8** | Instructor review & update workflow | APIs for updating lessons/modules, reordering, and approving | ✅ PASSED |

---

## 3. Technology Stack & Approach

| Component | Selected Technology | Rationale |
| :--- | :--- | :--- |
| **Data Contracts** | Pydantic v2 (`pydantic.BaseModel`) | Enforces schema validation, field constraints, and seamless JSON serialization for Contract 2. |
| **Pedagogical Sequencing** | Topological dependency traversal & Bloom's Taxonomy | Orders concepts from foundational prerequisites to advanced synthesis; categorizes learning objectives by cognitive level. |
| **Relational Storage** | SQLAlchemy 2.0 ORM | Maps curriculum trees directly into the `modules` and `lessons` relational tables with JSON array support. |
| **Dual-Mode Orchestration** | Structured Prompting + Deterministic Heuristics | Enables production LLM integration while guaranteeing deterministic, fast, and offline CI/CD test runs. |

---

## 4. Implementation Structure (`AI_Modules/CourseDesign/`)

```
AI_Modules/CourseDesign/
├── __init__.py                # Public exports (CourseDesigner, schemas, persistence, pipeline)
├── schemas.py                 # Pydantic v2 validation models for Contract 2 (CourseDesignOutput)
├── course_designer.py         # Curriculum engine, Bloom's objective generator & heuristic partitioner
├── persistence.py             # Database persistence (Module, Lesson) & instructor editing workflows
├── pipeline.py                # End-to-end CourseDesignPipeline orchestrator
└── tests/
    ├── __init__.py
    ├── conftest.py            # Extraction mocks (Contract 1) & in-memory SQLite fixtures
    ├── test_schemas.py        # Contract 2 validation and boundary test suite
    ├── test_course_designer.py# Pedagogical ordering, Bloom objectives, provenance test suite
    └── test_pipeline.py       # Persistence, state transitions, instructor review test suite
```

---

## 5. Architectural Detail & Core Algorithms

### 5.1 Contract 2 Pydantic Schemas (`schemas.py`)
- `LessonDesign`:
  - `lesson_sequence`: Integer $\ge 1$.
  - `title`: String ($2 \le \text{length} \le 255$).
  - `estimated_minutes`: Integer clamped to $[5, 30]$.
  - `learning_objectives`: Array of strings ($\ge 2$ items).
  - `target_concept_ids`: List of UUIDs ($\ge 1$ item).
  - `source_chunk_ids`: List of UUIDs ($\ge 1$ item).
- `ModuleDesign`:
  - `module_sequence`: Integer $\ge 1$.
  - `title`: String ($2 \le \text{length} \le 255$).
  - `description`: String ($\ge 5$ characters).
  - `lessons`: Array of `LessonDesign` ($1 \le \text{count} \le 3$).
- `CourseDesignOutput`:
  - `course_title`: String ($5 \le \text{length} \le 255$).
  - `description`: String ($\ge 20$ characters).
  - `modules`: Array of `ModuleDesign` ($2 \le \text{count} \le 4$).

### 5.2 Pedagogical Ordering & Lesson Partitioning (`course_designer.py`)
1. **Topological Prerequisite Ordering:**
   Calculates in-degree dependencies across extracted concepts. Concepts with zero prerequisites and `BEGINNER` difficulty are placed first, followed by `INTERMEDIATE` concepts, and finally `ADVANCED` concepts.
2. **Module Scaling:**
   Determines optimal module count ($2 \le \text{modules} \le 4$) based on total concept count:
   - $\le 3$ concepts: 2 modules.
   - $4\text{--}6$ concepts: 3 modules.
   - $\ge 7$ concepts: 4 modules.
3. **Bloom's Taxonomy Objective Generator:**
   Categorizes action verbs by cognitive depth:
   - `BEGINNER`: *Identify, Define, Explain, Describe, Recognize, Summarize, Differentiate, Clarify*.
   - `INTERMEDIATE`: *Apply, Implement, Analyze, Execute, Construct, Examine, Integrate, Demonstrate*.
   - `ADVANCED`: *Evaluate, Optimize, Formulate, Design, Assess, Synthesize, Standardize, Govern*.
   Every lesson receives $\ge 2$ distinct objectives directly incorporating the target concept names.

### 5.3 Database Persistence & Instructor Review (`persistence.py`)
- Maps `CourseDesignOutput` to `Module` and `Lesson` tables in the relational database.
- Manages course state machine transitions:
  - Ingestion complete: `EXTRACTED`
  - Generation active: `DESIGNING_COURSE`
  - Generation complete / Review ready: `PENDING_APPROVAL`
  - Approved by instructor: `GENERATING_ASSETS`
- Provides instructor modification services:
  - `update_lesson(session, lesson_id, update_data)`: Edit title, duration, or learning objectives.
  - `update_module(session, module_id, update_data)`: Edit module title and description.
  - `reorder_lessons(session, module_id, ordered_lesson_ids)`: Re-sequence lessons within a module.
  - `approve_course_design(session, course_id)`: Finalizes review and unlocks asset generation.

---

## 6. Automated Test Suite & Empirical Evidence

### Course Designer Test Suite (18 Tests, 100% Passing):
```
AI_Modules/CourseDesign/tests/test_course_designer.py::test_generate_curriculum_produces_contract_2_valid_output PASSED [  5%]
AI_Modules/CourseDesign/tests/test_course_designer.py::test_pedagogical_concept_sequencing PASSED [ 11%]
AI_Modules/CourseDesign/tests/test_course_designer.py::test_learning_objectives_bloom_taxonomy PASSED [ 16%]
AI_Modules/CourseDesign/tests/test_course_designer.py::test_citation_provenance_preservation PASSED [ 22%]
AI_Modules/CourseDesign/tests/test_course_designer.py::test_minimal_concepts_scaling PASSED [ 27%]
AI_Modules/CourseDesign/tests/test_course_designer.py::test_llm_prompt_generation_and_fallback_parsing PASSED [ 33%]
AI_Modules/CourseDesign/tests/test_pipeline.py::test_pipeline_end_to_end_persists_to_database PASSED [ 38%]
AI_Modules/CourseDesign/tests/test_pipeline.py::test_instructor_update_lesson PASSED [ 44%]
AI_Modules/CourseDesign/tests/test_pipeline.py::test_instructor_update_module PASSED [ 50%]
AI_Modules/CourseDesign/tests/test_pipeline.py::test_instructor_reorder_lessons PASSED [ 55%]
AI_Modules/CourseDesign/tests/test_pipeline.py::test_course_approval_workflow PASSED [ 61%]
AI_Modules/CourseDesign/tests/test_schemas.py::test_lesson_design_valid PASSED [ 66%]
AI_Modules/CourseDesign/tests/test_schemas.py::test_lesson_design_estimated_minutes_bounds PASSED [ 72%]
AI_Modules/CourseDesign/tests/test_schemas.py::test_lesson_design_learning_objectives_min_length PASSED [ 77%]
AI_Modules/CourseDesign/tests/test_module_design_lessons_count_bounds PASSED [ 83%]
AI_Modules/CourseDesign/tests/test_course_design_output_modules_bounds PASSED [ 88%]
AI_Modules/CourseDesign/tests/test_course_design_output_title_and_description_min_length PASSED [ 94%]
AI_Modules/CourseDesign/tests/test_instructor_update_schemas PASSED [100%]

============================= 18 passed in 0.34s ==============================
```

### Full Project Regression Status:
- Backend & Database Foundation (WBS 3.1): **71 tests passed**
- Content Extraction & Chunking (WBS 3.2): **27 tests passed**
- Course Designer Agent (WBS 3.3): **18 tests passed**
- **Cumulative Total:** **116 passed, 1 skipped (live GCS credentials), 0 failures**

---

## 7. Downstream Dependencies Enabled

* **Member 3 (WBS 3.4 - Video Generation Pipeline):** Consumes `Lesson` entries, reading their `learning_objectives`, `target_concept_ids`, and `source_chunk_ids` to generate narration scripts, slide decks, and audio.
* **Member 3 (WBS 3.5 - Assessment Engine):** Generates quizzes linked directly to the `Lesson` and its `target_concept_ids`.
* **Member 2 (WBS 4.2 - Tutor RAG):** Grounded Q&A uses the structured lesson context and source chunks to answer learner questions.
* **Member 1 (WBS 4.1 - Central Workflow Controller):** Orchestrates the job state transition from `COURSE_PENDING_APPROVAL` to `GENERATING_ASSETS` upon user confirmation.
