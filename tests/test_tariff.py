from mcp_servers.tariff import compute_bill

def test_compute_bill():
    print("Running Official MSEDCL Tariff Tests...\n")
    
    # Test 1: 50 units (Hits 1st slab: 5.58)
    # Energy: 50 * 5.58 = 279
    # Duty: 16% of 279 = 44.64
    # Fixed: 128
    # Total: 128 + 279 + 44.64 = 451.64
    res1 = compute_bill(50)
    assert "Rs 451.64" in res1, f"Failed Test 1: {res1}"
    print("[PASS] Test 1: 50 units = Rs 451.64")
    
    # Test 2: 150 units (Hits 1st and 2nd slab)
    # Energy: (100 * 5.58) + (50 * 11.46) = 558 + 573 = 1131
    # Duty: 16% of 1131 = 180.96
    # Fixed: 128
    # Total: 128 + 1131 + 180.96 = 1439.96
    res2 = compute_bill(150)
    assert "Rs 1439.96" in res2, f"Failed Test 2: {res2}"
    print("[PASS] Test 2: 150 units = Rs 1439.96")
    
    # Test 3: 350 units (Hits 1st, 2nd, and 3rd slab)
    # Energy: (100 * 5.58) + (200 * 11.46) + (50 * 15.72) = 558 + 2292 + 786 = 3636
    # Duty: 16% of 3636 = 581.76
    # Fixed: 128
    # Total: 128 + 3636 + 581.76 = 4345.76
    res3 = compute_bill(350)
    assert "Rs 4345.76" in res3, f"Failed Test 3: {res3}"
    print("[PASS] Test 3: 350 units = Rs 4345.76")
    
    print("\nAll 3 hand-checked tests matched the official Maharashtra tariff!")

if __name__ == "__main__":
    test_compute_bill()
