# Sample bill photos

Sample bills for trying the harness. The personal details on them are not real.

```bash
python cli.py "Is my bill correct?" --image bill_photos/cr9_bill.jpg
```

| File | Bill | What it tests | Result |
|---|---|---|---|
| `cr9_bill.jpg` | JVVNL Jaipur, domestic, solar net meter, 10 kW | Impossible units, state from city, import/export meter table | Wrong: 11,223,059 units are more than a 10 kW connection can use (max 7,440). Checked: 282 s |
| `test_gujarat_bill.png` | PGVCL Rajkot, domestic, 150 units, 2 kW (generated) | A normal, correct bill; state not printed | Correct: matches the tariff at Rs 655.25. Checked: 276 s |
| `MH_false.jpg` | MSEDCL Bhosari, industrial, 200 HP | Absurd amount, non-domestic, units not visible | Unusual amount (Rs 5,380 per unit even at full load), non-domestic. Checked: 236 s; complaint letter follow-up 90 s |
| `MH_Correct.webp` | MSEDCL Hadapsar, domestic, 86 units, 5 kW, May 2019 | A normal domestic bill from an older year | Not run end to end yet. Expected: about Rs 94.66 lower than the tariff (Rs 684.66), because `data/tariff.json` has 2024 rates and this bill is from 2019 |
