"""
Upload 20 Quantum Cheat Codes lesson (4 chapters, 20 quizzes) to the learning DB via API.
"""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

BASE_URL = "http://localhost:8999"
TOKEN = os.environ["WEBAPP_ACCESS_TOKEN"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

BOOK_ID = "themitmonk"
BOOK_TITLE = "theMITmonk"
LESSON_TITLE = "20 Quantum Cheat Codes That I Wish I Knew In My 20's"
LESSON_INDEX = 1

CHAPTERS = [
    {
        "chapter_index": 1,
        "title": "Money & Investing Foundations",
        "content": """## Money & Investing Foundations (Codes 1, 8–12)

### Code 1 — Invest, Don't Save

Saving is not investing. If you put $5,000/year into an S&P 500 index fund starting in your 20s, compound growth turns that into **$1.4 million** by retirement. Two rules only:
1. Put it in an index fund.
2. **Stay in the market** — never panic-sell.

> During the 2008 financial crisis, pulling out of the market and refusing to re-enter cost 40% of lifetime net worth. Doing nothing would have been the winning move.

Don't chase crypto, meme stocks, or derivatives. Stick to index funds and stay put.

### Code 8 — Emergency Fund

Save **3–6 months of expenses** in a separate, untouched account. Expect the unexpected — job loss, medical bills, family emergencies. Without this buffer, you're forced into bad decisions (selling investments at a loss, taking on debt) the moment life goes wrong.

### Code 9 — FBI: Financial Bureau of Investigation

Track where every dollar goes, then allocate across **4 Es in strict order**:

| Priority | Bucket | What It Covers |
|----------|--------|----------------|
| 1st | Emergency | Safety net — 3–6 months expenses |
| 2nd | Essentials | Rent, utilities, food |
| 3rd | Equity | Investments for long-term wealth |
| 4th | Enjoyment | Vacations, hobbies, fun |

**Only fund Enjoyment after the first three are covered.** Use apps (Mint, Goodbudget) to track and categorize spending automatically.

### Code 10 — Avoid Status Debt

Wealth isn't what you buy — it's **what you keep**. Average US credit card interest: 22–28%. Buying designer clothes or luxury goods on credit is paying a premium to look rich while becoming poorer.

First home purchased at 36 with mortgage at 22% of annual income. That discipline is what real wealth looks like.

### Code 11 — Financial Literacy

Three foundations to learn:
- **Compound interest** — Einstein called it the 8th wonder of the world; understand why it works
- **Credit scores** — your credit profile matters more than your dating profile
- **Taxes** — understand the rules; ignorance is expensive

Recommended books: *Psychology of Money* and *Algebra of Wealth* — focused on mindset and long-term principles, not get-rich-quick schemes.

### Code 12 — Automate Everything

Remove willpower from the equation:
- **Auto-invest** before your paycheck hits your account
- **Auto-pay** bills to never miss a payment or late fee
- **Auto-spending controls** to put guardrails on discretionary spending

If you hate saving, automation does it for you before you can spend it.
""",
    },
    {
        "chapter_index": 2,
        "title": "Career Building",
        "content": """## Career Building (Codes 2–7)

### Code 2 — Build Passion, Don't Follow It

A Canadian university study found only **4% of students** could monetize their passion. The other 96% can't. "Do what you love" is statistically terrible advice.

The correct model: **become great at something valuable, and passion follows mastery**. You don't find your passion — you build it.

### Code 3 — Practice, Practice, Practice

Taylor Swift and Kobe Bryant succeeded not because of talent alone, but because they **out-practiced** everyone else. Musicians from Berklee — among the most talented people on earth — still practice 8–10 hours a day, playing until their fingers bleed.

> "Banking on talent alone is like having a Ferrari with no engine — beautiful to look at, but it's not going anywhere."

Find your superpower (deep focus, communication, technical skill) and practice it relentlessly. Start today.

### Code 4 — Career = Investment Portfolio

Treat skills and connections as **compounding assets**. Starting at a help desk in a dark, windowless room with three smelly colleagues — working 14–15 hours/day for 5 years, accumulating ~15,000 hours of hard and soft skills — led to a program manager role, then CEO of a major tech company.

> "If you want to make more money than others, you have to offer more value than others."

In your 20s, being mistreated and micromanaged is fine — treat it as **getting paid to learn**. Be a learning chameleon.

### Code 5 — Move Where the Action Is

You can't grow your network sitting on Zoom calls in pajamas. Move to where the industry is happening. Moving to New York changed everything — still questions whether San Francisco in the early 2000s would have been even bigger.

Even in remote-friendly roles (legal, software, sales), if you're ambitious — **show up, be seen, collaborate face to face**. The skills built in-person can't be replicated remotely.

### Code 6 — Equity > Salary

> "Salary buys you furniture. Equity buys your future."

The top 1% chase equity, not paychecks. 9 out of 10 equity bets miss — but **one rainmaking event changes your life**. Beyond the upside, even a small equity stake changes how you think: you start acting like an owner, which changes everything about how you work.

Negotiate for equity whenever possible.

### Code 7 — Get a Mentor

Waited until 40 to find a real mentor — 15 years too late. Before that, navigating a career without guidance was like crossing a minefield blindfolded.

Within 10 years of finding the right mentor (a CEO), became a CEO. Skip the expensive executive coaches — find **real mentors who are genuinely invested in you**.

*Recommended reading: Trillion Dollar Coach (about Bill Campbell).*
""",
    },
    {
        "chapter_index": 3,
        "title": "Mindset & Resilience",
        "content": """## Mindset & Resilience (Codes 13–16)

### Code 13 — Go Analog

In the 1970s, 40% of US high school seniors read 6+ books a year. Today, those numbers have flipped — almost nobody reads.

> A **2017 study** found that even a **one-week social media detox** improves attention span and cognitive function.

Deep reading forces critical thinking, complex idea engagement, and vocabulary expansion. In a world where everyone is distracted, **the ability to focus is your competitive advantage**. Doom-scrolling is slowly eroding the very cognitive capability you need to succeed.

Replace scrolling with reading. One week to start.

### Code 14 — Failure = Teacher

Fired **three times**. Each time: on-the-spot, no warning. "We'll send your stuff in boxes. Go spend time with your family." Each time unemployed for **6+ months**. Brutal. Embarrassing. Hard to reach out to anyone.

But here's the truth:

> "Failure is not your tormentor — it's your teacher."

The most successful people fail the most. Every firing prepared the next move. If you learn from failure, it builds you. If you run from it, it haunts you.

### Code 15 — Ask for Help

Fear of rejection is the invisible force field that traps people in mediocrity. Ed Sheeran was rejected by **every single record label** — too ginger, too acoustic, too nerdy. Got booed while performing. Now sells out stadiums and sings with Beyoncé.

> "Help will always be given to those who ask for it." — Dumbledore

Find your tribe — people who inspire, support, and challenge you. The "no" you fear is almost never as bad as staying stuck. Ask this week.

### Code 16 — Don't Play the Victim

Stayed friends with bosses who fired him. Exchanged professional references with them. Had laughs about the day of the firing.

> "Business is never personal."

When you play the victim card, the only person you hurt is yourself. The world doesn't stop to be fair to you. Drop the grudge. Keep the relationship. Life is too short for resentment.

Every person who fired him later became part of his professional network — because he refused to make it personal.
""",
    },
    {
        "chapter_index": 4,
        "title": "Life & Happiness",
        "content": """## Life & Happiness (Codes 17–20)

### Code 17 — Choose Your Partner Wisely

The most important decision you will make is **who you go home to every day**. The wrong partner will leave you emotionally bankrupt regardless of how successful you are professionally.

Our brains operate in two modes:
- **System 1**: Fast, emotional, gut reaction — infatuation, attraction, excitement. Not deep.
- **System 2**: Slow, rational — evaluates long-term compatibility, conflict resolution, shared values.

Most people choose partners with System 1. The lesson: use **System 2**. Spent 6–7 years together before marrying, in the 30s. Understanding how each other thinks, resolves conflict with love and respect.

> "That one decision has made my life richer in every way possible."

### Code 18 — Forgive Your Past

Growing up with a physically abusive father. Left home as a teenager. Homeless in Mumbai, sleeping on train station benches. Joined an ashram to become a monk.

> "Our past is like a bag of bricks. We can decide to put it down."

Forgiveness is not about the other person — it's about freeing yourself. Carrying trauma and resentment doesn't punish them; it punishes you. Tony Stark had daddy issues. Luke Skywalker had daddy issues. You are not alone. **Put down the bag of bricks.**

### Code 19 — Bring Value to Others

> "You live only as long as the last person who remembers you dies." — Native American saying

Your career, your legacy, your impact — it all boils down to one thing: **what you do for other people**. The whispers, the stories, the kindness remembered long after you're gone.

As you grow older, the realization becomes clear: everything that truly matters is about others, not yourself. Impact over income. Legacy over salary.

### Code 20 — H = O/D

A senior monk — a former physician who gave up everything — shared the **happiness equation**:

$$H = \\frac{O}{D}$$

Where:
- **H** = Happiness
- **O** = What you Own (finite, even for the wealthiest)
- **D** = What you Desire (potentially infinite)

| Scenario | Result |
|----------|--------|
| Own > Desire | Happiness increases |
| Desire > Own | Happiness decreases |
| Desires → 0 | Happiness → ∞ |

The key insight: you cannot endlessly grow O (what you own is always finite). The leverage point is **managing D** — your desires.

> "When your desires approach zero, your happiness goes to infinity."

This doesn't mean wanting nothing — it means choosing your desires deliberately, not letting them accumulate unconsciously until they own you.
""",
    },
]

QUIZ_FILE = "data/quiz/themitmonk/250218_20_quantum_cheat_codes_that_i_wish_i_knew_in_my_2.json"
# Distribute 20 quizzes: 5 per chapter (sequential)
QUIZ_SPLITS = [
    slice(0, 5),   # Chapter 1: indices 0-4
    slice(5, 10),  # Chapter 2: indices 5-9
    slice(10, 15), # Chapter 3: indices 10-14
    slice(15, 20), # Chapter 4: indices 15-19
]


def post(path, body):
    r = requests.post(f"{BASE_URL}/api{path}", json=body, headers=HEADERS)
    if not r.ok:
        print(f"  ERROR {r.status_code}: {r.text}")
        sys.exit(1)
    return r.json()


def main():
    # Load quizzes
    with open(QUIZ_FILE) as f:
        all_quizzes = json.load(f)
    print(f"Loaded {len(all_quizzes)} quizzes from {QUIZ_FILE}")

    # 1. Create book
    print(f"\n[1] Creating book '{BOOK_ID}'...")
    book = post("/content/books", {"book_id": BOOK_ID, "title": BOOK_TITLE})
    print(f"    Book id={book['id']} title='{book['title']}'")

    # 2. Create lesson
    print(f"\n[2] Creating lesson '{LESSON_TITLE}'...")
    lesson = post("/content/lessons", {
        "book_id": BOOK_ID,
        "lesson_index": LESSON_INDEX,
        "title": LESSON_TITLE,
    })
    lesson_id = lesson["id"]
    print(f"    Lesson id={lesson_id}")

    # 3. Create chapters + upload quizzes
    for i, chapter in enumerate(CHAPTERS):
        print(f"\n[3.{i+1}] Creating chapter {chapter['chapter_index']}: '{chapter['title']}'...")
        ch = post("/content/chapters", {
            "lesson_id": lesson_id,
            "chapter_index": chapter["chapter_index"],
            "title": chapter["title"],
            "content": chapter["content"],
        })
        chapter_id = ch["id"]
        print(f"    Chapter id={chapter_id}")

        # Build quizzes for this chapter
        quiz_slice = all_quizzes[QUIZ_SPLITS[i]]
        quiz_payloads = []
        for q in quiz_slice:
            correct = q.get("correct_options", [])
            quiz_payloads.append({
                "quiz_type": "multiple_choice",
                "question": q["question"],
                "expected_answer": None,
                "option_a": q.get("option_a"),
                "option_b": q.get("option_b"),
                "option_c": q.get("option_c"),
                "option_d": q.get("option_d"),
                "correct_options": correct,
            })

        print(f"    Uploading {len(quiz_payloads)} quizzes...")
        result = post("/content/quizzes", {"chapter_id": chapter_id, "quizzes": quiz_payloads})
        print(f"    Inserted {result['inserted']} quizzes")

    print("\nDone! Book, lesson, 4 chapters, and 20 quizzes uploaded successfully.")


if __name__ == "__main__":
    main()
