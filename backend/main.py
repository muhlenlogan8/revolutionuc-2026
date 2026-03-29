from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from database import get_connection
from gemini_functions import initialize_inventory as gemini_initialize_inventory
from gemini_functions import check_inventory as gemini_check_inventory
from datetime import datetime
import shutil
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/tools")
def get_tools():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tools")
    tools = cursor.fetchall()
    conn.close()
    return [dict(row) for row in tools]

@app.post("/tools")
def add_tool(name: str, state: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tools (name, state, last_state_change) VALUES (?, ?, ?)", (name, state, datetime.now()))
    conn.commit()
    conn.close()
    return {"message": "Tool added successfully"}

@app.post("/initialize_inventory")
async def initialize_inventory(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    result = gemini_initialize_inventory(file_path)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Wipe old baseline
    cursor.execute("DELETE FROM tools")
    
    # Insert detected tools as baseline
    for tool in result["tools"]:
        cursor.execute("INSERT INTO tools (name, state, last_state_change) VALUES (?, ?, ?)", (tool["name"], "present", datetime.now()))
        
    conn.commit()
    conn.close()
    
    return {
        "message": "Inventory initialized",
        "tools": result.get("tools", [])
    }

@app.post("/check_inventory")
async def check_inventory(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # Expected tools come from the database
    cursor.execute("SELECT name FROM tools")
    db_tools = cursor.fetchall()
    expected_tools = [row["name"] for row in db_tools]
    
    result = gemini_check_inventory(file_path, expected_tools)
    
    now = datetime.now().isoformat()
    
    # Update states in database
    for tool in result.get("tools", []):
        new_state = "in" if tool["present"] else "out"
        
        cursor.execute("SELECT state FROM tools WHERE name = ?", (tool["name"],))
        existing = cursor.fetchone()
        
        if existing and existing["state"] != new_state:
            cursor.execute("UPDATE tools SET state = ?, last_state_change = ? WHERE name = ?", (new_state, now, tool["name"]))
            
    conn.commit()
    
    cursor.execute("SELECT * FROM tools")
    updated_tools = cursor.fetchall()
    conn.close()
    
    return {
        "message": "Inventory checked",
        "tools": [dict(row) for row in updated_tools]
    }
    
@app.delete("/tools")
def delete_all_tools():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tools")
    conn.commit()
    conn.close()
    return {"message": "All tools deleted"}

@app.post("/upload-image")
async def upload_image(request: Request):
    data = await request.body()
    
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    path = os.path.join(UPLOAD_DIR, filename)
    
    with open(path, "wb") as f:
        f.write(data)
        
    return {"message": "Image uploaded successfully", "filename": filename, "bytes": len(data)}