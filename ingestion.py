import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from supabase import create_client
import hashlib


load_dotenv()
client = genai.Client()
supabase = create_client(
    os.getenv("SUPABASE_URL"), 
    os.getenv("SUPABASE_KEY")
)

def load_chunks():
    
    paths= [
        "chunks/chunks_ar.json",
        "chunks/chunks_en.json",
        "chunks/chunks_fr.json"
    ]
    all_chunks= []
    for path in paths: 
        with open(path, "r", encoding="utf-8") as file:
            data= json.load(file)
            file_chunks = data.get("chunks", [])
            all_chunks.extend(file_chunks)
            
    return all_chunks



def embed_text(chunks: str) -> list[float]:
    """Generate a 786-dimensional vector embedding for a given string."""
    res = client.models.embed_content(
        model= "gemini-embedding-001",
        contents= chunks,
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    print(res.embeddings)
    return res.embeddings[0].values

def compute_content_hash(text: str)-> str:
    """Generates a SHA-256 hash string for tracking content changes."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def ingest_to_supabase ():
    chunks = load_chunks()
    records=[]
    for chunk in chunks:
        text_content= chunk["text"]
        vector = embed_text(text_content)
        text_hash = compute_content_hash(text_content)
        
        record = {
            "id": chunk["id"],
            "group_id": chunk["group_id"],
            "lang": chunk["lang"],
            "source_type": chunk["source_type"],
            "header": chunk["header"],
            "text": text_content,
            "metadata": chunk.get("metadata", {}),
            "embedding": vector,
            "embedding_model": "gemini-embedding-001",
            "content_hash": text_hash,
        }
        records.append(record)
    print(f"Upserting {len(records)} records into 'kb_chunks' table...")
    
    response= supabase.table("kb_chunks").upsert(records).execute()
    print("✅ Ingestion successfully completed!")



if __name__ == "__main__":
    ingest_to_supabase()

    