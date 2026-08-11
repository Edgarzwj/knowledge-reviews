# knowledge-reviews · Knowledge Review Generator

> A **reproducible, zero-hallucination, fully-sourced** enterprise knowledge-review pipeline.
> Built on semantic search over Tencent Yunzhi (Lexiang) knowledge bases, it renders a *single-file, fully-inlined, dark-tech-styled* HTML review report from one real search session.

[中文文档 →](./README.md)

---

## 1. What it does

Most teams' knowledge-base search results stay trapped in a chat window — untraceable and impossible to consolidate into shareable documents.

`knowledge-reviews` solves one thing: **turn a single real knowledge-base search into a sourced, clickable, offline-openable review report** — and the same input always renders the same output (reproducible).

Core principles (see [`docs/architecture.md`](./docs/architecture.md)):

1. **Zero hallucination** — every number, title, and link in the report must come from real search results. Nothing is fabricated.
2. **Full sourcing** — every claim carries an `[n]` superscript that maps to the "References" list at the bottom (title + link + keyword tags).
3. **Reproducible** — data (`spec.json`), content (`body.html` / `conclusion.html`), and rendering (`src/review_generator.py`) are strictly separated.
4. **Transparent retrieval** — the report ships a "Search Flow" visualization listing each `search_kb_search` call's `total` hits and `took_ms` latency.

---

## 2. Project layout

```
knowledge-reviews/
├─ README.md              # Chinese main doc
├─ README_EN.md           # English doc (this file)
├─ LICENSE                # MIT
├─ .gitignore
├─ docs/
│  ├─ conventions.md      # Project layout conventions (how to add a review)
│  └─ architecture.md     # First-principles design / approach
├─ src/
│  └─ review_generator.py # Reproducible generator (stdlib only, no deps)
└─ samples/               # Example: data + content + artifact
   ├─ spec.json           # Real search data (query stats / references)
   ├─ body.html           # Review body (with [n] superscripts)
   ├─ conclusion.html     # Conclusion + data-authenticity note
   └─ 企业知识问答系统_知识综述.html  # Example report generated from the above
```

> A copy of `企业知识问答系统_知识综述.html` also lives at the repo root for quick viewing; the canonical artifact is in `samples/`.

---

## 3. Reproduce the example report

No third-party packages required — just Python 3:

```bash
cd knowledge-reviews
python3 src/review_generator.py
# equivalent to:
python3 src/review_generator.py \
  --spec   samples/spec.json \
  --body   samples/body.html \
  --conclusion samples/conclusion.html \
  --out    samples/企业知识问答系统_知识综述.html
```

Output is a single-file HTML (inline CSS, no external fonts / scripts / images) that opens offline.

---

## 4. Where the example data comes from (authenticity note)

Everything under `samples/` comes from a **real search over Tencent Yunzhi (Lexiang)** on **2026-08-06**:

| Query | Hits `total` | Latency `took_ms` |
|-------|-------------:|------------------:|
| Q1 · Enterprise QA **RAG** retrieval-augmented generation | 7 | 96 ms |
| Q2 · Enterprise QA **Prompt** engineering | 7 | 46 ms |
| Q3 · Enterprise QA **Agent** | 7 | 84 ms |

- 21 raw hits across 3 queries → **7 unique documents** after dedup (5 content pages + 2 empty containers).
- Only the 5 content pages are cited; the 2 containers are excluded from claims.
- **Honest disclosure**: the "Prompt engineering" query overlaps entirely with the others — the knowledge base has no dedicated page on that method. This gap is stated explicitly; no extrapolation was made.

---

## 5. How to add a new review

Full workflow in [`docs/conventions.md`](./docs/conventions.md). Short version:

1. Search your Lexiang knowledge base with `search_kb_search`; record each query's `total` / `took_ms`.
2. Parse hits with `entry_describe_ai_parse_content`; extract snippet takeaways.
3. Fill `meta` / `queries` / `aggregation` / `references` per `samples/spec.json`.
4. Write the body into `body.html` (use `[n]` superscripts matching `references` order); write the conclusion into `conclusion.html`.
5. Run the generator, then verify superscripts and links before sharing.

**Red line**: anything not traceable to a real search result must not enter the report; existing gaps should be disclosed like the example, never glossed over or invented.

---

## 6. Roadmap

- [ ] Wire up the Lexiang MCP connector for one-shot "search → spec → generate"
- [ ] Multi-knowledge-base cross-search with dedup/aggregation
- [ ] Add Markdown / PDF offline export formats
- [ ] JSON Schema validation for `spec.json`

---

## Corpus sufficiency audit (what GitHub doesn't have)

Tools like scholar-rag and automated-slr-generator assume "the corpus is already good enough" and generate straight from it. They skip a more fundamental question: **is this knowledge base even worthy of powering reliable Q&A?** This project closes that gap.

`src/corpus_audit.py` takes several real searches (each with its hit document IDs and empty-container IDs), computes four hard metrics, and renders a verdict:

- **Unique documents** — total distinct documents after dedup.
- **Cross-query overlap** — whether different intents return the same document set (higher = more同质).
- **Content-page ratio** — share of documents that actually have body text, after excluding empty KB/folder containers.
- **Verdict** — sufficient / borderline / insufficient, with a one-line, number-backed reason.

Why is this more useful than "another pretty review"? Because RAG answer quality is capped by corpus quality. A corpus of a handful of demo docs can't be rescued by any "hallucination reduction" — the audit says so outright instead of dressing it up. In the report, the audit card follows the "Search Flow" section and shows the verdict as a red / yellow / green badge.

> Quality bar: this project's prose and code adopt the two rulers from [deaify](https://github.com/Edgarzwj/deaify) — `humanize-prose` (kill AI smell, take a stance, use numbers, don't recap the intro as the ending) and `code-no-slop` (YAGNI, shortest working diff, no fake modularity).

---

## 7. License

[MIT](./LICENSE) © 2026 Edgarzwj
