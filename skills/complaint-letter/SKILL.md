---
name: complaint-letter
description: Write a polite complaint letter to the electricity company about a wrong bill. Use after bill-checker found the bill wrong or higher by more than Rs 5, or when the user asks for a complaint letter.
---
# Complaint letter

1. Use the results already in this conversation. Do not read the bill photo again if `extract_bill_data` was already called. You need: discom (company), state, due date, units, bill total (total_amount_due), the warnings, and, if `compute_bill` was called, the computed total, its fixed, energy and duty parts and the difference. If nothing about the bill is in the conversation yet, follow the `bill-checker` skill first.
2. Write the letter using the template in `assets/letter-template.md`. Replace every `{field}` with the exact value from the tool results. Use the discom from `extract_bill_data` as `{company}`.
   - If `compute_bill` was not called (for example the warning was IMPOSSIBLE UNITS, UNUSUAL AMOUNT or NON-DOMESTIC), replace the tariff paragraph with one sentence that states the warning in simple words.
   - Leave out the readings sentence if the readings were not read.
3. Keep `[Your Name]`, `[Consumer Number]`, `[Address]`, `[Phone]` and `[Date]` as placeholders unless the user gave them. Never invent personal details.
4. Give the whole letter as the final answer, then remind the user to attach a copy of the bill.

Rules:
- Use only numbers that came from tools. Do not add new numbers.
- Write numbers with the same digits the tool returned (800589850.0 -> Rs 800589850). Do not add commas or change digits.
- Complain only about problems with the bill itself (impossible units, unusual amount, higher than the tariff). Never mention this tool's limits, such as values that could not be read, missing labels or unsupported tariffs.
- Polite and factual. No threats, no legal claims.
- Ask the company to recheck the meter reading and revise the bill.
