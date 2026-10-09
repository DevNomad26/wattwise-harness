import httpx
import json

class ThinkingController:
    def __init__(self, max_tokens: int = 2000, repeat_threshold: int = 3):
        self.max_tokens = max_tokens
        self.repeat_threshold = repeat_threshold

    def _check_repetition(self, text: str) -> bool:
        """Detects if a substantial phrase repeats 3+ times."""
        words = text.split()
        if len(words) < 15:
            return False
            
        # Check if the last 5 words repeat 3 times in the text
        phrase = " ".join(words[-5:])
        if text.count(phrase) >= self.repeat_threshold:
            return True
        return False

    async def stream_and_monitor(self, client: httpx.AsyncClient, url: str, payload: dict) -> str:
        """
        Streams the response from the LLM. 
        If it gets stuck in an infinite <think> loop or exceeds the token budget,
        aborts the stream and returns a specific cutoff signal.
        """
        payload["stream"] = True
        
        full_content = ""
        in_think_block = False
        think_content = ""
        token_count = 0
        
        # Async stream the response
        async with client.stream("POST", url, json=payload, timeout=300.0) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    chunk = data.get("message", {}).get("content", "")
                    
                    full_content += chunk
                    token_count += 1
                    
                    if "<think>" in chunk or "<think>" in full_content:
                        in_think_block = True
                        
                    if in_think_block:
                        think_content += chunk
                        
                        # 1. Failsafe: Token budget exceeded
                        if token_count > self.max_tokens:
                            print("\n[ThinkingController] Token budget exceeded! Cutting off thought process.")
                            return "<CUTOFF>_TOKEN_BUDGET"
                            
                        # 2. Failsafe: Repetition loop detected (check every ~10 tokens to save CPU)
                        if token_count % 10 == 0:
                            if self._check_repetition(think_content):
                                print("\n[ThinkingController] Infinite loop detected! Cutting off thought process.")
                                return "<CUTOFF>_REPETITION"
                                
                    if "</think>" in chunk or ("</think>" in full_content and in_think_block):
                        in_think_block = False
                        
                    if data.get("done", False):
                        break
                        
                except json.JSONDecodeError:
                    continue
                    
        return full_content
