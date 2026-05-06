---
name: careful-planning
description: Produce rigorous, verified implementation plans saved to ./plans/<slug>.md. Forces deep symbol exploration before planning, probes for LSP, and gates implementation behind explicit user confirmation. Use when the user asks for a plan, design, approach, breakdown, or "how should we do X" — especially with weaker models that hallucinate symbols or jump to coding.
---

# Careful Planning

## When to activate

Trigger on plan / design / approach / breakdown requests. Do **not** trigger for pure exploration ("what does this code do?") — no plan file, no confirmation gate there.

## Workflow

### 1. Probe LSP

Before exploring, try one LSP call (e.g. `definition` or `hover`) on a symbol you've already seen.

- **Works** → use LSP as primary navigation. Fall back to Grep/Read only when LSP returns nothing.
- **Unavailable / errors** → record this. The plan file must open with:
  > `> LSP unavailable — exploration used Grep/Read only. Symbol resolution may be less precise.`

State LSP status to the user in one line before exploring.

### 2. Explore — no shortcuts

For **every load-bearing symbol** the plan will touch (functions, variables, types, files), trace all four:

- **Definition** — `file:line` where defined
- **Callers/callees** — what calls it; what it calls
- **Data flow** — types/shapes flowing in and out
- **Related symbols** — siblings, overrides, implementations

**You are forbidden from writing the plan until these are mapped.** If you catch yourself assuming ("X probably does Y", "this likely returns Z"), stop and verify. Hallucinated symbol names break the plan — verify, don't guess.

Methods, in order: LSP `definition` / `references` / `hover` → Grep / Glob → Read.

### 3. Write the plan

Save to `./plans/<slug>.md`. Slug is short, kebab-case, derived from the task. Required sections:

```md
# <Title>

> [LSP banner if applicable]

## Goal
<one paragraph>

## Code map
<every load-bearing symbol with file:line, callers/callees, data flow, related symbols>

## Plan
<numbered steps, each referencing file:line>

## Risks / open questions
<concise list>
```

Every symbol named in **Plan** must appear in **Code map** with `file:line`. If it's not in the code map, it's not in the plan.

### 4. Verify the plan

After writing, re-read the plan file end-to-end and check it against reality:

- **Every `file:line` resolves** — open each one (LSP or Read) and confirm the symbol is actually there. Stale line numbers from earlier exploration are common; re-check.
- **Every Plan step has a Code map entry** — no orphan symbols introduced while drafting.
- **Each step is actionable** — names the file, the change, and what the post-state looks like. No "update X as needed".
- **No contradictions** — step N doesn't reference state that step N-1 removed.
- **Risks list is real** — at least one entry, or explicitly state "no known risks".

If anything fails, fix the plan file and verify again. Tell the user one line: what you verified and any fixes made.

### 5. Confirmation gate

After writing the plan, ask exactly:

> **Ready to implement? (reply to confirm)**

Then **stop**. Do not start implementing.

- **Clear affirmative** ("yes", "go", "approved", "lgtm", "ship it") → proceed.
- **Ambiguous** ("sounds good but...", "maybe", questions, conditional approval) → **not confirmed**. Iterate on the plan and re-ask.
- **Any plan edit after confirmation** → re-ask the gate. Old confirmation is void.

## Self-check before writing the plan

- [ ] LSP probed; status recorded
- [ ] Every load-bearing symbol verified with `file:line`
- [ ] Callers/callees traced for each
- [ ] Data flow traced for each
- [ ] Related symbols traced for each
- [ ] No symbol named in Plan that's missing from Code map
- [ ] No assumptions ("probably", "likely", "should") left unverified
- [ ] Post-write verification pass completed; every `file:line` re-resolved
