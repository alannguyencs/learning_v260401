## LLM benchmarks

**In one sentence:** An **LLM benchmark** is a frozen set of tasks plus an automatic scoring rule that lets you compare models apples-to-apples (a unit-test suite for an AI), and the table in the image ranks frontier LLMs across six **agentic** ones — benchmarks that measure not "does the model know the answer?" but "can it *do the job*: write code, drive a terminal, click around a computer, and reason across many steps to a verifiable result?"

### Key terminologies
The popular benchmarks listed in the image, each with the capability it scores and the column header from the table:

- **SWE-Bench Pro** *(Agentic coding, "69.2%")* — Scale AI's hard successor to SWE-Bench: real GitHub bug-fix/feature tasks across 41 repos, often spanning multiple files and hours of work, with **held-out** (secret) tasks to resist contamination. Score = % of issues whose patch passes the repo's tests.
  - *What the number means:* "Of all the real coding tasks, Opus 4.8 fully solved 69.2% of them (~7 in 10) on the first attempt." Higher is better. *(GPT-5.5: 58.6% → solved fewer.)*
- **Terminal-Bench 2.1** *(Agentic terminal coding, "74.6%")* — 89 hard, human-verified command-line tasks (build Linux from source, train a model, reverse-engineer a binary). Tests whether an agent can run commands, read errors, and keep state across a long CLI workflow. Score = **resolution rate** (all tests pass before a ~60-min timeout).
  - *What the number means:* "Opus 4.8 completed 74.6% of the 89 terminal tasks before timeout." This is the one row Opus 4.8 *loses* — **GPT-5.5 leads at 78.2%**.
- **Humanity's Last Exam (HLE)** *(Multidisciplinary reasoning, "49.8% / 57.9%")* — 2,500 graduate-level expert questions across math, physics, bio, CS, etc., designed to stay hard for *years*. "no tools" vs "with tools" = whether the model may use a calculator/web/code while answering.
  - *What the number means:* "Opus 4.8 answered 49.8% of the questions correctly from its own knowledge, rising to 57.9% when allowed tools." The same exam is run twice; the gap shows how much tool access helps. Scores are intentionally low — the exam is built to resist saturation.
- **OSWorld-Verified** *(Agentic computer use, "83.4%")* — 369 real desktop tasks (Ubuntu/Windows apps, file I/O, multi-app workflows) where the agent sees the **screen** and acts via mouse/keyboard. Tests GUI-driving "computer use" agents like Claude Computer Use.
  - *What the number means:* "On 83.4% of the desktop tasks, Opus 4.8 left the computer in the goal state." The table's highest scores — all four models cluster in the 76–83% range.
- **GDPval-AA** *(Knowledge work, "1890")* — OpenAI's benchmark of real economically-valuable deliverables (slides, spreadsheets, memos) across 44 occupations, graded by **head-to-head expert comparison** — hence an **Elo-style** number, not a percentage.
  - *What the number means:* **Not a percentage — an Elo rating.** 1890 is only meaningful *relative* to the other models in the same pool (Opus 4.7 = 1753, GPT-5.5 = 1769, Gemini = 1314). The ~120-point lead implies experts prefer Opus 4.8's deliverables ~66% of the time over the next model; the ~576-point gap over Gemini's 1314 implies ~97%.
- **Finance Agent v2** *(Agentic financial analysis, "~50.9%")* — Vals AI's 537 expert-written questions that force the model to dig through recent **SEC filings**, apply finance conventions, and carry exact numbers through multi-step calculations — the work of an entry-level analyst.
  - *What the number means:* "Opus 4.8 answered roughly half the finance questions correctly" (its exact value is obscured by the image caption; it's in the low-50s, leading GPT-5.5's 51.8% and Gemini's 43.0%).

### Background concepts
The supporting vocabulary you need to read those benchmark rows:

- **Benchmark** — A frozen set of tasks + a scoring function used to rank models on one capability. Like a standardized exam: everyone takes the same questions so scores are comparable.
- **Agentic (agent) task** — A task the model can't finish in one reply; it must take **actions in a loop** (run a command, read the output, decide the next step) over many turns. "Agentic" benchmarks score the *end result* of that loop, not individual messages.
- **Benchmark saturation** — When the best models score ~90%+ on a benchmark, it stops discriminating between them, so it's no longer useful and a harder one is built to replace it.
- **Data contamination** — When a benchmark's questions/answers leaked into a model's training data, so the model "remembers" rather than reasons. Inflates scores; fixed with **held-out** secret tasks.
- **Resolution rate / pass@1** — The fraction of tasks the model fully solves on its **first** attempt, verified by running tests. The headline metric for coding/agent benchmarks.
- **Elo rating** — A relative skill score borrowed from chess: instead of a percentage, models are ranked by who beats whom in head-to-head comparisons (used by GDPval's "1890"-style numbers).

### How these terms are related
Read this as why one benchmark leads to the next:

1. **Benchmark → it gets saturated.** Once models hit ~90% on classic exams (e.g. MMLU), the benchmark can't tell good models apart, so the field needs harder tests.
2. **Saturation → contamination-resistant benchmarks.** New benchmarks add **held-out** secret tasks and fresh data so models can't have memorized the answers — this is exactly the pitch of **SWE-Bench Pro** (vs the saturated SWE-Bench Verified) and **HLE** (vs MMLU).
3. **One-shot Q&A → agentic tasks.** Static Q&A doesn't capture real work, which is multi-step. So benchmarks moved to **agentic** loops: SWE-Bench Pro (edit a repo), **Terminal-Bench** (drive a shell), **OSWorld** (drive a GUI), **Finance Agent** (research filings with tools).
4. **Agentic → you need a verifiable score.** Because the model is *doing* something, scoring runs the result: **resolution rate / pass@1** (code passes tests). Where output is open-ended (a slide deck, a memo), tests don't work — so **GDPval** falls back to **expert head-to-head**, producing an **Elo**-style rating instead of a percentage.
5. **Different jobs → different benchmarks.** Each remaining benchmark just swaps the *environment* the agent acts in: a code repo (SWE-Bench Pro), a terminal (Terminal-Bench), a whole desktop (OSWorld), graduate exam questions (HLE), professional deliverables (GDPval), SEC filings (Finance Agent). Same idea, different sandbox.

**The chain in one line:**
`benchmark → saturation → contamination-resistant + agentic → verifiable scoring (pass@1 / Elo) → one benchmark per job (code / terminal / desktop / reasoning / knowledge-work / finance)`

### Concrete example
Take one row — **SWE-Bench Pro, 69.2%**. Behind that single number, for each of ~731 tasks:

```text
1. Agent is dropped into a real repo at a buggy commit + a human-written problem statement.
2. It runs an agentic loop:  read files → edit code → run the test suite → read failures → edit again ...
3. When it stops, the harness runs the repo's hidden test suite (FAIL_TO_PASS + PASS_TO_PASS).
4. Task counts as "resolved" only if ALL those tests pass — that's pass@1.
69.2% = fraction of tasks resolved.  Opus 4.8 (69.2) > GPT-5.5 (58.6) on this exact suite.
```

Notice every key term doing its job: it's **agentic** (a loop, not one reply), scored by **resolution rate**, and the held-out repos guard against **contamination**. Now compare to **GDPval-AA "1890"** — there's no test suite for a slide deck, so a human expert picks the better deliverable in pairwise matchups and the wins roll up into an **Elo** number. Same goal (rank models), different scoring because the task output is open-ended.

### Where you'll meet it
- **Model launch posts & system cards** (Anthropic Opus, OpenAI GPT, Google Gemini) — this exact table style.
- **Leaderboards:** [SWE-Bench](https://www.swebench.com/), Scale AI Labs, Artificial Analysis, [Vals AI](https://www.vals.ai/), llm-stats.com.
- **Coding-agent tooling** (Claude Code, Cursor, Devin) cite SWE-Bench / Terminal-Bench scores as marketing.
- The caption in your image — *"a bit more marketing than science"* — is the standard, healthy skepticism: vendors pick the benchmarks and settings (e.g. "with tools") that flatter them.

### Common confusions
- **Percentage vs Elo** — SWE-Bench Pro/HLE/OSWorld report **% solved**; GDPval's "1890" is an **Elo-style** rating from human comparisons. You can't compare a "1890" to a "69.2%".
- **"with tools" vs "no tools" (HLE)** — same questions, but whether the model may run code/search. Always check which column a quoted score is from.
- **SWE-Bench Pro ≠ SWE-Bench Verified** — Pro is the harder, contamination-resistant version; top models score ~23% on Pro's public set vs 70%+ on Verified, so don't compare across them.
- **Benchmark ≠ real-world performance** — a high score is necessary, not sufficient; production work differs from curated tasks (the "marketing than science" caveat).
- **Agentic coding vs agentic *terminal* coding** — SWE-Bench Pro fixes code *inside a repo*; Terminal-Bench tests broader *ops* in a raw shell (compiling, system tasks), not just editing source.

---
**Sources:**
- [SWE-Bench Pro: Raising the Bar for Agentic Coding — Scale AI](https://scale.com/blog/swe-bench-pro) · [paper (arXiv 2509.16941)](https://arxiv.org/pdf/2509.16941)
- [Terminal-Bench: Benchmarking Agents in Command Line Interfaces (arXiv 2601.11868)](https://arxiv.org/html/2601.11868v1) · [tbench.ai](https://www.tbench.ai/)
- [Humanity's Last Exam — Wikipedia](https://en.wikipedia.org/wiki/Humanity's_Last_Exam) · [paper (arXiv 2501.14249)](https://arxiv.org/abs/2501.14249)
- [OSWorld: Benchmarking Multimodal Agents in Real Computer Environments (arXiv 2404.07972)](https://arxiv.org/abs/2404.07972)
- [GDPval: Evaluating AI on Real-World Economically Valuable Tasks — OpenAI](https://openai.com/index/gdpval/) · [paper (arXiv 2510.04374)](https://arxiv.org/pdf/2510.04374)
- [Finance Agent v2 — Vals AI](https://www.vals.ai/benchmarks/fabv2) · [paper (arXiv 2508.00828)](https://arxiv.org/pdf/2508.00828)
