import os
import json
import base64
import urllib.request
from urllib.error import URLError, HTTPError
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("Vision Server")

OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
VISION_MODEL = os.getenv("VISION_MODEL", "gemma4:e4b")

def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

@mcp.tool()
def extract_bill_data(image_path: str) -> str:
    """Reads a photo of an electricity bill and extracts the reading data as JSON."""
    if not os.path.exists(image_path):
        return f'{{"error": "Image not found at {image_path}"}}'
        
    try:
        base64_image = image_to_base64(image_path)
    except Exception as e:
        return f'{{"error": "Failed to read image: {e}"}}'

    prompt = (
        "Extract the electricity bill data from this image. "
        "Return the output STRICTLY as JSON with the following keys: "
        "'state', 'months', 'previous_reading', 'current_reading', 'units', 'total_amount_due', 'due_date'."
    )
    
    payload = {
        "model": VISION_MODEL,
        "prompt": prompt,
        "images": [base64_image],
        "format": "json",
        "stream": False
    }
    
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate", 
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode())
            return result.get("response", "{}")
    except Exception as e:
        return f'{{"error": "Failed to call Vision model. Is Ollama running with {VISION_MODEL}? Details: {e}"}}'

if __name__ == "__main__":
    mcp.run(transport='stdio')
