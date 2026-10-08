import time
import httpx
from typing import List, Dict, Any

class OllamaClient:
    def __init__(self, model_name: str = "qwen3.5:4b", host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.host = host.rstrip('/')
        self.client = httpx.AsyncClient(timeout=300.0)

    async def generate(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "format": "json"
        }
        
        start_time = time.time()
        try:
            response = await self.client.post(f"{self.host}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            
            elapsed = time.time() - start_time
            print(f"[{self.model_name}] Call completed in {elapsed:.2f}s")
            
            return {
                "content": data["message"]["content"]
            }
        except Exception as e:
            print(f"[{self.model_name}] Request failed: {e}")
            raise
