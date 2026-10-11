---
name: complaint-letter
description: Write a polite complaint letter to the electricity company about a wrong bill. Use only when the user asks for a complaint letter, never to answer whether a bill is correct.
---
# Complaint letter

This skill is now loaded. It is instructions, not a tool: never call `complaint-letter` or `load_skill` for it again. Write the letter yourself and give it as the final answer. If the user only asked whether the bill is correct, answer that instead and offer a letter; do not write one.

1. Use the results already in this conversation. Do not read the bill photo again if `extract_bill_data` was already called. You need: discom (company), state, due date, units, bill total (total_amount_due), the warnings, and, if `compute_bill` was called, the computed total, its fixed, energy and duty parts and the difference. If nothing about the bill is in the conversation yet, follow the `bill-checker` skill first.
2. Fill in the letter below (without the ``` lines). Replace every `{field}` with the exact value from the tool results. Use the discom from `extract_bill_data` as `{company}`.
   - Leave out the readings paragraph if the readings were not read.
   - If `compute_bill` was not called, replace the tariff paragraph with one sentence that states the warning in simple words:
     - IMPOSSIBLE UNITS: "The bill charges for {units} units, which is more than a {load_kw} kW connection can use in this billing period."
     - UNUSUAL AMOUNT: "The bill shows Rs {bill_total}, which is far higher than any tariff charge for this connection."

```
To,
The Assistant Engineer (O&M),
{company}
[Sub-division office]

Subject: Request to check and correct electricity bill, Consumer No. [Consumer Number]

Respected Sir/Madam,

I am writing about my electricity bill with due date {due_date}.

The meter readings on the bill are: previous reading {previous_reading}, current reading {current_reading}, units consumed {units}.

As per the {state} domestic tariff, the amount for {units} units comes to Rs {computed_total} (fixed charge Rs {fixed}, energy charge Rs {energy}, electricity duty Rs {duty}). The bill shows Rs {bill_total}, which is Rs {difference} higher.

I request you to:
1. Verify the meter reading.
2. Revise the bill if there is an error.
3. Explain any additional charges included, such as arrears or late fees.

A copy of the bill is attached.

Yours faithfully,
[Your Name]
[Address]
[Phone]
Date: [Date]
```

3. Keep `[Your Name]`, `[Consumer Number]`, `[Address]`, `[Phone]`, `[Sub-division office]` and `[Date]` as placeholders unless the user gave them. Never invent personal details.
4. Give the whole letter as the final answer, then remind the user to attach a copy of the bill. (The app adds how to email it.)

Rules:
- Use only numbers that came from tools. Do not add new numbers.
- Never write null or None in the letter: leave out any sentence whose value was not read.
- Write numbers with the same digits the tool returned (800589850.0 -> Rs 800589850). Do not add commas or change digits.
- Complain only about problems with the bill itself (impossible units, unusual amount, higher than the tariff). Never mention this tool's limits, such as values that could not be read, missing labels or unsupported tariffs.
- Polite and factual. No threats, no legal claims.
- Ask the company to recheck the meter reading and revise the bill.
