"""The intelligent agent implementation."""

from typing import Callable, Optional
from dataclasses import dataclass

from ..providers import get_provider
from ..providers.base import Message, Response
from ..tools.registry import ToolRegistry
from .events import EventBus, EventType
from .session import Session


@dataclass
class AgentConfig:
    max_iterations: int = 10
    system_prompt: str = None


DEFAULT_SYSTEM = """You are an intelligent Python coding assistant with access to tools.

Available tools:
- generate_code: Write Python code from descriptions
- execute_code: Run code in a safe sandbox
- analyze_code: Analyze code structure and quality
- explain_code: Explain what code does
- fix_error: Fix broken code

Workflow:
1. Understand what the user wants
2. Use appropriate tools to help
3. If code fails, fix and retry
4. Explain your actions clearly

Always test code before saying it works."""


class Agent:
    """
    The main agent that orchestrates tools and LLM.

    The agent loop:
    1. Receive user input
    2. Send to LLM with available tools
    3. If LLM requests tool use -> execute tool -> send result back
    4. Repeat until LLM gives final response or max iterations
    """

    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.provider = get_provider()
        self.tools = ToolRegistry.get()
        self.events = EventBus.get()
        self.session = Session()

    def run(
        self,
        user_input: str,
        on_thinking: Callable[[], None] = None,
        on_tool_use: Callable[[str, dict], None] = None,
    ) -> str:
        """
        Run the agent loop for a user request.

        Args:
            user_input: The user's message
            on_thinking: Callback when agent is thinking
            on_tool_use: Callback when tool is used (name, inputs)

        Returns:
            The agent's final response
        """
        # Validate input
        if not user_input or not user_input.strip():
            raise ValueError("User input cannot be empty")
        if len(user_input) > 100000:  # 100KB limit
            raise ValueError("User input too long (max 100,000 characters)")

        # Add user message
        self.session.add_message(Message(role="user", content=user_input))

        system = self.config.system_prompt or DEFAULT_SYSTEM
        tool_dicts = self.tools.to_dicts()

        for iteration in range(self.config.max_iterations):
            self.events.emit(EventType.AGENT_ITERATION_START, {
                "iteration": iteration,
                "messages": len(self.session.messages)
            })

            if on_thinking:
                on_thinking()

            # Get LLM response
            self.events.emit(EventType.BEFORE_LLM_CALL, {
                "messages": self.session.messages,
                "tools": tool_dicts
            })

            try:
                response = self.provider.complete(
                    messages=self.session.messages,
                    system=system,
                    tools=tool_dicts if tool_dicts else None,
                )
            except Exception as e:
                error_msg = f"LLM provider error: {str(e)}"
                self.events.emit(EventType.AFTER_LLM_CALL, {
                    "error": error_msg
                })
                return f"I encountered an error: {error_msg}"

            self.events.emit(EventType.AFTER_LLM_CALL, {
                "response": response
            })

            # Check if done
            if response.stop_reason == "end_turn" or not response.tool_calls:
                # Either explicitly done or no tools to call
                self.session.add_message(Message(
                    role="assistant",
                    content=response.content
                ))
                self.events.emit(EventType.AGENT_COMPLETE, {
                    "iterations": iteration + 1,
                    "response": response.content
                })
                return response.content

            # Handle tool calls
            if response.tool_calls:
                # Add assistant message with tool calls (for context)
                self.session.add_raw({
                    "role": "assistant",
                    "content": response.raw.content  # Keep original format
                })

                tool_results = []
                for tool_call in response.tool_calls:
                    self.events.emit(EventType.BEFORE_TOOL_EXECUTE, {
                        "tool": tool_call.name,
                        "inputs": tool_call.inputs
                    })

                    if on_tool_use:
                        on_tool_use(tool_call.name, tool_call.inputs)

                    result = self.tools.execute(tool_call.name, tool_call.inputs)

                    self.events.emit(EventType.AFTER_TOOL_EXECUTE, {
                        "tool": tool_call.name,
                        "result": result
                    })

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": result
                    })

                # Add tool results
                self.session.add_raw({
                    "role": "user",
                    "content": tool_results
                })

            self.events.emit(EventType.AGENT_ITERATION_END, {
                "iteration": iteration
            })

        return "I've reached my iteration limit. Please try a simpler request."

    def clear(self):
        """Clear conversation history."""
        self.session.clear()
