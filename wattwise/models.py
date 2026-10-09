import time
import httpx
from typing import List, Dict, Any
from wattwise.thinking import ThinkingController

class OllamaClient:
    def __init__(self, model_name: str = "qwen3.5:4b", host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.host = host.rstrip('/')
        self.client = httpx.AsyncClient(timeout=300.0)
        self.thinking_controller = ThinkingController()

    async def generate(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
            "format": "json",
            "think": False
        }
        
        start_time = time.time()
        try:
            content = await self.thinking_controller.stream_and_monitor(
                self.client, 
                f"{self.host}/api/chat", 
                payload
            )
            
            elapsed = time.time() - start_time
            print(f"[{self.model_name}] Call completed in {elapsed:.2f}s")
            
            return {
                "content": content
            }
        except Exception as e:
            print(f"[{self.model_name}] Request failed: {e}")
            raise
