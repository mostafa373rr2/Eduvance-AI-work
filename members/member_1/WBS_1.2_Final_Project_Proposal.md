# Eduvance AI

## An Agentic AI Platform for Transforming Training Materials into Personalized Learning Experiences

### Member Information

**Member Name:** Member 1 
** ALI **


---

### Graduation Project Proposal

**Project:** Eduvance AI  
**Primary Language:** English  
**Team Size:** Four Students  
**Internal Completion Target:** 30 November 2026  
**AI-Service Budget:** Free-only  
**Supervisor Approval:** Confirmed  
**Representative Dataset:** To be selected in a subsequent project activity

---

## 1. Project Overview

Eduvance AI is a graduation project focused on designing, implementing, and evaluating an integrated AI-assisted learning platform that transforms a bounded collection of training documents into a structured and personalized learning experience.

The platform connects several learning activities within a single controlled workflow. Uploaded training materials are analyzed and organized into a course structure, transformed into lesson resources, used as the knowledge source for an AI tutor, connected to assessments, and used to support progress tracking, revision recommendations, and practical project suggestions.

The project focuses on the integration, orchestration, traceability, personalization, and evaluation of existing AI capabilities rather than the development or training of a new foundation model.

---

## 2. Problem Statement

Training materials are frequently distributed across lengthy documents, slides, and unstructured notes. Learners using these resources must manually identify important concepts, organize the material into a meaningful learning sequence, recognize prerequisite knowledge, find suitable explanations, and determine whether they have adequately understood the content.

Generative AI technologies can support individual activities such as content generation, question answering, summarization, and assessment generation. However, the Eduvance AI project addresses the broader challenge of integrating these capabilities into a bounded learning workflow in which generated learning materials remain connected and traceable to the uploaded source documents.

Eduvance AI therefore proposes an integrated platform that transforms uploaded training materials into an organized learning experience containing structured lessons, short educational videos, source-grounded tutoring, assessments, progress monitoring, revision recommendations, and an appropriate practical project.

---

## 3. Main Objective

The main objective of Eduvance AI is to design, implement, and evaluate an integrated AI-assisted learning platform that converts a bounded collection of training documents into a personalized learning experience.

---

## 4. Specific Objectives

Eduvance AI aims to:

1. Extract and organize concepts from uploaded training documents.
2. Generate a structured course containing modules, lessons, prerequisites, and learning objectives.
3. Produce short educational videos using generated scripts, slides, narration, and captions.
4. Provide an AI tutor that answers learner questions using the uploaded materials and provides relevant source references.
5. Generate assessments and provide appropriate feedback.
6. Track lesson completion and assessment performance to recommend appropriate revision activities.
7. Suggest a practical project aligned with the topics completed by the learner.

---

## 5. Proposed System Concept

Eduvance AI will operate as an integrated learning-content workflow rather than as a collection of unrelated AI features.

The proposal-level workflow is:

**Upload Documents → Analyze Content → Generate and Approve Course Structure → Generate Lesson Assets → Learn and Ask Questions → Complete Assessments → Update Progress → Receive Revision and Project Recommendations**

Training documents first enter the platform and are processed to identify relevant concepts and source information.

The extracted information supports generation of a structured course containing modules, lessons, learning objectives, and prerequisite relationships.

After the course structure has been reviewed, lesson resources can be produced. These resources include short educational videos based on generated scripts, slides, narration, and captions.

Learners can interact with a course-specific AI tutor while studying. The tutor uses relevant information retrieved from the uploaded materials when generating its answers and provides source references.

Learners subsequently complete assessments associated with lesson objectives. Assessment results and observable learning activities are recorded and used to update progress information.

Transparent personalization rules use these learning events to recommend lessons or concepts for revision.

When appropriate, the platform can also recommend a bounded practical project aligned with concepts the learner has completed.

---

## 6. Project Scope

### 6.1 Document Input

The initial platform will support text-based PDF documents.

A course will initially support approximately three uploaded files and a maximum of approximately fifty pages.

Scanned documents requiring OCR, presentation files, and additional document formats are deferred from the baseline implementation.

### 6.2 Content Understanding

The platform will identify and organize concepts contained in uploaded materials and support difficulty estimation and prerequisite identification.

Advanced knowledge-graph functionality is outside the baseline scope.

### 6.3 Course Generation

The platform will generate an initial course structure containing approximately three modules and six lessons.

The structure will contain learning objectives and support review and editing.

### 6.4 Educational Video Generation

The platform will produce short slide-based educational videos associated with lesson content.

The baseline video workflow will contain generated scripts, slides, narration, and captions.

Advanced animation, avatars, and richer visual-generation capabilities are not required for the baseline system.

### 6.5 AI Tutor

The platform will provide a course-specific Retrieval-Augmented Generation (RAG) tutoring experience.

Tutor responses will use uploaded course materials as their knowledge source and provide references to relevant source material.

Voice interaction and unrestricted external web research are outside the baseline scope.

### 6.6 Assessment

The platform will support multiple-choice and true/false questions with automatic scoring.

Practical exercises may use rubric-based feedback.

Automatic code execution and fully automated programming-project grading are outside the baseline scope.

### 6.7 Progress Tracking

The platform will track observable learning activities including lesson completion and quiz performance and maintain concept-level performance indicators.

Completion activity will not automatically be interpreted as evidence of mastery. For example, watching a lesson video can indicate completion but does not by itself prove that the learner has mastered its concepts.

Predictive learner modeling is outside the baseline scope.

### 6.8 Personalization

Personalization will use transparent rules based on observable learning activity and assessment performance.

These rules will recommend lessons or concepts that should be reviewed and provide understandable reasons for the recommendations.

Advanced reinforcement learning and complex adaptive sequencing are outside the baseline scope.

### 6.9 Project Mentor

The platform will recommend a bounded practical project aligned with completed course concepts.

A recommendation may contain a project brief, implementation steps, and an assessment rubric.

Autonomous project supervision is outside the baseline scope.

### 6.10 Deployment

The project will target a hosted demonstration environment with basic user accounts and user-data isolation.

Enterprise-scale deployment infrastructure is outside the baseline project requirements.

---

## 7. Project Priorities

### P0 — Foundation

P0 establishes the minimum technical foundation of the system and includes:

- Document upload
- Content extraction
- Course structure generation
- Data storage
- Basic user interface

### P1 — Required Learning Experience

P1 provides the required learner-facing AI capabilities and includes:

- Source-grounded tutor
- Simple educational videos
- Assessments
- Progress tracking
- Basic practical-project mentor

P0 and P1 together form the required project baseline.

### P2 — Optional Enhancements

P2 may include:

- Additional languages
- Richer visual generation
- Broader document-format support
- Advanced personalization

P2 functionality will only be considered after the P0 and P1 baseline has passed integration testing.

---

## 8. Expected Project Outputs

The principal project output will be a functional and evaluated Eduvance AI prototype demonstrating the required end-to-end learning workflow.

Expected technical outputs include document processing, source-linked content information, generated course structures, lesson resources, short educational videos, a source-grounded AI tutor, assessments, progress indicators, revision recommendations, practical-project recommendations, an integrated learner interface, and a hosted demonstration environment.

Expected academic and project-management outputs include the project report, architecture and workflow documentation, evaluation evidence, experimental results, documented limitations, user and developer guidance, demonstration materials, and a clear statement identifying individual and team contributions.

---

## 9. Academic Contribution

The academic contribution of Eduvance AI will focus on the design, integration, orchestration, traceability, personalization, and evaluation of an AI-assisted learning workflow.

### Integrated Workflow

The project will investigate how content understanding, course generation, educational media generation, source-grounded tutoring, assessment, progress tracking, and practical-project recommendations can operate within one bounded learning platform.

### Source Traceability

Generated learning experiences should maintain appropriate relationships with the uploaded training sources.

Traceability is particularly important for generated learning materials and tutor responses because it provides evidence of the relationship between generated information and the supplied training materials.

### Explainable Personalization

Personalization will use observable learner activity and assessment performance.

Revision recommendations should therefore have understandable reasons instead of relying on an opaque adaptive-learning mechanism.

### Systematic Evaluation

The prototype will be evaluated in terms of output quality, grounding and reliability, usability, workflow reliability, operational performance, and relevant operating cost.

Capabilities supplied by external or pre-trained AI models will be explicitly distinguished from contributions produced by the project team.

The project will not claim that the team created a new foundation model.

The project will also not claim improved learning outcomes unless appropriate experimental evidence supports such a conclusion.

---

## 10. Evaluation Intent

Evaluation will determine whether the implemented prototype satisfies the project's defined objectives and baseline requirements.

### Course Quality

Generated lessons will be examined for consistency with source materials, appropriate learning objectives, source traceability, and major factual errors.

### Tutor Grounding

The tutor will be tested with questions whose answers are present in the uploaded materials.

Responses will be evaluated for correctness and source support.

Questions whose answers are absent from the materials will also be tested to determine whether the tutor appropriately abstains or requests clarification instead of producing unsupported answers.

Retrieval-grounded responses will also be compared with responses generated without retrieved context.

### Assessment Quality

Generated assessment items will be reviewed using an established quality rubric. Problematic or rejected items will be recorded and corrected where appropriate.

### Video Quality

Generated lesson videos will be reviewed using a defined quality checklist.

### Personalization

Testing will verify that revision recommendations are triggered by the intended observable learning conditions and that their reasons can be explained.

### Workflow Reliability

Repeated end-to-end executions will evaluate whether the required workflow successfully completes and whether expected retry behavior operates correctly.

### Usability

Representative participants will perform defined core tasks using the integrated prototype. Task completion and usability feedback will be recorded.

### Operational Measurements

Relevant generation time, tutor response latency, and operating costs will be measured and documented.

Evaluation targets established during project planning will remain targets until actual experiments have been conducted.

Usability results will not be interpreted as evidence of improved learning outcomes.

---

## 11. Assumptions and Constraints

The primary content and interface language is English.

The representative training dataset has not yet been selected and will be selected during a subsequent project activity.

The project operates under a free-only AI-service and tooling budget. Subsequent technology decisions must therefore take this constraint into account.

Supervisor approval to proceed with the project has been confirmed.

Text-based PDF documents form the initial input boundary.

The size of the initial course-generation workload is deliberately bounded.

P0 and P1 functionality has priority over P2 enhancements.

The project will rely on existing AI models and technologies rather than train a new foundation model.

External AI technologies may introduce availability, latency, performance, resource, or usage limitations.

AI-generated outputs must be evaluated and must not automatically be assumed to be correct.

No official academic requirements document or formal university deadline will be available, so the confirmed Project Plan serves as the project's primary internal planning baseline.

The team has established 30 November 2026 as the internal target for full project completion.

The existing Project Plan describes a sixteen-week lifecycle. The internal completion target introduces a scheduling constraint that must be reconciled during project scheduling and management. This proposal does not silently redefine the original lifecycle.

---

## 12. Project Boundaries

Eduvance AI is not intended to train a new foundation model.

It is not intended to provide unrestricted general-purpose tutoring outside uploaded course materials.

It does not initially require OCR for scanned documents.

It does not initially require advanced knowledge graphs.

It does not require advanced video avatars or animation.

It does not require voice tutoring or unrestricted web research.

It does not require automatic execution and grading of learner code.

It does not require predictive learner modeling or reinforcement-learning-based personalization.

It does not require autonomous project supervision.

It does not target enterprise-scale deployment infrastructure during the graduation-project baseline.

Optional functionality must not delay completion and evaluation of the P0 and P1 baseline.

---

## 13. WBS 1.2 Acceptance Criteria

WBS 1.2 is considered complete when the approved proposal clearly establishes:

1. The project problem.
2. The main objective.
3. The seven specific objectives.
4. The proposed solution concept and high-level workflow.
5. In-scope functionality.
6. Deferred and out-of-scope functionality.
7. P0, P1, and P2 priorities.
8. Expected project outputs.
9. Intended academic contribution.
10. Evaluation intent.
11. Confirmed assumptions and constraints.
12. Boundaries preventing unsupported claims about AI capabilities or learner outcomes.

The proposal must remain consistent with the approved Project Plan and must not introduce new mandatory functionality without an explicit project decision.

---

## 14. Handoff to Subsequent Tasks

### WBS 1.3 — Related Systems and Research

The approved problem statement, objectives, system concept, scope, and academic-contribution areas establish the research boundary for WBS 1.3.

Related-work research should investigate systems and academic work relevant to the approved Eduvance AI problem without expanding the project's requirements.

### WBS 1.4 — Evaluation Questions, Datasets, and Metrics

The approved objectives and evaluation intent establish the input for WBS 1.4.

WBS 1.4 will formalize evaluation questions, datasets, experimental procedures, metrics, and measurement criteria.

### WBS 2 Boundary

WBS 1.2 does not determine the final software architecture, database design, AI models, frameworks, libraries, APIs, interface design, or video-generation technologies.

Those decisions belong to the relevant feasibility and design tasks and must be handled according to their own dependencies.

---

## 15. Proposal Status

**WBS:** 1.2 — Problem Statement, Objectives, Scope, and Proposal  
**Owner:** Member 1 under the confirmed WBS 1–2 ownership arrangement  
**Proposal baseline:** Complete  
**Supervisor approval:** Confirmed  
**Primary language:** English  
**Dataset:** Selection deferred  
**AI-service budget:** Free-only  
**Internal completion target:** 30 November 2026  
**Status:** Pending final member acceptance
