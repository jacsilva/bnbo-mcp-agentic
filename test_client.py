"""
Test Client for MCP Agentic RAG Application
Demonstrates how to interact with the MCP server and test both tools.
"""

import requests
import json
import uuid


def test_mcp_server(query: str, tool_name: str, server_url: str = "http://127.0.0.1:8080"):
    """
    Send a query to the MCP server via SSE and call a specific tool.
    
    Args:
        query: The user's question
        tool_name: Name of the MCP tool to call
        server_url: URL of the MCP server endpoint
    """
    print(f"\n{'=' * 70}")
    print(f"QUERY: {query}")
    print(f"TOOL: {tool_name}")
    print('=' * 70)
    
    try:
        # Step 1: Get SSE endpoint
        sse_response = requests.get(f"{server_url}/sse", stream=True, timeout=5)
        
        # Extract session endpoint from SSE stream
        session_endpoint = None
        for line in sse_response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith('data: '):
                    session_endpoint = decoded.replace('data: ', '').strip()
                    break
        
        if not session_endpoint:
            print("\nERROR: Could not get session endpoint from SSE")
            return
        
        # Step 2: Construct full messages URL
        messages_url = f"{server_url}{session_endpoint}"
        
        # Step 3: Create MCP JSON-RPC request to call the tool
        mcp_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": {
                    "query": query
                }
            }
        }
        
        # Step 4: Send the request
        response = requests.post(
            messages_url,
            json=mcp_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Pretty print the response
        print("\nRESPONSE:")
        if "result" in result:
            content = result["result"].get("content", [])
            if content and len(content) > 0:
                text = content[0].get("text", "No text in response")
                # Truncate long responses
                if len(text) > 500:
                    print(text[:500] + "...")
                else:
                    print(text)
            else:
                print(json.dumps(result["result"], indent=2))
        elif "error" in result:
            print(f"ERROR: {result['error']}")
        else:
            print(json.dumps(result, indent=2))
        
    except requests.exceptions.Timeout:
        print("\nERROR: Request timed out")
    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to server. Is it running?")
    except Exception as e:
        print(f"\nERROR: {e}")
    
    print('=' * 70)


def main():
    """Run test cases for both MCP tools."""
    
    print("\n" + "=" * 70)
    print("MCP AGENTIC RAG - TEST CLIENT")
    print("=" * 70)
    print("\nThis script will test both tools:")
    print("  1. Python FAQ Retrieval Tool (Vector DB)")
    print("  2. Firecrawl Web Search Tool")
    print("\nMake sure the MCP server is running before executing these tests!")
    print("=" * 70)
    
    # Test Case 1: Python FAQ Query (should use vector DB tool)
    print("\n\n### TEST CASE 1: Python FAQ Query ###")
    print("Expected: Should use 'python_faq_retrieval_tool'")
    test_mcp_server(
        "Can you explain list comprehensions in Python?",
        "python_faq_retrieval_tool"
    )
    
    # Test Case 2: Another Python FAQ Query
    print("\n\n### TEST CASE 2: Python Decorators Query ###")
    print("Expected: Should use 'python_faq_retrieval_tool'")
    test_mcp_server(
        "What are Python decorators?",
        "python_faq_retrieval_tool"
    )
    
    # Test Case 3: Web Search Query (should use web search tool)
    print("\n\n### TEST CASE 3: Web Search Query ###")
    print("Expected: Should use 'firecrawl_web_search_tool'")
    test_mcp_server(
        "What is the new Polars DataFrame library?",
        "firecrawl_web_search_tool"
    )
    
    # Test Case 4: Current Events Query
    print("\n\n### TEST CASE 4: Current Events Query ###")
    print("Expected: Should use 'firecrawl_web_search_tool'")
    test_mcp_server(
        "What are the latest developments in AI in 2026?",
        "firecrawl_web_search_tool"
    )
    
    print("\n\n" + "=" * 70)
    print("TEST SUITE COMPLETED")
    print("=" * 70)
    print("\nNote: Review the responses above to verify:")
    print("  - Correct tool selection for each query type")
    print("  - Relevant and accurate information retrieval")
    print("  - Proper error handling")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
