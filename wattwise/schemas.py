from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

class Step(BaseModel):
    action: str = Field(..., description="'think', 'tool', or 'final'")
    thought: Optional[str] = Field(None, description="The reasoning for this step")
    tool_name: Optional[str] = Field(None, description="Name of tool if action is 'tool'")
    tool_args: Optional[Dict[str, Any]] = Field(None, description="Args for the tool")
    final_answer: Optional[str] = Field(None, description="The final answer to the user")

class BillData(BaseModel):
    state: str = Field(..., description="The state or region of the electricity board")
    months: float = Field(..., description="Number of months this bill covers (usually 1)")
    previous_reading: float = Field(..., description="The previous meter reading")
    current_reading: float = Field(..., description="The current meter reading")
    units: float = Field(..., description="Total units consumed (current_reading - previous_reading)")
    total_amount_due: Optional[float] = Field(None, description="The total amount due on the bill")
    due_date: Optional[str] = Field(None, description="The due date of the bill in YYYY-MM-DD format if available")
