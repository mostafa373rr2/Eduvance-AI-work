# Task WBS 3.2: Document Extraction, Chunking & Source References

### Member Information
- **Member Name:** Member 2
- **Role:** Content and RAG Engineer
- **Assigned Work Package (WBS):** WBS 3.2 (Implement upload validation, extraction, and source references)
- **Task Name:** Document Extraction, Chunking & Source References
- **Week:** Weeks 4–5
- **Status:** COMPLETED (All 7 Steps Finished & Verified - 27 Passing Tests)

---

## 1. Executive Summary & Objective

WBS 3.2 delivers the foundational content extraction and ingestion engine for **Eduvance AI**. As the first operational AI pipeline stage, this module takes uploaded training documents (bounded text-based PDFs $\le$ 50 pages) and transforms them into an atomic, source-grounded representation. 

The primary objectives are:
1. **Validation & Ingestion Gate:** Verify uploaded PDFs against strict criteria (page count $\le$ 50, valid text stream, rejection of scanned/empty documents).
2. **Deterministic Page-Anchored Extraction:** Extract text content page-by-page while preserving exact originating document IDs and physical page numbers (`page_number`).
3. **Context-Preserving Chunking Engine:** Divide document text into atomic segments (300–500 tokens with 50-token overlap) that maintain syntactic coherence and section header hierarchy.
4. **Contract-Conforming Schema Output:** Structure the extracted chunks and initial concept entities to strictly fulfill **Contract 1 (`ContentExtractionOutput`)** defined in WBS 2.1.
5. **Relational Persistence:** Provide automated persistence into the database tables `content_chunks` and `concepts` (`Database/models/all_models.py`).

---

## 2. Requirements & Acceptance Criteria

* **Document Boundaries:** Only text-based PDF documents are processed. A single course accepts up to 3 files and a maximum cumulative page count of 50 pages.
* **Scanned/Image Detection:** Documents with an average textual density of $< 100$ characters per page are flagged as scanned/unusable with a descriptive validation error.
* **Traceability Guarantee:** Every generated chunk must link to its originating `document_id` and `page_number` for downstream RAG citations and auditability.
* **Minimum Content Threshold:** Extracted chunks must meet a minimum character length ($\ge 50$ characters) to eliminate noisy page artifacts or isolated numbers.
* **Deterministic Token Budget:** Chunk windows default to 400 tokens with a 50-token overlap, ensuring predictable context sizes for embedding models.

---

## 3. Technology Stack & Approach

| Component | Selected Technology | Rationale |
| :--- | :--- | :--- |
| **PDF Extraction Engine** | `pypdf` (>= 4.2.0) | Pure Python, lightweight, resilient to malformed xref tables, fast page-by-page text extraction without heavy native C dependencies. |
| **Data Contracts** | Pydantic v2 (`pydantic.BaseModel`) | Enforces schema validation, fast serialization, and strict compatibility with FastAPI and SQLAlchemy models. |
| **Token Estimation** | Whitespace-heuristic & word-ratio tokenizer | Deterministic, zero-dependency token approximation (~1.3 tokens per word) ensuring consistent chunk sizes without requiring heavy model weights at ingestion. |
| **Relational Storage** | SQLAlchemy 2.0 ORM | Maps atomic chunks to the `content_chunks` table and concepts to the `concepts` table. |

---

## 4. Work Breakdown & Implementation Steps

| Step | Scope | Target Deliverable | Status |
| :--- | :--- | :--- | :--- |
| **Step 1** | **Contracts & Schemas** | `AI_Modules/Extraction/schemas.py`, Task Tracking File | ✅ **COMPLETED** |
| **Step 2** | **PDF Ingestion & Validation** | `AI_Modules/Extraction/pdf_validator.py`, `text_extractor.py` | ✅ **COMPLETED** |
| **Step 3** | **Deterministic Chunking** | `AI_Modules/Extraction/chunker.py` (token sliding window & page anchors) | ✅ **COMPLETED** |
| **Step 4** | **Concept Extraction & Linking** | `AI_Modules/Extraction/concept_extractor.py` | ✅ **COMPLETED** |
| **Step 5** | **Database Persistence & Pipeline**| `AI_Modules/Extraction/pipeline.py` (pipeline runner & DB commit) | ✅ **COMPLETED** |
| **Step 6** | **Automated Test Suite** | `AI_Modules/Extraction/tests/test_extraction.py` (pytest suite) | ✅ **COMPLETED** |
| **Step 7** | **Final Audit & Verification** | Complete documentation, test logs, and milestone closure | ✅ **COMPLETED** |


---

## 5. Step 1 Deliverables Summary

### 5.1 Contract Models Implemented (`schemas.py`)
* `DifficultyLevel`: Enum (`BEGINNER`, `INTERMEDIATE`, `ADVANCED`).
* `DocumentValidationResult`: Validates document size, page boundaries, and character density.
* `ExtractedPage`: Page-level container capturing spatial page numbers (`page_number`) and text density metrics.
* `ExtractedChunk`: Represents atomic chunks (`chunk_id`, `document_id`, `chunk_index`, `page_number`, `text_content`, `token_count`, `section_header`).
* `ExtractedConcept`: Represents domain concepts (`concept_id`, `name`, `description`, `difficulty`, `prerequisite_names`, `source_chunk_ids`).
* `ContentExtractionOutput`: Root container conforming to WBS 2.1 Contract 1 (`course_id`, `chunks`, `concepts`).

---

## 6. Step 2 Deliverables Summary

### 6.1 PDF Validation Service (`pdf_validator.py`)
* Enforces single PDF boundary ($\le 50$ pages) with descriptive rejection messaging.
* Scanned / image-only PDF detection: Evaluates average character density ($< 100$ chars/page triggers `is_scanned_or_empty=True`).
* Gracefully intercepts password-encrypted PDFs and corrupt stream structures.

### 6.2 Page-by-Page Extraction Service (`text_extractor.py`)
* Extracts text page-by-page while preserving exact 1-indexed `page_number` anchors.
* Text normalization pipeline:
  * Unicode NFKC normalization.
  * Cross-line hyphen reconnection (e.g. `cyber-\nsecurity` $\rightarrow$ `cybersecurity`).
  * Paragraph separation preservation while collapsing multiple blank line artifacts.

---

## 7. Step 3 Deliverables Summary

### 7.1 Deterministic Chunking Engine (`chunker.py`)
* Implements token-bounded sliding window algorithm (target 400 tokens, 50-token overlap).
* Spatial Page Anchoring: Every chunk strictly records the `page_number` of originating blocks.
* Section Header Recognition: Automatically extracts Markdown headings (`## ...`) and numbered section headers (`1.1 ...`, `Section 2 ...`).
* Enforces minimum chunk length threshold ($\ge 50$ characters) to reject trailing OCR/page artifacts.
* Sequential 0-indexed ordering (`chunk_index = 0, 1, 2, ...`) for ordered course assembly.

---

## 8. Step 4 Deliverables Summary

### 8.1 Domain Concept Extraction Service (`concept_extractor.py`)
* Discovers domain concepts via heading analysis, formal definition patterns (`X is defined as Y`, `X refers to Y`), and core taxonomy entities.
* Synthesizes coherent, clean definitions ($\ge 10$ characters).
* Estimates pedagogical difficulty (`BEGINNER`, `INTERMEDIATE`, `ADVANCED`) based on relative text position and domain complexity keywords.
* Builds directed prerequisite associations ensuring earlier foundational concepts precede advanced topics.
* Traceability guarantee: Populates `source_chunk_ids` linking every concept to originating chunk UUIDs.

---

## 9. Step 5 Deliverables Summary

### 9.1 Database Persistence Service (`persistence.py`)
* Persists `ExtractedChunk` entities to `content_chunks` table as SQLAlchemy models with JSON metadata.
* Resolves prerequisite concept names to matching UUID foreign keys in `concepts.prerequisite_concept_ids`.
* Maps source chunk references into `concepts.source_chunk_ids` for complete citation traceability.
* Updates `Document.upload_status` to `"EXTRACTED"` and `Course.status` to `"EXTRACTED"`.
* Supports two-way round-trip retrieval via `load_extraction_output`.

### 9.2 Content Extraction Pipeline Orchestrator (`pipeline.py`)
* Unifies validator, extractor, chunker, concept engine, and persistence into `ContentExtractionPipeline.process_course_documents`.
* Fulfills WBS 2.1 Contract 1 (`ContentExtractionOutput`) with strong typing and automated validation.

---

## 10. Step 6 Deliverables Summary

### 10.1 Automated Integration & Boundary Test Suite (`test_extraction.py`)
* Multi-document course processing: Validates up to 3 documents ingested simultaneously with global sequential chunk indexing across files.
* Strict spatial traceability verification: Asserts every chunk traces to a valid originating document ID and 1-indexed page, and every concept references existing chunk UUIDs.
* Input validation & exception handling: Tests rejection of empty document lists, scanned/image-only PDFs, and corrupted files.
* Pipeline determinism: Asserts that running extraction repeatedly on identical inputs generates identical chunk boundaries, tokens, and concept definitions.

### 10.2 Automated Pytest Verification (Complete Suite: 27 Tests)
All 27 unit and integration tests across `AI_Modules/Extraction/tests/` executed successfully:
```text
platform win32 -- Python 3.14.6, pytest-9.1.1
collected 27 items

AI_Modules/Extraction/tests/test_chunker.py::test_chunker_invalid_overlap_raises PASSED    [  3%]
AI_Modules/Extraction/tests/test_chunker.py::test_chunker_single_page_basic PASSED        [  7%]
AI_Modules/Extraction/tests/test_chunker.py::test_chunker_multi_page_and_sequential_index PASSED [ 11%]
AI_Modules/Extraction/tests/test_chunker.py::test_chunker_section_header_detection PASSED [ 14%]
AI_Modules/Extraction/tests/test_chunker.py::test_chunker_token_estimation PASSED         [ 18%]
AI_Modules/Extraction/tests/test_concept_extractor.py::test_concept_extractor_empty_chunks PASSED [ 22%]
AI_Modules/Extraction/tests/test_concept_extractor.py::test_concept_extractor_definitional_patterns PASSED [ 25%]
AI_Modules/Extraction/tests/test_concept_extractor.py::test_concept_extractor_section_header_concept PASSED [ 29%]
AI_Modules/Extraction/tests/test_concept_extractor.py::test_concept_extractor_difficulty_grading PASSED [ 33%]
AI_Modules/Extraction/tests/test_extraction.py::test_multi_document_processing PASSED     [ 37%]
AI_Modules/Extraction/tests/test_extraction.py::test_pipeline_traceability_guarantee PASSED [ 40%]
AI_Modules/Extraction/tests/test_extraction.py::test_pipeline_rejects_empty_document_list PASSED [ 44%]
AI_Modules/Extraction/tests/test_extraction.py::test_pipeline_rejects_scanned_pdf PASSED  [ 48%]
AI_Modules/Extraction/tests/test_extraction.py::test_pipeline_determinism PASSED         [ 51%]
AI_Modules/Extraction/tests/test_extractor.py::test_pdf_validator_valid_pdf PASSED        [ 55%]
AI_Modules/Extraction/tests/test_extractor.py::test_pdf_validator_page_limit_exceeded PASSED [ 59%]
AI_Modules/Extraction/tests/test_extractor.py::test_pdf_validator_scanned_or_empty_rejected PASSED [ 62%]
AI_Modules/Extraction/tests/test_extractor.py::test_pdf_validator_corrupt_stream PASSED   [ 66%]
AI_Modules/Extraction/tests/test_extractor.py::test_text_extractor_extracts_pages_accurately PASSED [ 70%]
AI_Modules/Extraction/tests/test_extractor.py::test_text_extractor_clean_text_normalizations PASSED [ 74%]
AI_Modules/Extraction/tests/test_extractor.py::test_text_extractor_raises_on_invalid_pdf PASSED [ 77%]
AI_Modules/Extraction/tests/test_pipeline.py::test_pipeline_end_to_end_and_persistence PASSED [ 81%]
AI_Modules/Extraction/tests/test_schemas.py::test_document_validation_result PASSED        [ 85%]
AI_Modules/Extraction/tests/test_schemas.py::test_extracted_chunk_valid PASSED             [ 88%]
AI_Modules/Extraction/tests/test_schemas.py::test_extracted_chunk_min_length_validation PASSED [ 92%]
AI_Modules/Extraction/tests/test_schemas.py::test_extracted_concept_valid PASSED           [ 96%]
AI_Modules/Extraction/tests/test_schemas.py::test_content_extraction_output_root PASSED     [100%]

============================= 27 passed in 2.90s ==============================
```

---

## 11. Downstream Dependencies Enabled

* **Member 1 (WBS 4.1 - Workflow Controller):** Can invoke `ContentAgent.process_course_documents(course_id)` expecting the standardized `ContentExtractionOutput` contract.
* **Member 2 (WBS 3.3 - Course Designer):** Consumes `ExtractedChunk` and `ExtractedConcept` objects to generate structured modules and lessons.
* **Member 2 (WBS 4.2 - Tutor RAG):** Directly indexes `content_chunks` for vector similarity search and source citations.

---

## 12. Final Audit, Defense Evidence & Limitations

### 12.1 Acceptance Criteria Conformance Verification
* **Scope Compliance:** Only digital text-based PDFs ($\le 50$ pages) are accepted. Scanned or image-only documents are rejected with descriptive messages ($< 100$ characters/page threshold).
* **Traceability Guarantee:** 100% of persisted chunks record physical originating `page_number` ($\ge 1$) and `document_id`.
* **Contract Conformance:** Fulfills WBS 2.1 Contract 1 (`ContentExtractionOutput`) with complete Pydantic v2 validation.
* **Relational Persistence:** Chunks are saved to `content_chunks`, concepts to `concepts`, and document/course status flags are properly transitioned.
* **Test Health:** 27 automated tests pass with 100% success rate across clean test environments.

### 12.2 Academic Report Documentation Ready
* **Methodology Chapter (Section 4.1):** Text extraction, Unicode normalization, sliding-window chunking, and prerequisite DAG construction are formally documented.
* **Limitations Acknowledged:** 
  1. Multi-column academic layouts rely on PyPDF text stream extraction order without full visual OCR layout bounding boxes (deferred to P2 enhancements).
  2. Tables and embedded formulas are extracted as flat text rather than structured LaTeX or markdown tables.






