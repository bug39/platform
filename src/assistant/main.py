"""Main entry point for the coding assistant."""

import sys
from .providers.anthropic import get_provider
from .providers.base import Message


def main():
    """Main entry point."""
    print("Coding Assistant v0.1.0")
    print("Phase 0: Testing LLM provider connection\n")

    try:
        # Get provider
        provider = get_provider()
        print(f"Using provider: {provider.name}")

        # Test with a simple message
        messages = [
            Message(role="user", content="Say 'Hello! I am working!' and nothing else.")
        ]

        print("\nSending test message to LLM...")
        response = provider.complete(messages)

        print(f"\nResponse: {response.content}")
        print(f"Tokens used: {response.usage['input_tokens']} in, {response.usage['output_tokens']} out")
        print("\n✓ LLM provider is working correctly!")

        return 0

    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
