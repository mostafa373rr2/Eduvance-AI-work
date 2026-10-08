# Eduvance AI

> **An Agentic AI Platform for Transforming Training Materials into Personalized Learning Experiences**

Eduvance AI is an undergraduate graduation project that ingests bounded training materials (text-based PDFs $\le$ 50 pages) and deterministically transforms them into a structured, personalized, and source-grounded learning pathway featuring slide-based video lessons, interactive RAG tutoring with source citations, deterministic assessment grading, and milestone-driven capstone projects.

---

## 1. System Architecture & Workflow

The platform operates via a central workflow controller coordinating specialized agents through strongly typed data contracts:

```text
Upload Documents (PDFs <= 50 pages)
        │
        ▼
Content Agent (Text extraction, chunking, concept mapping, and page anchors)
        │
        ▼
Course Designer Agent (Curriculum structure: ~3 modules and ~6 lessons with objectives)
        │
        ▼
[Course Structure Review & Approval]
        │
        ▼
Video Pipeline Agent (Slide rendering, neural narration via edge-tts, WebVTT captions)
        │
        ▼
Learning Experience & Tutoring (Lesson player + source-grounded RAG tutor with abstention)
        │
        ▼
Assessment Agent (Objective MCQs, True/False questions, and practical rubrics)
        │
        ▼
Progress Component (Deterministic mastery scoring, audit logging, and revision rules)
        │
        ▼
Project Mentor Agent (Capstone practical project brief, milestones, and grading rubric)
```

---

## 2. Repository Structure

The repository is organized into two core areas following the **GitHub Workflow Strategy**:

```text
Eduvance-AI-work/
│
├── Backend/                 # FastAPI REST API, authentication, routers, services, tests
│   ├── core/                # Application configuration & Pydantic settings
│   ├── services/            # Storage and file management services
│   ├── scripts/             # Verification and maintenance utilities
│   ├── tests/               # Automated test suite (72 test cases)
│   ├── requirements.txt     # Backend dependency specification
│   ├── constraints-windows-py313.txt # Exact reproducible package snapshot
│   └── .env.example         # Environment template
│
├── Database/                # Relational persistence & migrations
│   ├── models/              # SQLAlchemy 2.0 ORM models (14 entities / 16 tables)
│   ├── migrations/          # Alembic migrations (revision 0001)
│   └── session.py           # Database engine & sessionmaker
│
├── AI_Modules/              # Agentic AI processing engines
│   ├── Extraction/          # Document text extraction & chunking (Member 2)
│   ├── CourseDesign/        # Syllabus & concept sequencing (Member 2)
│   ├── Video_Pipeline/      # Slide generation & audio synthesis (Member 3)
│   ├── Tutor_RAG/           # Grounded RAG retrieval & Q&A (Member 2)
│   └── Assessment/          # Quiz & rubric generators (Member 3)
│
├── Frontend/                # User interface client (Member 4)
│
├── Documentation/           # System design diagrams, specifications & schemas
│
└── members/                 # Individual team member task records & milestones
    ├── member_1/            # Project Manager & Backend/Deployment Engineer
    ├── member_2/            # Content and RAG Engineer
    ├── member_3/            # Generative Media and Assessment Engineer
    └── member_4/            # Frontend and User Experience Engineer
```

---

## 3. Getting Started (Backend Local Setup)

### Prerequisites
* **Python 3.10+** (Tested on Python 3.13.5 Windows x64)
* **Git**

### Installation

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/mostafa373rr2/Eduvance-AI-work.git
   cd Eduvance-AI-work
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   pip install --upgrade pip
   pip install -r Backend/requirements.txt
   ```

4. **Configure environment variables:**
   ```powershell
   Copy-Item Backend/.env.example .env
   ```

5. **Run database migrations:**
   ```powershell
   alembic upgrade head
   ```

6. **Run the automated test suite:**
   ```powershell
   python -m pytest Backend/tests -v
   ```
   *(Expected result: 71 passed, 1 skipped)*

7. **Launch the development server:**
   ```powershell
   python -m uvicorn Backend.main:app --reload --port 8000
   ```
   * Interactive API Documentation (Swagger UI): `http://localhost:8000/docs`
   * Health Check: `http://localhost:8000/health/live`
   * Readiness Check: `http://localhost:8000/health/ready`

---

## 4. Team Structure & Work Breakdown Status

| Member | Role | Completed Milestones | Active Milestone |
| :--- | :--- | :--- | :--- |
| **Member 1** | Project Manager & Backend Engineer | WBS 1.1, 1.2, 2.1, **3.1** | **WBS 4.1 (Workflow Controller Engine)** |
| **Member 2** | Content & RAG Engineer | WBS 1.3, 1.4 | **WBS 3.2 (Document Extraction & Chunking)** |
| **Member 3** | Generative Media & Assessment Engineer | WBS 2.3 (Feasibility Study) | **WBS 4.3 (Video Pipeline Implementation)** |
| **Member 4** | Frontend & UX Engineer | WBS 2.2 (UI/UX Wireframes) | **WBS 3.4 (Upload & Review Screens)** |

Detailed task records, experiments, benchmarks, and acceptance criteria are documented under [`members/`](members/).