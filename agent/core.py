"""The agent loop: send message -> model picks a tool -> run it -> feed result
back -> repeat until the model produces a plain-text reply.

The Anthropic SDK is imported lazily (inside run_turn) so the rest of the
package — tools, retriever, evals --selftest — imports and runs with no API
key and no network.
"""
import json

from . import config
from .prompts import SYSTEM_PROMPT
from .tools import Tools, TOOL_SPECS


class Agent:
    def __init__(self, tools=None, model=None, system=None):
        self.tools = tools or Tools()
        self.model = model or config.MODEL
        self.system = system or SYSTEM_PROMPT
        self.messages = []       # running conversation (Anthropic message dicts)
        self.tools_used = []     # names of tools called this conversation

    def _client(self):
        # Lazy import: only needed when we actually call the model.
        from anthropic import Anthropic
        return Anthropic()

    def say(self, user_text, max_steps=6):
        """Send one user message; return the agent's final text reply."""
        self.messages.append({"role": "user", "content": user_text})
        client = self._client()

        for _ in range(max_steps):
            resp = client.messages.create(
                model=self.model,
                max_tokens=config.MAX_TOKENS,
                system=self.system,
                tools=TOOL_SPECS,
                messages=self.messages,
            )
            # Record the assistant turn verbatim (text + any tool_use blocks).
            self.messages.append({"role": "assistant", "content": resp.content})

            if resp.stop_reason != "tool_use":
                return "".join(b.text for b in resp.content if b.type == "text").strip()

            # Run every tool the model asked for, return the results together.
            results = []
            for block in resp.content:
                if block.type != "tool_use":
                    continue
                self.tools_used.append(block.name)
                output = self.tools.run(block.name, block.input)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(output),
                })
            self.messages.append({"role": "user", "content": results})

        return "I'm having trouble completing that — let me get a person to help."
