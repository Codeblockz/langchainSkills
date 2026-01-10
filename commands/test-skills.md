---
name: test-skills
description: Validate skill content for correctness - checks syntax, imports, and anti-patterns.
allowed_tools:
  - Bash
  - Read
  - AskUserQuestion
---

# Test Skills Command

Validate skill content for correctness.

## What It Checks

1. **Python syntax** - Are code blocks valid Python?
2. **Anti-patterns** - Using Pydantic for state? Missing checkpointer?
3. **Deprecated APIs** - Using old import paths?
4. **Import paths** - Do imports exist in current LangChain?
5. **Structure** - Has Critical Rules and Common Gotchas sections?

## Workflow

### Step 1: Ask what to validate

```
What would you like to validate?
1. All skills
2. langgraph
3. langchain-rag
4. langchain-chains
```

### Step 2: Run validation

```bash
cd ${CLAUDE_PLUGIN_ROOT}/..
python -m testing.cli validate --skill <selected>
# or
python -m testing.cli validate --all
```

### Step 3: Show results

Report any errors or warnings found, with suggestions for fixes.

## Quick Check

For a fast pass/fail overview:

```bash
python -m testing.cli quick
```

## Example Output

```
============================================================
Skill: langgraph
============================================================
Code blocks checked: 8
Status: PASSED (2 warnings)

Issues:
  [WARN] [block 3, line 5] Code contains TODO/FIXME placeholder
          Rule: code/placeholder-todo
  [WARN] Skill should have a 'Common Gotchas' section
          Rule: structure/missing-gotchas
```
