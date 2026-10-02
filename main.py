from fastapi import FastAPI, HTTPException
from supabase import create_client, Client
from pydantic import BaseModel, Field, field_validator
from langchain_core.messages import HumanMessage 
from fastapi.middleware.cors import CORSMiddleware
from  tools.services import fetch_available_services
from tools.services import fetch_available_services
from assistant import app as agent_app
from dotenv import load_dotenv
import os
import re

load_dotenv()

app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")) # pyright: ignore[reportArgumentType]


PROMPT_INJECTION_PATTERN = re.compile(
    r"(ignore\s+(all\s+)?(previous|above)\s+instructions|system\s+prompt|reveal\s+instructions|you\s+are\s+now\s+DAN)",
    re.IGNORECASE,
)

class ChatRequest (BaseModel):
    message: str=  Field(
        ...,
        min_length=2, 
        max_length=800,
        description= "User query for the cleaning assistant.",
        examples=["كم سعر تنظيف الأرائك؟"]
    )
    thread_id: str= Field(
        ...,
        min_length=3,
        max_length=64,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        description="Session or user thread ID.",
        examples=["user_session_101"],
    )
    
class ChatResponse (BaseModel):
    reply: str
    thread_id: str
    


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    
    config = {"configurable": {"thread_id": req.thread_id}}
    input_data = {"messages": [HumanMessage(content=req.message)]}
    
    try:
        result = await agent_app.ainvoke(input_data, config=config) # pyright: ignore[reportArgumentType]
        
        final_message = result["messages"][-1]
        reply_content = str(final_message.content) 
        return ChatResponse(reply=reply_content, thread_id=req.thread_id)
    
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal Agent Error: {str(e)}"
        )


@app.get("/")
async def root():
    return {"status": "online", "service": "Brahtk AI Assistant API"}


@app.get("/services")
async def services():
     return fetch_available_services()
    


if __name__ == "__main__":
 import uvicorn
 uvicorn.run(app, host="0.0.0.0", port=8000)