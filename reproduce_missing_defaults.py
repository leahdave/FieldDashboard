from utils import _calculate_weighted_score

def test_missing_defaults():
    print("Testing Scoring for Cell 1, 2, 3...")
    
    # Case 1: Exact Prefix Match
    # T: "Cell 1 Buyers..."
    # A: "Cell 1 Buyers..." (Ideal)
    # A: "Cell 1 : Current" (Likely actual)
    
    t1 = "Cell 1 Buyers N=100"
    a1 = "Cell 1 : Current"
    
    s1 = _calculate_weighted_score(t1, a1)
    print(f"'{t1}' vs '{a1}' -> {s1}")
    
    # Case 2: Cell 2 (User said this wasn't populating)
    t2 = "Cell 2 Same Design N=100"
    a2 = "Cell 2 : Current" # Assuming this exists?
    
    s2 = _calculate_weighted_score(t2, a2)
    print(f"'{t2}' vs '{a2}' -> {s2}")
    
    # Case 3: Cell 3
    t3 = "Cell 3 Different N=100"
    a3 = "Cell 3 : Current"
    
    s3 = _calculate_weighted_score(t3, a3)
    print(f"'{t3}' vs '{a3}' -> {s3}")
    
    # Threshold in app.py or utils.py is 60?
    
    if s1 < 60 or s2 < 60 or s3 < 60:
        print("[FAIL] Scores are below default threshold (60)!")
    else:
        print("[PASS] Scores look okay, maybe it's the uniqueness contest?")

if __name__ == "__main__":
    test_missing_defaults()
