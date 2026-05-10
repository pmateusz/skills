---
name: prd-to-ferment
description: Reframe a PRD markdown document into answers to four discovery questions (build, goal, success criteria, non-negotiables) without losing information. Use when the user wants to ferment, distill, or reframe a PRD, or mentions "prd-to-ferment".
---

# prd-to-ferment

Reframe a PRD into a Q&A structure so the user can iterate on it.

## Input

A file path to a PRD markdown document, passed as the skill argument.

## Workflow

1. Read the PRD file at the provided path.
2. Reframe its contents into answers to the four questions below. Preserve every piece of information from the source — redistribute, do not summarize away.
3. Print the result to chat using the output template. Do not write a file.

## The four questions

1. **What would you like to build?** — Reference the source PRD path on the first line, then describe scope/shape of the thing.
2. **What does done look like? (goal)** — The end state. What exists when this is finished.
3. **How will we know we got there? (success criteria)** — Observable, checkable signals. Metrics, behaviors, acceptance tests.
4. **What should we avoid? Any non-negotiables?** — Constraints, anti-goals, hard limits, things explicitly out of scope.

## Output template

```md
**Source:** `<path/to/prd.md>`

### 1. What would you like to build?
<answer>

### 2. What does done look like? (goal)
<answer>

### 3. How will we know we got there? (success criteria)
<answer>

### 4. What should we avoid? Any non-negotiables?
<answer>
```

## Rules

- No information loss. If a PRD detail does not obviously fit one question, place it in the closest match rather than dropping it.
- Do not invent content not present in the PRD. If a question has no source material, answer with `_(not specified in PRD)_`.
- Keep the user's original wording where it carries meaning; rephrase only to fit the question frame.
- After printing, ask the user which answer they want to revise first.
