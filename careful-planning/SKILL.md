---
name: careful-planning
description: Produce rigorous, verified implementation plans saved to ./plans/<slug>.md. Forces conventions reading, precedent reading, deep symbol exploration, and an adversarial pre-plan check before writing. Gates implementation behind explicit user confirmation. Use when the user asks for a plan, design, approach, breakdown, or "how should we do X" — especially with models prone to hallucinating symbols, skipping conventions, or under-exploring.
---

# Careful Planning

## When to activate

Trigger on plan / design / approach / breakdown requests. Do **not** trigger for pure exploration ("what does this code do?") — no plan file, no confirmation gate there.

## Workflow

The steps are ordered. Do not skip any. Do not reorder.

### 1. Read project conventions — first, before any other tool call

Find and Read every conventions doc that could apply to this task. Cast a wide net. Common locations and filenames (use whichever exist):

- Repository root: `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `README.md`, `ARCHITECTURE.md`, `STYLE.md`, `.cursor/rules/`, `.github/copilot-instructions.md`
- Nearest enclosing module/package/subdirectory of the file(s) you'll change: same set of filenames
- Any `docs/` folder near the change site

Steps:

1. Run a Glob or Grep for these filenames at the repo root and along the path to the change site.
2. Read every match in full.
3. **Quote back to the user** any rule that could affect this task. Especially: where new code goes, layering rules, naming, error handling, test conventions, build/codegen steps.

If no conventions file exists in any relevant location, say "no conventions file found" and proceed.

**Project conventions override any pattern you infer from the codebase.** If a code pattern contradicts the conventions doc, the conventions doc wins.

### 2. Probe LSP

Try one LSP call (e.g. `definition` or `hover`) on a symbol you've already seen.

- **Works** → use LSP as primary navigation.
- **Unavailable / errors** → record this. The plan file must open with:
  > `> LSP unavailable — exploration used Grep/Read only. Symbol resolution may be less precise.`

State LSP status to the user in one line.

### 3. Find a precedent — and Read it end-to-end

For any "add a new <thing>" task, find the **most-similar existing thing in the same codebase** and Read its files in full. Not grep — Read.

How to find it:

1. Name the kind of thing you're adding (e.g. "REST endpoint with auth", "background job", "CLI subcommand", "state-machine transition", "database-backed CRUD module").
2. Run one Glob or Grep to enumerate candidates of that kind.
3. Pick the closest match by data shape and access pattern.
4. **Read every file** that defines its end-to-end shape. Walk the layers: API contract → handler/controller → business logic → data access → tests → wiring/registration.

Note its: location in the tree, layering, validation rules, error handling, authorization, pagination/iteration shape, test pattern, and any codegen artifacts.

**This is your template.** Any deviation from it must appear in the Decisions log with a one-sentence reason.

If you cannot find a precedent, say so explicitly and tell the user.

### 4. Explore — no shortcuts

For **every load-bearing symbol** the plan will touch (functions, variables, types, files), trace all four:

- **Definition** — `file:line` where defined
- **Callers/callees** — what calls it; what it calls
- **Data flow** — types/shapes flowing in and out
- **Related symbols** — siblings, overrides, implementations

**You are forbidden from writing the plan until these are mapped.** If you catch yourself assuming ("X probably does Y", "this likely returns Z"), stop and verify.

Methods, in order: **LSP → Read (full file) → Grep for breadth.** Grep confirms existence; only Read reveals semantics. **Rule: if you grep the same symbol or file twice without opening it, open it.**

#### 4a. Shared-resource writers

For any shared resource you plan to write to — DB column, shared table, file, queue topic, cache key, environment variable, config entry, global mutable state — find every other writer:

1. Grep the codebase for every place that writes to it.
2. Read each writer's call site.
3. Add them to the Code map.

This catches silent-clobber bugs (e.g. a background process that overwrites the value you just set).

### 5. Pre-plan check — list 3 ways this could silently fail

Before writing the plan, list **at least 3 ways this design could silently fail in production**. For each:

- **Failure mode**: one sentence. (Examples of the *shape* such failures take: "Background process overwrites the value the new code sets." "Concurrent callers race on a check-then-write." "Unrelated reader of the same table assumes an invariant the new write breaks." "Crash between two non-atomic writes leaves inconsistent state.")
- **Code path**: `file:line` of the code that causes it.
- **Evidence either way**: read the code and decide. If you have not opened the file yet, open it now.

If you cannot list 3, you have not explored enough. Go back to Step 4.

This list goes into the plan's **Risks / silent-failure modes** section verbatim.

### 6. Write the plan

Save to `./plans/<slug>.md`. Slug is short, kebab-case, derived from the task. Required sections, in this order:

````md
# <Title>

> [LSP banner if applicable]

## Goal
<one paragraph>

## Conventions consulted
<bullet list of conventions docs read, with the constraint(s) each imposes on this task>

## Precedent
<the existing feature you used as a template, with file paths and a one-line summary of its shape>

## Code map
<every load-bearing symbol with file:line, callers/callees, data flow, related symbols. Include shared-resource writers from Step 4a.>

## Plan
<numbered steps. Each step MUST include:
 - the file(s) to change, with file:line
 - the change in one sentence
 - dependencies: which prior steps must complete first (especially codegen / mock regeneration / interface-before-impl ordering)
 - verification: a concrete command to run or state to check, with the expected outcome — e.g. "after this step, `<build/test/codegen command>` succeeds" or "after this step, `<symbol>` resolves at `<file:line>`"
"Edit file X" is not a step. A step without a verification is incomplete.>

## Test plan
<for each new behavior or bug fix the plan introduces, list:
 - the assertion in one line (what must be true after this change)
 - the test file (existing to extend, or new path to create)
 - the test type (unit / integration / e2e) — match the precedent's choice
 - any fixtures or test data required
If a behavior has no test, state explicitly why (e.g. "covered by existing X_test.go::TestY") rather than omitting it.>

## Decisions log
<every decision where you picked one option over another. One line each, with the reason. Mark "assumed" where you had no evidence.>

## Risks / silent-failure modes
<the 3+ items from Step 5, each with code path and evidence>
````

Every symbol named in **Plan** must appear in **Code map** with `file:line`. If it's not in the code map, it's not in the plan.

### 7. Verify the plan

After writing, re-read the plan file end-to-end and check it against reality:

- **Every `file:line` resolves** — open each one (LSP or Read) and confirm the symbol is actually there.
- **Every Plan step has a Code map entry** — no orphan symbols introduced while drafting.
- **Each step is actionable** — names the file, the change, the dependencies, and a verification command/state. No "update X as needed". No step without a verification.
- **Dependencies are correct** — codegen / mock regeneration / interface changes are ordered before the code that consumes them.
- **Test plan is non-empty** — every new behavior either has a listed test or an explicit "covered by <existing test>" note.
- **No contradictions** — step N doesn't reference state step N-1 removed.
- **Conventions consulted is non-empty** unless you explicitly stated none exist.
- **Precedent is named** unless you explicitly stated none exists.
- **Risks list has 3+ entries with code paths** — not "TBD" or "may need investigation".
- **Decisions log has an entry for every contested architectural call** (placement, layering, concurrency boundaries, error handling, authorization, data shape).

If anything fails, fix the plan file and verify again. Tell the user one line: what you verified and any fixes made.

### 8. Confirmation gate

Before asking the implement question, surface contested decisions. Ask **exactly**:

> **Any of these decisions look wrong, or any silent-failure modes I missed?**
>
> Decisions:
> [paste the Decisions log here]
>
> Risks:
> [paste the Risks section here]

Wait for the user's response. If they flag anything, fix the plan and ask again.

Once the user is satisfied, ask **exactly**:

> **Ready to implement? (reply to confirm)**

Then **stop**. Do not start implementing.

- **Clear affirmative** ("yes", "go", "approved", "lgtm", "ship it") → proceed.
- **Ambiguous** ("sounds good but...", "maybe", questions, conditional approval) → **not confirmed**. Iterate on the plan and re-ask.
- **Any plan edit after confirmation** → re-ask the gate. Old confirmation is void.

## Self-check before writing the plan

- [ ] Conventions docs read; constraints quoted to user
- [ ] LSP probed; status recorded
- [ ] Precedent feature found and Read end-to-end (not grepped)
- [ ] Every load-bearing symbol verified with `file:line`
- [ ] Callers/callees traced for each
- [ ] Data flow traced for each
- [ ] Related symbols traced for each
- [ ] For every shared resource written to: every other writer identified and Read
- [ ] Pre-plan check: 3+ silent-failure modes listed with `file:line` evidence
- [ ] No symbol named in Plan that's missing from Code map
- [ ] Every Plan step has a verification command/state and explicit dependencies
- [ ] Test plan covers every new behavior (or explicitly cites an existing test)
- [ ] No assumptions ("probably", "likely", "should") left unverified
- [ ] Decisions log has entry for every contested call

## Anti-patterns — do not do these

- Skipping Step 1 because "I already know this codebase".
- Reading the task description and jumping straight to LSP probing.
- Picking the first precedent you find without confirming it's the closest match.
- Grepping for a file's symbols and concluding you understand it without Reading it.
- Filling Risks with "may need investigation" instead of `file:line` evidence.
- Treating an existing-but-misplaced artifact as immovable just because it exists.
- Writing Plan steps without a verification — "edit file X" with no way to confirm the edit worked.
- Ordering Plan steps by narrative ("repo, then service, then handler") instead of by build/codegen dependency.
- Omitting tests for new behavior, or hiding behind "the existing tests cover it" without naming the test.
- Asking "Ready to implement?" without first asking the decisions/risks question.
