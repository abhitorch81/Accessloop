"""Bounded tool-use loop with explicit decisions and observable events."""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class Decision:
    """Exactly one action or a final response per model turn."""
    final: str | None = None
    call: ToolCall | None = None

    def __post_init__(self) -> None:
        if (self.final is None) == (self.call is None):
            raise ValueError("Decision requires exactly one of final or call")


class Model(Protocol):
    def decide(self, messages: list[dict[str, Any]], tools: list[dict[str, str]]) -> Decision: ...


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    run: Callable[[dict[str, Any]], Any]
    requires_approval: bool = False


@dataclass(frozen=True)
class AgentConfig:
    max_steps: int = 8
    max_seconds: float = 60.0
    max_tool_output_chars: int = 6000

    def __post_init__(self) -> None:
        if min(self.max_steps, self.max_seconds, self.max_tool_output_chars) <= 0:
            raise ValueError("Budgets must be positive")


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class RunResult:
    run_id: str
    answer: str
    messages: list[dict[str, Any]]
    steps: int


class Store(Protocol):
    def save(self, run_id: str, messages: list[dict[str, Any]], event: dict[str, Any]) -> None: ...
    def load(self, run_id: str) -> list[dict[str, Any]]: ...


@dataclass
class Agent:
    model: Model
    tools: list[Tool]
    config: AgentConfig = field(default_factory=AgentConfig)
    store: Store | None = None
    approve: Callable[[ToolCall], bool] = lambda _call: False
    on_event: Callable[[dict[str, Any]], None] = lambda _event: None

    def run(self, task: str | None = None, *, run_id: str | None = None) -> RunResult:
        if (task is None) == (run_id is None):
            raise ValueError("Pass exactly one of task or run_id")
        if run_id is not None and self.store is None:
            raise ValueError("Resume requires a store")
        identifier = run_id or str(uuid.uuid4())
        messages = self.store.load(identifier) if run_id else [{"role": "user", "content": task}]
        if not messages:
            raise ValueError("Cannot resume an empty run")
        if run_id and messages[-1]["role"] == "assistant" and "content" in messages[-1]:
            return RunResult(identifier, messages[-1]["content"], messages, 0)
        tool_map = {tool.name: tool for tool in self.tools}
        if len(tool_map) != len(self.tools):
            raise ValueError("Duplicate tool name")
        started = time.monotonic()

        def record(event: dict[str, Any]) -> None:
            payload = {"run_id": identifier, **event}
            if self.store:
                self.store.save(identifier, messages, payload)
            self.on_event(payload)

        for step in range(1, self.config.max_steps + 1):
            if time.monotonic() - started >= self.config.max_seconds:
                raise BudgetExceeded("Time budget exceeded")
            decision = self.model.decide(list(messages), [{"name": t.name, "description": t.description} for t in self.tools])
            if decision.final is not None:
                messages.append({"role": "assistant", "content": decision.final})
                record({"type": "final", "step": step})
                return RunResult(identifier, decision.final, messages, step)

            call = decision.call
            assert call is not None
            if call.name not in tool_map:
                outcome = {"error": "unknown_tool", "name": call.name}
            elif tool_map[call.name].requires_approval and not self.approve(call):
                outcome = {"error": "approval_denied", "name": call.name}
            else:
                try:
                    outcome = {"result": tool_map[call.name].run(call.arguments)}
                except Exception as exc:
                    outcome = {"error": "tool_failed", "detail": str(exc)}
            encoded = json.dumps(outcome, default=str, ensure_ascii=False)
            if len(encoded) > self.config.max_tool_output_chars:
                encoded = json.dumps({"error": "tool_output_too_large", "name": call.name})
            messages.append({"role": "assistant", "tool_call": {"name": call.name, "arguments": call.arguments}})
            messages.append({"role": "tool", "name": call.name, "content": encoded[: self.config.max_tool_output_chars]})
            record({"type": "tool", "step": step, "name": call.name, "status": "error" if "error" in outcome else "ok"})
        raise BudgetExceeded("Step budget exceeded; resume from checkpoint with a larger budget")
