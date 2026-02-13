from utils import get_smart_unique_matches

def test_smart_defaults():
    print("Testing Smart Unique Defaults...")
    
    # Scenario:
    # Target: "Apple", "Apples"
    # Dashboard: "Apple", "Applesauce"
    
    # "Apple" matches "Apple" (100%)
    # "Apples" matches "Apple" (90%) and "Applesauce" (50%)
    
    # Naive approach: Both pick "Apple".
    # Smart approach: "Apple" gets "Apple". "Apples" must pick next best? Or no match if threshold high?
    
    # Let's try a collision case where 2nd best is viable.
    # T: "Widget A", "Widget B"
    # D: "Widget A", "Widget B_OLD"
    
    # T: "Alpha", "Alpha Beta"
    # D: "Alpha", "Beta"
    
    # Alpha -> Alpha (100)
    # Alpha Beta -> Alpha (90), Beta (90)
    
    target_items = ["Item One", "Item One Two"]
    candidate_items = ["Item One", "Item Two"]
    
    # "Item One" -> "Item One" (100)
    # "Item One Two" -> "Item One" (90), "Item Two" (90)
    
    merged = get_smart_unique_matches(target_items, candidate_items)
    print(f"Assignments: {merged}")
    
    # Expect:
    # Item One -> Item One
    # Item One Two -> Item Two (because Item One is taken)
    
    assert merged["Item One"][0] == "Item One"
    assert merged["Item One Two"][0] == "Item Two"
    
    print("[PASS] Unique assignment logic works.")

if __name__ == "__main__":
    test_smart_defaults()
