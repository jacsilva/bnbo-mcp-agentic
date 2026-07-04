"""
CLI de exemplo para o supervisor LangGraph de referência.

Uso:
    MCP_TRANSPORT=streamable-http python3 -m server.mcp_server &
    python3 -m client.reference.run_supervisor "Busque ocorrências similares a roubo de celular com faca"
"""

import asyncio
import sys

from client.reference.supervisor import build_supervisor


async def main():
    if len(sys.argv) < 2:
        print("Uso: python3 -m client.reference.run_supervisor \"<pergunta>\"")
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
