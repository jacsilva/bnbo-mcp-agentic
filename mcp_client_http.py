"""
Cliente MCP via Streamable HTTP — harness de teste para as tools do P2 Linkage Criminal.
"""

import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def call_tool(session: ClientSession, tool_name: str, arguments: dict):
    print(f"\n{'=' * 70}")
    print(f"Calling tool: {tool_name}")
    print(f"Arguments: {arguments}")
    print('=' * 70)

    try:
        result = await session.call_tool(tool_name, arguments=arguments)
        print("\n✓ SUCCESS\n")
        if hasattr(result, 'content') and result.content:
            for item in result.content:
                if hasattr(item, 'text'):
                    try:
                        parsed = json.loads(item.text)
                        print(json.dumps(parsed, indent=2, ensure_ascii=False)[:1500])
                    except json.JSONDecodeError:
                        print(item.text[:1500])
        else:
            print(result)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")

    print('=' * 70)


async def list_available_tools(session: ClientSession):
    print("\n" + "=" * 70)
    print("AVAILABLE MCP TOOLS")
    print("=" * 70)
    try:
        tools = await session.list_tools()
        if tools and hasattr(tools, 'tools'):
            for i, tool in enumerate(tools.tools, 1):
                print(f"\n{i}. {tool.name}")
                if tool.description:
                    print(f"   Description: {tool.description.strip().splitlines()[0]}")
        else:
            print("No tools found")
    except Exception as e:
        print(f"Error listing tools: {e}")
    print("=" * 70)


async def main():
    HOST = "127.0.0.1"
    PORT = 8080
    SERVER_URL = f"http://{HOST}:{PORT}/mcp"

    print("\n" + "=" * 70)
    print("MCP HTTP CLIENT - P2 LINKAGE CRIMINAL")
    print("=" * 70)
    print(f"\nConnecting to MCP server via Streamable HTTP at {SERVER_URL}...")

    try:
        async with streamablehttp_client(SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✓ Connected to MCP server via Streamable HTTP!\n")

                await list_available_tools(session)

                print("\n\n### TEST 1: Busca por texto livre ###")
                await call_tool(session, "buscar_ocorrencias_similares", {
                    "texto_livre": "roubo de celular com uso de faca em via pública",
                    "top_k": 5,
                })

                print("\n\n### TEST 2: Disparar reindexação assíncrona ###")
                await call_tool(session, "reindexar_embeddings", {"batch_size": 50})

                print("\n\n" + "=" * 70)
                print("ALL TESTS COMPLETED")
                print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n✗ ERROR: Failed to connect to MCP server via HTTP")
        print(f"Details: {e}")
        print("\nMake sure:")
        print("  1. The MCP server is running with Streamable HTTP transport")
        print(f"  2. Server is accessible at {SERVER_URL}")
        print("  3. Run server with: MCP_TRANSPORT=streamable-http python3 mcp_server.py")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
