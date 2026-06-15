I am building English vocabulary, especially phrases.
To do that, please help me with a story series that gradually extends the phrases collection.
The story style is that, assume you are a manager in an IT department, and you will guide a junior staff member in working on something or introduce some new things.

## Output format

1. **The story is pure story.** Write `vocab/stories/{yymmdd}_{story name}.md` as a continuous narrative (narration + dialogue) only — no tables, no vocabulary lists, no maps, no recall prompts inside the story file. The target phrases should appear naturally in the prose.

2. **Phrases live in JSON.** Put the phrases taught by each story in `vocab/phrases/{yymmdd}_{story name}.json`, using the same `{yymmdd}_{story name}` base name as the story so they pair up. Each phrase entry has: `phrase`, `meaning`, `example` (the sentence from the story), and `category`.

3. **Cumulative.** Each new story builds on earlier ones and introduces a new batch of phrases, so the collection keeps growing.

## Stories so far

- `260613_the_grand_tour` — onboarding tour of a large company; vocabulary for showing directions and locations.
