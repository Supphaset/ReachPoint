"""Send a chat message from the command line."""

import argparse
import asyncio

from langchain_core.messages import HumanMessage

from agent.graph import graph


def main() -> None:
    """Run one conversation turn."""
    parser = argparse.ArgumentParser(description="Chat with Gemini")
    parser.add_argument("message", help="Message to send")
    args = parser.parse_args()
    result = asyncio.run(graph.ainvoke({"messages": [HumanMessage(content=args.message)]}))
    print(result["messages"][-1].text)


if __name__ == "__main__":
    main()
