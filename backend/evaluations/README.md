# Golden evaluation cases

`golden_cases.json` is the deterministic regression set for the three supported investigation scenarios. Each case checks the expected category, safe next step, minimum confidence, required evidence sources, citation validity, and prompt version.

Run the evaluation from the Compose environment:

```bash
docker compose run --rm --user root api pytest -q tests/test_evaluation.py
```

When the prompt version changes, update the case version deliberately and compare the case results before accepting the change.
