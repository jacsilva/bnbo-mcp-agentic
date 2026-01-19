"""
MCP HTTP Client for Agentic RAG Application
Uses SSE (Server-Sent Events) transport to communicate with the MCP server via HTTP.
"""

import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client


async def call_tool(session: ClientSession, tool_name: str, query: str):
    """
    Call an MCP tool with a query.
    
    Args:
        session: Active MCP client session
        tool_name: Name of the tool to call
        query: Query string to send to the tool
    """
    print(f"\n{'=' * 70}")
    print(f"Calling tool: {tool_name}")
    print(f"Query: {query}")
    print('=' * 70)
    
    try:
        result = await session.call_tool(tool_name, arguments={"query": query})
        
        print("\n✓ SUCCESS")
        print("\nResponse:")
        
        # Extract and display the content
        if hasattr(result, 'content') and result.content:
            for item in result.content:
                if hasattr(item, 'text'):
                    # Truncate long responses for readability
                    text = item.text
                    if len(text) > 500:
                        print(text[:500] + "...\n")
                    else:
                        print(text + "\n")
        else:
            print(result)
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
    
    print('=' * 70)


async def call_tool_cmd(session: ClientSession, tool_name: str, cmd: str):
    """
    Call an MCP tool that executes shell commands.
    Adapted specifically for the execute_shell_command tool.
    
    Args:
        session: Active MCP client session
        tool_name: Name of the tool to call (typically 'execute_shell_command')
        cmd: Shell command string to execute
    """
    print(f"\n{'=' * 70}")
    print(f"Calling tool: {tool_name}")
    print(f"Command: {cmd}")
    print('=' * 70)
    
    try:
        result = await session.call_tool(tool_name, arguments={"cmd": cmd})
        
        print("\n✓ SUCCESS")
        print("\nCommand Output:")
        
        # Extract and display the content
        if hasattr(result, 'content') and result.content:
            for item in result.content:
                if hasattr(item, 'text'):
                    # Display full output for shell commands (usually not too long)
                    text = item.text
                    if len(text) > 1000:
                        print(text[:1000] + "...\n")
                    else:
                        print(text + "\n")
        else:
            print(result)
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
    
    print('=' * 70)


async def list_available_tools(session: ClientSession):
    """List all available tools from the MCP server."""
    print("\n" + "=" * 70)
    print("AVAILABLE MCP TOOLS")
    print("=" * 70)
    
    try:
        tools = await session.list_tools()
        
        if tools and hasattr(tools, 'tools'):
            for i, tool in enumerate(tools.tools, 1):
                print(f"\n{i}. {tool.name}")
                if hasattr(tool, 'description') and tool.description:
                    print(f"   Description: {tool.description}")
                if hasattr(tool, 'inputSchema'):
                    print(f"   Input: {tool.inputSchema}")
        else:
            print("No tools found")
            
    except Exception as e:
        print(f"Error listing tools: {e}")
    
    print("=" * 70)


async def main():
    """Main function to run MCP HTTP client tests."""
    
    # Server configuration
    HOST = "127.0.0.1"
    PORT = 8080
    SERVER_URL = f"http://{HOST}:{PORT}/sse"
    
    print("\n" + "=" * 70)
    print("MCP HTTP CLIENT - AGENTIC RAG")
    print("=" * 70)
    print(f"\nConnecting to MCP server via SSE at {SERVER_URL}...")
    
    try:
        async with sse_client(SERVER_URL) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                print("✓ Connected to MCP server via HTTP/SSE!\n")
                
                # List available tools
                await list_available_tools(session)
                
                # Test Case 1: Python FAQ - List Comprehensions
                print("\n\n### TEST 1: Python FAQ - List Comprehensions ###")
                await call_tool(
                    session,
                    "python_faq_retrieval_tool",
                    "Can you explain list comprehensions in Python?"
                )
                
                # Test Case 2: Python FAQ - Decorators
                print("\n\n### TEST 2: Python FAQ - Decorators ###")
                await call_tool(
                    session,
                    "python_faq_retrieval_tool",
                    "What are Python decorators?"
                )
                
                # Test Case 3: Python FAQ - == vs is
                print("\n\n### TEST 3: Python FAQ - == vs is ###")
                await call_tool(
                    session,
                    "python_faq_retrieval_tool",
                    "What is the difference between == and is in Python?"
                )
                
                # Test Case 4: Web Search - Polars
                print("\n\n### TEST 4: Web Search - Polars DataFrame ###")
                await call_tool(
                    session,
                    "firecrawl_web_search_tool",
                    "What is the Polars DataFrame library?"
                )

                # Test Case 5: Shell Command - List files
                print("\n\n### TEST 5: Shell Command - List files ###")
                await call_tool_cmd(
                    session,
                    "execute_shell_command",
                    "ls -la"
                )
                
                print("\n\n" + "=" * 70)
                print("ALL TESTS COMPLETED")
                print("=" * 70)
                print("\n✓ MCP HTTP Client successfully communicated with server")
                print("✓ All tools tested and working")
                print("=" * 70 + "\n")
                
    except Exception as e:
        print(f"\n✗ ERROR: Failed to connect to MCP server via HTTP")
        print(f"Details: {e}")
        print("\nMake sure:")
        print("  1. The MCP server is running with SSE transport")
        print(f"  2. Server is accessible at {SERVER_URL}")
        print("  3. Run server with: MCP_TRANSPORT=sse python3 mcp_server.py")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
