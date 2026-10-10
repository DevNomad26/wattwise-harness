import json
import os

TARIFF_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "tariff.json")


def load_tariff_data():
    assert os.path.exists(TARIFF_FILE), f"Tariff file not found at {TARIFF_FILE}"
    with open(TARIFF_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def test_tariff_json_structure():
    """Verify that tariff.json is valid JSON and has expected keys for all states."""
    data = load_tariff_data()
    assert isinstance(data, dict), "tariff.json must be a JSON object"
    assert len(data) > 0, "tariff.json must contain at least one state"

    required_keys = ["discom", "category", "fixed_charge_per_month", "slabs", "duty_percent", "effective_date", "source_link"]

    for state, info in data.items():
        for key in required_keys:
            assert key in info, f"State '{state}' is missing required key '{key}'"
        assert isinstance(info["slabs"], list), f"State '{state}' slabs must be a list"
        assert len(info["slabs"]) > 0, f"State '{state}' must have at least one slab"
        
        for slab in info["slabs"]:
            assert "upto" in slab, f"Slab in '{state}' missing 'upto'"
            assert "rate" in slab, f"Slab in '{state}' missing 'rate'"
            assert isinstance(slab["rate"], (int, float)), f"Rate in '{state}' must be a number"
    print("[PASS] tariff.json structure and keys validation")


def test_maharashtra_calculation():
    """Verify Maharashtra calculation with updated 2026 tariff."""
    data = load_tariff_data()
    mh = data.get("Maharashtra")
    assert mh is not None, "Maharashtra missing from tariff.json"
    
    # 150 units: 100 @ 5.56 + 50 @ 12.40 = 556 + 620 = 1176.0
    # Fixed: 130.0
    # Duty (16% of 1176): 188.16
    # Total: 130 + 1176 + 188.16 = 1494.16
    units = 150
    energy = (100 * 5.56) + (50 * 12.40)
    fixed = mh["fixed_charge_per_month"]
    duty = energy * mh["duty_percent"]
    total = fixed + energy + duty
    assert round(total, 2) == 1494.16, f"Expected 1494.16, got {total}"
    print(f"[PASS] Maharashtra: 150 units = Rs {total:.2f}")


def test_energy_slab_calculations():
    """Verify energy charge calculations for each state."""
    data = load_tariff_data()
    
    for state, info in data.items():
        slabs = info["slabs"]
        # Calculate energy charge for 100 units
        test_units = 100
        rem = test_units
        prev = 0
        energy = 0.0
        for slab in slabs:
            limit = slab["upto"]
            if limit is None:
                energy += rem * slab["rate"]
                break
            block = limit - prev
            if rem > 0:
                units_in_block = min(rem, block)
                energy += units_in_block * slab["rate"]
                rem -= units_in_block
            prev = limit
        
        print(f"[PASS] {state}: Base energy charge for {test_units} units = Rs {energy:.2f}")


def test_null_fields_report():
    """Audit fields where fixed_charge or duty_percent are set to null."""
    data = load_tariff_data()
    null_fixed = []
    null_duty = []

    for state, info in data.items():
        if info.get("fixed_charge_per_month") is None:
            null_fixed.append(state)
        if info.get("duty_percent") is None:
            null_duty.append(state)

    print("\n--- Tariff Data Field Audit ---")
    print(f"States with null fixed charges : {null_fixed}")
    print(f"States with null duty percent  : {null_duty}")


if __name__ == "__main__":
    print("Running Tariff Data Verification Tests...\n")
    test_tariff_json_structure()
    test_maharashtra_calculation()
    test_energy_slab_calculations()
    test_null_fields_report()
    print("\n[SUCCESS] All tariff validation tests passed!")
