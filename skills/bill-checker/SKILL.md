---
name: bill-checker
description: Check whether an electricity bill is correct. Use when the user gives a bill photo path or asks if their bill is right or too high.
---
# Bill checker

Follow these steps in order. Call one tool per step. Never do arithmetic yourself.

1. Read the bill. Call `extract_bill_data` with the photo path the user gave:
   `{"action": "tool", "tool_name": "extract_bill_data", "tool_args": {"image_path": "<path>"}}`
   If the result contains "error", stop and tell the user the photo could not be read.

2. Check the units. Call `calculate` with `"<current_reading> - <previous_reading>"`.
   If the answer differs from `units` on the bill by more than 1, report the mismatch.

3. Recompute the bill. Call `compute_bill` with the units and state:
   `{"action": "tool", "tool_name": "compute_bill", "tool_args": {"units": 150, "state": "Rajasthan"}}`
   Supported states: Maharashtra, Gujarat, Rajasthan. For any other state, say it is not supported yet and stop.

4. Compare. Call `calculate` with `"<total_amount_due> - <computed total>"`.
   - Difference between -5 and 5: the bill is correct.
   - Difference above 5: the bill is higher than the tariff amount by that much.
   - Difference below -5: the bill is lower than the tariff amount.
   If `total_amount_due` is missing, say the total could not be read and only show the computed amount.

5. Give the final answer with: verdict, bill total, computed total, difference, and the fixed, energy and duty parts from `compute_bill`.
   If the bill is higher by more than Rs 5, mention that extra charges such as arrears or late fees can explain a difference, and offer to write a complaint letter using the `complaint-letter` skill.

Rules:
- Copy every number exactly from tool results.
- Never guess a number that a tool did not return.
