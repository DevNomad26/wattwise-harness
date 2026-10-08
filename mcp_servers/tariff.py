import os
import json
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("Tariff Server")

TARIFF_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tariff.json")

def load_tariff():
    with open(TARIFF_FILE, "r") as f:
        return json.load(f)

@mcp.tool()
def get_tariff_info() -> str:
    """Returns the official electricity tariff slabs and fixed charges."""
    data = load_tariff()
    info = f"Electricity Tariff Information for {data['discom']} (Effective: {data['effective_from']}):\n"
    info += f"- Fixed Charge: Rs {data['fixed_charge_per_month']}\n"
    for slab in data['slabs']:
        upto = slab['upto'] if slab['upto'] else "Above"
        info += f"- Up to {upto} units: Rs {slab['rate']} per unit\n"
    info += f"- Electricity Duty: {data['duty_percent']*100}%\n"
    info += f"Source: {data['source_url']}\n"
    return info

@mcp.tool()
def compute_bill(units: float) -> str:
    """Calculates the total electricity bill based on official tariff data."""
    if units < 0:
        return "Error: Units cannot be negative."
        
    data = load_tariff()
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
    # Add duty (16% of energy charge usually)
    duty = energy_charge * data.get('duty_percent', 0.16)
    total_cost += duty
    
    return f"Total bill for {units} units is Rs {total_cost:.2f} (Includes Rs {data['fixed_charge_per_month']} fixed, Rs {energy_charge:.2f} energy, Rs {duty:.2f} duty)."

if __name__ == "__main__":
    mcp.run(transport='stdio')
