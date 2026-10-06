# Eduvance AI

## WBS 1.3 — Related Systems and Research Review


### Member Information

**Member Name:** Member 2 
**Role:** Content and RAG Engineer
**Assigned Work Package (WBS):** WBS 1.3 Review related systems/research + comparison table  
**Task Name:** Related Systems and Research Review
**Week:** Week 2–3

---

### Status
Final draft for acceptance

---

## 1. Purpose

The purpose of this review is to position Eduvance AI within current research and existing AI-supported learning systems.

The review focuses on technologies directly related to the approved Eduvance scope:

- AI-assisted tutoring
- Retrieval-Augmented Generation and source grounding
- AI-generated learning content
- Assessment generation
- Personalized learning
- Educational multimedia
- Learner progress support
- Integrated AI learning platforms

The review is intended to identify prior work, relevant limitations, overlapping capabilities, and a defensible research position for Eduvance.

It does not redefine the approved project scope.

---

# 2. Related Academic Research

## 2.1 Large Language Models in Education

Large Language Models are increasingly used in educational applications, particularly intelligent tutoring.

A systematic review covering 88 empirical studies identified Intelligent Tutoring Systems as one of the most prominent applications of LLMs in education. Reported benefits included support for academic performance, engagement, accessibility, and learning activities, while recurring concerns included technical reliability, over-reliance, fairness, and privacy. ([sciencedirect.com](https://www.sciencedirect.com/science/article/pii/S2666920X25001699?utm_source=chatgpt.com))

This supports the relevance of Eduvance's AI tutor while also demonstrating that AI-generated educational responses cannot simply be assumed to be correct.

For Eduvance, tutor quality therefore needs to be considered in terms of:

- factual correctness;
- source support;
- grounding;
- unsupported claims; and
- behavior when the source documents do not contain an answer.

This is consistent with the project's planned grounding and abstention evaluation. fileciteturn0file0L235-L254

---

## 2.2 Retrieval-Augmented Generation

Retrieval-Augmented Generation is particularly relevant to Eduvance because the platform is intended to answer questions using the learner's uploaded course documents.

A 2025 systematic survey reviewed 51 studies involving RAG in education. Applications included interactive learning environments, educational-content generation, assessment, and educational ecosystems. The review also identified continuing challenges such as hallucination, incomplete or outdated knowledge, computational requirements, and multimodal limitations. ([sciencedirect.com](https://www.sciencedirect.com/science/article/pii/S2666920X25000578?utm_source=chatgpt.com))

RAG therefore provides an appropriate technical concept for bounded educational question answering, but its use does not guarantee correctness.

For Eduvance, the research implication is that a successful tutor should demonstrate:

- retrieval of relevant evidence;
- consistency between evidence and generated answers;
- source traceability;
- reduced unsupported generation; and
- appropriate handling of unanswered questions.

This supports the Project Plan's emphasis on traceability from generated outputs back to supplied sources. fileciteturn0file0L35-L44

---

## 2.3 Personalized Learning

AI-supported personalization is well represented in educational research.

A systematic review of 45 higher-education studies found AI being used to tailor content, feedback, instructional methods, and learning experiences. It also emphasized privacy, ethical considerations, teacher preparation, standardized evaluation, and the need for stronger long-term evidence. ([mdpi.com](https://www.mdpi.com/2813-4346/4/2/17?utm_source=chatgpt.com))

A broader review of 125 studies covering multiple educational settings similarly found widespread use of machine learning, recommender systems, intelligent tutoring, and generative AI for personalized learning. ([link.springer.com](https://link.springer.com/article/10.1007/s44163-025-00598-x?utm_source=chatgpt.com))

Eduvance deliberately adopts a narrower approach.

Rather than implementing predictive learner modeling or reinforcement-learning-based sequencing, its baseline personalization uses transparent rules based on observable learner activity and assessment performance.

This makes the recommendations easier to inspect and explain within the graduation-project scope.

---

## 2.4 Assessment Generation

Generative AI can support question generation and assessment creation, but assessment outputs require validation.

The wider literature reports risks involving incorrect answer keys, unsuitable questions, hallucinated information, unclear wording, and misalignment with intended learning goals.

For Eduvance, generated assessments should therefore be linked to course content and lesson objectives and later evaluated for characteristics such as:

- relevance;
- correctness;
- answerability;
- clarity;
- usefulness; and
- alignment with learning objectives.

The final evaluation protocol remains part of WBS 1.4 rather than WBS 1.3.

---

## 2.5 AI Learning Tools and Evaluation

A 2025 systematic review of AI-based learning tools in higher education found growing use of AI for personalization, feedback, and flexible learning while also noting that consistent design and evaluation practices are still developing. ([link.springer.com](https://link.springer.com/article/10.1186/s41239-025-00540-2?utm_source=chatgpt.com))

This supports evaluating Eduvance across multiple dimensions rather than using a single success criterion.

Relevant categories include:

- output quality;
- grounding;
- reliability;
- usability;
- workflow completion;
- recommendation transparency;
- latency; and
- operating constraints.

---

# 3. Existing Systems

Four systems were selected for direct comparison:

1. Google NotebookLM
2. Coursera
3. Khanmigo / Khan Academy
4. Docebo

These systems were selected because they overlap with different parts of the Eduvance workflow.

---

# 4. NotebookLM

Google NotebookLM demonstrates strong overlap with the source-grounding side of Eduvance.

Google describes NotebookLM as grounding responses in the user's supplied sources and providing citations. Supported sources include PDFs, Google documents, websites, audio, and other materials. ([blog.google](https://blog.google/innovation-and-ai/products/notebooklm-audio-video-sources/?utm_source=chatgpt.com))

NotebookLM also supports source-derived multimedia. Audio Overviews transform uploaded sources into AI-generated discussions, while newer functionality includes Video Overviews, slide decks, and other generated representations of supplied information. ([blog.google](https://blog.google/innovation-and-ai/products/notebooklm-audio-overviews/?utm_source=chatgpt.com))

### Relevance to Eduvance

NotebookLM demonstrates that the following should not be presented as individually novel:

- uploaded-source interaction;
- source-grounded answers;
- citations;
- AI-generated study materials;
- generated multimedia.

Eduvance therefore needs to distinguish itself through the specific integration of these ideas with course structuring, assessment, progress tracking, revision rules, and the Project Mentor workflow.

---

# 5. Coursera

Coursera provides significant overlap with both AI tutoring and AI-assisted course creation.

Coursera Coach provides interactive assistance embedded in course learning. Official documentation describes explanations, summaries, practice questions, feedback, and assistance anchored in Coursera's expert learning content. ([coursera.org](https://www.coursera.org/explore/coach/?trk=article-ssr-frontend-pulse_little-text-block&utm_source=chatgpt.com))

Coursera Course Builder supports AI-assisted course authoring. It can auto-generate course outlines, descriptions, learning objectives, and editable assessment questions while incorporating organization-specific materials and Coursera content. ([coursera.org](https://www.coursera.org/business/course-builder?utm_source=chatgpt.com))

### Relevance to Eduvance

Coursera demonstrates existing combinations of:

- AI course authoring;
- learning-objective generation;
- assessment generation;
- AI tutoring;
- structured learning environments.

Eduvance therefore should not claim novelty based solely on combining course creation with AI tutoring and assessment.

Its narrower research focus remains transformation of bounded supplied documents into a source-traceable end-to-end learning workflow.

---

# 6. Khanmigo / Khan Academy

Khanmigo provides a strong comparison for pedagogical tutoring and educational support tools.

Khan Academy documents teacher tools for:

- lesson planning;
- assignment recommendations;
- exit tickets;
- learning objectives;
- class performance snapshots;
- multiple-choice assessments;
- question generation; and
- rubric generation. ([blog.khanacademy.org](https://blog.khanacademy.org/khanmigo-features/?utm_source=chatgpt.com))

Its lesson-planning tools can also produce student-facing slide decks based on generated plans. ([khanacademy.org](https://www.khanacademy.org/khan-for-educators/khanmigo-teacher-tools?utm_source=chatgpt.com))

Khan Academy continues to extend its targeted AI practice functionality, including teacher-controlled AI-generated practice introduced in 2026. ([blog.khanacademy.org](https://blog.khanacademy.org/new-ai-tools-bring-interactive-diagrams-and-targeted-practice-thanks-to-khan-academys-partnership-with-google-org/?utm_source=chatgpt.com))

### Relevance to Eduvance

Khanmigo shows that the following capabilities already exist in current educational AI systems:

- tutoring;
- learning-objective generation;
- assessment generation;
- performance monitoring;
- suggested learner activities;
- lesson planning.

The Eduvance contribution therefore cannot rely on these features being individually new.

---

# 7. Docebo

Docebo provides a broader enterprise-learning comparison.

Its platform combines LMS functionality with AI-supported course creation, learning delivery, analytics, recommendations, and AI assistance.

Compared with Eduvance, Docebo represents a much broader commercial environment rather than a bounded academic prototype.

### Relevance to Eduvance

Docebo demonstrates that integrated AI-supported learning platforms already exist commercially.

Consequently, Eduvance should not claim that integrating multiple AI learning capabilities into one platform is unprecedented.

Instead, Eduvance can focus on implementing and evaluating its specific bounded workflow and maintaining explicit relationships between uploaded training sources and generated learning artifacts.

---

# 8. Related-Systems Comparison

| Capability | NotebookLM | Coursera | Khanmigo / Khan Academy | Docebo | Eduvance Target |
|---|---|---|---|---|---|
| User-supplied training documents | Yes | Partial | Partial | Yes | **Yes** |
| Source-grounded Q&A | Yes | Yes | Content-bounded | Yes | **Yes** |
| Explicit source citations | Yes | Not confirmed | Not confirmed | Not confirmed | **Yes** |
| Course-structure generation | Partial | Yes | Partial | Yes | **Yes** |
| Learning-objective generation | Not confirmed | Yes | Yes | Not confirmed | **Yes** |
| Learning-content generation | Yes | Yes | Yes | Yes | **Yes** |
| Generated multimedia | Yes | Limited/varies | Partial | Yes | **Yes** |
| AI tutoring | Yes | Yes | Yes | Yes | **Yes** |
| Assessment generation | Yes/related | Yes | Yes | Yes/related | **Yes** |
| Automatic objective scoring | Not confirmed | Yes | Platform-supported | Platform-supported | **Yes** |
| Progress tracking | Not a core documented function | Yes | Yes | Yes | **Yes** |
| Personalized recommendations | Partial | Partial | Partial | Yes | **Yes — transparent rules** |
| Practical-project recommendation tied to completed concepts | Not confirmed | Not confirmed | Not confirmed | Not confirmed | **Yes** |
| Source-traceable end-to-end document → learning workflow | Partial | Partial | Partial | Partial | **Targeted project workflow** |

**Important:** “Not confirmed” means that the feature was not established from the reviewed official documentation. It does not prove that the system lacks the capability.

---

# 9. Key Comparison Findings

The comparison shows substantial overlap between Eduvance and existing systems.

### NotebookLM

Strong overlap:

**Sources → grounding → citations → generated learning material → multimedia**

### Coursera

Strong overlap:

**Course authoring → objectives → tutoring → practice → assessment**

### Khanmigo

Strong overlap:

**Tutoring → lesson planning → objectives → assessment → learner-performance support**

### Docebo

Strong overlap:

**Learning authoring → delivery → AI assistance → personalization → analytics**

These findings mean Eduvance must avoid claiming novelty based solely on any one of those features.

---

# 10. Research Challenges Identified

The literature consistently identifies several challenges relevant to Eduvance:

| Challenge | Eduvance Component Affected |
|---|---|
| Hallucination | Tutor, generated lessons, assessments |
| Retrieval quality | RAG tutor |
| Incomplete source material | Tutor and course generation |
| Incorrect generated assessment items | Assessment Agent |
| Over-reliance on AI | Tutor interaction |
| Privacy | Uploaded documents and learner data |
| Explainability | Personalization |
| Inconsistent evaluation | Entire prototype |
| Computational/service limitations | Free-only project constraint |
| Unsupported claims of learning benefit | Project evaluation/reporting |

RAG research specifically warns that retrieval augmentation reduces some limitations but does not eliminate hallucination or source-quality problems. ([sciencedirect.com](https://www.sciencedirect.com/science/article/pii/S2666920X25000578?utm_source=chatgpt.com))

Similarly, broader LLM-in-education research identifies reliability, over-reliance, privacy, and fairness as continuing concerns. ([sciencedirect.com](https://www.sciencedirect.com/science/article/pii/S2666920X25001699?utm_source=chatgpt.com))

---

# 11. Eduvance Research Position

Based on the reviewed research and systems, Eduvance should not be described as:

- the first AI learning platform;
- the first RAG educational tutor;
- the first system to generate courses using AI;
- the first platform to generate AI assessments;
- the first system to personalize learning;
- the first platform to transform documents into educational assets.

The evidence does not support these statements.

A defensible positioning is:

**Eduvance AI investigates the design, integration, and evaluation of a bounded AI-assisted learning workflow that transforms supplied training documents into a structured course and connects source-traceable learning materials, generated lesson media, grounded tutoring, assessments, learner-progress information, explainable revision recommendations, and a practical project within one prototype.**

The project emphasis is therefore:

**Integration + Source Traceability + Bounded Orchestration + Explainable Personalization + Systematic Evaluation**

This is consistent with the Project Plan's stated academic contribution. fileciteturn0file0L35-L44

---

# 12. Research Gap Statement

Existing academic research and commercial platforms demonstrate substantial prior work in tutoring, RAG, course generation, multimedia generation, assessment, learner analytics, and personalized learning.

Therefore, the Eduvance research and engineering problem is not the absence of these capabilities individually.

The relevant project investigation is whether these capabilities can be implemented within a controlled end-to-end workflow where:

1. bounded training documents form the principal knowledge source;
2. generated educational materials retain meaningful source relationships;
3. tutor responses are grounded in supplied evidence;
4. assessments are connected to lesson objectives;
5. observable learner events update progress;
6. transparent rules provide explainable revision recommendations;
7. completed learning topics can inform a bounded practical-project recommendation; and
8. the complete workflow can be systematically evaluated for quality, grounding, usability, reliability, latency, and operating constraints.

This statement defines Eduvance's project investigation without claiming that no similar system exists elsewhere.

---

# 13. Implications for Eduvance

The related-work review produces several requirements for later project stages.

### Grounding must be evaluated

RAG alone is insufficient evidence of tutor reliability.

### Generated content must be validated

Lessons, assessments, and other generated outputs should not automatically be considered correct.

### Personalization should remain explainable

The approved rule-based baseline provides a clearer and more testable graduation-project scope than opaque advanced adaptive mechanisms.

### Claims must remain evidence-based

Existing research may demonstrate benefits of AI-supported education generally, but those results cannot be transferred directly to Eduvance.

Eduvance must produce its own evaluation evidence before making claims about its performance.

---

# 14. WBS 1.3 Acceptance Criteria

WBS 1.3 is complete when:

- relevant academic research areas have been reviewed;
- major existing systems have been identified;
- four selected systems have been compared against Eduvance;
- overlaps with existing work have been documented;
- inappropriate novelty claims have been eliminated;
- a defensible research-position statement has been established;
- a related-systems comparison table has been produced;
- identified limitations have been linked to Eduvance;
- the review remains within the approved project scope; and
- the output establishes sufficient research context for WBS 1.4.

---

# 15. Handoff to WBS 1.4

The related-work review establishes the evidence base needed to formalize Eduvance's evaluation questions.

WBS 1.4 can now define:

- research/evaluation questions;
- representative datasets;
- experimental cases;
- baselines;
- metrics;
- quality rubrics;
- quantitative targets; and
- recording procedures.

The WBS 1.3 literature findings particularly support evaluation of:

**grounding, correctness, unsupported generation, assessment quality, workflow reliability, explainability, usability, latency, and operating constraints.**

No WBS 1.4 evaluation design is finalized within this document.

---

## 16. WBS 1.3 Status

**Task:** Review related systems/research and create comparison table  
**Owner:** Member 1 under the WBS 1–2 ownership override  
**Dependency:** Defined research scope from WBS 1.2  
**Dependency status:** Satisfied  
**Primary comparison systems:** NotebookLM, Coursera, Khanmigo, Docebo  
**Output:** Related-work review + comparison table + research-gap positioning  
**Status:** Pending final member acceptance