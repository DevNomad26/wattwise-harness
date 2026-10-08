---
name: complaint-letter
description: Write a polite complaint letter to the electricity company about a wrong bill. Use only after bill-checker found the bill higher by more than Rs 5.
---
# Complaint letter

1. Make sure you have these from earlier tool results: state, previous reading, current reading, units, bill total, computed total, difference, and the fixed, energy and duty amounts. If anything is missing, follow the `bill-checker` skill first.
2. Get the company name. Call `get_tariff_info` with the state; the first line names the company (for example JVVNL).
3. Write the letter using the template in `assets/letter-template.md`. Replace every `{field}` with the exact number from the tool results.
4. Keep `[Your Name]`, `[Consumer Number]`, `[Address]`, `[Phone]` and `[Date]` as placeholders unless the user gave them. Never invent personal details.
5. Give the letter as the final answer, then remind the user to attach a copy of the bill.

Rules:
- Use only numbers that came from tools. Do not add new numbers.
- Polite and factual. No threats, no legal claims.
- Ask the company to recheck the meter reading and revise the bill.
