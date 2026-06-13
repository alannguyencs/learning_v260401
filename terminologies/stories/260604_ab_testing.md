# A/B Testing

Let me start with a situation you'll meet on basically any product team. Somebody believes a green "Buy" button will sell more than the blue one you have now. The instinct is to argue about it — the designer has a taste, the manager has a hunch, somebody quotes a blog post. And I want you to notice, right at the top, that *none of that is evidence*. The only honest way to find out whether a change helps is to stop opinionating and **run an experiment**: show the old thing to some real users, show the new thing to others, and watch what they actually do. Everything we're going to talk about today is just the machinery that makes that comparison trustworthy.

So the first two words you need are **control** and **treatment**. The control is the version your users already see — the blue button. The treatment is the new version with **exactly one thing changed** — the green button, and *only* the color, nothing else. That "only one thing" rule is not fussiness; it's the whole game. If you change the color *and* the wording *and* the size all at once and sales go up, you've learned nothing, because you can't tell which change did it. Keep everything identical except the single variable, and any difference in behavior can be honestly pinned on that one change.

```
control (A) ──> blue button   (what users see now)
treatment (B) ─> green button (one thing changed)
```

Now, the moment you decide to show two versions to two groups of people, a new danger appears: what if the groups aren't fair? Suppose, by bad luck, group B ends up full of weekend shoppers who were going to buy anyway. Then green looks better, but it was never the color — it was the crowd. So you need the two groups to be **statistically equivalent on average**, and the way you get that is **randomized assignment**. As each user arrives, you flip a coin — in practice you hash their user ID — and that flip drops them into A or B. Do this across enough people and all the messy confounding factors, device type, time of day, new versus returning, spread evenly across both groups and cancel out. This is exactly the logic of a randomized controlled trial in medicine: randomize, and the only systematic difference left between the groups is the thing you're testing.

```
user arrives → hash(user_id) → coin flip → A  or  B
            confounders spread evenly, cancel out
```

Next you need something to actually compare, because "which is better" is too vague to measure. You pick one **conversion metric** — one outcome rate. Purchases divided by visitors, signups divided by visitors, clicks divided by sessions. Pick one and commit to it, because that single number is now your scoreboard; it's the **dependent variable**, the thing that decides the winner. In our example the metric is purchases over visitors, and when the experiment runs we get blue at 500 purchases out of 10,000 visitors, which is 5.00%, and green at 560 out of 10,000, which is 5.60%. So green is ahead by 0.6 percentage points.

```
conversion = purchases ÷ visitors
   blue  500/10,000 = 5.00%
   green 560/10,000 = 5.60%   (+0.6pp)
```

And here is where the real subtlety begins, so slow down with me. You're looking at 5.6% versus 5.0% and you want to shout "green wins!" But pause: even **two identical pages** almost never convert at exactly the same rate. Flip a fair coin a thousand times twice and you won't get the same number of heads. So a gap by itself proves nothing — the question is whether *this* gap is a real effect or just the kind of wobble random chance produces anyway. To answer that, statisticians do something that feels backwards at first: they start by assuming the change did **nothing**. That assumption is the **null hypothesis**, written H₀ — "blue and green have the same true conversion rate, and the gap you see is just noise." And against it they put the **alternative hypothesis**, H₁, which is the thing you actually hope is true — "green's true rate is genuinely different from blue's." Here's the part students always trip on: you never prove H₁ directly. The whole method is built only to try to **disprove H₀**. You play the skeptic and see if the data can knock the skeptic down.

```
H0: blue = green  (change does nothing, gap is luck)
H1: blue ≠ green  (the thing you hope for)
strategy: try to DISPROVE H0
```

So how do you measure whether the data knocks H₀ down? With the **p-value**, and you have to hold its definition very precisely or you'll misuse it for the rest of your career. The p-value is the probability of seeing a gap **at least as large** as the one you got, *assuming H₀ were true* — assuming the colors really convert identically. In our button test, a two-proportion z-test on those numbers gives a p-value of about 0.06. Read that out loud the right way: *if blue and green truly converted the same*, you'd still see a gap this big, just from luck, about 6% of the time. A small p-value means "this gap would be a weird fluke under pure chance," which is evidence against the skeptic. And notice what the p-value is emphatically **not** — it is *not* the probability that green is better. It's computed in a world where H₀ is assumed true; it can't also tell you the chance H₀ is false. Keep those separate.

```
p-value = P(gap this big | H0 true)
   button test: p ≈ 0.06
   = "even if equal, you'd see this 6% of the time"
   NOT "the chance green is better"
```

A p-value is just a number, though — you still need a rule that turns it into a yes or no. That rule is the **significance level**, called α, and the discipline is that you fix it **before** you run the test, not after you've seen the result. The usual choice is α = 0.05, and one minus α — here 95% — is what people call the **confidence level**. The decision is mechanical: if your p-value comes in below α, you **reject H₀** and declare a winner; if it doesn't, you don't. But α is secretly doing a second job, and it's the reason you must commit to it up front: α is also your **false-positive rate**. It's the chance you crown a winner when there was actually no difference at all — that mistake has a name, a **Type I error** — so setting α at 0.05 is you saying "I accept being fooled by noise at most 5% of the time." In our example, p ≈ 0.06 is *above* 0.05, so we **fail to reject H₀**. Green is not a winner. It's tantalizingly close, but borderline, and borderline doesn't ship.

```
if p < α  → reject H0 → ship B
else      → fail to reject → don't ship
α = 0.05 = false-positive rate = Type I error
   button: 0.06 > 0.05 → not a winner
```

Now you might feel cheated — green *was* ahead, why didn't it count? And the answer reveals the last piece: **sample size analysis**. With too few users, the p-value jumps around wildly, so a real effect can hide and a fake one can sparkle. The fix is to compute, *before you ever launch*, how many users each group needs. You feed in three things you decide in advance — your baseline rate (blue's 5%), the smallest lift you care about detecting (say half a percentage point), and your α — and out comes n, the users needed **per group**. Run the numbers for our button and it says you needed about **30,000 visitors in each group**, not 10,000. So the experiment was starved of data from the start, three times too small, and that is *exactly* why a promising 0.6-point lead came back inconclusive. The discipline that follows is iron: plan that number up front and run all the way to it before you judge — never peek mid-stream and stop the instant the numbers happen to look pretty, because that's just cherry-picking noise.

```
inputs (fixed first): baseline p, target lift δ, α
        │
        ▼
   n per group
   button: need ~30,000/group, had 10,000 → starved → inconclusive
```

And that — all of it, stacked together — *is* **A/B testing**. You randomly split real users into control and treatment, you measure one conversion metric, you set up the skeptical null against the alternative, you compute a p-value and compare it to a pre-committed α, and you do it at a sample size you planned in advance so the verdict is trustworthy. Pull any one piece out and it falls apart: no randomization and your groups are unfair; no fixed α and you'll rationalize any result; no sample-size plan and your p-value is noise. Together they turn "I think green is nicer" into "green beats blue, and here's the evidence."

```
randomize → metric → H0/H1 → p vs α → planned sample size
                = A/B testing (a trustworthy verdict)
```

Before I let you go, a few places you'll actually run into this, and a few traps. You'll meet A/B testing everywhere serious software is shipped — Google, Meta, Netflix, Booking.com, Microsoft, all running *thousands* of experiments at once, where "ship it behind an experiment" is just how things are done; you'll meet it through platforms like Optimizely, Statsig, GrowthBook, and Eppo, and through the feature-flag and canary-release plumbing that splits the traffic underneath. Now the traps. First, don't confuse the **A/B test** with the **hypothesis test** — the A/B test is the real-world experiment, randomizing users and changing one thing; the hypothesis test is the statistical procedure that judges the result. The experiment gathers the evidence; the hypothesis test delivers the verdict. Second, **statistical significance is not practical significance** — pour in a huge enough sample and a microscopic, useless 0.01% lift can come out "significant"; significance tells you the effect is *real*, not that it's *big enough to bother shipping*. Third — and I'll say it one more time because it's the single most abused idea in the field — the **p-value is not the probability that green is better**; it's computed assuming H₀ is true, which is a different question entirely. And finally, know that what we did today is the **frequentist** flavor — fix the sample size, report a p-value. There's a **Bayesian** sibling that instead reports the probability that B beats A and copes better with peeking as you go, and there are richer designs, **A/B/n** for several variants of one element and **multivariate** for combinations of many — but every one of them is chasing the same thing we started with: turning an argument about a button into an honest, measured answer.
