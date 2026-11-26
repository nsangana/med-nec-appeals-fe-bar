# Evidence 18 — Full test run (all suites)

Captured 2026-11-26T08:40Z on the builder's machine against the committed code (local paths shown as <repo>). REAL output, abbreviated to per-file results + summary.

## 1. Python: generator, GenAI parser, eval logic, static guards (pytest)

```
........................................................................ [ 35%]
........................................................................ [ 71%]
..........................................................               [100%]
202 passed in 0.64s
```

Per-file test counts:

```
  14 genai/test_appeal_parser.py
  26 genai/test_eval_logic.py
 123 genai/test_parameterization.py
   2 genai/test_sql_quotes.py
  37 generator/tests/test_generator.py
```

## 2. App: typecheck, lint, unit tests (vitest), production build

```
> tsc -b tsconfig.server.json && tsc -b tsconfig.client.json

> eslint .

 Test Files  5 passed (5)
      Tests  73 passed (73)
✓ built in 1.23s
```

## 3. Bundle

```
deploy_all.sh: syntax OK
Found 1 warning
Validation OK!
```

## What these tests guard

- Generator: determinism (same seed → same data), schema completeness, label/deadline mix, the hero record, laterality consistency, template evidence rules.
- GenAI: response parsing (malformed → NEEDS REVIEW, never WARRANTED), SQL/Python parity, eval logic and the judge-context drift guard.
- Static guards: balanced quotes in every SQL file (regression for a real failure); no hard-coded catalog/schema in SQL; identifier validation in notebooks.
- App: worklist query builder and filters (bound parameters only), review-action guard, edited-letter diff/preview.
