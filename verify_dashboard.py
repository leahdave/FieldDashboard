import pandas as pd
from utils import load_data, _process_block
import os

def test_dashboard_parsing():
    print("Testing Dashboard Parsing (Complex)...")
    
    # Simulated structure in data/dashboard_complex.csv:
    # Sales Table (Row 0)
    # Item, Revenue, Units (Row 1)
    # TOTAL, 1000, 500, COUNT (Row 2 - Should be skipped)
    # Widget A, 100, 50 (Row 3 - Data)
    
    tables = load_data(open('data/dashboard_complex.csv', 'rb'), parse_mode='dashboard')
    
    print(f"Tables found: {list(tables.keys())}")
    
    assert "Sales Table" in tables
    df_sales = tables["Sales Table"]
    
    print(f"Sales Table:\n{df_sales}")
    
    # Logic check:
    # Header should be detected as Row 1 (Item, Revenue, Units)
    assert "Revenue" in df_sales.columns
    assert "Units" in df_sales.columns
    
    # Data should NOT contain TOTAL row
    # If TOTAL row was kept, one row's item would be "TOTAL"
    assert "TOTAL" not in df_sales['Item'].values
    
    # Data should contain Widget A
    assert "Widget A" in df_sales['Item'].values
    
    print("[PASS] Dashboard parsing correctly skipped TOTAL/COUNT row.")
    
    # Check standard parsing on same file just to see diff (optional)
    # tables_std = load_data(open('data/dashboard_complex.csv', 'rb'), parse_mode='standard')
    # print(f"Standard Parse Sales:\n{tables_std['Sales Table'].head()}")

if __name__ == "__main__":
    try:
        test_dashboard_parsing()
        print("\nALL DASHBOARD TESTS PASSED")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        exit(1)
