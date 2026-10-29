"""Command-line chat with the booking agent.

    python -m agent                 # interactive
    python -m agent "book a gel mani friday"   # single message

Needs ANTHROPIC_API_KEY in .env (see .env.example).
"""
import sys

from .core import Agent


def main():
    agent = Agent()
    if len(sys.argv) > 1:
        print(agent.say(" ".join(sys.argv[1:])))
        return
    print(f"{agent.tools.store.__class__.__name__} ready. Type 'quit' to exit.\n")
    while True:
        try:
            user = input("you: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user.lower() in {"quit", "exit"}:
            break
        if user:
            print("agent:", agent.say(user), "\n")


if __name__ == "__main__":
    main()
