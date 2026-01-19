"""
Simple Test Client for MCP Agentic RAG Application
Tests the tools by calling them directly via Python imports.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the FAQ engine and tools
from rag_app import FAQEngine, PYTHON_FAQ_TEXT
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configuration
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "python_faq_collection"


def test_vector_db_tool():
    """Test the Vector DB FAQ retrieval tool."""
    print("\n" + "=" * 70)
    print("TEST 1: VECTOR DB TOOL - Python FAQ Retrieval")
    print("=" * 70)
    
    # Initialize FAQ Engine
    print("\nInitializing FAQ Engine...")
    faq_engine = FAQEngine(qdrant_url=QDRANT_URL, collection_name=COLLECTION_NAME)
    
    # Test queries
    test_queries = [
        "Can you explain list comprehensions in Python?",
        "What are Python decorators?",
        "What is the difference between == and is?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Query {i} ---")
        print(f"Q: {query}")
        print("\nA:")
        try:
            result = faq_engine.answer_question(query)
            print(result[:500] + "..." if len(result) > 500 else result)
            print("\n✓ SUCCESS")
        except Exception as e:
            print(f"✗ ERROR: {e}")
    
    print("\n" + "=" * 70)


def test_web_search_tool():
    """Test the Web Search tool."""
    print("\n" + "=" * 70)
    print("TEST 2: WEB SEARCH TOOL - Firecrawl API")
    print("=" * 70)
    
    api_key = os.getenv('FIRECRAWL_API_KEY')
    
    if not api_key or api_key == "your_firecrawl_api_key_here":
        print("\n⚠ WARNING: FIRECRAWL_API_KEY not configured!")
        print("Skipping web search test.")
        print("To enable: Add your API key to .env file")
        print("=" * 70)
        return
    
    test_queries = [
        "What is the Polars DataFrame library?",
        "Latest Python 3.12 features"
    ]
    
    url = "https://api.firecrawl.dev/v1/search"
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Query {i} ---")
        print(f"Q: {query}")
        print("\nSearching...")
        
        try:
            payload = {"query": query, "timeout": 60000}
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            results = response.json().get("data", [])
            
            if results:
                print(f"\nFound {len(results)} results:")
                for idx, result in enumerate(results[:3], 1):
                    if isinstance(result, dict):
                        title = result.get('title', 'No title')
                        url_link = result.get('url', 'No URL')
                        print(f"  {idx}. {title}")
                        print(f"     {url_link}")
                print("\n✓ SUCCESS")
            else:
                print("No results found")
                
        except requests.exceptions.Timeout:
            print("✗ ERROR: Request timed out")
        except Exception as e:
            print(f"✗ ERROR: {e}")
    
    print("\n" + "=" * 70)


def test_server_health():
    """Test if MCP server is running."""
    print("\n" + "=" * 70)
    print("TEST 0: MCP SERVER HEALTH CHECK")
    print("=" * 70)
    
    try:
        response = requests.get("http://127.0.0.1:8080/sse", timeout=5)
        if response.status_code == 200:
            print("\n✓ MCP Server is RUNNING on port 8080")
            print(f"  Response: {response.text[:100]}...")
        else:
            print(f"\n⚠ Server responded with status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("\n✗ MCP Server is NOT running")
        print("  Start it with: python3 mcp_server.py")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
    
    print("=" * 70)


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("MCP AGENTIC RAG - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print("\nThis will test:")
    print("  0. MCP Server health")
    print("  1. Vector DB Tool (Python FAQ)")
    print("  2. Web Search Tool (Firecrawl)")
    print("\n" + "=" * 70)
    
    # Test server
    test_server_health()
    
    # Test Vector DB
    test_vector_db_tool()
    
    # Test Web Search
    test_web_search_tool()
    
    # Summary
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)
    print("\n✓ Vector DB Tool: Tested")
    print("✓ Web Search Tool: Tested (if API key configured)")
    print("✓ MCP Server: Health checked")
    print("\nFor full MCP integration testing, use an MCP client like:")
    print("  - Claude Desktop")
    print("  - Custom MCP client application")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
