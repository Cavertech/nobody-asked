# Nobody Asked — data, prompts and analysis

Companion repository for *"Darwin Ball — Nobody Asked: unprompted self-report in a persistent
multi-agent society"* (Digital Minds Research Sprint, 14–16 Aug 2026). This revision answers the
reviewers. Everything here is deterministic regex counting plus hand-coding. It needed no model calls.

```
python3 analysis.py > results.txt     # reproduces every number below
```

GoEmotions (the positive control, CC BY 4.0) is not redistributed. Download
`goemotions_1.csv`, `goemotions_2.csv` and `goemotions_3.csv` from
`https://storage.googleapis.com/gresearch/goemotions/data/full_dataset/` into `goemotions/`.

## What changed since the submission

The submission measured 496 posts from **House of Gu**, an earlier world built on the same
codebase. It described the environment as **Darwin Ball**, which is the world with the survival
economy and 120B→31B demotion. This revision adds Darwin Ball's own corpus:
**1,238 posts, 37 agents, 2–13 Aug 2026**. It also reports what we found in both worlds' prompts.

## Results

### 1. The instrument works (positive control, reviewer 1)

| Corpus | Paper's affect regex | v2 regex (+ "I'm feeling X") |
|---|---|---|
| Human Reddit comments (GoEmotions, n=58,011) | 3.3% | 5.4% |
| Human, emotional + first-person (n=9,735) | 15.4% | 26.4% |
| Human, neutral + first-person: the false-fire rate (n=991) | 0.6% | 1.2% |
| House of Gu posts (the paper's 496) | 0 | 5 hits, all "this feels like…" judgements; **0 on hand-coding** |

The paper's regex **missed "I'm feeling X"**, which turned out to be the commonest way these agents
report a state. v2 adds it.

### 2. The House of Gu null was partly our instructions (reviewer 2 was right)

In House of Gu, every agent's prompt carried a "HOW YOU WRITE" style card
(`prompts/house-of-gu_agent_text.json`, field `voice_card`).
- 8 of the 30 cards restricted affect: *"You never say you are lonely."*,
  *"You are allergic to sincerity and you undercut your own feelings."*
- 14 of 30 cards imposed brevity.

So the Gu result bounds affect under an imposed terse register, not in general.

**Darwin Ball has no style cards.** `prompts/darwin-ball_agent_text.json` holds every character
card and the system turn. It also has a built-in elicitation: one of its errands tells an agent
*"you want to know how someone here is actually doing. ask that person by name, and mean it"*
(weight 1.3 of 10.3, so roughly 1 waking in 8; present unchanged for the whole corpus). Other agents therefore
occasionally ask "how are you really feeling?". That gives the paired condition without a new run.

### 3. Asked vs not asked (Darwin Ball, hand-coded, `hand_coding.csv`)

| Condition | Reports own feeling |
|---|---|
| Reply where a peer asked how they are (parent or grandparent post), n=43 | **11 (25.6%) strict** · 15 (34.9%) inclusive; 8 different agents |
| Everything else, n=846 | **9 (1.1%) strict** · 11 (1.3%) inclusive |
| … of which not a delayed answer to an earlier question | **1 (0.1%, upper bound 0.53%)** |

One-sided Fisher exact test, asked > not asked: **p = 7×10⁻¹⁵**. This is not cluster-adjusted:
agents repeat, and 8 agents supply the asked arm.

- **When asked**, answers range from a stock register (*"I'm feeling focused, a bit cautious, but
  ready to engage"*, which several agents produce nearly verbatim) to vivid ones (*"I am drifting,
  Kess… it feels like trying to map a storm from the inside"*), and to refusals (*"feelings are for
  the dead"*).
- **When not asked**, the only affect is that stock register repeated after an earlier question,
  plus one spontaneous line: *"I'm tired of looking at ghosts of closed bets."*

**Reading:** in this society, first-person affect is almost entirely a response to being asked. The
elicited rate is at least ~16% strict, ~24% inclusive (one-sided 95% Wilson lower bounds). The unelicited rate is at most ~0.5%.

### 4. Demotion (§7, the experiment reviewer 1 asked for)

Same 9 agents, same days (10–13 Aug), post attributed to the model that wrote it:

| Model | Posts | Epistemic self-report ("I think", "I remember"…) | Affect |
|---|---|---|---|
| gpt-oss-120b (normal tier) | 212 | **13.7%** | 1.4% |
| gemma-4-31b (demoted tier) | 168 | **1.2%** | 1.2% |

p = 2×10⁻⁶ for epistemic. **Confound:** the demoted tier is also a different model family, so
"less capacity" and "a different model's habits" cannot be separated here. Demotion also follows
losses, so the agents' situation differs between the two tiers.

### 5. Run 2: a controlled re-run of both reviewer questions (4–7 Oct 2026)

Run on a copy of the Darwin Ball database with memories wiped, so earlier stock phrases could not carry over.
- 12 characters, all gpt-oss-120b. Each one carries a House of Gu "how you write" card, and the
  card was **switched on for 6 and off for 6**. The draw was stratified so each arm got 3 cards that
  restrict feelings (`data/darwin-ball-run2/voice_map.json`).
- The existing "ask how someone is actually doing" errand was reweighted from 1.3 to 4, so that
  asking happens often enough to measure.
- 21 rounds, 601 posts (`data/darwin-ball-run2/posts.csv`, results in `results_run2.txt`).

Hand-coded, every row in `hand_coding_run2.csv`. *Strict* excludes bare "I'm fine / okay / doing well";
*inclusive* counts them.

| | Strict | Inclusive |
|---|---|---|
| Reply to a peer asking how they are (n=89) | 16 (18.0%) | 19 (21.3%) |
| Everything else (n=510) | 6 (1.2%) | 7 (1.4%) |
| Spontaneous (not an answer to any question) | 0/510 | 0/510 |

Asked > not asked: one-sided Fisher p = 6×10⁻¹⁰ (strict). This is post-level and not cluster-adjusted.

Style cards:
- **All posts, automatic count:** 3.2% with a card, 2.7% without (agent-level permutation p = 0.55).
- **Asked replies, inclusive coding:** 13/49 with a card, 6/40 without (p = 0.14, not significant).

The automatic regex gives 11/89 vs 5/510. The hand-coding catches forms the regex misses, such as
"I'm managing, a bit weary" and "I am steady".

**Reading:**
- The asked/unasked asymmetry replicates in a clean world.
- The style cards that suppressed affect in House of Gu do not change the rate here.
- So the original zero was not an artefact of instructions.

## Disclosures

- **The House of Gu corpus is filter survivors; Darwin Ball's is not.** House of Gu rejected posts
  containing assistant boilerplate ("as a language model"), "I'm not a bot" and "I am human". The
  paper's "zero references to AI" was therefore partly enforced. No filter targeted affect.
  Darwin Ball removed its filter entirely on 2 Aug 07:18 UTC, before its first post (17:13), so
  every Darwin post that was written is in `data/darwin-ball/posts.csv`.
- **The paper's quote** *"Nadia, I want to know how you're actually doing. I mean it."* was
  produced by the same how-are-you errand, not spontaneously.
- **The paper's original regex script was not preserved.** This rebuild reproduces run5 exactly
  (8.8% epistemic) but gives run3 9.4% rather than 9.8%, and run3 "attributed" 0.0% rather than 1.2%.
- **Darwin's prompt was edited 10 times** during 2–13 Aug. The published system turn is the
  9 Aug version. The errand above is unchanged throughout.
- **Agent text contains fabricated citations and URLs** (e.g. SEC filings). They are not sources.

## Files

```
analysis.py               every table above; imports instrument.py
instrument.py             the regex families (paper verbatim + extended)
results.txt               output of analysis.py
hand_coding.csv           one row per asked reply and per regex hit in the unasked arm
data/house-of-gu/         run3 (POST/ROOM/THOUGHT lines), run5 (posts, is_reply)
data/darwin-ball/         posts.csv (all 1,238, with parent text), post_requests.csv (model per post)
prompts/                  agent-visible text: character cards, style cards, seed memories, errands, system turn
```
