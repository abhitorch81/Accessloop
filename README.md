# AccessLoop Agent

A small, reusable Python agent harness for tool-driven tasks. The core is independent of any model provider or browser library. It supports bounded runs, explicit tool approval, event hooks, and SQLite checkpoints. The long-term application is evidence-backed web accessibility investigation and repair.

**Status:** v0.1 prototype. The agent-loop demo simulates an observation. The optional CLI captures real page controls and keyboard focus order; source patch generation, automated task success evaluation, and comprehensive accessibility audits are roadmap items.

## Try it

```bash
python -m pip install -e .
python examples/demo.py
python -m unittest discover -s tests -v
```

## Build an agent

Implement `decide(messages, tools) -> Decision` for your provider. Return either `Decision(final="...")` or `Decision(call=ToolCall("tool_name", {"argument": "value"}))`. Register tools with `Tool(name, description, run)`. Tools are ordinary Python callables receiving a dictionary. Tools marked `requires_approval=True` are denied until you supply an `approve` callback. Store snapshots and events with `SQLiteStore("runs.db")` and resume using `agent.run(run_id=previous_id)`.

The default tool approval callback denies approval. Tool exceptions become observations the model can handle. Step and wall-clock limits bound runs; the time budget is checked between model calls and cannot interrupt a blocking tool. Oversized tool output becomes a structured error observation.

## Inspect a real page

```bash
python -m pip install -e '.[browser]'
python -m playwright install chromium
accessloop inspect https://example.org --tabs 10
accessloop inspect file:///absolute/path/to/examples/inaccessible.html --tabs 10
```

The inspection command collects DOM metadata for the first 100 interactive controls and the focus sequence reached with Tab. It does not click or submit forms. It reports observations, not a WCAG conformance judgment. Only inspect sites you are authorized to test. Optional screenshots may contain private information, so save and share them deliberately.

## Design

The agent loop asks the model for a decision, executes at most one tool, records the outcome, and repeats. `Model` and `Store` are protocols, so integrations can be written without changing the core. Events contain status metadata; tool observations reside in checkpoints, so treat the SQLite file as sensitive when tools handle private data.

## Roadmap

1. Reproducible keyboard-navigation tasks and a public benchmark of intentionally broken pages.
2. Source-aware patch suggestions with before/after task replay.
3. Evaluation-driven proposals to improve harness instructions, gated by held-out regression tasks.

## Contributing

Open an issue describing the intended behavior and a small reproducible task. Run `python -m unittest discover -s tests -v` before a pull request. Contributions to the core should keep model-provider dependencies optional and preserve readable event traces.

MIT licensed. This project is independent of REA and is not affiliated with it.
