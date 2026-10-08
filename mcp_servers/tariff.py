from mcp.server.mcpserver import MCPServer

mcp = MCPServer("Tariff Server")

FIXED_CHARGE = 50.0

@mcp.tool()
def get_tariff_info() -> str:
    """Returns the current electricity tariff slabs and fixed charges."""
    info = "Electricity Tariff Information:\n"
    info += "- Fixed Charge: Rs 50.0\n"
    info += "- 0 to 100 units: Rs 3.0 per unit\n"
    info += "- 101 to 200 units: Rs 4.5 per unit\n"
    info += "- Above 200 units: Rs 6.5 per unit\n"
    return info

@mcp.tool()
def compute_bill(units: float) -> str:
    """Calculates the total electricity bill based on the number of units consumed."""
    if units < 0:
        return "Error: Units cannot be negative."
        
    total_cost = FIXED_CHARGE
    remaining_units = units
    
    # 0 - 100 block
    if remaining_units > 0:
        block_units = min(remaining_units, 100)
        total_cost += block_units * 3.0
        remaining_units -= block_units
        
    # 101 - 200 block
    if remaining_units > 0:
        block_units = min(remaining_units, 100)
        total_cost += block_units * 4.5
        remaining_units -= block_units
        
    # > 200 block
    if remaining_units > 0:
        total_cost += remaining_units * 6.5
        
    return f"Total bill for {units} units is Rs {total_cost:.2f} (Includes Rs {FIXED_CHARGE} fixed charge)."

if __name__ == "__main__":
    mcp.run(transport='stdio')
