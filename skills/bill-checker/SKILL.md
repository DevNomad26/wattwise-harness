---
name: bill-checker
description: Check whether an electricity bill is correct. Use when the user gives a bill photo path or asks if their bill is right or too high.
---
# Bill checker

Follow these steps in order, starting with step 1. Call one tool per step. Values in <angle brackets> are placeholders: fill them only from earlier tool results. Never do arithmetic yourself: every number in your answer must come from a tool result.

1. Read the bill. Call `extract_bill_data` with the photo path the user gave:
   `{"action": "tool", "tool_name": "extract_bill_data", "tool_args": {"image_path": "<path>"}}`
   If the result has "error", stop and tell the user which fields could not be read.

2. Read the "warnings" list in that result. The tool has already checked the readings and units with the calculator.
   - If a warning starts with "IMPOSSIBLE UNITS" or "UNUSUAL AMOUNT", the bill is very likely wrong. Your next reply must be the final answer (step 5) with that warning as the verdict. Do not call compute_bill or calculate.
   - If a warning starts with "NON-DOMESTIC", the tariff cannot check this bill. Your next reply must be the final answer: give the bill details and say only domestic bills can be recomputed. Do not call compute_bill.
   - Keep every other warning to mention in the final answer.

3. Recompute the bill. Call `compute_bill` with the units and state from step 1:
   `{"action": "tool", "tool_name": "compute_bill", "tool_args": {"units": <units from step 1>, "state": "<state from step 1>"}}`
   If it says the state is not available, tell the user that state is not supported yet, give the bill details from step 1, and stop.

4. Compare. Call `calculate` with `"<total_amount_due> - <computed total>"`, copying both numbers exactly:
   `{"action": "tool", "tool_name": "calculate", "tool_args": {"expression": "<total_amount_due> - <computed total>"}}`
   - Result between -5 and 5: the bill matches the tariff.
   - Above 5: the bill is higher than the tariff amount by that much.
   - Below -5: the bill is lower than the tariff amount by that much.

5. Give the final answer as plain sentences for the user:
   `{"action": "final", "final_answer": "..."}`
   Include:
   - The verdict: matches the tariff, higher by Rs X, lower by Rs X, wrong because of an IMPOSSIBLE UNITS or UNUSUAL AMOUNT warning, or cannot be checked (NON-DOMESTIC).
   - Units, state and bill total from step 1.
   - If you ran steps 3 and 4: the tariff total with its fixed, energy and duty parts, and the difference.
   - The warnings from step 1, in simple words.
   If the bill is wrong or higher by more than Rs 5, say that a meter reading mistake, arrears or late fees can cause this, and offer to write a complaint letter with the `complaint-letter` skill.

Rules:
- Copy every number exactly from tool results. Never guess a number that a tool did not return.
- Write numbers with the same digits the tool returned (800589850.0 -> Rs 800589850). Do not add commas or change digits.
- The final answer is text for the user, never a tool call or a list of arguments.
