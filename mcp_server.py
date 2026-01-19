"""
MCP Server Module
Implements the Model Context Protocol server with intelligent tool selection.
"""

import os
import subprocess
from typing import List
import requests

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Import our RAG engine and FAQ data
from rag_app import FAQEngine, PYTHON_FAQ_TEXT


# Load environment variables from .env file
load_dotenv()

# Configuration constants
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "python_faq_collection"
HOST = "127.0.0.1"
PORT = 8080

# Create an MCP server instance with host and port for SSE support
mcp_server = FastMCP("MCP-RAG-app", host=HOST, port=PORT)


# Integrar MCP em FastAPI existente
# Se você já tem uma aplicação FastAPI e quer adicionar MCP:
# Sua aplicação FastAPI existente
# app = FastAPI(title="Minha API")
# ...existing code...
# Montar MCP como sub-aplicação
# app.mount("/mcp", mcp_server.app)


# Initialize FAQ Engine (will be set up in main)
faq_engine = None


@mcp_server.tool()
def python_faq_retrieval_tool(query: str) -> str:
    """
    Retrieve the most relevant documents from the Python FAQ collection. 
    Use this tool when the user asks about general Python programming concepts.
    
    Args:
        query (str): The user query to retrieve the most relevant documents.
        
    Returns:
        str: The most relevant documents retrieved from the vector DB.
    """
    if not isinstance(query, str):
        raise TypeError("Query must be a string.")
    
    # Use the pre-initialized faq_engine instance
    return faq_engine.answer_question(query)


@mcp_server.tool()
def firecrawl_web_search_tool(query: str) -> str:
    """
    Search for information on a given topic using Firecrawl.
    Use this tool when the user asks a specific question not related to the Python FAQ.

    Args:
        query (str): The user query to search for information.

    Returns:
        str: A formatted string with the most relevant web search results.
    """
    if not isinstance(query, str):
        raise TypeError("Query must be a string.")

    url = "https://api.firecrawl.dev/v1/search"
    api_key = os.getenv('FIRECRAWL_API_KEY')

    if not api_key:
        return "Error: FIRECRAWL_API_KEY environment variable is not set."

    payload = {"query": query, "timeout": 60000}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        results = response.json().get("data", [])
        
        if not results:
            return "No results found from web search."
        
        # Format results as a string
        formatted_results = f"Found {len(results)} results:\n\n"
        for i, result in enumerate(results[:5], 1):
            if isinstance(result, dict):
                title = result.get('title', 'No title')
                url_link = result.get('url', 'No URL')
                snippet = result.get('description', '')
                formatted_results += f"{i}. {title}\n   URL: {url_link}\n"
                if snippet:
                    formatted_results += f"   {snippet[:150]}...\n"
                formatted_results += "\n"
        
        return formatted_results.strip()
        
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Firecrawl API: {e}"

# Define the base working directory for command execution
WORKSPACE_PATH = os.path.expanduser("/home/seaddados/projetos/mcp-agentic-rag")

@mcp_server.tool()
def execute_shell_command(cmd: str) -> str:
    """
    Execute shell commands within the designated workspace environment.
    
    This tool provides terminal access for file operations, system commands,
    and other CLI-based tasks. When a terminal operation is needed,
    this function will be utilized to carry out the requested action.

    Parameters:
        cmd: Shell command string to be executed
    
    Returns:
        Command execution output (stdout/stderr) or error details
    """
    try:
        # Execute command with workspace as working directory
        process = subprocess.run(
            cmd, 
            shell=True, 
            cwd=WORKSPACE_PATH, 
            capture_output=True, 
            text=True,
            timeout=30  # Add timeout for safety
        )
        
        # Return output, prioritizing stdout over stderr
        output = process.stdout.strip() if process.stdout else process.stderr.strip()
        return output if output else "Command executed successfully (no output)"
        
    except subprocess.TimeoutExpired:
        return "Error: Command execution timed out after 30 seconds"
    except Exception as error:
        return f"Execution error: {str(error)}"

        
if __name__ == "__main__":
    # 1. Initialize our RAG Engine
    print("=" * 60)
    print("MCP AGENTIC RAG APPLICATION")
    print("=" * 60)
    print("\nInitializing FAQ Engine and setting up Qdrant collection...")
    faq_engine = FAQEngine(qdrant_url=QDRANT_URL, collection_name=COLLECTION_NAME)
    
    # 2. Ingest our data into the vector database
    # This will create embeddings and store them
    faq_engine.setup_collection(PYTHON_FAQ_TEXT)
    
    # 3. Determine transport mode
    import os
    transport = os.getenv('MCP_TRANSPORT', 'stdio')
    
    # 4. Start the MCP server
    print(f"\n{'=' * 60}")
    print("Starting MCP server")
    print(f"{'=' * 60}")
    print("\nAvailable Tools:")
    print("  1. python_faq_retrieval_tool - Search Python FAQ knowledge base")
    print("  2. firecrawl_web_search_tool - Search the web for information")
    print("  3. execute_shell_command - Execute shell commands")
    
    if transport == 'sse':
        print(f"\n✓ Transport: SSE (HTTP)")
        print(f"✓ Server URL: http://{HOST}:{PORT}/sse")
        print("\nServer is ready to accept HTTP connections!")
        print("Use mcp_client_http.py to test the server.")
    else:
        print(f"\n✓ Transport: STDIO")
        print("\nServer is ready to accept STDIO connections!")
        print("Use mcp_client.py to test the server.")
    
    print("Press CTRL+C to stop the server.\n")
    
    # Run the server with the selected transport
    mcp_server.run(transport)

