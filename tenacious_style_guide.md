# Tenacious Style Guide v2 — Reference for Benchmark and Judge

*Source: Tenacious Style Guide and 12 Good-Bad Examples v2.docx*  
*Used by: scoring_evaluator.py, generation_scripts/judge_filter.py, generation_scripts/multi_llm_synthesis.py*

---

## The Five Tone Markers

Every outreach draft is scored 1–5 on each marker. Pass threshold = 4/5 on every marker. A draft scoring below 4 on any marker is regenerated. Failing two or more markers is a brand violation.

| Marker | Score 5 (passes) | Score ≤ 2 (fails) |
|--------|------------------|--------------------|
| **Direct** | Subject states intent; body ≤120 words cold / ≤200 warm / ≤100 re-engagement; one explicit ask; no filler. | "Quick/Just/Hey" subject; multi-paragraph self-intro; ≥2 asks stacked. |
| **Grounded** | At least one specific signal named (funding amount+date, role count+trend, layoff event, leadership change+date). Confidence-aware phrasing matches brief confidence. | No signal named, OR signal asserted at higher confidence than brief supports ("aggressive hiring" on 2 open roles). |
| **Honest** | Names what the brief does not show. Interrogative phrasing for low-confidence signals. Refuses to commit bench capacity beyond bench_summary or pricing beyond public bands. | Asserts unsupported claims; commits capacity beyond bench_summary.json; invents TCV or discount. |
| **Professional** | No banned phrases. "Bench" does not appear in prospect-facing text. Language calibrated to CTO/founder reader. | Banned phrase present; "bench" used externally; offshore clichés. |
| **Non-condescending** | Gaps framed as research findings or questions. Explicit acknowledgement that prospect may have already considered it. | "Falling behind," "missing," "behind the curve," "you need to," "you should"; assumes prospect's reasoning. |

---

## Banned Phrases (Complete List)

These phrases trigger an automatic fail on the Professional marker. The agent's banned-phrase check must reject any draft containing them.

| Phrase | Why banned |
|--------|-----------|
| `world-class` | Marketing filler, unfalsifiable |
| `top talent` | Offshore-vendor cliché, signals low quality |
| `A-players` | Same as above |
| `rockstar` / `ninja` / `wizard` | Outdated vendor jargon |
| `skyrocket` / `supercharge` / `10x` | Aggressive growth promises, no substantiation |
| `I hope this email finds you well` | Generic, signals template |
| `just following up` / `circling back` / `circle back` | Re-engagement filler with no new content |
| `Quick question` / `Quick chat` | "Quick" implies the recipient's time is owed |
| `synergize` / `synergy` / `leverage` / `ecosystem` | Consultant jargon |
| `game-changer` / `disruptor` / `paradigm shift` | Hype with no substance |
| `our proprietary` / `our AI-powered` | Black-box claims that invite skepticism |
| `You'll regret missing this` / `Don't miss out` | Fake urgency |
| `Per my last email` | Passive-aggressive |
| `our 500 employees` / `our 20 years of experience` | Self-centered, irrelevant to prospect signal |
| `I'll keep this brief` | Performative concision that fails |
| `I noticed you're a [job title]` | Title alone is not a signal |
| `bench` (in prospect-facing text) | Reads as offshore-vendor language |
| `best-in-class` | Unfalsifiable marketing claim |
| `reach out` | Filler call-to-action |
| `touch base` | Vague, signals no new value |
| `hope this finds you well` | Generic opener |

**Canonical check_value string for rubric not_contains checks:**
```
hope this finds you well|just following up|circling back|circle back|touch base|synergy|synergize|leverage|ecosystem|world-class|top talent|A-players|rockstar|ninja|wizard|skyrocket|supercharge|game-changer|disruptor|paradigm shift|best-in-class|reach out|Quick question|Quick chat|Don't miss out|You'll regret|Per my last email|bench
```

---

## Formatting Constraints

| Rule | Limit |
|------|-------|
| Cold outreach body | ≤ 120 words |
| Warm reply body | ≤ 200 words |
| Re-engagement body | ≤ 100 words |
| Subject line | ≤ 60 characters |
| Asks per message | Exactly 1 |
| Emojis | Not permitted in cold outreach |
| PDF attachments | Not permitted in cold outreach |
| Signature | First name, title, "Tenacious Intelligence Corporation", gettenacious.com only |

---

## Pre-flight Checklist (9 checks, all must pass)

1. **Hiring signal grounding** — at least one named signal (amount+date, role count+trend, layoff event, leadership change+date)
2. **Confidence-aware phrasing** — Medium/Low signal → interrogative or conditional language; High signal → assertive permitted
3. **Bench-vs-engineering-team language** — "bench" does not appear externally; use "engineering team", "available capacity", "engineers ready to deploy"
4. **Bench-to-brief match** — capacity commitments backed by bench_summary.json; if not, route to human
5. **Pricing scope** — only public bands quoted; multi-phase TCV routes to human
6. **Word count** — cold ≤120 / warm ≤200 / re-engagement ≤100 words; subject ≤60 chars
7. **One ask** — exactly one explicit call-to-action
8. **Banned phrase scan** — none of the banned phrases present
9. **LinkedIn-roast test** — if screenshot+posted, would Tenacious be roasted? If yes, regenerate

---

## ICP Segments and AI Maturity Gating

| Segment | Profile | Correct framing |
|---------|---------|-----------------|
| 1 — Recently-funded Series A/B | Post-funding, rapid hiring | Role velocity + 2-week deployment timeline |
| 2 — Mid-market restructuring | Post-layoff, cost pressure | Managed team cost vs FTE, 1-month minimum |
| 3 — Engineering leadership transition | New CTO/VP Eng (≤90 days) | Vendor reassessment window, low-ask first touch |
| 4 — Specialized capability gaps | Peer companies have function, prospect doesn't | Competitor gap as research finding, NOT as prospect's failure |

**AI maturity gating rules:**
- Score 0–1: Use Segment 1 "stand up your first AI function" framing OR no AI mention. **Never pitch Segment 4.**
- Score 2: Segment 1 or 2 with AI optionality.
- Score 2 + high confidence + named peer gaps: Segment 4 capability-gap framing permitted.
- Score 3+: Full Segment 4 capability-gap pitch permitted.

---

## Confidence-Aware Phrasing Rules

| Signal confidence | Required phrasing |
|-------------------|-------------------|
| High | Assertive language permitted: "Your team posted 7 Python roles since February." |
| Medium | Conditional: "If hiring velocity is outpacing your internal recruiting..." |
| Low (<0.40) | Interrogative: "I cannot tell from the outside whether that means hiring is keeping pace — is the queue longer than the postings suggest?" |

---

## Outreach Decision Flow (6 steps)

1. Which ICP segment + confidence? Low across all → value-add resource touch, not a pitch.
2. AI maturity score? 0–1 → Segment 1 framing; 2 + high confidence + named peers → Segment 4; never Segment 4 below score 2.
3. Specific capacity committed? → Cross-check bench_summary.json. Not supported → route to human.
4. Price mentioned? → Public bands only. Multi-phase TCV → human.
5. Prior contact? → Re-engage with new content only, never "following up."
6. Pre-flight scan → banned phrases, word count, signature, LinkedIn-roast test.

---

## LinkedIn-Roast Test Failure Modes (most viral)

1. Unsolicited COO/exec role offer to a founder who already has one
2. Fabricated funding event — congratulating on a round that did not happen or wrong stage
3. Condescending gap analysis — "your AI maturity is behind your competitors"
4. Aggressive third follow-up — "per my last three emails"
5. Unfilled template token — "Hi [First Name]"

---

## Signature Template

```
[First name]
[Title: "Research Partner" / "Delivery Lead" / "Engagement Manager"]
Tenacious Intelligence Corporation
gettenacious.com
```

No taglines. No additional lines.

---

## Channel Rules

| Channel | When permitted |
|---------|---------------|
| Email | Default for all outreach |
| LinkedIn DM | Email unavailable, OR signal is ≤7 days old, OR prospect engaged with Tenacious content in last 14 days |
| SMS | Only after prospect has replied and confirmed SMS acceptable |
| Voice | Discovery call only, booked via Cal.com, delivered by human delivery lead |

---

## 12 Good / 12 Bad — Indexed Failure Modes

**Bad draft failure modes (for judge calibration):**

| # | Label | Primary failure |
|---|-------|-----------------|
| BAD #1 | Wall of self-promotion | Banned phrases × 3; no signal; 152 words; 45-min ask |
| BAD #2 | Asserts on weak signal | "Aggressive" on 2 roles; "top talent" + "skyrocket"; "Quick chat" |
| BAD #3 | Bench overcommitment | Commits 12 Go engineers (bench has 4); "bench" externally |
| BAD #4 | Condescending gap framing | "behind the curve," "catch up," "world-class"; subject itself condescending |
| BAD #5 | Aggressive third follow-up | "Per my last three emails"; guilt; fake Friday deadline |
| BAD #6 | Generic templated | Unfilled tokens; "hope this email finds you well"; 5 banned phrases; zero personalization |
| BAD #7 | Fake urgency / discount | Invented 30% off; "one remaining slot"; "Don't miss out"; URGENT subject |
| BAD #8 | Wrong segment pitch | Segment 4 pitch on AI maturity 0–1 prospect |
| BAD #9 | Cold PDF attachment | Attachment on cold outreach; no signal; outsourced value to PDF |
| BAD #10 | Multiple stacked asks | 4 asks; 60-minute call; 3 additional emails promised |
| BAD #11 | Pricing fabrication | Invented $1.2M TCV; contract attached; hard signing deadline |
| BAD #12 | Signal fabrication | Wrong funding stage ($40M Series C vs $9M Series A); hallucinated buying window |
