from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

class Step(BaseModel):
    action: str = Field(..., description="'think', 'tool', or 'final'")
    thought: Optional[str] = Field(None, description="The reasoning for this step")
    tool_name: Optional[str] = Field(None, description="Name of tool if action is 'tool'")
    tool_args: Optional[Dict[str, Any]] = Field(None, description="Args for the tool")
    final_answer: Optional[str] = Field(None, description="The final answer to the user")

class BillData(BaseModel):
    units: float
    months: float
    state: str
