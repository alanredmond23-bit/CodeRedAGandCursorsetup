# RAG v1 Corpus – Modules 1 & 2 (antigravityCodeRed)

**Goal**  
Stand up a **minimal but powerful** Retrieval-Augmented Generation (RAG) layer that makes Modules 1 and 2 self-aware:

- The IDE/agent system can **read its own docs** (rules, architecture, workflows).
- Architect/Orchestrator/Code/Test/Review agents can **look up the truth** instead of hallucinating.
- All of this is **logged into Supabase** in the `codered.corpora`, `codered.documents`, `codered.chunks`, and `codered.embeddings` tables.

This is **RAG v1**: scoped tightly to Modules 1 & 2 so we can ship fast, then expand.

---

## 1. Scope of RAG v1

### 1.1 Included Modules

RAG v1 covers:

- **Module 1 – System Spine**
  - Repo conventions, architecture, Supabase schema, CI/CD, and orchestrator flow.
- **Module 2 – Agents & Orchestration Brain**
  - Agent definitions, YAML configs, guardrails, memory model, prompt routing, and long-horizon behavior.

### 1.2 Use Cases

The corpus must support the following **immediate** use cases:

1. **ArchitectAgent**  
   - Reads architecture, schema, and conventions before planning changes.
2. **CodeAgent**  
   - Looks up file layout, naming rules, and infra expectations before coding.
3. **TestAgent / InfraAgent**  
   - Loads CI/CD rules and known failure modes before touching pipelines.
4. **OrchestratorAgent**  
   - Understands milestones, tasks, and agent responsibilities.
5. **SafetyAgent**  
   - Applies guardrails, especially around legal/RED zones, and detects when it must refuse or escalate.
6. **CynicAgent (later phase but prepped now)**  
   - Pulls scoring rubrics and evaluation criteria from the docs instead of inventing them.

---

## 2. Corpus Definitions (codered.corpora)

We will seed **two core corpora** for Modules 1 & 2, with room to grow:

1. `Core CodeRed Docs` – the **global brain** for this repo.
2. `Module 1–2 Rules & Workflows` – the **high-signal, high-importance** subset, pinned.

### 2.1 Corpus: Core CodeRed Docs

- **Table:** `codered.corpora`
- **Example row:**

  - `name`: `Core CodeRed Docs`
  - `description`: `All primary documentation for antigravityCodeRed: architecture, agents, orchestration, infra, RAG, and learning.`
  - `project_id`: `<id of antigravityCodeRed project>`
  - `domain_tags`: `['core','orchestration','agents','infra','rag']`
  - `risk_level`: `internal`

This corpus will contain **all** docs we write for Modules 1 & 2 and, later, more.

### 2.2 Corpus: Module 1–2 Rules & Workflows

- **Table:** `codered.corpora`
- **Example row:**

  - `name`: `Module 1–2 Rules & Workflows`
  - `description`: `High-signal rules, flows, and setup guides for Modules 1 and 2.`
  - `project_id`: `<id of antigravityCodeRed project>`
  - `domain_tags`: `['core','rules','workflows','guardrails']`
  - `risk_level`: `internal`

This corpus holds the **most important** docs, heavily pinned, used in almost every call by Architect/Orchestrator/Safety.

---

## 3. Document Inventory (codered.documents)

Below is the **initial document set** for RAG v1. All paths assume repo root.

Each document becomes a row in `codered.documents` with:

- `corpus_id`: one of the two corpora above.
- `title`: descriptive doc name.
- `source_path`: Git path.
- `domain_tags`: topic tags.
- `risk_level`: usually `internal` for these.
- `is_pinned`: `true` for the most critical references.

### 3.1 Core System Docs

These live in **both** corpora, with `is_pinned = true` in the Module 1–2 corpus.

1. **Supabase schema design**  
   - `title`: `Supabase Schema Design – CodeRed`  
   - `source_path`: `docs/schema-supabase.md`  
   - `domain_tags`: `['architecture','database','supabase','rag']`  
   - `risk_level`: `internal`  
   - `is_pinned`: `true` (Module 1–2 corpus), `false` (Core corpus)

2. **Base migration SQL**  
   - `title`: `Base Migration – codered schema`  
   - `source_path`: `migrations/0001_codered_base.sql`  
   - `domain_tags`: `['database','supabase','sql']`  
   - `risk_level`: `internal`  
   - `is_pinned`: `true` (Module 1–2), `false` (Core)

3. **Architecture overview**  
   - `title`: `Architecture – antigravityCodeRed`  
   - `source_path`: `docs/architecture.md`  
   - `domain_tags`: `['architecture','orchestration','agents','infra']`  
   - `risk_level`: `internal`  
   - `is_pinned`: `true`

4. **Agents overview**  
   - `title`: `Agents and Roles`  
   - `source_path`: `docs/agent.md`  
   - `domain_tags`: `['agents','roles','permissions','zones']`  
   - `risk_level`: `internal`  
   - `is_pinned`: `true`

5. **Orchestration and pipelines**  
   - `title`: `Orchestration Pipeline`  
   - `source_path`: `docs/orchestration.md`  
   - `domain_tags`: `['orchestration','pipeline','tasks','milestones']`  
   - `risk_level`: `internal`  
   - `is_pinned`: `true`

6. **Prompt routing and modes**  
   - `title`: `Prompt Routing and Modes`  
   - `source_path`: `docs/prompt-routing.md`  
   - `domain_tags`: `['prompting','routing','modes','reasoning']`  
   - `risk_level`: `internal`  
   - `is_pinned`: `true`

7. **Memory and guardrails**  
   - `title`: `Memory & Guardrails`  
   - `source_path`: `docs/memory-and-guardrails.md`  
   - `domain_tags`: `['guardrails','memory','safety','legal']`  
   - `risk_level`: `internal` (with RED references to legal-critical areas)  
   - `is_pinned`: `true`

8. **Tokens and cost policy**  
   - `title`: `Tokens & Cost Policy`  
   - `source_path`: `docs/tokens-and-costs.md`  
   - `domain_tags`: `['tokens','costs','budget','orchestrator']`  
   - `risk_level`: `internal`  
   - `is_pinned`: `true` (for Orchestrator and Architect)

9. **LLM routing strategy**  
   - `title`: `LLM Routing Strategy`  
   - `source_path`: `docs/llm-routing.md`  
   - `domain_tags`: `['llm','routing','models','grok','opus','chatgpt','gemini']`  
   - `risk_level`: `internal`  
   - `is_pinned`: `true`

10. **Extensions & MCP/tool registry**  
    - `title`: `Extensions, MCP, and Tools`  
    - `source_path`: `docs/extensions-and-mcp.md`  
    - `domain_tags`: `['extensions','mcp','tools','apis']`  
    - `risk_level`: `internal`  
    - `is_pinned`: `true` (for Code/Infra/Orchestrator)

11. **CI/CD & Infra policy**  
    - `title`: `Infra & CI/CD Policy`  
    - `source_path`: `docs/infra-ci-cd.md`  
    - `domain_tags`: `['infra','ci','cd','vercel','github-actions']`  
    - `risk_level`: `internal`  
    - `is_pinned`: `true`

12. **Learning & feedback**  
    - `title`: `Learning & Feedback System`  
    - `source_path`: `docs/learning-and-feedback.md`  
    - `domain_tags`: `['learning','feedback','lessons','bug_patterns']`  
    - `risk_level`: `internal`  
    - `is_pinned`: `true`

13. **KISS operator guide**  
    - `title`: `KISS Operator Guide`  
    - `source_path`: `KISS.md`  
    - `domain_tags`: `['operator','overview','usage']`  
    - `risk_level`: `internal`  
    - `is_pinned`: `true`

### 3.2 Setup & First 5 Hours

These are heavily used by Orchestrator and Architect when spinning up or attaching to a repo.

14. **First 5 hours setup**  
    - `title`: `First 5 Hours – Setup`  
    - `source_path`: `FIRST5HOURS/SETUP.md`  
    - `domain_tags`: `['setup','bootstrap','first_run']`  
    - `risk_level`: `internal`  
    - `is_pinned`: `true`

15. **README**  
    - `title`: `Repo README`  
    - `source_path`: `README.md`  
    - `domain_tags`: `['overview','repo','getting_started']`  
    - `risk_level`: `internal`  
    - `is_pinned`: `true` (for Module 1–2 corpus)

---

## 4. Chunking Strategy (codered.chunks)

We want chunks that are:

- Big enough to carry **full concepts** (sections), but
- Small enough to **mix and match** in retrieval.

### 4.1 Default Chunking Rules

For RAG v1, we use simple **markdown-aware** chunking:

- Target **600–900 tokens** per chunk.
- Split on **top-level and secondary headings** (`#`, `##`, `###`), without splitting mid-sentence.
- If a section is longer than ~900 tokens, break further on paragraphs/bullets.
- Keep each chunk’s `content` self-contained:
  - Start with the section title (e.g., `## Orchestration Pipeline`).
  - Follow with paragraphs and bullet points.

### 4.2 Chunk Metadata

For each chunk we write into `codered.chunks`:

- `document_id`: link to the parent doc.
- `project_id`: antigravityCodeRed project.
- `chunk_index`: 0-based index within the document.
- `content`: raw text chunk.
- `token_count`: approximate token count (for debugging / future tuning).
- `embedding_id`: FK to `codered.embeddings` once created.

The embedding size in `codered.embeddings.embedding` is currently **1536** (PG vector dimension), and we can adjust via a later migration if we standardize around a different embedding model.

---

## 5. Embedding Strategy (codered.embeddings)

### 5.1 Embedding Model (v1)

For RAG v1, pick **one** embedding model and stick to it across all Module 1–2 docs. The exact model name will be captured in the `model` column, for example:

- `model`: `text-embedding-3-large` (or equivalent high-quality model)

Consistency simplifies nearest-neighbor search and later analytics.

### 5.2 Indexing and Search

- `codered.embeddings.embedding`: `vector(1536)` with an `ivfflat` index.
- Search pattern per query:
  1. Filter by `project_id = antigravityCodeRed`.
  2. Optionally filter by `domain_tags` for domain-specific queries (`core`, `guardrails`, `infra`, etc.).
  3. Use **similarity search** over `embedding` to get top-k candidates.
  4. Re-rank or filter by `is_pinned` if we want to bias toward pinned docs.

We can also implement **hybrid search** later by combining BM25 text search with vector similarity; for v1, pure vector + some filtering is enough.

---

## 6. Pinning Rules

“Pinned” docs/chunks should **always be high in the ranking** or pulled into context even without a semantic query, especially for:

- ArchitectAgent
- OrchestratorAgent
- SafetyAgent
- CynicAgent (when active)

### 6.1 Pinned Documents

In `codered.documents` for the Module 1–2 corpus, `is_pinned = true` for:

- `docs/schema-supabase.md`
- `migrations/0001_codered_base.sql`
- `docs/architecture.md`
- `docs/agent.md`
- `docs/orchestration.md`
- `docs/prompt-routing.md`
- `docs/memory-and-guardrails.md`
- `docs/tokens-and-costs.md`
- `docs/llm-routing.md`
- `docs/extensions-and-mcp.md`
- `docs/infra-ci-cd.md`
- `docs/learning-and-feedback.md`
- `KISS.md`
- `FIRST5HOURS/SETUP.md`
- `README.md`

### 6.2 Pinned Chunks

For pinned documents, we can additionally:

- Create a **summary chunk** at `chunk_index = 0` that is a hand-written or agent-generated short summary of the entire doc.
- Mark that summary chunk as “always pull for certain roles,” enforced in agent prompt logic (e.g., ArchitectAgent always gets the architecture summary chunk).

These summary chunks are normal rows in `codered.chunks` with `document_id` pointing to the same doc and a special tag stored in `domain_tags` or as metadata in the chunk content (e.g., `SUMMARY:` prefix).

---

## 7. Ingestion Pipeline – Step-by-Step

This is the **operational flow** for loading RAG v1.

### 7.1 One-Time Bootstrap

1. **Create corpora**
   - Insert `Core CodeRed Docs` into `codered.corpora`.
   - Insert `Module 1–2 Rules & Workflows` into `codered.corpora`.

2. **Register documents**
   - For each doc listed in Section 3, insert into `codered.documents` **twice**:
     - Once in `Core CodeRed Docs`.
     - Once in `Module 1–2 Rules & Workflows` (with `is_pinned = true` for that corpus).

3. **Parse & chunk docs**
   - Read file from `source_path`.
   - Apply markdown-aware splitter (600–900 token chunks).
   - Insert each chunk into `codered.chunks` with:
     - `document_id` pointing to the appropriate document row.
     - `chunk_index` incrementing from 0.
     - `project_id` set to antigravityCodeRed project.

4. **Generate embeddings**
   - For each chunk:
     - Compute embedding with chosen model.
     - Insert into `codered.embeddings` with `project_id`, `document_id`, `chunk_id`, and `model`.
     - Update `codered.chunks.embedding_id` with the new `codered.embeddings.id`.

### 7.2 Incremental Updates

When a doc changes (e.g., `docs/agent.md` updated):

1. Increment `version` in `codered.documents` for that document record (or treat as a new row with a new version; old versions can be archived).
2. Re-chunk:
   - Delete the old `chunks` and `embeddings` for that `document_id` (or mark them as `deprecated` in a future schema).
   - Re-run chunking and embedding steps.
3. Optionally generate/update a **summary chunk** for that doc with a short, curated explanation of what changed.

### 7.3 Agent Usage Flow

For a typical ArchitectAgent call:

1. Identify target project (antigravityCodeRed).
2. Issue a semantic query like “Orchestration pipeline for CodeRed” against `codered.embeddings` filtered by:
   - `project_id`
   - `domain_tags` containing `orchestration` or `core`
3. Retrieve top N chunk candidates from `codered.chunks` and `codered.documents`.
4. Always **prepend** pinned summary chunks for:
   - `KISS.md`
   - `docs/architecture.md`
   - `docs/orchestration.md`
   - `docs/agent.md`
   - `docs/memory-and-guardrails.md`
5. Build the final context window and feed into the model.

Same pattern for other agents, but with different **domain_tags filters** and pinned chunk sets.

---

## 8. Safety & Legal Segregation (v1 rules)

For Modules 1 & 2, the only potentially legal-adjacent doc is:

- `docs/memory-and-guardrails.md` – includes rules around legal and RED zones.

RAG v1 **must not** pull in any **case-specific** legal evidence or superseding indictment materials. Those belong in a **separate Supabase project** and corpus with stricter rules.

SafetyAgent and ArchitectAgent should:

- Use this RAG corpus only for **system behavior, rules, and infra**, not for legal facts.
- Defer legal fact-finding to the dedicated Legal RAG later, under much stricter guardrails.

---

## 9. MVP Definition for RAG v1

RAG v1 is considered **“on”** when:

1. Both corpora (`Core CodeRed Docs`, `Module 1–2 Rules & Workflows`) exist.
2. All documents listed in Section 3 are registered in `codered.documents`.
3. All documents are chunked and embedded in `codered.chunks` and `codered.embeddings`.
4. ArchitectAgent, OrchestratorAgent, CodeAgent, SafetyAgent can:
   - Retrieve from these corpora using embeddings.
   - Automatically include pinned summary chunks for core docs.
5. At least one **end-to-end run** has been completed with:
   - Orchestrator → Architect → Code → Test → Review → Infra → Safety,
   - Using RAG v1 to read `docs/architecture.md` and `docs/infra-ci-cd.md` before writing code/infra.

Once this is done, Modules 1 & 2 stop guessing and start reading their own brain.

