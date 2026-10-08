from mcp_servers.tariff import compute_bill

def test_compute_bill():
    print("Running Tariff Tests...")
    
    # Test 1: 50 units (Only hits first slab)
    # Expected: 50 fixed + (50 * 3.0) = 50 + 150 = 200.00
    res1 = compute_bill(50)
    assert "Rs 200.00" in res1, f"Failed Test 1: {res1}"
    print("[PASS] Test 1 Passed (50 units = Rs 200.00)")
    
    # Test 2: 150 units (Hits first and second slab)
    # Expected: 50 fixed + (100 * 3.0) + (50 * 4.5) = 50 + 300 + 225 = 575.00
    res2 = compute_bill(150)
    assert "Rs 575.00" in res2, f"Failed Test 2: {res2}"
    print("[PASS] Test 2 Passed (150 units = Rs 575.00)")
    
    # Test 3: 250 units (Hits all three slabs)
    # Expected: 50 fixed + (100 * 3.0) + (100 * 4.5) + (50 * 6.5) = 50 + 300 + 450 + 325 = 1125.00
    res3 = compute_bill(250)
    assert "Rs 1125.00" in res3, f"Failed Test 3: {res3}"
    print("[PASS] Test 3 Passed (250 units = Rs 1125.00)")
    
    print("All 3 hand-checked tests passed successfully!")

if __name__ == "__main__":
    test_compute_bill()
