import os
import json
from dotenv import load_dotenv
from PIL import Image
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def extract_json(text: str):
    text = text.strip()
    
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
        
    return json.loads(text.strip())

def initialize_inventory(image_path: str):
    image = Image.open(image_path)
    
    prompt = """
    You are analyzing an image of tools for an inventory system.
    
    Return ONLY valid JSON in this exact format:
    {
        "tools": [
            {
                "name": "hammer",
                "present": true,
                "box_2d": [ymin, xmin, ymax, xmax]
            }
        ]
    }
    
    Rules:
    - Only include clearly visible tools
    - Use simple names like hammer, pliers, wrench, screwdriver, etc.
    - box_2d must use integers normalized from 0 to 1000
    - present should always be true for initialization
    - No markdown
    - No explaination
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, image]
    )
    
    return extract_json(response.text)

def check_inventory(image_path: str, expected_tools):
    image = Image.open(image_path)
    expected_tools_str = ", ".join(expected_tools)
    
    prompt = f"""
    You are checking wheter expected tools are visible in an image.
    
    Expected tools: {expected_tools_str}
    
    Return ONLY valid JSON in this exact format:
    {{
        "tools": [
            {{
                "name": "hammer",
                "present": true,
            }}
        ]
    }}
    
    Rules:
    - Return one entry for every expected tool
    - present = true if visible
    - present = false if not visible
    - No markdown
    - No explaination
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, image]
    )
    
    return extract_json(response.text)

if __name__ == "__main__":
    init_result = initialize_inventory(r"Images\IMG_5839.jpeg")
    print("Initialization Result:")
    print(json.dumps(init_result, indent=2))
    
    expected = [tool["name"] for tool in init_result["tools"]]
    
    check_result = check_inventory(r"Images\IMG_5840.jpeg", expected)
    print("\nCheck Result:")
    print(json.dumps(check_result, indent=2))