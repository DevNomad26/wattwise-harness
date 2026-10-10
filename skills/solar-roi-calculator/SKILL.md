---
name: solar-roi-calculator
description: Calculate rooftop solar plant capacity, estimated setup cost, PM Surya Ghar government subsidy, monthly savings, and payback period. Use when the user asks about installing solar panels or rooftop solar savings.
---
# Solar ROI Calculator

Follow these steps in order. Call one tool per step. Never do arithmetic yourself: every number in your answer must come from a tool result.

1. **Determine Monthly Consumption & State**:
   - Reuse `units` and `state` from earlier conversation turns or user prompt.
   - If not provided, ask the user for their average monthly electricity units or monthly bill amount.

2. **Calculate Required Solar Capacity (kW)**:
   - In India, a 1 kW rooftop solar system generates approximately 120 units (kWh) per month (~4 units/day).
   - Use `calculate` to determine required plant capacity rounded to 1 decimal place:
     `{"action": "tool", "tool_name": "calculate", "tool_args": {"expression": "round(<units> / 120, 1)"}}`

3. **Calculate System Cost and PM Surya Ghar Subsidy**:
   - Estimated benchmark system cost is Rs 55,000 per kW.
   - Use `calculate` for gross system cost:
     `{"action": "tool", "tool_name": "calculate", "tool_args": {"expression": "round(<capacity_kw> * 55000, 0)"}}`
   - Apply Central Government Subsidy (PM Surya Ghar Muft Bijli Yojana):
     - For systems up to 1 kW: Rs 30,000
     - For 2 kW systems: Rs 60,000
     - For 3 kW and higher: Rs 78,000 (maximum cap)
   - Use `calculate` for net cost out of pocket:
     `{"action": "tool", "tool_name": "calculate", "tool_args": {"expression": "<gross_cost> - <subsidy>"}}`

4. **Calculate Bill Savings and Payback Period**:
   - Call `compute_bill` with current units to determine monthly grid electricity spend.
   - Call `calculate` for estimated annual savings:
     `{"action": "tool", "tool_name": "calculate", "tool_args": {"expression": "round(<monthly_bill> * 12, 0)"}}`
   - Call `calculate` for estimated payback period in years:
     `{"action": "tool", "tool_name": "calculate", "tool_args": {"expression": "round(<net_cost> / (<monthly_bill> * 12), 1)"}}`

5. **Final Answer**:
   Present the estimate in a clean structured format:
   - **Recommended System Size**: `<capacity_kw> kW` (requires ~100 sq.ft shade-free roof per kW).
   - **Gross Estimated Cost**: `Rs <gross_cost>`
   - **PM Surya Ghar Subsidy**: `Rs <subsidy>`
   - **Net Out-of-Pocket Cost**: `Rs <net_cost>`
   - **Estimated Annual Savings**: `Rs <annual_savings> / year`
   - **Estimated Payback Period**: `<payback_years> years` (solar panels typically have a 25-year warranty).

Rules:
- All numbers and arithmetic must come strictly from `calculate` and `compute_bill` tool calls.
- Mention that actual generation depends on shadow-free rooftop space and orientation.
