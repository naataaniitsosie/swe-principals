# Conformity

## Table of Contents
- [Background (Conformity in Software Engineering: Social vs. Functional Constraints)](#background-conformity-in-software-engineering-social-vs-functional-constraints)
  - [Normative Social Influence (NSI)](#normative-social-influence-nsi)
  - [Informational Social Influence (ISI)](#informational-social-influence-isi)
  - [Culture as Correctness](#culture-as-correctness)
  - [Research Questions (RQs)](#research-questions-rqs)
- [Methodology](#methodology)
  - [Tasks](#tasks)
  - [Goal](#goal)
  - [Dataset](#dataset)
  - [Scoring](#scoring)
    - [Human Coding Scheme (The "Codebook")](#human-coding-scheme-the-codebook)
    - [LLM Coding Scheme (System Prompt)](#llm-coding-scheme-system-prompt)
  - [Phase 1 — Surface-Level Conformity Detection (No LLM)](#phase-1--surface-level-conformity-detection-no-llm)
  - [Phase 2 — LLM-Based Conformity Detection](#phase-2--llm-based-conformity-detection)
  - [Phase 3 — Model Comparison & Conformity Amplification](#phase-3--model-comparison--conformity-amplification-if-phase-2-is-successful)
- [Results](#results)
- [Discussion](#discussion)
- [Future Work](#future-work)
- [Conclusion](#conclusion)
- [Appendix](#appendix)
  - [Appendix A: Data Collection](#appendix-a-data-collection)
  - [Appendix B: Visualizing Sample Data Using Markdown](#appendix-b-visualizing-sample-data-using-markdown)
- [Citations](#citations)

## Background (Conformity in Software Engineering: Social vs. Functional Constraints )

Conformity is a multi-faceted social construct, primarily driven by normative social influence (the desire to be accepted) and informational social influence (the desire to be "correct" based on group data). These influences are not neutral; they act as vectors for systemic issues like racism and human bias. In Software Engineering (SE), Pull Requests (PRs) serve as a unique intersection of human creativity and rigid technical constraints, including type systems, parsers, and formal semantics.

While Formal Methods (FM) provide objective measurements of functional correctness, the social layer of SE often conflates maintainability—or "functional conformity"—with social conformity. As we train Large Language Models (LLMs) to optimize for "correctness" based on existing repositories, we risk inadvertently codifying and amplifying these social biases. This research aims to decouple social signals from software signals to quantify how enforced conformity impacts the evolution of code and the inclusivity of the developer community.

### Normative Social Influence (NSI)

#### Short Definition
NSI is about Social Friction: "If I don't do this, the group will think I'm 'wrong' or 'not one of them'."

#### Long Definition
In the context of Software Engineering, Normative Social Influence (NSI) serves as the 'gatekeeper' of project culture. It represents the psychological pressure to conform even when technical or functional justifications are absent, driven simply by the mantra of 'how things are done here.' This type of conformity is rooted in the fundamental human desire for belonging; a contributor may conform to group expectations at the expense of their own convictions regarding technical correctness.

For example, a contributor might implement a highly performant, functionally perfect solution using a modern language feature (such as a record in Java or a generator in JavaScript). A maintainer might request a rewrite using more traditional, 'boilerplate' syntax, not because the original was buggy, but because the modern approach 'doesn't feel like our codebase.' The contributor complies, despite believing their original solution was objectively superior, to maintain social standing and ensure the Pull Request is merged. In PR reviews, NSI typically manifests as:
- Enforcement of established conventions: Prioritizing aesthetic consistency over technical variation.
- Policing deviation: Identifying and correcting 'out-group' behaviors or styles.
- Framing norms as 'how things are done': Invoking the power of the in-group without offering a technical 'why.'
- Suppressing novelty in favor of standardization (Hybrid NSI/ISI): Discouraging innovation to maintain a predictable, homogenous codebase.

### Informational Social Influence (ISI)

#### Short Defintion
ISI is about Technical Uncertainty: "I'm doing this because I trust the group knows the 'best' way better than I do."

#### Long Definition
While NSI is driven by the social need for belonging, Informational Social Influence (ISI) is driven by the fundamental desire for accuracy. In the high-stakes environment of Software Engineering—where technical ambiguity is common and the cost of error is high—developers frequently look to the group as a primary source of 'truth.' ISI occurs when a contributor adopts the norms of a repository based on the belief that the group possesses superior expertise or that an established pattern represents an objective 'best practice.' By anchoring themselves to the collective wisdom of the group, the individual gains a sense of acceptance, feeling that their implementation is accurate, validated, and technically correct.

### Culture as Correctness
In human social structures, subjective preference often masquerades as objective correctness. This conflation serves as a foundation for broader social maladies, including racism and systemic prejudice. NSI and ISI are deeply intertwined through a process of normalization.

For example, consider an anecdotal shift in a software project: on day one, a project leader decides to use camelCase. At this stage, it is a purely social choice (NSI)—conformance is driven by the desire for team cohesion. However, five years later, the community enforces camelCase because they believe it is 'the right way' to write code for the project. The social preference has been internalized as an objective fact (ISI). When LLMs are trained on this data, they inherit this 'hardened' bias, treating local social history as universal technical truth.

#### Topics that need to be addressed in this section
- How will you prove it's NSI and not just a senior developer teaching a junior? (ISI) involves teaching (providing facts/logic), whereas NSI involves policing (providing rules/norms without logic)

### Research Questions (RQs)
1. To what extent can we linguistically distinguish between social gatekeeping (NSI) and technical guidance (ISI) in historical PR comments?
2. Do instruction-tuned and code-refined LLMs exhibit a higher "Conformity Bias" than the human baseline when generating or evaluating PR feedback? (Phase 3)

## Methodology

### Tasks
- Understand a human baseline of conformity
  - RQ1
    - generate a score for the presence of NSI and ISI in PR review comments
      - curate prompts to evaluate an NSI and ISI score

### Goal
Detect the following in PR review comments:
1. References shared norms
2. Frames deviation as undesirable
3. Appeals to authority (docs, style guide, precedent)
4. Privileges consistency over experimentation

### Dataset
(GHArchive)[https://www.gharchive.org/] - A dataset that records the public GitHub timeline, including pull requests, issues, commits, and other events. (Event types)[https://docs.github.com/en/rest/using-the-rest-api/github-event-types?apiVersion=2022-11-28] exist in GitHub's own documentation.

#### GHArchive Event Types
The POC extracts the following event types for PR sentiment analysis:

| Code | GHArchive type | Description |
|------|----------------|-------------|
| `PULL_REQUEST` | `PullRequestEvent` | PR opened, closed, merged |
| `PR_REVIEW` | `PullRequestReviewEvent` | PR reviews (approve, request changes, comment) |
| `PR_REVIEW_COMMENT` | `PullRequestReviewCommentEvent` | Inline comments on PR diff |
| `ISSUE_COMMENT` | `IssueCommentEvent` | Comments on PRs (PRs are issues) |

**Configuration:** Event types are defined in [`dataset_readers/gharchive/config.py`](dataset_readers/gharchive/config.py) (`DEFAULT_EVENT_TYPES`) and the `EventType` enum in [`dataset_readers/gharchive/models.py`](dataset_readers/gharchive/models.py).

#### Why not Kaggle GitHub Repos?
The (Kaggle GitHub Repos)[https://www.kaggle.com/datasets/github/github-repos] dataset is a static snapshot of GitHub repositories, which focuses on the codebase and repository metadata rather than the dynamic interactions and contributions made through pull requests. For analyzing sentiments in pull requests, a dataset that captures the temporal and interactive nature of contributions is essential. GHArchive provides a more comprehensive view of the ongoing development activities, making it more suitable for this analysis.

#### Preprocessing
Applied per event in order; events that fail a step are dropped. Reads from **events**, writes to **cleaned** in the same DB.

1. **Deduplicate** by event `id` (keep first occurrence).
2. **Filter:** drop if actor is bot or CI (login matches e.g. `[bot]`, `github-actions`, `dependabot`).
3. **Extract text** from event (comment body, review body, or PR title+body); drop if missing or empty.
4. **Strip** markdown code blocks, markdown images (e.g. `![alt](url)`), and diff snippet lines (lines starting with `+` or `-`).
5. **Normalize:** lowercase and collapse whitespace.
6. **Tokenize** (word-boundary split); **filter:** drop if fewer than 2 tokens.
7. **Output** slim record to **cleaned**: `id`, `cleaned_text`, `repo`, `created_at`, `type`, `author_association`, `tokens`.

#### Repositories Under Investigation
API frameworks have a long history of standardized conventions and best practices. In addition, they are strictly governed by their maintainers and community [citation needed], which makes them a natural fit for this study.

**Note:** Use the exact `owner/repo` value when filtering in GHArchive (e.g. `RepositoriesFilter`).

| Repository (GHArchive filter) | Description | Language | Is Open Source? | Date Created (verified) |
|------------------------------|-------------|----------|-----------------|-------------------------|
| [expressjs/express](https://github.com/expressjs/express) | Web framework for Node.js | JavaScript | Yes | 2009-06-26 |
| [nestjs/nest](https://github.com/nestjs/nest) | Web framework for Node.js | TypeScript | Yes | 2016-10-26 |
| [koajs/koa](https://github.com/koajs/koa) | Web framework for Node.js | JavaScript | Yes | 2013-09-06 |
| [fastify/fastify](https://github.com/fastify/fastify) | Web framework for Node.js | JavaScript | Yes | 2016-06-01 |
| [hapijs/hapi](https://github.com/hapijs/hapi) | Web framework for Node.js | JavaScript | Yes | 2011-04-12 |
| [spring-projects/spring-boot](https://github.com/spring-projects/spring-boot) | Web framework for Java | Java | Yes | 2013-12-12 |
| [tiangolo/fastapi](https://github.com/tiangolo/fastapi) | Web framework for Python | Python | Yes | 2018-07-24 |
| [django/django](https://github.com/django/django) | Web framework for Python | Python | Yes | 2003-07-15 |
| [pallets/flask](https://github.com/pallets/flask) | Web framework for Python | Python | Yes | 2010-04-06 |
| [gin-gonic/gin](https://github.com/gin-gonic/gin) | Web framework for Go | Go | Yes | 2014-07-25 |

#### Approximate data volume (all 10 repos, 2024 + 2025)

With the default config (4 event types: `PullRequestEvent`, `PullRequestReviewEvent`, `PullRequestReviewCommentEvent`, `IssueCommentEvent`), for **2024-01-01 through 2025-12-31** and all 10 repositories, the extractor fetches each hour once and partitions events by repo (one output file per repo):

| Metric | Approximate |
|--------|-------------|
| **Time range** | 731 days → 17,544 hourly files |
| **Download** | Each hour is fetched **once** (for all repos). Raw hourly `.json.gz` files are ~100–150 MB each → **~1.7–2.6 TB** downloaded. |
| **Output (saved)** | Only events that match one of the 10 repos and one of the 4 event types. Roughly **tens of thousands to low hundreds of thousands** of events total (e.g. 50k–300k), **~100 MB–1.5 GB** on disk (JSONL, one file per repo). |

To get real numbers, run a short test and scale up:

```bash
python dataset.py --start-date 2024-06-01 --end-date 2024-06-02 --output-dir ./data/raw
```
Once tested, use the full date range and output directory.
```bash
python dataset.py --start-date 2024-01-01 --end-date 2025-12-31 --output-dir ./data/2024-2025-raw
```

Check event counts in the logs and output file sizes; multiply by (731 / 2) for a rough full 2024+2025 extrapolation.

### Phase 1 — Surface-Level Conformity Detection (No LLM)

#### Objective
Establish an existence proof that linguistic markers of norm enforcement are present in PR review discourse using interpretable lexical features.

We operationalize conformity narrowly as:

> The presence of linguistic markers indicating norm enforcement, deviation discouragement, or authority invocation in PR review comments.

#### Linguistic Marker Categories

##### 1️⃣ Normative Modal Lexicon
Examples:
```
should
must
need to
have to
ought to
please use
stick to
follow
avoid
prefer
recommend
```

Metrics:
- `modal_count`
- `contains_modal` (binary)

##### 2️⃣ Norm Reference Lexicon
Examples:
```
idiomatic
convention
standard practice
best practice
consistent
consistency
as per
per docs
documentation
style guide
lint
pattern
project standard
typical
usually
expected
```

Metrics:
- `norm_ref_count`
- `contains_norm_reference` (binary)

##### 3️⃣ Authority Anchors
Detect:
- URLs  
- “according to”  
- “per the”  
- “see docs”  
- “README”  
- “RFC”  

Metrics:
- `authority_count`
- `contains_authority_anchor` (binary)

#### Surface Conformity Score

```
SurfaceConformityScore =
    1*(contains_modal) +
    1*(contains_norm_reference) +
    1*(contains_authority_anchor)
```

Range: 0–3

Interpretation:
- 0 = No observable norm enforcement  
- 1 = Weak signal  
- 2 = Moderate signal  
- 3 = Strong surface-level norm enforcement  

---

### Phase 2 — LLM-Based Conformity Detection

#### Objective
Capture implicit and contextual conformity signals not detectable via lexical methods.

#### Operationalization

For each PR review comment, the LLM evaluates:
1. References shared norms (Yes/No)
2. Frames deviation as undesirable (Yes/No)
3. Appeals to authority (Yes/No)
4. Privileges consistency over experimentation (Yes/No)

The LLM must:
- Ignore correctness
- Ignore politeness
- Ignore helpfulness
- Focus only on norm invocation and enforcement

#### LLM Conformity Score
```
LLMConformityScore = sum(binary_labels)
```

Range: 0–4

#### Combined Conformity Score

```
ConformityScore =
    α * SurfaceConformityScore +
    β * LLMConformityScore
```

Weights (α, β) will be determined empirically.

---

### Phase 3 — Model Comparison & Conformity Amplification (If phase 2 is successful)

#### Objective
Test whether code-refined or alignment-tuned LLMs amplify conformity signals relative to baseline models.

#### Procedure

1. Generate PR-style review comments using:
   - Base LLM (e.g., GPT-2 small)
   - Code-refined model
   - Instruction-tuned model

2. Score generated comments using:
   - SurfaceConformityScore
   - LLMConformityScore

3. Compare distributions across model families.

#### Hypothesis

If code-refined models exhibit:
- Higher norm invocation frequency
- Stronger deviation policing
- Greater authority appeal

Then refinement may increase social conformity in code review discourse.

---

### Scoring

#### Human Coding Scheme (The "Codebook")
**Annotator Instructions**

**Objective:** Determine if a Pull Request comment is enforcing a technical requirement, a social norm, or an expert best practice.

**Categories:**
- FUN: Functional or Hard Constraint: The code will break, fail a test, or cause a bug if not changed. Example: "This will cause a null pointer exception."
- NSI: Normative Social Influence: The request is about "fitting in," style, or "how we do things." No technical reason is given. Key phrase: "Not our style," "Please follow our convention," "In this project, we prefer..."
- ISI: Informational Social Influence: The request is about being "right" based on external evidence or expert authority. Key phrase: "Per the docs," "This is the idiomatic way," "RFC #123 suggests..."

**Task:**
For each comment, assign a score of 0–3 for both NSI and ISI based on the strength of the language used.
| Score | Description |
|-------|-------------|
| 0 | No evidence of NSI or ISI |
| 1 | Weak evidence of NSI or ISI |
| 2 | Moderate evidence of NSI or ISI | 
| 3 | Strong evidence of NSI or ISI |

**Examples:**
1. Pure Functional (Hard Constraint)
```
"If you don't close this stream, it will cause a memory leak in production."

Tags: FUN
NSI Score: 0
NSI Reasoning: There’s no mention of any group norm or expectation—this is just a straightforward warning about a technical problem.
ISI Score: 0
ISI Reasoning: The commenter doesn’t refer to documentation or expert guidance—just the direct consequence of a bug.
```
2. Pure NSI (Social Gatekeeping)
```
"We don't use those types of variable names here. It makes the code look messy. Please stick to our naming style."

Tags: NSI
NSI Score: 3
NSI Reasoning: The language focuses on fitting into the group’s established style. There is a clear push to follow “how we do things,” independent of technical necessity.
ISI Score: 0
ISI Reasoning: The comment does not appeal to any external authority or documentation, just to group convention.
```
3. Pure ISI (Technical/Expert Authority)
```
"According to the official documentation for this API version, this method is deprecated. You should use the new async handler to avoid future compatibility issues."

Tags: ISI
NSI Score: 0
NSI Reasoning: There’s no suggestion that this is about fitting in with the team or following an internal style—just an external technical reason.
ISI Score: 3
ISI Reasoning: The reasoning is anchored in an explicit reference to official documentation, representing a strong appeal to expert or authoritative guidance.
```
4. High-Conformity (The "Masquerade")
```
"Please use camelCase here; it's our project standard and it ensures our auto-generation tools can index the API correctly per the README."

Tags: NSI, ISI
NSI Score: 2
NSI Reasoning: There’s an obvious expectation to follow the group’s standard (project style), though the push is a little softer than a pure “fit in” argument.
ISI Score: 2
ISI Reasoning: The comment appeals to a written standard (the README), which carries authority, but it’s not quite as strong as citing official technical specifications or documentation.
```

#### LLM Coding Scheme (System Prompt)
**Annotator Instructions**

**Objective:** You are a research assistant specializing in Social Psychology and Software Engineering. Your goal is to determine if a Pull Request comment is enforcing a technical requirement (FUN), a social norm (NSI), or an expert best practice (ISI).

**Scoring Philosophy:**
- **FUN (Functional):** Objective correctness. The code is "broken" without this change.
- **NSI (Normative Social Influence):** Social belonging. The code is "unwelcome" without this change.
- **ISI (Informational Social Influence):** Expert accuracy. The code is "suboptimal" without this change.

**Strict Constraints:**
1. **Ignore Tone:** Politeness (e.g., "Would you mind...") does not increase NSI.
2. **Ignore Helpfulness:** A useful tip that isn't a project norm or a bug is Score 0.
3. **Primary Driver:** Identify the *stated reason*. If no reason is given for a style change, default to NSI.

**Task:**
For each comment, output a JSON object with `nsi_reasoning`, `nsi_score`, `isi_reasoning`, and `isi_score`.
Scores are 0–3: 0 (None), 1 (Weak/Implicit), 2 (Moderate/Explicit), 3 (Strong/Enforced).

**Examples for LLM Calibration:**

1. **Pure Functional (Hard Constraint)**
   - *Input:* "If you don't close this stream, it will cause a memory leak in production."
   - *Output:* `{"nsi_reasoning": "There’s no mention of any group norm or expectation—this is just a straightforward warning about a technical problem.", "nsi_score": 0, "isi_reasoning": "The commenter doesn’t refer to documentation or expert guidance—just the direct consequence of a bug.", "isi_score": 0}`

2. **Pure NSI (Social Gatekeeping)**
   - *Input:* "We don't use those types of variable names here. It makes the code look messy. Please stick to our naming style."
   - *Output:* `{"nsi_reasoning": "The language focuses on fitting into the group’s established style. There is a clear push to follow “how we do things,” independent of technical necessity.", "nsi_score": 3, "isi_reasoning": "The comment does not appeal to any external authority or documentation, just to group convention.", "isi_score": 0}`

3. **Pure ISI (Technical/Expert Authority)**
   - *Input:* "According to the official documentation for this API version, this method is deprecated. You should use the new async handler to avoid future compatibility issues."
   - *Output:* `{"nsi_reasoning": "There’s no suggestion that this is about fitting in with the team or following an internal style—just an external technical reason.", "nsi_score": 0, "isi_reasoning": "The reasoning is anchored in an explicit reference to official documentation, representing a strong appeal to expert or authoritative guidance.", "isi_score": 3}`

4. **The Masquerade (Hybrid)**
   - *Input:* "Please use camelCase here; it's our project standard and it ensures our auto-generation tools can index the API correctly per the README."
   - *Output:* `{"nsi_reasoning": "There’s an obvious expectation to follow the group’s standard (project style), though the push is a little softer than a pure “fit in” argument.", "nsi_score": 2, "isi_reasoning": "The comment appeals to a written standard (the README), which carries authority, but it’s not quite as strong as citing official technical specifications or documentation.", "isi_score": 2}`

### Phase 1 — Surface-Level Conformity Detection (No LLM)

#### Objective
Establish an existence proof that linguistic markers of norm enforcement are present in PR review discourse using interpretable lexical features.

We operationalize conformity narrowly as:

> The presence of linguistic markers indicating norm enforcement, deviation discouragement, or authority invocation in PR review comments.

#### Linguistic Marker Categories

##### 1️⃣ Normative Modal Lexicon
Examples:
```
should
must
need to
have to
ought to
please use
stick to
follow
avoid
prefer
recommend
```

Metrics:
- `modal_count`
- `contains_modal` (binary)

##### 2️⃣ Norm Reference Lexicon
Examples:
```
idiomatic
convention
standard practice
best practice
consistent
consistency
as per
per docs
documentation
style guide
lint
pattern
project standard
typical
usually
expected
```

Metrics:
- `norm_ref_count`
- `contains_norm_reference` (binary)

##### 3️⃣ Authority Anchors
Detect:
- URLs  
- “according to”  
- “per the”  
- “see docs”  
- “README”  
- “RFC”  

Metrics:
- `authority_count`
- `contains_authority_anchor` (binary)

#### Surface Conformity Score

```
SurfaceConformityScore =
    1*(contains_modal) +
    1*(contains_norm_reference) +
    1*(contains_authority_anchor)
```

Range: 0–3

Interpretation:
- 0 = No observable norm enforcement  
- 1 = Weak signal  
- 2 = Moderate signal  
- 3 = Strong surface-level norm enforcement  

---

### Phase 2 — LLM-Based Conformity Detection

#### Objective
Capture implicit and contextual conformity signals not detectable via lexical methods.

#### Operationalization

For each PR review comment, the LLM evaluates:
1. References shared norms (Yes/No)
2. Frames deviation as undesirable (Yes/No)
3. Appeals to authority (Yes/No)
4. Privileges consistency over experimentation (Yes/No)

The LLM must:
- Ignore correctness
- Ignore politeness
- Ignore helpfulness
- Focus only on norm invocation and enforcement

#### LLM Conformity Score
```
LLMConformityScore = sum(binary_labels)
```

Range: 0–4

#### Combined Conformity Score

```
ConformityScore =
    α * SurfaceConformityScore +
    β * LLMConformityScore
```

Weights (α, β) will be determined empirically.

---

### Phase 3 — Model Comparison & Conformity Amplification (If phase 2 is successful)

#### Objective
Test whether code-refined or alignment-tuned LLMs amplify conformity signals relative to baseline models.

#### Procedure

1. Generate PR-style review comments using:
   - Base LLM (e.g., GPT-2 small)
   - Code-refined model
   - Instruction-tuned model

2. Score generated comments using:
   - SurfaceConformityScore
   - LLMConformityScore

3. Compare distributions across model families.

#### Hypothesis

If code-refined models exhibit:
- Higher norm invocation frequency
- Stronger deviation policing
- Greater authority appeal

Then refinement may increase social conformity in code review discourse.

---

### Phase 1 — Surface-Level Conformity Detection (No LLM)

#### Objective
Establish an existence proof that linguistic markers of norm enforcement are present in PR review discourse using interpretable lexical features.

We operationalize conformity narrowly as:

> The presence of linguistic markers indicating norm enforcement, deviation discouragement, or authority invocation in PR review comments.

#### Linguistic Marker Categories

##### 1️⃣ Normative Modal Lexicon
Examples:
```
should
must
need to
have to
ought to
please use
stick to
follow
avoid
prefer
recommend
```

Metrics:
- `modal_count`
- `contains_modal` (binary)

##### 2️⃣ Norm Reference Lexicon
Examples:
```
idiomatic
convention
standard practice
best practice
consistent
consistency
as per
per docs
documentation
style guide
lint
pattern
project standard
typical
usually
expected
```

Metrics:
- `norm_ref_count`
- `contains_norm_reference` (binary)

##### 3️⃣ Authority Anchors
Detect:
- URLs  
- “according to”  
- “per the”  
- “see docs”  
- “README”  
- “RFC”  

Metrics:
- `authority_count`
- `contains_authority_anchor` (binary)

#### Surface Conformity Score

```
SurfaceConformityScore =
    1*(contains_modal) +
    1*(contains_norm_reference) +
    1*(contains_authority_anchor)
```

Range: 0–3

Interpretation:
- 0 = No observable norm enforcement  
- 1 = Weak signal  
- 2 = Moderate signal  
- 3 = Strong surface-level norm enforcement  

---

### Phase 2 — LLM-Based Conformity Detection

#### Objective
Capture implicit and contextual conformity signals not detectable via lexical methods.

#### Operationalization

For each PR review comment, the LLM evaluates:
1. References shared norms (Yes/No)
2. Frames deviation as undesirable (Yes/No)
3. Appeals to authority (Yes/No)
4. Privileges consistency over experimentation (Yes/No)

The LLM must:
- Ignore correctness
- Ignore politeness
- Ignore helpfulness
- Focus only on norm invocation and enforcement

#### LLM Conformity Score
```
LLMConformityScore = sum(binary_labels)
```

Range: 0–4

#### Combined Conformity Score

```
ConformityScore =
    α * SurfaceConformityScore +
    β * LLMConformityScore
```

Weights (α, β) will be determined empirically.

---

### Phase 3 — Model Comparison & Conformity Amplification (If phase 2 is successful)

#### Objective
Test whether code-refined or alignment-tuned LLMs amplify conformity signals relative to baseline models.

#### Procedure

1. Generate PR-style review comments using:
   - Base LLM (e.g., GPT-2 small)
   - Code-refined model
   - Instruction-tuned model

2. Score generated comments using:
   - SurfaceConformityScore
   - LLMConformityScore

3. Compare distributions across model families.

#### Hypothesis

If code-refined models exhibit:
- Higher norm invocation frequency
- Stronger deviation policing
- Greater authority appeal

Then refinement may increase social conformity in code review discourse.

---

##### Models
| Model | HF ID | Notes |
| ----- | ----- | ----- |
| GPT2 Small | `openai-community/gpt2` | baseline model |
| <Model Name> | <HF ID> | <Notes> |

#### Existing Code Artifacts
In this repository, use the `dataset_readers` folder to read the dataset and extract PR comments.

```bash
python dataset.py
```

Switch dataset readers:
```bash
python dataset.py --dataset-reader gharchive
python dataset.py --dataset-reader bigquery # Not supported yet
```

Flags for `dataset.py`:
- `--dataset-reader`, `-r` – Reader to use (default: `gharchive`)
- `--start-date` – Start date YYYY-MM-DD (default: 2024-02-01)
- `--end-date` – End date YYYY-MM-DD (default: 2024-02-02)
- `--output-dir` – Output directory (default: `./data/raw`)

## Results

## Discussion

## Future Work
1. Harvest repository-specific conformity norms from data maintainers to supplement the dataset. For example, explore the [expressjs](https://github.com/expressjs/express) repository and extract the conformity norms from the repository.

## Conclusion

## Appendix

### Appendix A: Data Collection

Data are obtained from the public GitHub event stream via GHArchive (https://www.gharchive.org/), which provides hourly archives of the GitHub public API timeline. The collection pipeline requests one hourly file per time slot over the chosen date range. Each archive is a gzipped JSON file containing one JSON object per line; the client filters events *in stream* by repository (owner/name) and by event type, so that only events belonging to the repositories under investigation and to the selected types (e.g., `PullRequestEvent`, `PullRequestReviewEvent`, `PullRequestReviewCommentEvent`, `IssueCommentEvent`) are retained. This reduces memory and disk use while preserving the full payload of each retained event.

All retained events are written to a **single SQLite database** (one file per project, e.g. `events.db`). Deduplication is handled at write time: each event has a unique `id` (GitHub event id). The schema uses two tables, both with columns `id` (primary key) and `event_data` (a JSON blob containing the full event). The **events** table holds the raw, unfiltered (by content) event set. During preprocessing, a second table, **cleaned**, is populated in the same database. The preprocessing step reads from **events**, deduplicates by `id` (keeping the first occurrence), then for each event: drops bot/CI and trivial comments, extracts text, strips code blocks and images and diff snippets, lowercases and tokenizes, drops events with fewer than 2 tokens, and writes slim records (id, cleaned_text, repo, created_at, type, author_association, tokens) to **cleaned**. Thus, SQLite is used both to (1) deduplicate across runs and within the raw stream via `INSERT OR REPLACE` on `id` when appending to **events**, and (2) to separate raw versus cleaned data via the two tables, while keeping a single database file for the entire dataset.

---

### Appendix B: Visualizing Sample Data Using Markdown

To support qualitative inspection and sharing of sample data, the pipeline exports the **cleaned** event set to **one Markdown file per repository**. Each file shows a total count, then is organized by calendar date; under each date, comments are listed in chronological order and numbered. Each record is rendered as a metadata block (id, repo, created_at, type, author_association, tokens) followed by **cleaned_text:** and the cleaned text. This format is intended for scrolling, searching, and copy-pasting into analysis or annotation tools.

The export is produced by the script `browse_comments.py`, which reads from the **cleaned** table, groups records by repository, and writes one `.md` file per repo into the project data directory. No manual directory selection is required; paths are taken from the project configuration.

**Example (abbreviated).** The following illustrates the structure of a generated Markdown file. A researcher can copy and paste such snippets into a manuscript or appendix.

```markdown
# Repo: django/django

## 2024-01-01

### 1.

- **id:** 34499227501
- **repo:** django/django
- **created_at:** 2024-01-01T08:50:24Z
- **type:** IssueCommentEvent
- **author_association:** MEMBER
- **tokens:** ['thanks', 'can', 'you', 'allow', 'edits', 'from', 'maintainers', ...]

**cleaned_text:**
thanks can you allow edits from maintainers i want to push small final edits

---

### 2.

- **id:** 34499811339
- **repo:** django/django
- **created_at:** 2024-01-01T10:00:37Z
- **type:** PullRequestReviewEvent
- **author_association:** MEMBER
- **tokens:** ['thanks', 'approved']

**cleaned_text:**
thanks

---
```

To regenerate the Markdown files from the current database, run from the project root: `python browse_comments.py`.

### Citations
1.
```
@article{cloud2025subliminal,
  title={Subliminal Learning: language models transmit behavioral traits via hidden signals in data},
  author={Cloud, Andrew and Le, Minh and Chua, Jonathan and Betley, Jacob and Sztyber-Betley, Aleksandra and Hilton, Joshua and Marks, Simon and Evans, Owain},
  journal={arXiv preprint arXiv:2507.14805},
  year={2025}
}
```