"""Offline demonstration: python examples/demo.py"""
from accessloop import Agent, Decision, SQLiteStore, Tool, ToolCall


class DemoModel:
    def decide(self, messages, tools):
        if messages[-1]["role"] == "user":
            return Decision(call=ToolCall("inspect_page", {"url": "demo://checkout"}))
        return Decision(final="Checkout has an unlabeled submit button. Evidence: " + messages[-1]["content"])


agent = Agent(
    model=DemoModel(),
    tools=[Tool("inspect_page", "Inspect a page and return evidence", lambda args: {"url": args["url"], "button": {"text": "", "accessible_name": ""}})],
    store=SQLiteStore("accessloop-demo.db"),
)
result = agent.run("Identify the accessibility blocker in checkout")
print(result.answer)
print("Run ID:", result.run_id)
