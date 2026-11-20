import tempfile
import unittest
from pathlib import Path

from accessloop import Agent, AgentConfig, BudgetExceeded, Decision, SQLiteStore, Tool, ToolCall


class Model:
    def decide(self, messages, tools):
        if messages[-1]["role"] == "tool":
            return Decision(final=messages[-1]["content"])
        return Decision(call=ToolCall("read", {}))


def test_run_and_resume():
    tmp_path = Path(tempfile.mkdtemp())
    store = SQLiteStore(tmp_path / "runs.db")
    agent = Agent(Model(), [Tool("read", "Read data", lambda _: "ok")], store=store)
    result = agent.run("read")
    assert "ok" in result.answer
    assert [event["type"] for event in store.events(result.run_id)] == ["tool", "final"]
    assert 'ok' in agent.run(run_id=result.run_id).answer


def test_approval_defaults_to_denial():
    result = Agent(Model(), [Tool("read", "Sensitive", lambda _: "secret", requires_approval=True)]).run("read")
    assert "approval_denied" in result.answer


def test_budget_and_checkpoint():
    tmp_path = Path(tempfile.mkdtemp())
    store = SQLiteStore(tmp_path / "runs.db")
    agent = Agent(Model(), [Tool("read", "Read", lambda _: 1)], AgentConfig(max_steps=1), store=store)
    with unittest.TestCase().assertRaises(BudgetExceeded):
        agent.run("read")
    with store._connect() as db:
        run_id = db.execute("SELECT id FROM runs").fetchone()[0]
    assert len(store.load(run_id)) == 3
    agent.config = AgentConfig(max_steps=2)
    assert agent.run(run_id=run_id).answer == '{"result": 1}'

if __name__ == "__main__":
    for test in (test_run_and_resume, test_approval_defaults_to_denial, test_budget_and_checkpoint):
        test()
    print("3 tests passed")


class CoreTests(unittest.TestCase):
    def test_run_and_resume(self):
        test_run_and_resume()

    def test_approval_defaults_to_denial(self):
        test_approval_defaults_to_denial()

    def test_budget_and_checkpoint(self):
        test_budget_and_checkpoint()
