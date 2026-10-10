---
name: energy-saving-advisor
description: Advise users on practical steps to save electricity, lower unit consumption, and drop to a cheaper tariff slab. Use when the user asks how to reduce their bill, save power, or cut costs.
---
# Energy Saving Advisor

Follow these steps in order. Call one tool per step. Never do arithmetic yourself: every number in your answer must come from a tool result.

1. **Get bill consumption data**:
   - If the bill was already read in earlier conversation turns, reuse the units, load (kW), and state.
   - If the user provides a new bill photo, call `extract_bill_data` with the image path.
   - If the user only gave units/state in text, use those numbers directly.

2. **Check tariff slabs and target threshold**:
   - Call `get_tariff_info` with the state to view the slab boundaries and rates.
   - Find the upper limit of the lower slab just below current consumption (e.g. if current usage is 240 units and slab boundary is 200 units, target reduction is 40 units).
   - Use `calculate` to compute the required unit reduction:
     `{"action": "tool", "tool_name": "calculate", "tool_args": {"expression": "<current_units> - <lower_slab_limit>"}}`

3. **Calculate potential savings**:
   - Call `compute_bill` for current units and `compute_bill` for target reduced units.
   - Use `calculate` to find the exact rupee savings per month:
     `{"action": "tool", "tool_name": "calculate", "tool_args": {"expression": "<current_bill_total> - <reduced_bill_total>"}}`

4. **Provide targeted appliance-level advice**:
   Based on the unit reduction target, provide high-impact recommendations:
   - **Air Conditioner (AC)**:
     - Set temperature to 24°C–26°C (each 1°C increase reduces AC power by ~6%).
     - Clean air filters every 2 weeks (improves efficiency by 5–15%).
     - Reducing AC usage by 2 hours/day saves ~90 units/month (1.5 kW × 2 hrs × 30 days).
   - **Water Heater / Geyser**:
     - Switch off immediately after heating (avoid standby heat loss).
     - Reducing geyser usage by 30 mins/day saves ~30 units/month (2 kW × 0.5 hr × 30 days).
   - **Refrigerator**:
     - Maintain medium cooling setting and ensure door gasket seal is intact.
   - **Standby Power / Phantom Loads**:
     - Turn off power strips and set-top boxes at the switch (saves ~10–15 units/month).

5. **Final Answer**:
   Present a clear, concise summary with:
   - Current units and current monthly cost.
   - Target units to drop to the cheaper tariff slab.
   - Potential monthly savings in Rupees.
   - Top 3 actionable tips for their household.

Rules:
- Keep advice practical, actionable, and specific to Indian households.
- Every number and calculation must strictly come from the `calculate` or `compute_bill` tool results.
- If the user wrote in Hindi, reply in simple Hindi.
