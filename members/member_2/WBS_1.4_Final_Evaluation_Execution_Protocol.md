# WBS 1.4 — Step 4  
## Final Experiment Execution Protocol, Logging, and Reporting


### Member Information

**Member Name:** Member 2 
**Role:** Content and RAG Engineer
**Assigned Work Package (WBS):** Define evaluation questions, datasets, metrics
**Task Name:** Final Evaluation Execution Protocol
**Week:** Week 2–3



## 1. Purpose

This protocol defines how the Eduvance evaluation will be executed once the prototype reaches the required evaluation stage.

It ensures that:

- datasets are frozen before final testing;
- experiments use controlled configurations;
- failed runs remain recorded;
- human reviews follow the approved rubrics;
- baseline comparisons are fair;
- results are reported without post-hoc threshold changes;
- system configurations can be traced to reported results.

No evaluation results are claimed during WBS 1.4.

---

# 2. Final Evaluation Freeze

Before final experiments begin, the following must be frozen.

### Dataset

**Dataset ID:** `EDU-NIST-CSF-SB-v1`

Freeze:

- original NIST PDF;
- checksum;
- page count;
- extracted source representation;
- document/source IDs.

### Ground Truth

Freeze:

- 40 in-scope tutor questions;
- 40 reference answers;
- supporting source locations;
- 20 source-absent questions;
- expected abstention behavior;
- human reference concept structure.

### Rubrics

Freeze the approved rubrics for:

- course quality;
- tutor correctness and grounding;
- tutor abstention;
- assessment quality;
- video quality;
- personalization behavior.

### Thresholds

Freeze:

- Course: ≥8/10 with critical conditions
- Tutor: ≥36/40 correct and source-supported
- Abstention: ≥18/20
- Assessment: ≥27/30
- Videos: 6/6 pass
- Personalization: 12/12
- End-to-end workflow: ≥18/20
- Usability: ≥80% core tasks without assistance

No threshold may be lowered after seeing final results.

---

# 3. Evaluation Configuration Record

Every final experiment batch must have a unique configuration identifier.

Example:

`EDU-EVAL-CONFIG-001`

The configuration record must contain:

| Field | Required |
|---|---|
| Evaluation date | Yes |
| Dataset ID/version | Yes |
| Application version/commit | Yes |
| Model name | Yes |
| Model version | If available |
| Embedding model | If applicable |
| Prompt version | Yes |
| Retrieval configuration | Yes |
| Chunk configuration | Yes |
| Top-k / retrieval count | Yes |
| Generation parameters | Yes |
| Runtime environment | Yes |
| CPU/GPU information | When relevant |
| Dependency versions | Yes |
| Notes | Yes |

The Project Plan already requires versions, prompts, parameters, and dates to be recorded. fileciteturn0file0L235-L254

---

# 4. Experiment IDs

Every experiment must receive a stable identifier.

Proposed experiment groups:

| ID | Experiment |
|---|---|
| EXP-CQ | Course Quality |
| EXP-TR | Tutor RAG |
| EXP-TN | Tutor No-Retrieval Baseline |
| EXP-TA | Tutor Abstention |
| EXP-AS | Assessment Quality |
| EXP-VD | Video Quality |
| EXP-PR | Personalization Rules |
| EXP-E2E | End-to-End Reliability |
| EXP-US | Usability |
| EXP-OP | Operational Performance |

Individual cases extend the identifier.

Examples:

`EXP-TR-001`  
`EXP-TA-014`  
`EXP-AS-027`  
`EXP-E2E-019`

This gives every reported result a direct link to a raw experimental record.

---

# 5. Recommended Evaluation Execution Order

Final experiments should be executed in the following sequence.

### Phase A — Static Generated Output Review

1. Course quality
2. Assessment quality
3. Video quality

This identifies severe content errors before user testing.

### Phase B — Tutor Evaluation

4. 40 RAG tutor questions
5. Same 40 questions without retrieval
6. 20 source-absent questions

### Phase C — Deterministic Logic

7. 12 personalization scenarios

### Phase D — Integrated System

8. 20 end-to-end workflow runs

### Phase E — Human Interaction

9. Usability testing with approximately 8–12 participants

### Phase F — Operational Analysis

10. Aggregate generation-time, tutor-latency, resource, and cost measurements

Usability testing should occur only after major functional defects identified by earlier tests have been resolved.

---

# 6. Tutor Experiment Log

Each tutor execution should record:

| Field | Example |
|---|---|
| Experiment ID | EXP-TR-001 |
| Question ID | Q-IN-001 |
| Question | Stored text |
| Condition | RAG / No Retrieval |
| Retrieved chunk IDs | IDs |
| Retrieved text references | References |
| Model | Model/version |
| Prompt version | P-03 |
| Raw response | Full output |
| Response latency | ms/sec |
| Error/retry | Value |
| Correct | 0/1 |
| Source-supported | 0/1 |
| Citation correct | 0/1 |
| Unsupported claim | 0/1 |
| Reviewer 1 | Score |
| Reviewer 2 | Score |
| Consensus | Result |
| Notes | Text |

Raw responses must be retained.

Do not store only the final score.

---

# 7. RAG Baseline Fairness Controls

The RAG and no-retrieval experiments must use:

- the same 40 questions;
- the same underlying model;
- the same generation parameters;
- the same scoring rubric;
- the same reference answers;
- the same reviewer process.

The main intended experimental difference is:

**retrieved source context present vs absent.**

Any unavoidable configuration difference must be reported.

---

# 8. Assessment Evaluation Log

Each assessment item should record:

- assessment ID;
- lesson ID;
- learning objective;
- item type;
- generated question;
- generated answer key;
- human reference answer;
- source evidence;
- factual correctness;
- answer-key correctness;
- source alignment;
- objective alignment;
- clarity;
- answerability;
- distractor quality for MCQs;
- reviewer scores;
- final pass/fail;
- error severity;
- correction/regeneration status.

Both original and corrected versions must be preserved if regeneration is required.

---

# 9. Video Evaluation Log

Each generated video record should include:

- video ID;
- lesson ID;
- script version;
- slide version;
- narration version;
- caption version;
- video filename/version;
- render duration;
- generation duration;
- factual-accuracy result;
- source-alignment result;
- script/lesson alignment;
- slide/script consistency;
- visual readability;
- narration quality;
- caption quality;
- rendering quality;
- reviewer results;
- pass/fail;
- defects identified.

A failed first version must not disappear from the experiment history after correction.

---

# 10. Personalization Experiment Log

Each of the 12 scenarios must record:

- scenario ID;
- learner state;
- completed lessons;
- assessment scores;
- concept indicators;
- expected rule;
- expected recommendation;
- expected explanation;
- triggered rule;
- actual recommendation;
- actual explanation;
- rule match;
- explanation match;
- pass/fail.

Because these rules are deterministic, a failed scenario should be classified as an implementation defect.

---

# 11. End-to-End Run Log

Each of the 20 final workflow runs should record the status of:

1. Document upload
2. Validation
3. Extraction
4. Source mapping
5. Course generation
6. Course approval
7. Lesson generation
8. Video generation
9. Tutor readiness
10. Assessment availability
11. Learning event recording
12. Progress update
13. Revision recommendation
14. Project recommendation

Additionally record:

- start time;
- finish time;
- total duration;
- component failures;
- retries;
- recovery outcome;
- final run status.

A run is successful only when all required stages complete without an unresolved failure.

---

# 12. Failure Classification

Failures should be classified into categories such as:

- input validation;
- extraction;
- retrieval;
- model generation;
- parsing/structured output;
- database/storage;
- media generation;
- timeout;
- external dependency;
- integration;
- interface;
- unknown.

This allows the final report to describe not only the success rate but also where failures occurred.

---

# 13. Retry Reporting

Retries must not be hidden.

For each failure:

\[
\text{Retry Count} = \text{number of additional attempts}
\]

Record:

- original failure;
- retry trigger;
- retry count;
- whether recovery succeeded;
- final state.

The Project Plan explicitly includes retries within workflow evaluation. fileciteturn0file0L77-L93

---

# 14. Usability Execution Protocol

Approximately **8–12 participants** will perform the approved core tasks.

Each participant receives the same core task instructions wherever possible.

Record for every task:

- participant anonymous ID;
- task ID;
- start time;
- completion time;
- completed independently;
- completed with assistance;
- failed;
- observed error;
- assistance provided;
- participant comment.

Personal identifying information should not be included in the evaluation dataset unless required and appropriately handled.

---

# 15. Usability Result Reporting

The main quantitative result remains:

\[
\text{Independent Task Completion Rate}
=
\frac{\text{independently completed tasks}}
{\text{attempted tasks}}
\times100
\]

Target:

\[
\geq80\%
\]

Also report:

- task-specific completion rates;
- commonly observed difficulties;
- participant comments/themes;
- assistance frequency.

Because the sample is small and intended for prototype usability testing, results should be described as evidence about this prototype and participant sample rather than generalized to all learners.

---

# 16. Operational Metrics

## Tutor Latency

Record each response latency.

Report:

- number of observations;
- mean;
- median;
- minimum;
- maximum;
- 95th percentile where meaningful.

## Generation Time

For each major generation operation, record:

- course generation time;
- lesson generation time;
- assessment generation time;
- video generation time.

Report mean and median where repeated measurements exist.

## Monetary Cost

Because the project operates under the approved **free-only** budget constraint:

- required API/service monetary cost should remain zero unless scope changes;
- any unexpected paid requirement must be documented as a constraint or failure.

## Compute/Resource Observation

Where feasible, record:

- CPU/GPU environment;
- memory requirements;
- locally observed execution constraints.

---

# 17. Statistical Reporting Strategy

The Eduvance evaluation will primarily use **descriptive statistics** because most datasets are small, bounded engineering-evaluation sets rather than samples designed for population-level inference.

Report exact values rather than percentages alone.

Example:

**37/40 (92.5%)**, not only **92.5%**.

### Binary Metrics

For:

- tutor pass rate;
- abstention;
- assessment pass rate;
- video pass rate;
- personalization pass rate;
- end-to-end success;

report:

**numerator / denominator + percentage**

### Continuous Metrics

For latency and execution time report:

- N
- mean
- median
- range
- P95 where appropriate

### Human Ratings

Report:

- individual reviewer scores;
- consensus score;
- raw agreement;
- Cohen's kappa where appropriate.

### RAG vs No Retrieval

Report:

| Metric | RAG | No Retrieval | Absolute Difference |
|---|---:|---:|---:|
| Correctness | | | |
| Source support | | | |
| Unsupported claims | | | |

No statistical-significance claim is required by the Project Plan.

If a significance test is later added, it must be declared before interpretation and reported as secondary analysis rather than retrofitted to create a stronger claim.

---

# 18. Negative and Unexpected Results

Negative results must remain in the final evaluation.

Examples:

- RAG fails to improve correctness;
- no-retrieval condition performs similarly;
- tutor misses the 90% target;
- one or more videos fail;
- usability falls below 80%;
- workflow fails more than twice.

The report should state the result, probable cause where evidence exists, and limitation.

Targets must not be reported as achieved results unless the experiment actually demonstrates them.

This principle is explicitly required by the Project Plan. fileciteturn0file0L235-L254

---

# 19. Experimental Change Control

If a defect is discovered during final evaluation:

1. record the failed result;
2. identify the defect;
3. fix the implementation;
4. record the new software/configuration version;
5. rerun affected experiments;
6. retain both pre-fix and post-fix evidence.

Do not silently overwrite failed experimental outputs.

---

# 20. Proposed Result Directory Structure

When implementation reaches evaluation, the evidence package can use a structure such as:

`evaluation/`

- `dataset/`
- `ground_truth/`
- `configs/`
- `course_quality/`
- `tutor_rag/`
- `tutor_no_retrieval/`
- `tutor_abstention/`
- `assessments/`
- `videos/`
- `personalization/`
- `end_to_end/`
- `usability/`
- `operational/`
- `analysis/`
- `final_tables/`

This is an evaluation-package design, not repository implementation during WBS 1.4.

---

# 21. Minimum Final Evaluation Tables

The report should ultimately contain at least:

### Table A — Course Quality

Six lessons with scores and pass/fail.

### Table B — Tutor Evaluation

40 questions with summary metrics.

### Table C — Abstention

20 source-absent questions.

### Table D — RAG Baseline

RAG vs no retrieval.

### Table E — Assessment Quality

30 items and rubric results.

### Table F — Video Quality

Six video checklist results.

### Table G — Personalization

12 scenarios.

### Table H — End-to-End Reliability

20 workflow runs.

### Table I — Usability

Core task-completion results.

### Table J — Operational Performance

Generation time, latency, and cost/resource observations.

---

# 22. Reproducibility Package

The final evaluation evidence should preserve enough information for another team member or examiner to understand how the reported numbers were produced.

At minimum preserve:

- dataset version;
- ground truth;
- prompts;
- model/configuration details;
- retrieval settings;
- evaluation rubrics;
- raw outputs;
- reviewer scores;
- analysis calculations;
- software version/commit;
- execution dates.

Current experimental reproducibility guidance likewise emphasizes recording datasets, prompts, experimental settings, hyperparameters/configuration, evaluation procedures, and compute-relevant settings when those affect results. ([researchgate.net](https://www.researchgate.net/publication/405684002_Harness-1_Reinforcement_Learning_for_Search_Agents_with_State-Externalizing_Harnesses?utm_source=chatgpt.com))

Recent LLM evaluation tooling also emphasizes structured logging and retaining configuration/session information so experiments can be rerun and audited. ([researchgate.net](https://www.researchgate.net/publication/414411695_Open_OTK_An_Ollama_toolkit_for_local_LLM_orchestration_hybrid_RAG_and_automated_evaluation?utm_source=chatgpt.com))

---

# 23. WBS 1.4 Final Deliverables

WBS 1.4 now defines:

1. Ten evaluation questions
2. Primary dataset: `EDU-NIST-CSF-SB-v1`
3. Six demo lessons
4. Forty in-scope tutor questions
5. Twenty source-absent questions
6. RAG vs no-retrieval baseline
7. Thirty assessment items
8. Six generated videos
9. Twelve personalization scenarios
10. Twenty end-to-end runs
11. Approximately 8–12 usability participants
12. Course-quality rubric
13. Tutor-grounding rubric
14. Assessment rubric
15. Video checklist
16. Personalization pass rules
17. Reviewer procedure
18. Logging protocol
19. Statistical/result-reporting structure
20. Reproducibility requirements

---

# 24. WBS 1.4 Acceptance Criteria

WBS 1.4 is complete when:

- evaluation questions are approved;
- primary dataset is approved;
- test-case construction protocol is approved;
- baselines are defined;
- metrics are defined;
- Project Plan targets are preserved;
- additional project thresholds are explicitly identified;
- rubrics are approved;
- reviewer procedure is approved;
- execution order is defined;
- experiment logs are defined;
- result-reporting rules are defined;
- reproducibility requirements are defined;
- no experimental results are falsely claimed.

---

# 25. WBS 1.4 Status

**Task:** Define evaluation questions, datasets, and metrics  
**Owner:** Member 1 under the WBS 1–2 ownership override  
**Dependency:** Project objectives  
**Dependency status:** Satisfied  
**Primary dataset:** EDU-NIST-CSF-SB-v1  
**Evaluation design:** Complete  
**Experiments executed:** No  
**Results claimed:** None  
**Status:** Pending final member acceptance