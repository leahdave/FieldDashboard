from utils import get_smart_unique_matches, _calculate_weighted_score

def test_complex_assignment():
    print("Testing Complex Greedy Assignment...")
    
    # User Scenario:
    # T1: "Cell 1 Buyers..." (Score 88)
    # T2: "Cell 2 Same..." (Score 87)
    # T3: "Cell 3 Diff..." (Score 100)
    
    # Candidates:
    # C1: "Cell 1 : Current"
    # C2: "Cell 2 : Current"
    # C3: "Cell 3 : Current"
    
    # What if there's a distractor?
    # T4: "Cell 1 : Previous" (Maybe unmatched in target?)
    
    targets = [
        "Cell 1 Buyers N=100",
        "Cell 2 Same Design N=100",
        "Cell 3 Different N=100"
    ]
    
    candidates = [
        "Cell 1 : Current",
        "Cell 2 : Current",
        "Cell 3 : Current",
        "Cell 4 : Current"
    ]
    
    # Run the function
    assignments = get_smart_unique_matches(targets, candidates, threshold=60)
    
    print("\nAssignments:")
    for t, match in assignments.items():
        print(f"Target: '{t}' -> Mapped: '{match}'")
        
    # Check correctness
    if assignments.get(targets[0])[0] == candidates[0]:
        print("[PASS] Cell 1 mapped to Cell 1")
    else:
        print("[FAIL] Cell 1 NOT mapped to Cell 1")
        
    if assignments.get(targets[1])[0] == candidates[1]:
        print("[PASS] Cell 2 mapped to Cell 2")
    else:
        print(f"[FAIL] Cell 2 NOT mapped to Cell 2 (Got {assignments.get(targets[1])})")

if __name__ == "__main__":
    test_complex_assignment()
