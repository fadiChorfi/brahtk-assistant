from fastapi import FastAPI, HTTPException
from supabase import create_client, Client
from pydantic import BaseModel
from tools.services import fetch_available_services
from dotenv import load_dotenv
from assistant import app as agent_app
from langchain_core.messages import HumanMessage 
import os

load_dotenv()

app = FastAPI()

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")) # pyright: ignore[reportArgumentType]

class ChatRequest (BaseModel):
    message: str
    thread_id: str
    
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



if __name__ == "__main__":
 import uvicorn
 uvicorn.run(app, host="0.0.0.0", port=8000)