import json
import re
from typing import Dict, Any, List
import json_repair
from rapidfuzz import process, fuzz

def extract_json_block(text: str) -> str:
    """Extracts JSON from markdown code blocks if the model wraps it."""
    match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    return text

def parse_step_json(raw_content: str) -> Dict[str, Any]:
    """Extracts, repairs, and parses JSON output from models."""
    cleaned_text = extract_json_block(raw_content)
    
    # json_repair fixes trailing commas, missing quotes, unescaped chars
    repaired = json_repair.repair_json(cleaned_text)
    
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        raise ValueError("Could not parse or repair JSON from model output.")

def match_tool_name(requested_name: str, available_tools: List[str]) -> str:
    """Fuzzy matches the requested tool name to handle slight hallucinations."""
    if not requested_name or not available_tools:
        return requested_name
        
    if requested_name in available_tools:
        return requested_name
        
    # Find the best match using RapidFuzz
    match = process.extractOne(requested_name, available_tools, scorer=fuzz.WRatio)
    if match:
        best_match_name, score, _ = match
        # If the score is decently high (> 80), auto-correct it
        if score > 80:
            return best_match_name
            
    return requested_name
