import os
import json
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("Tariff Server", log_level="WARNING")

TARIFF_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tariff.json")

def load_tariff():
    with open(TARIFF_FILE, "r") as f:
        return json.load(f)

@mcp.tool()
def get_tariff_info(state: str) -> str:
    """Returns the official electricity tariff slabs and fixed charges for the requested state."""
    full_data = load_tariff()
    
    # Simple matching logic just in case AI capitalizes wrongly
    matched_state = next((k for k in full_data.keys() if k.lower() in state.lower()), None)
    if not matched_state:
        return f"Error: Tariff data for state '{state}' is not available."
        
    data = full_data[matched_state]
    info = f"Electricity Tariff Information for {data['discom']}:\n"
    info += f"- Fixed Charge: Rs {data['fixed_charge_per_month']}\n"
    for slab in data['slabs']:
        upto = slab['upto'] if slab['upto'] else "Above"
        info += f"- Up to {upto} units: Rs {slab['rate']} per unit\n"
    info += f"- Electricity Duty: {data['duty_percent']*100}%\n"
    return info

@mcp.tool()
def compute_bill(units: float, state: str) -> str:
    """Calculates the total electricity bill based on official tariff data for a specific state."""
    if units < 0:
        return "Error: Units cannot be negative."
        
    full_data = load_tariff()
    matched_state = next((k for k in full_data.keys() if k.lower() in state.lower()), None)
    if not matched_state:
        return f"Error: Tariff data for state '{state}' is not available."
        
    data = full_data[matched_state]
    total_cost = data['fixed_charge_per_month']
    remaining_units = units
    energy_charge = 0.0
    
    prev_limit = 0
    for slab in data['slabs']:
        limit = slab['upto']
        if limit is None:
            # Infinite slab
            energy_charge += remaining_units * slab['rate']
            break
            
        block_size = limit - prev_limit
        if remaining_units > 0:
            block_units = min(remaining_units, block_size)
            energy_charge += block_units * slab['rate']
            remaining_units -= block_units
        prev_limit = limit
        
    total_cost += energy_charge
    # Add duty
    duty = energy_charge * data.get('duty_percent', 0.16)
    total_cost += duty
    
    return f"Total bill for {units} units in {matched_state} is Rs {total_cost:.2f} (Includes Rs {data['fixed_charge_per_month']} fixed, Rs {energy_charge:.2f} energy, Rs {duty:.2f} duty)."

if __name__ == "__main__":
    mcp.run(transport='stdio')
