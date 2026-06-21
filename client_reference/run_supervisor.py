"""
CLI de exemplo para o supervisor LangGraph de referência.

Uso:
    MCP_TRANSPORT=sse python3 mcp_server.py &
    python3 client_reference/run_supervisor.py "Busque ocorrências similares a roubo de celular com faca"
"""

import asyncio
import sys

from client_reference.supervisor import build_supervisor


async def main():
    if len(sys.argv) < 2:
        print("Uso: python3 client_reference/run_supervisor.py \"<pergunta>\"")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    supervisor = await build_supervisor()

    result = await supervisor.ainvoke({"messages": [{"role": "user", "content": query}]})

    print("\n" + "=" * 70)
    print("RESPOSTA DO SUPERVISOR")
    print("=" * 70)
    for message in result["messages"]:
        role = getattr(message, "type", message.get("role") if isinstance(message, dict) else "?")
        content = getattr(message, "content", message.get("content") if isinstance(message, dict) else message)
        print(f"\n[{role}] {content}")


if __name__ == "__main__":
    asyncio.run(main())
