## A/B Testing

**In one sentence:** A/B testing is a **controlled online experiment** that randomly splits real users into two groups — the current version (A) and a changed version (B) — and uses **statistical hypothesis testing** to decide whether the difference in their behavior is a real effect or just luck.

### Key terminologies
These build on each other; read top to bottom and the last term (A/B testing) falls out naturally.

- **Control vs. treatment (variant A vs. variant B)** — The **control** is the existing version users already see; the **treatment** is the new version with exactly one thing changed (a headline, a button color, a checkout flow). Keeping everything else identical is what lets you attribute any behavior difference to that one change.
- **Randomized assignment** — Each incoming user is assigned to A or B by a coin flip (often hashing their user ID). Randomization makes the two groups statistically equivalent on average, so confounding factors (device, time of day, returning vs. new) cancel out — the same logic as a randomized controlled trial in medicine.
- **Conversion / metric** — The measurable outcome you compare, usually a rate: clicks ÷ visitors, signups ÷ visitors, purchases ÷ sessions. This is your **dependent variable** — the number that decides the winner.
- **Null hypothesis (H₀)** — The skeptical default: "the change does nothing; A and B have the same true conversion rate, and any observed gap is random noise." A/B testing is built to try to *disprove* this.
- **Alternative hypothesis (H₁)** — The claim you actually hope is true: "B's true conversion rate differs from A's." You never prove H₁ directly — you gather enough evidence to **reject H₀**.
- **p-value** — The probability of seeing a gap *at least as large* as the one you observed **if H₀ were true** (i.e. if the change really did nothing). A small p-value means "this gap would be a weird fluke under pure chance," which is evidence against H₀. Crucially it is *not* the probability that B is better.
- **Significance level (α) and confidence level** — α is the p-value threshold you commit to *before* running, usually 0.05. **Confidence level** is 1 − α (e.g. 95%). α is also your **false-positive rate**: the chance you declare a winner when there's actually no difference (a **Type I error**).
- **Sample size analysis** — Before running, you compute how many users each group needs so that, given your α, target lift, and baseline rate, the test is trustworthy. Too small → noisy and unreliable; too large → wasted traffic and time.
- **A/B testing** — The full method: randomly split users into control (A) and treatment (B), measure a conversion metric, and run a hypothesis test (compute a p-value, compare to α) to decide whether B's difference is real and worth shipping.

### How these terms are related
Read this as a cause-and-effect chain — each step forces the next:

1. **Want to know if a change helps → run an experiment, not an opinion.** You have a new design (the **treatment**) and the old one (the **control**); the only honest way to compare is to show both to real users.
2. **Comparing two groups → they must be fair → randomized assignment.** If group B happened to get all the weekend shoppers, the comparison is meaningless. Random assignment makes A and B equivalent on average, isolating your one change.
3. **Need something to compare → a conversion metric.** You pick one outcome rate so "which is better" becomes "which has the higher rate."
4. **Observed a gap → is it real or noise? → hypothesis testing.** Even two identical pages rarely convert at *exactly* the same rate, so you set up **H₀** ("no difference") against **H₁** ("B differs") and ask how surprising your gap is.
5. **Quantify the surprise → the p-value.** The p-value measures how unlikely your gap would be if H₀ were true.
6. **Need a decision rule → the significance level α.** Fix α (say 0.05) up front; if `p < α` you **reject H₀** and call B a winner. Because α is also your **false-positive rate**, it caps how often you'd crown a winner that doesn't actually exist (a **Type I error**).
7. **Want that verdict to be trustworthy → sample size analysis.** A tiny sample makes the p-value jump around, so *before* launching you compute how many users each group needs to detect your target lift at that α.
8. **All of it together → A/B testing.** Randomization + a conversion metric + a pre-registered hypothesis test (p-value vs. α) at a planned sample size = a trustworthy verdict on whether to ship B.

**The chain in one line:**
`control vs. treatment → randomized assignment → conversion metric → H₀/H₁ → p-value vs. α → sample size → A/B testing`

### Concrete example
You want to know if a green "Buy" button beats the current blue one.

```text
Setup:
  A (control):   blue button   — 10,000 visitors, 500 purchases  → 5.00% conversion
  B (treatment): green button  — 10,000 visitors, 560 purchases  → 5.60% conversion
  Observed lift: +0.60 percentage points (a 12% relative improvement)

Question: is +0.6pp real, or could random chance produce it even if the
          colors truly convert equally (H₀)?
```

A two-proportion z-test on these numbers gives a **p-value ≈ 0.06**. Walk the terms:

- H₀ = "blue and green convert identically." p ≈ 0.06 means: *if that were true*, you'd still see a gap this big about 6% of the time by luck alone.
- With **α = 0.05**, 0.06 > 0.05 → you **fail to reject H₀**. Not yet a winner — borderline.
- A **sample size analysis** beforehand (baseline 5%, target lift = 0.5pp, α = 0.05) would have told you each group actually needs **~30,000 visitors**, not 10,000 — so the test had far too few users, which is exactly why a promising result is inconclusive.
- The fix is to plan that sample size up front and run all the way to it before judging — not to stop the moment the numbers happen to look good.

```python
from statsmodels.stats.proportion import proportions_ztest
# successes (purchases), trials (visitors) for [A, B]
stat, pval = proportions_ztest([500, 560], [10000, 10000])
print(round(pval, 3))   # ~0.061  -> not significant at alpha=0.05
```

### Computing the sample size
You fix these inputs *before* the test, then solve for **n**, the users needed **per group**:

- **Baseline rate `p`** — the control's current conversion rate (e.g. 5%).
- **Target lift `δ`** — the absolute improvement you want the test to be able to detect (e.g. 0.5pp, so `p₂ = p + δ = 5.5%`).
- **Significance `α`** — usually 0.05 (two-sided) → `z_{α/2} = 1.96`.
- **Detection-reliability constant `z_β`** — a fixed constant for how dependably you want to catch a true effect; the standard choice gives `z_β = 0.84`.

The two-proportion formula (users **per group**):

```text
        (z_{α/2} + z_β)² · [ p₁(1−p₁) + p₂(1−p₂) ]
  n  =  ───────────────────────────────────────────
                        (p₂ − p₁)²
```

Plug in the button example (`p₁=0.05`, `p₂=0.055`, `α=0.05`, `z_β=0.84`):

```text
  (1.96 + 0.84)²              = 2.8²        = 7.84
  p₁(1−p₁) + p₂(1−p₂)         = 0.0475 + 0.051975 = 0.099475
  (p₂ − p₁)²                  = 0.005²      = 0.000025

  n = 7.84 × 0.099475 / 0.000025 ≈ 31,000 users per group  (≈ 62,000 total)
```

So 10,000/group was far too few — exactly why the earlier p ≈ 0.06 was inconclusive.

A handy back-of-envelope for small rates uses the pooled approximation `2·p(1−p)`, which makes `(z_{α/2}+z_β)² ≈ 7.84` double to `≈ 16`:

```text
  n ≈ 16 · p(1−p) / δ²  = 16 × 0.0475 / 0.000025 ≈ 30,400 per group
```

In practice, let a library do it (it handles the pooled-variance and continuity details):

```python
from statsmodels.stats.proportion import proportion_effectsize
from statsmodels.stats.power import NormalIndPower

effect = proportion_effectsize(0.055, 0.05)          # standardized effect size (Cohen's h)
n = NormalIndPower().solve_power(effect, power=0.80, alpha=0.05, alternative="two-sided")
print(round(n))   # ~31,000 per group
```

Key levers: **a smaller target lift `δ`, lower baseline rate, or stricter α all push n up** — halving `δ` roughly **quadruples** n (it's in the squared denominator).

### Where you'll meet it
- **Product & web companies** — Google, Meta, Netflix, Booking.com, and Microsoft run *thousands* of concurrent A/B tests; "ship it behind an experiment" is standard practice.
- **Experimentation platforms** — Optimizely, VWO, Google Optimize (retired), LaunchDarkly, Statsig, GrowthBook, and Eppo.
- **Feature flags / canary releases** — the engineering plumbing that splits traffic for an A/B test.
- **Courses** — shows up in intro statistics (inferential statistics, hypothesis testing), data science interviews, and product-analytics curricula.

### Common confusions
- **A/B test vs. hypothesis test** — A/B testing is the real-world *experiment* (randomize users, change one thing); hypothesis testing is the *statistical procedure* it uses to judge the result. The A/B test is the experiment; the hypothesis test is the verdict.
- **Statistical vs. practical significance** — A huge sample can make a microscopic, useless +0.01% lift "statistically significant." Significance says the effect is *real*; it doesn't say it's *big enough to matter*.
- **p-value ≠ probability B is better** — p is computed *assuming H₀ is true*; it is not "the chance the change works." (Frequentist p-values and Bayesian "probability B beats A" answer different questions.)
- **A/B test vs. A/B/n and multivariate** — A/B compares two variants on one change; **A/B/n** compares several variants of one element; **multivariate** tests combinations of *multiple* changed elements at once.
- **Frequentist vs. Bayesian A/B testing** — Frequentist fixes the sample size and reports a p-value; Bayesian reports the probability that B beats A and tolerates continuous monitoring better. Same goal, different machinery.

---
**Sources:**
- [A/B Testing Statistics Made Simple — Invesp](https://www.invespcro.com/blog/ab-testing-statistics-made-simple/)
- [Statistical Significance in A/B testing (Calculation, p-value and the Math) — data36](https://data36.com/statistical-significance-in-ab-testing/)
- [Understanding Statistical Significance in A/B Testing — Convert.com](https://www.convert.com/blog/a-b-testing/statistical-significance/)
- [A/B Testing vs Hypothesis Testing: The Critical Differences — Kameleoon](https://www.kameleoon.com/blog/ab-testing-vs-hypothesis-testing)
- [Hypothesis Testing for A/B Test: An Application of Inferential Statistics — Towards Data Science](https://towardsdatascience.com/hypothesis-testing-for-a-b-test-an-application-of-inferential-statistics-5ae2e779ff04/)
