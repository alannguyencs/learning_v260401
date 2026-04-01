# 3C Compress Lesson Template

Save to: `data/lesson/{channel_slug}/{yymmdd}_{slug}.md`

See SKILL.md for the `{channel_slug}/{yymmdd}_{slug}` naming convention. Must match the metadata file.

Generate a document with sections separated by `---` horizontal rules. All channels have 6 sections.

Use the Write tool (not Bash) to create the lesson file directly.

---

## Section 0: ## Material

```markdown
## Material

- **Video:** [Video Title](https://www.youtube.com/watch?v=VIDEO_ID)
- **Channel:** Channel Name
- **Published:** YYYY-MM-DD
- **Duration:** M:SS
- **Metadata:** [data/metadata/{channel_slug}/{yymmdd}_{slug}.json](data/metadata/{channel_slug}/{yymmdd}_{slug}.json)
```

---

## Section 1: ## Summary

Structure — answer three questions, each as bullet points:
1. **What** — 2-4 bullets describing the main topic, claim, or situation
2. **Why** — 2-4 bullets on why it matters, with specific numbers/stats from transcript
3. **How** — 2-4 bullets on what to do or how to apply the insight

### Guidelines
- Pull specific numbers, percentages, and quotes from the transcript
- Bold the most important phrases for scannability
- Each bullet should be self-contained — understandable without reading the rest

### Example

```markdown
## Summary

**What:**
- Hong Kong's 2025 graduate job market hit a **5-year low** with vacancies dropping **55%**
- A "jobless recovery" — GDP grows but entry-level jobs don't follow
- Corporate structure shifting from pyramid to diamond: **fewer junior roles, wider management band, small AI-powered base**

**Why:**
- Youth unemployment (ages 20-24) reached **12.3%** — second highest on record
- Only ~30,000 full-time graduate jobs available, lowest in 5 years
- Employers now demand "job-ready" graduates — no bandwidth for training from scratch

**How:**
- Build **AI literacy** — tools like ChatGPT, automation scripting, prompt engineering
- Get internship experience before graduating — 85% of hires come via referrals, not portals
- Adopt an **"AI Plus" mindset** — augment your output with AI rather than compete against it
```

---

## Section 2: ## Recommendation (ASCII flowchart)

An ASCII-style flowchart showing the recommended action plan based on the lesson content. This makes the advice concrete and sequential.

### Guidelines
- Start with `START HERE` at the top
- Use box-drawing characters (`┌ ─ ┐ │ └ ┘ ▼ ▶`) for clean boxes and arrows
- Show a clear step-by-step flow from top to bottom
- Branch into parallel paths when the content has distinct tracks (e.g., job vs freelance vs founder)
- Each box should have a numbered step name and 2-3 lines of actionable detail
- Include specific numbers, thresholds, or rules from the lesson (e.g., "< 5%", "3-6 months", "90%")
- Side boxes can show details or options (connected with `────>`)
- End with a memorable closing box (e.g., "REPEAT. COMPOUND. WAIT." or "STAY IN THE RACE.")
- Place this section between Connect to Known and Create Chunk

### Example

```markdown
## Recommendation

\```
+─────────────────────────────────────────────────────────────────────+
│              ACTION FLOWCHART: FROM $0 TO INVESTING                 │
+─────────────────────────────────────────────────────────────────────+

  START HERE
      │
      ▼
┌───────────────────────────┐
│ 1. SHIFT YOUR MINDSET     │
│    Read "Psychology of     │
│    Money". Investing is    │
│    systematic, not gambling│
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐     ┌──────────────────────────────┐
│ 2. BUILD EMERGENCY FUND   │     │  HIGH-YIELD SAVINGS ACCOUNT  │
│    3-6 months of living   │────>│  Do NOT invest until this    │
│    expenses. Non-negotiable│     │  is fully funded.            │
└─────────────┬─────────────┘     └──────────────────────────────┘
              │
              ▼
┌───────────────────────────┐
│ 3. DESIGN ASSET ALLOCATION│
│    This drives 90% of     │
│    your returns.           │
└─────────────┬─────────────┘
              │
       ┌──────┴──────────────────────────┐
       │                                  │
       ▼                                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  YOUNG       │  │  MID-CAREER  │  │  NEAR        │
│  (20s-30s)   │  │  (40s)       │  │  RETIREMENT  │
│ Stocks: 80%  │  │ Stocks: 60%  │  │ Stocks: 40%  │
│ Bonds:  15%  │  │ Bonds:  30%  │  │ Bonds:  50%  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       └──────────┬───────┘                 │
                  └─────────┬───────────────┘
                            │
                            ▼
               ┌──────────────┐
               │   REPEAT.    │
               │  COMPOUND.   │
               │   WAIT.      │
               └──────────────┘
\```
```

---

## Section 3: ## One-Liners

- **Quotable one-liners** (5) — pithy, memorable phrases that compress the main insights
- Use italics for each line
- Draw directly from the transcript — exact quotes or tightly compressed versions

### Example (from "20 Quantum Cheat Codes")

```markdown
## One-Liners

*"Saving is not investing."*

*"Salary buys you furniture. Equity buys your future."*

*"Failure is not your tormentor — it's your teacher."*

*"Wealth isn't about what you buy. It's about what you keep."*

*"When your desires approach zero, your happiness goes to infinity."*
```

### Example (from "From Homeless to MIT Grad")

```markdown
## One-Liners

*"Solve a problem, nail a product, and the mission will follow."*

*"Passions don't last, but problems do."*

*"Everybody lies — watch what customers do, not what they say."*

*"Revenue is not cash. Profit is not cash. Only cash is real. The rest is accounting."*

*"Lead with love: people → product → profits, in that order."*
```

---

## Section 4: ## Visual Chunk (ASCII workflow)

A single ASCII diagram that captures the main process/framework. Guidelines:
- Title the workflow clearly
- Show cause-and-effect or flow relationships
- Include 2-3 columns or lanes if comparing dimensions (e.g. Economy | Structure | Impact)
- Use arrows (`-->`, `v`, `|`) to show direction
- End with a `KEY:` line summarizing the core insight

```
+-----------------------------------------------------------------------------+
|                    THE GRADUATE JOB SQUEEZE (2025)                           |
+-----------------------------------------------------------------------------+
|                                                                             |
|   ECONOMY          CORPORATE STRUCTURE         GRADUATE REALITY             |
|                                                                             |
|   GDP Growth       Few Executives                                           |
|     +2.5%             /\                  400 applications                  |
|       |              /  \                     0 offers                      |
|       v             / Mgr \                     |                           |
|   But hiring       / Wide  \                    v                           |
|   is FLAT    +--->/ Band    \        "Entry level: 2 yrs exp"              |
|              |   /___________\               |                              |
|   "Jobless   |   |  AI Base  |               v                              |
|    Recovery" |   |  (small)  |        Salary: HK$21K/mo                    |
|              |   +-----+-----+        (0.5% growth YoY)                    |
|              |         |                                                    |
|              |         v                                                    |
|              |   Automates:                                                 |
|              |   - Data cleaning        WHAT GRADUATES NEED:               |
|              |   - Basic analysis       +--------------------------+       |
|              |   - Admin tasks     ---->| 1. AI literacy (tools)   |       |
|              |   - Creative work        | 2. Internship experience |       |
|              |                          | 3. "AI Plus" mindset     |       |
|              |   = Fewer junior         | 4. Soft skills + adapt   |       |
|              |     roles needed         +--------------------------+       |
|                                                                             |
+-----------------------------------------------------------------------------+
|  KEY: The bottom of the ladder is gone. Build skills above the AI line.     |
+-----------------------------------------------------------------------------+
```

---

## Section 5: ## Story

Write a simple, engaging story that a high school student can read to understand the main content of the article. Guidelines:

- **Use a concrete analogy** — translate technical concepts into an everyday scenario (e.g., a pizza shop, a school club, a sports team)
- **Map each key concept** to a character or element in the story
- **Cover the full arc** — the problem, the trigger, the strategy, and the outcome
- **Keep it conversational** — short paragraphs, simple vocabulary, no jargon
- **End with a bold one-liner** summarizing the lesson: `**The lesson:** ...`

### Example

```markdown
## Story

There's a criminal gang that runs an illegal pizza delivery business. The boss bakes poisoned pizzas (that's the ransomware), and he recruits delivery drivers all over town (the affiliates) to drop them at people's doors. When someone eats a slice and gets sick, the only cure costs $600 — and the boss keeps 30% while the driver pockets 70%. Business is booming because 70% of victims just pay up.

One day, a delivery driver drops a poisoned pizza at the apartment of a girl named Elena. What the driver doesn't know is that Elena's boyfriend, Mihai, is the best hacker at a secret cybersecurity team. Mihai is furious.

Mihai and his team start reverse-engineering the poison. They figure out the antidote and publish the recipe online for free. The boss changes the recipe. They crack that too. Five times over two and a half years.

The delivery drivers start quitting — why deliver poisoned pizzas if every victim can just Google the free cure? Without drivers, the boss has no customers. He announces he's "retiring."

**The lesson:** Ransomware works like a franchise — break the trust between the boss and the delivery drivers, and the whole business collapses.
```
