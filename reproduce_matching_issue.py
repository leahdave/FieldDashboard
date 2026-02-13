from utils import _calculate_weighted_score

def test_fix():
    print("Testing Prefix Bias Fix...")
    
    t1 = "Cell 1 Buyers N=100"
    t2 = "Cell 2 Same Design N=100"
    
    candidate = "Cell 1 : Current"
    
    # Test Scorer
    s1 = _calculate_weighted_score(t1, candidate)
    s2 = _calculate_weighted_score(t2, candidate)
    
    print(f"'{t1}' vs '{candidate}' -> {s1}")
    print(f"'{t2}' vs '{candidate}' -> {s2}")
    
    # Expect s1 >> s2
    # s1 should match "Cell" == "Cell", "1" == "1" -> Boost
    # s2 should match "Cell" == "Cell", "2" != "1" -> Penalty
    
    assert s1 > s2
    assert s1 > 80
    assert s2 < s1
    
    print("[PASS] Prefix Bias Correct: 'Cell 1' beats 'Cell 2' for 'Cell 1' target.")

if __name__ == "__main__":
    test_fix()
