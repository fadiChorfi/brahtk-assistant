from fastapi import FastAPI
from supabase import create_client, Client
from pydantic import BaseModel
from tools.services import fetch_available_services
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")) # pyright: ignore[reportArgumentType]

    

@app.get("/services")
async def get_available_services():
    return fetch_available_services()




if __name__ == "__main__":
 import uvicorn
 uvicorn.run(app, host="0.0.0.0", port=8000)