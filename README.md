# GenLearn-agentic-learn-content-system

GenLearn is a compact deterministic prototype for a self-evaluating lesson generator.

## Workflow

Load Memory -> Generate -> Fact Check -> Hard Validate -> Rubric Evaluate -> Repair if Failed -> Re-evaluate -> Write Memory -> Output

The current submission uses a deterministic template-driven generator plus deterministic validators and repair logic. No external LLM is required.

## Run

```bash
python -m pip install -e .
python -m genlearn.cli --topic "Introduction to RAG"
```

## Fault injection demo

```bash
python -m genlearn.cli --topic "Introduction to RAG" --inject-fault
```

The CLI prints a JSON result with the final lesson, pass/fail details, rejection log, and persisted memory updates.

## How it works

1. `Load Memory` reads prior runs and failure patterns from `data/memory.json`.
2. `Generate` builds a beginner lesson and claim list from the deterministic topic fact pack.
3. `Fact Check` verifies the claims against the curated fact pack.
4. `Hard Validate` checks required sections, claims presence, grounding, and length.
5. `Rubric Evaluate` applies atomic pass/fail quality checks.
6. `Repair` rebuilds the lesson from the curated template using the failed criteria.
7. `Re-evaluate` runs fact check, hard validation, and rubric evaluation again.
8. `Write Memory` stores the run, failed criteria, and fix pattern for future runs.

Fault injection deliberately swaps in a wrong claim on the first attempt so the repair loop can be demonstrated.
