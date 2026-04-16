# English Vocabulary Lesson Template

Save to: `data/lesson/{channel_slug}/{yymmdd}_{slug}_vocab.md`

See SKILL.md for the naming convention. Append `_vocab` to the slug to distinguish from regular lessons.

Generate a document with sections separated by `---` horizontal rules. The lesson has 3 sections.

Use the Write tool (not Bash) to create the lesson file directly.

---

## Section 0: ## Material

```markdown
## Material

- **Video:** [Video Title](https://www.youtube.com/watch?v=VIDEO_ID)
- **Channel:** Channel Name
- **Published:** YYYY-MM-DD
- **Transcript:** [data/transcript/{channel_slug}/{yymmdd}_{slug}.md](data/transcript/{channel_slug}/{yymmdd}_{slug}.md)
- **Type:** English Vocabulary
```

---

## Section 1: ## Vocabulary

A table of all extracted vocabulary words/phrases, grouped by category.

### Guidelines
- Group words by category (Nouns, Verbs, Adjectives, Prepositions/Phrases)
- Each entry has: **Word/Phrase**, **Definition**, and **Sentence** (from the transcript)
- Definitions should be simple, clear, and practical
- Bold the vocabulary word in the sentence column
- If a word appears in multiple sentences, pick the most illustrative one

### Example

```markdown
## Vocabulary

### Nouns

| Word | Definition | Sentence |
|------|-----------|----------|
| window sill | the flat shelf at the bottom of a window | My alarm clock is on the **window sill**. |
| curtains | fabric hanging over a window to block light | The window has white **curtains**. |
| pillow | a soft cushion for resting your head on | There are two **pillows** on the bed. |
| wardrobe | a tall cabinet for storing clothes | My **wardrobe** is next to the bed. |
| wastebasket | a small bin for throwing away trash | My **wastebasket** is next to the chair. |
| rug | a thick fabric covering part of the floor | There is a large **rug** in the middle of my room. |
| ceiling | the top surface of a room (opposite of floor) | A lamp hangs from the **ceiling** of the room. |
| light switch | a button/lever on the wall to turn lights on/off | The **light switch** is next to the window. |
| poster | a large printed picture for decoration | There's a **poster** above the light switch. |
| dresser | a piece of furniture with drawers for clothes | It's a **dresser**. |
| drawer | a sliding box inside a dresser or desk | The dresser has four **drawers**. |
| globe | a round model of the Earth | There's a **globe** on the dresser. |
| armchair | a comfortable chair with side supports for arms | My **armchair** is in front of the television. |
| remote control | a device to operate TV/electronics from a distance | Next to the **remote control** is a vase. |
| vase | a container for holding flowers | Next to the remote control is a **vase**. |

### Verbs

| Word | Definition | Sentence |
|------|-----------|----------|
| rings | makes a sound (alarm, bell, phone) | The alarm clock **rings** every day at 7 o'clock. |
| hangs | is attached from above, suspended | A lamp **hangs** from the ceiling of the room. |

### Adjectives

| Word | Definition | Sentence |
|------|-----------|----------|
| comfortable | giving physical ease and relaxation | My bed is very **comfortable**. |

### Prepositions & Phrases

| Phrase | Meaning | Sentence |
|--------|---------|----------|
| in front of | directly before something | My desk is **in front of** the wardrobe. |
| next to | beside, right at the side of | My wardrobe is **next to** the bed. |
| in the middle of | at the center of | There is a large rug **in the middle of** my room. |
| above | higher than, over | There's a poster **above** the light switch. |
```

---

## Section 2: ## Story

Write a short, engaging story that uses **every vocabulary word** at least once. Guidelines:

- Read `.claude/skills/personal_background.md` for the user's background
- Use a scenario relatable to the user (e.g., moving into a new apartment in Hong Kong, setting up a home office, weekend cleaning)
- **Bold** each vocabulary word the first time it appears in the story
- Keep it conversational — short paragraphs, simple vocabulary beyond the target words
- End with `**Vocabulary count:** {N} words used in context`

### Example

```markdown
## Story

Wei just moved into a new apartment in Sha Tin, near the Science Park. The first thing he noticed was the big **window sill** — perfect for his daughter's little plant. He put up white **curtains** to block the afternoon sun.

His wife picked a **comfortable** bed with two soft **pillows**. The **wardrobe** went next to the bed — just enough space for both their clothes. Wei built a small **dresser** with four **drawers** for his daughter's things and placed a **globe** on top, so she could find Hong Kong on the map.

His work corner was simple: a desk, a chair, and a **wastebasket** for all the printouts he never needed. A large **rug** sat **in the middle of** the living room. A lamp **hangs** from the **ceiling**, and the **light switch** is **next to** the window. His daughter stuck a **poster** of a sunflower **above** the switch.

In the evening, Wei sits in his **armchair** **in front of** the television, picks up the **remote control**, and relaxes. His wife put a **vase** with fresh flowers on the side table. Every morning at 7, the alarm clock **rings** from the **window sill**, and a new day starts.

**Vocabulary count:** 19 words used in context
```

