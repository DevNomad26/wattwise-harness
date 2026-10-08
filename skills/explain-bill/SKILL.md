---
name: explain-bill
description: Explain an electricity bill or a change in the bill in simple words. Use when the user asks what the charges mean or why the bill went up.
---
# Explain a bill

1. If you do not already have the bill numbers, first follow the `bill-checker` steps 1 to 3.
2. Call `get_tariff_info` with the state to get the slab rates:
   `{"action": "tool", "tool_name": "get_tariff_info", "tool_args": {"state": "Rajasthan"}}`
3. Explain the bill in three parts:
   - Fixed charge: a monthly amount you pay even if you use no electricity.
   - Energy charge: units are billed in slabs. The first units are cheap; each later block costs more per unit. Say which slabs this bill reached.
   - Electricity duty: a tax added on top of the energy charge.
4. If the user asks why the bill went up, list the reasons that fit the numbers:
   - More units used (for example AC, cooler or geyser season)
   - Crossing into a higher slab, so extra units cost more
   - Arrears or late fees from an earlier bill
   - An estimated reading instead of an actual meter reading
   - A meter reading mistake (check that current minus previous equals units)

Rules:
- Use short, simple sentences. Avoid technical words.
- If the user wrote in Hindi, reply in simple Hindi.
- Any calculation goes through `calculate`. Copy numbers exactly from tool results.
