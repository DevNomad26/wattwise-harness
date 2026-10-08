from mcp_servers.tariff import compute_bill

def test_multi_state_compute():
    print("Running Multi-State Tariff Tests...\n")
    
    # Maharashtra Test (150 units)
    # Energy: (100 * 5.58) + (50 * 11.46) = 1131
    # Duty: 16% of 1131 = 180.96
    # Fixed: 128
    # Total: 128 + 1131 + 180.96 = 1439.96
    res1 = compute_bill(150, "Maharashtra")
    assert "Rs 1439.96" in res1, f"MH Failed: {res1}"
    print("[PASS] Maharashtra: 150 units = Rs 1439.96")
    
    # Gujarat Test (100 units)
    # Energy: (50 * 3.05) + (50 * 3.50) = 152.5 + 175 = 327.5
    # Duty: 15% of 327.5 = 49.125 (49.12)
    # Fixed: 40
    # Total: 40 + 327.5 + 49.125 = 416.62
    res2 = compute_bill(100, "Gujarat")
    assert "Rs 416.6" in res2, f"GJ Failed: {res2}"
    print("[PASS] Gujarat: 100 units = Rs 416.62")
    
    # Rajasthan Test (50 units)
    # Energy: 50 * 4.75 = 237.5
    # Duty: 5% of 237.5 = 11.875
    # Fixed: 275
    # Total: 275 + 237.5 + 11.875 = 524.38
    res3 = compute_bill(50, "Rajasthan")
    assert "Rs 524.3" in res3, f"RJ Failed: {res3}"
    print("[PASS] Rajasthan: 50 units = Rs 524.38")
    
    print("\nAll states calculated perfectly!")

if __name__ == "__main__":
    test_multi_state_compute()
