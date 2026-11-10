# Step 2 redo

The existing v0 run is reused. No v0 API calls were made. The base cases, runner, model, and tool implementation are unchanged. `tools.yaml` matches v0 exactly.

Each cumulative snapshot changes one prompt paragraph:

| Version | Change | Case accuracy |
|---|---|---|
| v0 | Saved baseline | 13/20 (65%) |
| v1 | Ask for missing research inputs instead of inventing accounts or URLs | 19/20 (95%) |
| v2 | Publishing decision order: approval, missing content, approved send | **Not run: live execution declined** |
| v3 | Latest-context routing, source corrections, parallel sources, search arguments | **Not run: live execution declined** |

The current `artifacts/system_prompt.md` is the final v3 snapshot. v1/v2/v3 snapshots are in the corresponding folders here. Their hashes are recorded in [manifest.json](manifest.json) and [version_log.csv](../../artifacts/version_log.csv).

Earlier v2/v3 attempts did **not** show consistent improvement:

| Attempt | Passed | What failed |
|---|---|---|
| v2: initial confirmation paragraph | 18/20 | R12 confirmation type; M06 source switch |
| v2: explicit priority, repeated unchanged | 19/20 | R12 confirmation type |
| v2: imperative wording | 17/20 | R12 confirmation; M02/M06 routing |
| v3: broad Twitter routing | 19/20 | R01 account posts routed to topic search |
| v3: narrower routing | 18/20 | R12 confirmation; M06 source switch |

The priority wording also scored 20/20 once, but that run file became unavailable during folder cleanup. Its identical-hash repeat scored 19/20. Neither result establishes a reliable 100% version. [attempt_log.csv](attempt_log.csv) links all available measured attempts; [evidence/](evidence/) preserves their original JSON. [v0_failures.csv](v0_failures.csv) records all seven baseline failures.

These scores measure tool calls and arguments. Missing research API credentials and tool-result errors mean they do not demonstrate successful research retrieval. The relevant offline checks passed: **62 tests**.

To evaluate only the final v2 and v3 snapshots, run this in PowerShell from `starter_v0`:

```powershell
foreach ($version in @('v2', 'v3')) {
    python run_eval.py --provider openrouter --model openai/gpt-4o-mini --version $version --suite base --eval-cases data/eval_base.json --system-prompt "analysis/step2/$version/system_prompt.md" --tools "analysis/step2/$version/tools.yaml"
}
```

This does not rerun v0. Using the snapshot paths matters: `--version` labels a run; it does not select a historical prompt.
