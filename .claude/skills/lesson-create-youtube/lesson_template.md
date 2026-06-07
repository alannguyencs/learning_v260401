# Lesson Template

Save to: `data/lesson/{channel_slug}/{yymmdd}_{slug}.md`

See SKILL.md for the `{channel_slug}/{yymmdd}_{slug}` naming convention. Must match the metadata file.

Generate a document with sections separated by `---` horizontal rules.

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

## Sections 1-3: Three Major Sections

Read the full transcript carefully, identify all key points, then group them into **at most 3 major sections** by theme. Each section covers a coherent cluster of ideas from the transcript.

### Guidelines

- **Group by theme, not by order** — rearrange transcript points so related ideas sit together
- **Section headings** use `## I. Title`, `## II. Title`, `## III. Title` — titles should be short and descriptive
- **Bullet points** — each section uses bullet points to cover its key insights
- **~100 words per section** — keep each section concise but include specific stories, numbers, and examples from the transcript
- **ASCII diagram per section** — each section ends with an ASCII diagram that visually illustrates its key points
- **Full coverage** — every key point from the transcript must appear in one of the three sections. Re-read the transcript after drafting to verify nothing is missing.

### ASCII Diagram Guidelines

- Use simple box-drawing characters (`+`, `-`, `|`, `v`, `>`) and arrows
- Show relationships: flow, hierarchy, convergence, or comparison
- Keep it readable — no more than ~25 lines
- Include key terms, names, and numbers from the transcript

### Example

```markdown
## I. Find the Right Product

- Skip the grand mission — solve a real problem first. Microsoft started as two guys writing software; Facebook started as FaceMash. Theranos and FTX had inspiring missions and the founders are in prison.
- Chase problems, not passion — Airbnb was born from two broke founders who couldn't afford a hotel. Sandeep's search engine company got crushed by Google, so they pivoted: sold search to Yahoo, rebuilt as B2B information retrieval, and Microsoft bought them for $1.2B. Passions don't last, but problems do.
- Subtract ruthlessly — Southwest built a giant business by removing fancy meals, reserved seats, and big airport reps. Steve Jobs saved Apple by cutting almost all product lines to focus on iMac. The most important subtraction is internal: focus on the essential, subtract the noise — that's what preserves your sanity.
- Find founder-market fit — Melanie Perkins was a design instructor who saw people struggle daily. That pain became Canva.
- Find product-market fit — Burbn pivoted to photo sharing and became Instagram. Track activation rate, retention rate, and churn rate.

\```
  REAL PROBLEM
       |
       v
  +-----------+    +-----------+    +-----------+
  | Mission?  |    | Passion?  |    | Too much? |
  | Skip it.  |    | Skip it.  |    | Cut it.   |
  +-----------+    +-----------+    +-----------+
       |                |                |
       v                v                v
  Solve first,    Chase the pain,  Subtract to
  mission follows problems last    focus
       |                |                |
       +--------+-------+--------+-------+
                |                |
                v                v
        FOUNDER-MARKET FIT  PRODUCT-MARKET FIT
        You ARE the market  Users show you what
        (Perkins -> Canva)  they want
                |           (Burbn -> Instagram)
                |                |
                +-------+--------+
                        |
                        v
                  RIGHT PRODUCT
\```

---

## II. Understand Your Customers

- Run experiments instead of trusting your ego — Sandeep's company discovered a winning pricing model (volume-based) they'd never considered through A/B testing.
- Sell promises, not products: Nike beat Adidas not with better shoes but by selling a dream.
- Watch what customers do, not what they say — Sandeep's AI fraud company heard endless praise from prospects who never bought, then retargeted high-urgency customers for explosive growth.
- Test willingness to pay early: startups that charged found 90% retention dropped to 10%, revealing they never had real product-market fit.

\```
          YOUR CUSTOMERS
                |
    +-----------+-----------+
    |           |           |
    v           v           v
  THINK       FEEL        DO
  (ego)     (dreams)    (behavior)
    |           |           |
    v           v           v
  Run A/B     Sell the    Watch what
  experiments promise,    they do, not
  not gut     not the     what they say
  feelings    product     (Ford: "faster
    |         (Nike:       horses")
    |          dream >         |
    |          shoes)          |
    +--------+---------+-------+
             |
             v
      TEST WILLINGNESS TO PAY
      Free = hobby, not business
      90% retention -> 10% when
      you charge = no real PMF
             |
             v
       EXPLOSIVE GROWTH
\```
```
