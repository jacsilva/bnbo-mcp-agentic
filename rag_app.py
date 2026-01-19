"""
RAG Application Module
Implements the FAQ Engine for embedding, indexing, and querying Python FAQ data.
"""

import os
import uuid
from itertools import islice
from typing import List, Dict, Any, Generator

# Configure HuggingFace timeouts before importing
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '300'  # 5 minutes timeout
os.environ['CURL_CA_BUNDLE'] = ''  # Disable SSL verification if needed

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from tqdm import tqdm
from qdrant_client import models, QdrantClient


# Python FAQ Knowledge Base
PYTHON_FAQ_TEXT = """
Question: What is the difference between a list and a tuple in Python?
Answer: Lists are mutable, meaning their elements can be changed, while tuples are immutable. Lists use square brackets `[]` and tuples use parentheses `()`.

Question: What are Python decorators?
Answer: Decorators are a design pattern in Python that allows a user to add new functionality to an existing object without modifying its structure. They are often used for logging, timing, and access control.

Question: How does Python's Global Interpreter Lock (GIL) work?
Answer: The GIL is a mutex that protects access to Python objects, preventing multiple threads from executing Python bytecode at the same time. This means that even on a multi-core processor, only one thread can execute Python code at once.

Question: What is the difference between `==` and `is` in Python?
Answer: `==` checks for equality of value (do two objects have the same content?), while `is` checks for identity (do two variables point to the same object in memory?).

Question: Explain list comprehensions and their benefits.
Answer: List comprehensions provide a concise way to create lists. They are often more readable and faster than using traditional `for` loops and `.append()` calls.

Question: What is `*args` and `**kwargs` in function definitions?
Answer: `*args` allows you to pass a variable number of non-keyword arguments to a function, which are received as a tuple. `**kwargs` allows you to pass a variable number of keyword arguments, received as a dictionary.

Question: What are Python's magic methods (e.g., `__init__`, `__str__`)?
Answer: Magic methods, or dunder methods, are special methods that you can define to add "magic" to your classes. They are invoked by Python for built-in operations, like `__init__` for object creation or `__add__` for the `+` operator.

Question: How does error handling work in Python?
Answer: Python uses `try...except` blocks to handle exceptions. Code that might raise an error is placed in the `try` block, and the code to handle the exception is placed in the `except` block.

Question: What is the purpose of the `if __name__ == "__main__":` block?
Answer: This block ensures that the code inside it only runs when the script is executed directly, not when it is imported as a module into another script.

Question: What are generators in Python?
Answer: Generators are a simple way to create iterators. They are functions that use the `yield` keyword to return a sequence of values one at a time, saving memory for large datasets.
"""


def batch_generator(data: List[Any], batch_size: int) -> Generator[List[Any], None, None]:
    """
    Yields successive n-sized chunks from a list.
    
    Args:
        data: List of items to batch
        batch_size: Size of each batch
        
    Yields:
        List chunks of specified size
    """
    for i in range(0, len(data), batch_size):
        yield data[i : i + batch_size]


class FAQEngine:
    """
    An engine for setting up and querying a FAQ database using Qdrant and HuggingFace embeddings.
    
    This class handles:
    - Loading and initializing embedding models
    - Creating and managing Qdrant collections
    - Embedding and indexing FAQ documents
    - Performing semantic search queries
    """
    
    def __init__(self,
                 qdrant_url: str = "http://localhost:6333",
                 collection_name: str = "python-faq",
                 embed_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize the FAQ Engine.
        
        Args:
            qdrant_url: URL of the Qdrant server
            collection_name: Name of the collection to create/use
            embed_model_name: HuggingFace model name for embeddings
                            Default: sentence-transformers/all-MiniLM-L6-v2 (fast, lightweight)
                            Alternative: nomic-ai/nomic-embed-text-v1.5 (better quality, larger)
        """
        self.collection_name = collection_name
        
        # Initialize the embedding model
        print(f"Loading embedding model: {embed_model_name}...")
        print("(This may take a few minutes on first run to download the model)")
        
        try:
            self.embed_model = HuggingFaceEmbedding(
                model_name=embed_model_name,
                trust_remote_code=True
            )
        except Exception as e:
            print(f"Error loading model {embed_model_name}: {e}")
            print("Falling back to default model: sentence-transformers/all-MiniLM-L6-v2")
            self.embed_model = HuggingFaceEmbedding(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                trust_remote_code=False
            )
        
        # Dynamically get the vector dimension from the model
        self.vector_dim = len(self.embed_model.get_text_embedding("test"))
        print(f"Embedding model loaded. Vector dimension: {self.vector_dim}")

        # Initialize the Qdrant client
        self.client = QdrantClient(url=qdrant_url, prefer_grpc=True)
        print("Connected to Qdrant.")

    @staticmethod
    def parse_faq(text: str) -> List[str]:
        """
        Parses the raw FAQ text into a list of Q&A strings.
        
        Args:
            text: Raw FAQ text with Q&A pairs separated by blank lines
            
        Returns:
            List of cleaned Q&A strings
        """
        return [
            qa.replace("\n", " ").strip()
            for qa in text.strip().split("\n\n")
        ]

    def setup_collection(self, faq_text: str, batch_size: int = 64):
        """
        Creates a Qdrant collection (if it doesn't exist) and ingests the FAQ data.
        
        Args:
            faq_text: Raw FAQ text to parse and index
            batch_size: Number of documents to process in each batch
        """
        # Parse FAQ text into individual contexts
        faq_contexts = self.parse_faq(faq_text)
        
        # Check if collection exists, create if not
        try:
            self.client.get_collection(collection_name=self.collection_name)
            print(f"Collection '{self.collection_name}' already exists. Skipping creation.")
            return  # Skip ingestion if collection already exists
        except Exception:
            print(f"Creating collection '{self.collection_name}'...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_dim,
                    distance=models.Distance.DOT
                )
            )

        print(f"Embedding and ingesting {len(faq_contexts)} documents...")
        
        # Process data in batches
        for batch in tqdm(batch_generator(faq_contexts, batch_size), 
                          total=(len(faq_contexts) // batch_size) + 1,
                          desc="Ingesting FAQ data"):
            
            # 1. Get embeddings for the batch
            embeddings = self.embed_model.get_text_embedding_batch(batch, show_progress_bar=False)
            
            # 2. Create Qdrant points with unique IDs and payloads
            points = [
                models.PointStruct(
                    id=str(uuid.uuid4()),  # Generate a unique ID for each point
                    vector=vector,
                    payload={"context": context}
                )
                for context, vector in zip(batch, embeddings)
            ]
            
            # 3. Upload points to the collection
            self.client.upload_points(
                collection_name=self.collection_name,
                points=points,
                wait=False  # Asynchronous upload for speed
            )
            
        print("Data ingestion complete.")
        print("Updating collection indexing threshold...")
        self.client.update_collection(
            collection_name=self.collection_name,
            optimizer_config=models.OptimizersConfigDiff(indexing_threshold=20000)
        )
        print("Collection setup is finished.")

    def answer_question(self, query: str, top_k: int = 3) -> str:
        """
        Searches the vector database for a given query and returns the most relevant contexts.
        
        Args:
            query: User's question
            top_k: Number of top results to return
            
        Returns:
            Formatted string with relevant FAQ contexts
        """
        # 1. Create an embedding for the user's query
        query_embedding = self.embed_model.get_query_embedding(query)

        # 2. Search Qdrant for the most similar vectors
        try:
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=top_k,
                score_threshold=0.5  # Optional: filter out less relevant results
            ).points
        except AttributeError:
            # Fallback for older qdrant-client versions
            from qdrant_client.models import SearchRequest
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=0.5
            )

        # 3. Format the results into a single string
        if not search_result:
            return "I couldn't find a relevant answer in my knowledge base."

        relevant_contexts = [
            hit.payload["context"] for hit in search_result
        ]
        
        # Combine the contexts into a final, readable output
        formatted_output = "\n\n---\n\n".join([
            f"Here are the most relevant pieces of information I found:\n\n{ctx}"
            for ctx in relevant_contexts
        ])
        return formatted_output

