# LLM benchmarks

Let me start by giving you the one idea that everything today hangs from, because if you hold onto it the rest of the lecture writes itself. Whenever someone says a model "scored 69.2%," they're quoting a **benchmark**, and a benchmark is just two things bolted together: a **frozen set of tasks** that never changes, and an **automatic scoring rule** that turns the model's behaviour into a number. That's it. Think of it as a unit-test suite for an AI — everyone takes the exact same questions under the exact same scoring, so the scores are finally comparable apples-to-apples. Without that frozen, shared exam, "this model is smarter" is just vibes. With it, you can line four frontier models up in a table and actually rank them.

```
benchmark  =  frozen tasks  +  automatic scoring  →  comparable number
```

Now here's the first thing I want you to feel, because it explains *why* the benchmarks keep changing. A good benchmark has a shelf life. The classic exams — something like MMLU, a big bank of multiple-choice knowledge questions — were genuinely useful for years. But models got better, and one day the best of them are all scoring around ninety-plus percent. And the moment everyone clusters at the top, the exam stops doing its only job: it can no longer tell the good models *apart*. We call that **benchmark saturation**. A saturated benchmark isn't wrong, it's just *finished* — it's run out of discriminating power, so the field has to go build a harder one to replace it.

```
everyone scores ~90%+  →  saturation  →  benchmark can't rank anymore  →  build a harder one
```

But "harder" isn't the only thing the new benchmark has to fix, and this is the second pressure pushing the design. There's a sneaky failure mode called **data contamination**. Remember these models are trained on a huge slice of the internet — and if the benchmark's questions and answers happened to be sitting on that internet, then the model isn't *reasoning* its way to the answer, it's just *remembering* it. The score looks brilliant and means nothing. So the fix the new benchmarks reach for is **held-out** tasks — secret questions kept off the public web, fresh data the model couldn't possibly have memorised. That's the whole pitch of **SWE-Bench Pro** sitting on top of the older, leakier SWE-Bench, and of **Humanity's Last Exam** sitting on top of the saturated MMLU: harder *and* contamination-resistant.

```
answers on the internet  →  model memorises, not reasons  →  inflated score
fix:  held-out (secret) tasks  →  nothing to memorise
```

Now the third pressure, and this is the big one, because it changes the *shape* of the test entirely. Old benchmarks were one-shot question-and-answer: here's a question, give me the answer, I'll grade the answer. But that's not what real work looks like, is it? Real work is a *loop*. You don't fix a bug in one reply — you read some files, you edit some code, you run the tests, you read the failures, you edit again. A task the model can't finish in a single reply, one where it has to **take actions in a loop** over many turns, is what we call an **agentic** task. And an agentic benchmark scores the *end result* of that whole loop — did the job actually get done? — not whether any individual message sounded clever.

```
one-shot:   question ──> answer ──> grade        (a single reply)
agentic:    act → observe → decide → act → ...   →  grade the END RESULT
```

So once you've decided to test the agent on a real loop, a new question lands in your lap: how do you *score* it? And the beautiful answer for anything code-shaped is — you just **run it**. Because the model actually *did* something, you don't need a human to judge taste, you can verify the result mechanically. The headline metric here is the **resolution rate**, also called **pass@1**: the fraction of tasks the model fully solves on its *first* attempt, confirmed by running the tests. Tests pass, task resolved. Tests fail, didn't count. Clean, objective, no arguing.

```
agentic result  →  run the tests  →  pass@1 / resolution rate  =  % solved first try
```

But hold on — what about jobs where there *is no* test suite? You can't run pytest on a slide deck or a strategy memo. There's no green checkmark for "good slides." When the output is **open-ended** like that, verifiable scoring breaks down, and the field falls back to the oldest trick we have: ask a human expert to compare two deliverables side by side and pick the better one. Do thousands of those head-to-head matchups and the wins roll up into an **Elo rating** — the same relative-skill number chess uses, where you're ranked by who-beats-whom rather than by any absolute percentage. This is why one number in our table is going to look completely different from the others, and I'll come back to that.

```
output is open-ended (slides, memos)  →  no test to run
→  expert picks better of two  →  head-to-head wins  →  Elo rating (not a %)
```

So now you understand the whole machine, and the last move is almost boring in how simple it is. Once you have "agentic loop, scored by running the result," the only thing left to vary is *which environment* you drop the agent into — and each environment becomes its own benchmark. Same idea, different sandbox. Let me walk you across the six in our table so you can hear each one as a variation on that single theme.

```
same recipe  →  swap the sandbox:
code repo · terminal · desktop · exam questions · pro deliverables · SEC filings
```

First, **SWE-Bench Pro**, scored **69.2%**, the agentic *coding* benchmark — this is Scale AI's hard successor to the original SWE-Bench. The sandbox is a real GitHub repo with a real bug, across forty-one different codebases, tasks that often span multiple files and hours of human work, with those held-out secret tasks we talked about so the model can't have memorised them. The score is the share of issues whose patch passes the repo's own tests. So when you read "Opus 4.8: 69.2%," translate it in your head to "of all those real coding tasks, it fully solved about seven in ten on the first try" — and notice GPT-5.5 sits behind at 58.6%, solving fewer of the *exact same* tasks.

Next, **Terminal-Bench 2.1**, scored **74.6%**, agentic *terminal* coding — and I want you to hear how this differs from the last one, because it's a classic confusion. SWE-Bench fixes code *inside a repo*; Terminal-Bench drops the agent into a raw command line and tests broader *ops*: eighty-nine hard, human-verified tasks like building Linux from source, training a model, reverse-engineering a binary. Can the agent run commands, read the errors that come back, and hold its state together across a long workflow before a roughly sixty-minute timeout? The score is the resolution rate, same pass@1 idea. And here's the one row where Opus 4.8 actually *loses* — **GPT-5.5 leads at 78.2%**. Good. A benchmark where one model wins everything is a benchmark you should distrust.

```
SWE-Bench Pro:    fix bugs INSIDE a repo
Terminal-Bench:   broader OPS in a raw shell  (build, train, reverse-engineer)
```

Third, **Humanity's Last Exam**, written as **49.8% / 57.9%** — and the moment you see two numbers separated by a slash, your antenna should go up. This is the multidisciplinary reasoning exam: twenty-five hundred *graduate-level* expert questions across maths, physics, biology, CS, deliberately built to stay hard for years. The two numbers are the *same exam run twice* — "no tools" on the left, meaning answer from your own knowledge, and "with tools" on the right, meaning you may reach for a calculator, the web, or code. So 49.8% is what Opus 4.8 knows cold; 57.9% is where it climbs once you hand it tools, and the gap between them tells you how much the tools helped. And don't be alarmed that the numbers are *low* — that's the point. The exam is engineered to resist saturation, so a low score today is a feature, not a failure.

```
HLE  →  same questions, two runs:
   no tools  (own knowledge)  |  with tools  (calculator / web / code)
```

Fourth, **OSWorld-Verified**, scored **83.4%**, agentic *computer use*. Here the sandbox is an entire desktop — three hundred sixty-nine real tasks on Ubuntu and Windows apps, file operations, workflows that hop between several programs — and crucially the agent doesn't get an API, it gets the **screen**, and it acts with mouse and keyboard like a person would. This is what tests the "computer use" agents you've heard about. The score is the share of tasks where the agent left the computer in the goal state. Notice all four models cluster tightly in the seventy-six to eighty-three range here — when scores bunch up like that, the benchmark is starting to whisper that it's heading toward saturation.

Fifth — and this is the odd one out, so slow down — **GDPval-AA**, listed as **1890**. Not a percentage. An **Elo rating**, exactly the open-ended case we set up earlier. This is OpenAI's benchmark of genuinely economically-valuable deliverables — slides, spreadsheets, memos — across forty-four occupations, and because you can't unit-test a memo, it's graded by expert head-to-head comparison. So 1890 means *nothing on its own*; it only means something next to the others in the same pool: Opus 4.7 at 1753, GPT-5.5 at 1769, Gemini down at 1314. That roughly hundred-and-twenty-point lead implies the experts prefer Opus 4.8's work about two-thirds of the time over the next model; the yawning five-hundred-plus-point gap over Gemini implies they prefer it something like ninety-seven percent of the time. You feel the difference from a percentage? A "1890" answers "who wins more often," not "what fraction did it get right."

```
% benchmarks:   how many tasks solved          (SWE-Bench, HLE, OSWorld)
Elo (GDPval):   who beats whom, head-to-head    1890 only means "vs the others"
```

And sixth, **Finance Agent v2**, around **50.9%**, agentic financial analysis — Vals AI's five hundred thirty-seven expert-written questions that force the model to dig through recent **SEC filings**, apply real finance conventions, and carry exact numbers through multi-step calculations, basically the day-job of an entry-level analyst. It answered roughly half — the exact figure is partly hidden behind the image caption, but it's in the low fifties, ahead of GPT-5.5's 51.8% and Gemini's 43.0%.

Let me pull one row apart all the way down, so every term we've met does its job in front of you. Take **SWE-Bench Pro, 69.2%**. Behind that one number, for *each* task: the agent is dropped into a real repo frozen at a buggy commit, with a human-written description of what's wrong. It runs its **agentic** loop — read files, edit code, run the suite, read the failures, edit again. When it finally stops, the harness runs the repo's *hidden* test suite, and the task counts as resolved only if *all* of those tests pass — that's **pass@1**. The fraction of tasks resolved is your 69.2%, and on this exact suite Opus 4.8's 69.2 beats GPT-5.5's 58.6. See all three ideas working at once: it's **agentic** because it's a loop not a reply, it's scored by **resolution rate** because we ran the result, and the held-out repos are what guard against **contamination**. Now hold that next to GDPval's **1890** — there's no test suite for a slide deck, so a human expert picks the better one in pairwise matchups, the wins become an **Elo**. Same goal, rank the models; different scoring, because one output is checkable and the other is a matter of judgement.

```
SWE-Bench Pro 69.2%:  drop in repo → loop → run hidden tests → ALL pass? → pass@1
GDPval 1890:          no test for a deck → expert picks winner → Elo
```

So where will you actually run into all this, and how should you hold it? You'll see this exact table style in **model launch posts and system cards** from Anthropic, OpenAI, and Google; on **leaderboards** like SWE-Bench's own site, Artificial Analysis, Vals AI; and quoted as marketing by **coding tools** like Claude Code, Cursor, and Devin. And here's the healthy skepticism to carry in with you — the caption on the image you were looking at literally said *"a bit more marketing than science,"* and that's the right instinct. The vendor picks *which* benchmarks to show and *which* settings flatter them — notice how "with tools" always gets quoted when it's higher. So when you read a benchmark number, always ask which column it came from and whether the comparison is fair.

Let me leave you with the handful of traps that catch people, because they're all just the lecture said backwards. Don't ever compare a **percentage to an Elo** — a "1890" and a "69.2%" live in different universes. With **HLE always check "with tools" versus "no tools,"** because it's the same exam and the gap is large. Don't confuse **SWE-Bench Pro with the older SWE-Bench Verified** — top models score around twenty-three percent on Pro's public set against seventy-plus on Verified, so a number from one means nothing against the other. Don't mix up **agentic coding with agentic *terminal* coding** — one edits source inside a repo, the other runs broad ops in a bare shell. And the deepest one of all: **a benchmark is not real-world performance.** A high score is *necessary* but never *sufficient* — production work is messier than any curated task, which is exactly what that "marketing than science" caveat is trying to tell you. Keep the chain in your head and you'll read any of these tables correctly: a benchmark gets saturated, so we build harder contamination-resistant agentic ones, we score them by running the result as pass@1 or by expert Elo when we can't, and then we just swap the sandbox — code, terminal, desktop, exam, knowledge-work, finance — one benchmark per job.

```
benchmark → saturation → contamination-resistant + agentic
→ verifiable scoring (pass@1 / Elo) → one benchmark per job
```
