import os
from typing import Any, cast
from dotenv import load_dotenv
from google import genai
from google.genai import types
from langchain_core.tools import Tool
from supabase import Client, create_client

load_dotenv()

gemini_client = genai.Client()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables.")

supabase: Client = create_client(supabase_url, supabase_key)


def search_company_knowledge(query: str = "") -> str:
    """Perform vector search on company FAQs, policies, and general background information."""
    try:
        embed_response = gemini_client.models.embed_content(
        model="gemini-embedding-001",
        contents=query,
        config=types.EmbedContentConfig(output_dimensionality=768),
        )

        if not embed_response.embeddings or len(embed_response.embeddings) == 0:
            return "Error: Failed to generate query vector embedding."

        query_vector = embed_response.embeddings[0].values

        response = supabase.rpc("match_kb_chunks", {
            "query_embedding": query_vector,
            "match_count": 3
        }).execute()

        if not response.data or not isinstance(response.data, list):
            return "No relevant information found in knowledge base."

        records = cast(list[dict[str, Any]], response.data)

        results = []
        for row in records:
            header = row.get("header", "Info")
            text = row.get("text", "")
            results.append(f"[{header}]\n{text}")

        return "\n\n---\n\n".join(results)

    except Exception as e:
        return f"Error retrieving knowledge base context: {str(e)}"


search_company_knowledge_tool = Tool(
    name="search_company_knowledge",
    func=search_company_knowledge,
    description="Search company background information, policies, FAQs, working hours, coverage areas, equipment, and general procedures."
)






""" if __name__ == "__main__":
    print("Testing search_company_knowledge tool...\n")
    
    test_query = "What is your satisfaction guarantee policy?"
    
    result = search_company_knowledge(test_query)
    
    print("=== Vector Search Output ===")
    print(result) """
     