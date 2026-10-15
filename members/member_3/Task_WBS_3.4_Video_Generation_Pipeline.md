# Task WBS 3.4: Automated Lesson Video Generation Pipeline

### Member Information
- **Member Name:** Member 3
- **Role:** Generative Media and Assessment Engineer
- **Assigned Work Package (WBS):** WBS 3.4 (Automated Lesson Video Generation Pipeline)
- **Task Name:** Video Pipeline Implementation (Slides, TTS, Captions, Assembly)
- **Week:** Weeks 6–7
- **Status:** COMPLETED (All Steps Finished & Verified - 20 Passing Tests, 136 Project-Wide)

---

## 1. Executive Summary & Objective

WBS 3.4 delivers the production **Video Pipeline Agent** for **Eduvance AI**. Building upon the zero-cost feasibility findings confirmed in **WBS 2.3** and consuming the structured lesson definitions produced in **WBS 3.3**, this subsystem automates the synthesis of synchronized, source-grounded instructional videos and multimedia presentation packages.

### Core Deliverables Achieved:
1. **Contract 3 Interface Adherence:** Implements strict Pydantic v2 validation models (`LessonVideoAssetOutput`, `SlideSpec`) conforming precisely to **Agent Contract 3** established in WBS 2.1.
2. **Instructional Scripting & Storyboarding:** Generates 3 to 8 structured slides per lesson with concise bullet points ($2 \le \text{bullets} \le 5$), visual composition cues, and engaging voiceover scripts ($\ge 20$ chars, total duration $\le 420$ seconds / 7 minutes).
3. **Programmatic 1080p Slide Rasterization:** Uses **Python Pillow (PIL)** to render high-contrast, professional 1920x1080 presentation slides featuring academic dark slate surfaces (`#0F172A`), topic badges, word-wrapped bullet hierarchy, visual focus cards, and explicit source citation footers.
4. **Neural Voiceover Narration:** Integrates **`edge-tts`** with neural voices (`en-US-ChristopherNeural`, `en-US-JennyNeural`) paired with an offline deterministic fallback engine to guarantee zero-cost and 100% test reliability.
5. **Millisecond-Accurate Subtitle Alignment:** Formats synchronized **SubRip (`.srt`)** and **WebVTT (`.vtt`)** caption files aligned with spoken phrases and inter-slide transition pauses.
6. **Video Packaging & Assembly:** Features a dual-path assembler that compiles MP4 videos via FFmpeg when available, or packages high-resolution slides, audio tracks, and subtitles into a structured multimedia manifest bundle.
7. **Relational Persistence:** Maps generated media into the `video_assets` table (`Database/models/all_models.py`), linked directly to the parent `Lesson` entity.

---

## 2. Requirements & Acceptance Criteria Conformance

| Criterion | Contract Requirement | Implementation Mechanism | Verification Result |
| :--- | :--- | :--- | :---: |
| **AC-3.4.1** | Slide count bounded between 3 and 8 slides | Bounded in `script_generator.py` and validated by `schemas.py` | ✅ PASSED |
| **AC-3.4.2** | Bullet points bounded between 2 and 5 points | Enforced in `SlideSpec.bullet_points` Pydantic validator | ✅ PASSED |
| **AC-3.4.3** | Narration script minimum length $\ge 20$ characters | Validated by `SlideSpec.narration_script` | ✅ PASSED |
| **AC-3.4.4** | Total estimated duration $\le 420$ seconds (7 min) | Calculated from speech rate and validated by Contract 3 schema | ✅ PASSED |
| **AC-3.4.5** | Every slide links to source chunk provenance | `source_chunk_id` UUID recorded on every slide | ✅ PASSED |
| **AC-3.4.6** | Programmatic 1080p (1920x1080) slide rendering | `SlideRenderer` generates 1920x1080 PNGs via Pillow | ✅ PASSED |
| **AC-3.4.7** | Synchronized `.srt` and `.vtt` subtitles | `CaptionSynchronizer` outputs valid SubRip and WebVTT files | ✅ PASSED |
| **AC-3.4.8** | Relational persistence into `video_assets` | `VideoAssetPersistenceService` commits status `COMPLETED` | ✅ PASSED |

---

## 3. Technology Stack & Approach

| Component | Selected Technology | Technical Justification | Operating Cost |
| :--- | :--- | :--- | :--- |
| **Data Contracts** | Pydantic v2 (`pydantic.BaseModel`) | Enforces Contract 3 schema boundaries, slide limits, and duration constraints. | **$0.00** |
| **Slide Rendering** | Python Pillow (`PIL.Image`, `ImageDraw`) | Lightweight, zero browser runtime overhead, deterministic 1920x1080 rasterization. | **$0.00** |
| **Neural TTS** | `edge-tts` + Offline Fallback | Natural neural speech cadences with guaranteed offline test reproducibility. | **$0.00** |
| **Subtitles** | Custom Synchronizer (`.srt`, `.vtt`) | Millisecond-accurate phrase segmentation with monotonic timing advancement. | **$0.00** |
| **Assembly** | FFmpeg CLI Subprocess + Manifest Bundler | H.264/AAC encoding with graceful fallback to multimedia presentation manifests. | **$0.00** |
| **Database** | SQLAlchemy 2.0 ORM | Maps generated video metadata into the `video_assets` table. | **$0.00** |

---

## 4. Implementation Structure (`AI_Modules/Video_Pipeline/`)

```
AI_Modules/Video_Pipeline/
├── __init__.py               # Package exports (VideoGenerationPipeline, renderers, synthesizers)
├── schemas.py                # Pydantic v2 schemas strictly fulfilling WBS 2.1 Contract 3
├── script_generator.py       # Storyboard and narration script generator (Contract 3)
├── slide_renderer.py         # 1080p Pillow rasterization engine (dark slate, cards, citations)
├── audio_synthesizer.py      # edge-tts neural voiceover engine with offline fallback
├── caption_synchronizer.py   # Word/phrase timing parser generating .srt and .vtt files
├── video_assembler.py        # Video compilation & multimedia manifest packager
├── persistence.py            # Relational database persistence into video_assets table
├── pipeline.py               # Master VideoGenerationPipeline orchestrator
└── tests/
    ├── __init__.py
    ├── conftest.py           # Synthetic lesson fixtures & in-memory SQLite DB
    ├── test_schemas.py       # Contract 3 validation tests
    ├── test_script_generator.py # Storyboard & script generation tests
    ├── test_slide_renderer.py   # 1080p image rasterization tests
    ├── test_caption_sync.py     # Subtitle synchronization tests
    └── test_video_pipeline.py   # End-to-end integration & persistence tests
```

---

## 5. Architectural Detail & Core Algorithms

### 5.1 Contract 3 Pydantic Schemas (`schemas.py`)
- `SlideSpec`:
  - `slide_number`: Integer $\ge 1$.
  - `header`: String ($3 \le \text{length} \le 200$).
  - `bullet_points`: Array of strings ($2 \le \text{items} \le 5$).
  - `visual_cue`: Visual directive string (e.g., `"Thematic Agenda Card"`, `"Architectural Flow Diagram"`).
  - `narration_script`: Voiceover string ($\ge 20$ characters).
  - `source_chunk_id`: UUID reference to originating source chunk.
- `LessonVideoAssetOutput`:
  - `lesson_id`: UUID.
  - `total_estimated_seconds`: Integer in $[10, 420]$.
  - `slides`: Array of `SlideSpec` ($3 \le \text{items} \le 8$).

### 5.2 Slide Rasterization Pipeline (`slide_renderer.py`)
- Canvas: 1920x1080 (16:9 widescreen), Deep Slate background (`#0F172A`).
- Top Stripe: Primary Brand Blue (`#2563EB`) accent bar.
- Badge: `SLIDE X OF Y • EDUVANCE AI` in Cyan (`#38BDF8`).
- Content Card: Rounded card (`#1E293B`) with bullet indicators and word-wrapped typography.
- Visual Cue Box: Dark Navy box (`#0D203D`) with cyan/blue accents detailing visual directives.
- Provenance Footer: Explicit reference string (`Source Provenance: Chunk {id} | Graduation Project 2026`).

### 5.3 Speech Synthesis & Caption Alignment (`audio_synthesizer.py`, `caption_synchronizer.py`)
- **Speech Rate:** Configured to a natural pedagogical cadence of 140 words per minute (~2.33 words/second).
- **Phrase Segmentation:** Narration scripts are split into 6–12 word phrases.
- **Inter-Slide Pacing:** A 500 ms buffer is inserted between slide transitions to prevent auditory crowding.
- **Formats Emitted:** Standard SubRip (`.srt`) and WebVTT (`.vtt`) files with zero backwards timing drift.

### 5.4 Database Persistence (`persistence.py`)
- Creates or updates `VideoAsset` records in `video_assets`:
  - `lesson_id`: Foreign key to `lessons.id`.
  - `script_json`: Complete Contract 3 JSON payload.
  - `slide_deck_json`: Array of slide metadata (image paths, dimensions).
  - `audio_path`: Path to synthesized audio track.
  - `srt_subtitles_path`: Path to generated `.srt` subtitle file.
  - `duration_seconds`: Total runtime in seconds.
  - `generation_status`: Marked as `"COMPLETED"`.

---

## 6. Automated Test Suite & Empirical Evidence

### Video Pipeline Test Suite (20 Tests, 100% Passing in 0.63s):
```
AI_Modules/Video_Pipeline/tests/test_caption_sync.py::test_format_timestamp PASSED [  5%]
AI_Modules/Video_Pipeline/tests/test_caption_sync.py::test_generate_srt_and_vtt_subtitles PASSED [ 10%]
AI_Modules/Video_Pipeline/tests/test_caption_sync.py::test_cumulative_timing_monotonicity PASSED [ 15%]
AI_Modules/Video_Pipeline/tests/test_schemas.py::test_slide_spec_valid PASSED [ 20%]
AI_Modules/Video_Pipeline/tests/test_schemas.py::test_slide_spec_bullet_points_bounds PASSED [ 25%]
AI_Modules/Video_Pipeline/tests/test_schemas.py::test_slide_spec_narration_script_min_length PASSED [ 30%]
AI_Modules/Video_Pipeline/tests/test_schemas.py::test_lesson_video_asset_output_valid PASSED [ 35%]
AI_Modules/Video_Pipeline/tests/test_schemas.py::test_lesson_video_asset_output_slides_bounds PASSED [ 40%]
AI_Modules/Video_Pipeline/tests/test_schemas.py::test_lesson_video_asset_output_max_duration PASSED [ 45%]
AI_Modules/Video_Pipeline/tests/test_schemas.py::test_rendered_slide_and_subtitle_schemas PASSED [ 50%]
AI_Modules/Video_Pipeline/tests/test_script_generator.py::test_generate_lesson_script_satisfies_contract_3 PASSED [ 55%]
AI_Modules/Video_Pipeline/tests/test_script_generator.py::test_first_and_final_slide_conventions PASSED [ 60%]
AI_Modules/Video_Pipeline/tests/test_script_generator.py::test_custom_slide_count_bounds PASSED [ 65%]
AI_Modules/Video_Pipeline/tests/test_script_generator.py::test_script_generator_rejects_empty_chunks PASSED [ 70%]
AI_Modules/Video_Pipeline/tests/test_slide_renderer.py::test_render_single_slide PASSED [ 75%]
AI_Modules/Video_Pipeline/tests/test_slide_renderer.py::test_render_slide_deck PASSED [ 80%]
AI_Modules/Video_Pipeline/tests/test_slide_renderer.py::test_slide_renderer_text_wrapping PASSED [ 85%]
AI_Modules/Video_Pipeline/tests/test_video_pipeline.py::test_video_pipeline_end_to_end_persists_to_database[asyncio] PASSED [ 90%]
AI_Modules/Video_Pipeline/tests/test_video_pipeline.py::test_audio_synthesizer_offline_mock[asyncio] PASSED [ 95%]
AI_Modules/Video_Pipeline/tests/test_video_pipeline.py::test_video_assembler_without_ffmpeg PASSED [100%]

============================= 20 passed in 0.63s ==============================
```

### Full Repository Regression Status:
- Backend & Database Foundation (WBS 3.1): **71 tests passed**
- Content Extraction & Ingestion (WBS 3.2): **27 tests passed**
- Course Designer Agent (WBS 3.3): **18 tests passed**
- Video Generation Pipeline (WBS 3.4): **20 tests passed**
- **Cumulative Total:** **136 passed, 1 skipped (live GCS credentials), 0 failures**

---

## 7. Downstream Dependencies Enabled

* **Member 4 (WBS 3.6 / UI):** The Lesson Player component can directly render generated 1080p slide images, stream master audio, and display synchronized `.vtt` / `.srt` captions.
* **Member 1 (WBS 4.1 - Workflow Controller):** Can trigger `VideoGenerationPipeline.process_lesson_video()` during the `GENERATING_ASSETS` course phase.
* **Member 3 (WBS 3.5 - Assessment Engine):** Quizzes and exercises align directly with the instructional content and concepts covered in the generated video slides.
