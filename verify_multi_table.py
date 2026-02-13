import pandas as pd
from utils import load_data
import os

def test_multi_table():
    print("Testing Multi-Table Parsing...")
    # csv simulates the structure:
    # North Region, Goal (Header)
    # Item A, 100
    # Item B, 200
    # (Blank)
    # South Region, Goal (Header)
    
    # NOTE: pd.read_csv might skip blank lines by default if not careful, 
    # but load_data uses specific logic or reads as raw file in memory?
    # Our load_data for CSV uses pd.read_csv. pd.read_csv(skip_blank_lines=True) is default.
    # We need to ensure we read blanks.
    # Ah, in load_data implementation for CSV, I used pd.read_csv without skip_blank_lines=False.
    # Let's verify if my implementation actually catches the blank line or merges them.
    # If it merges them, we get one big table, which is wrong.
    
    tables = load_data(open('data/multi_table.csv', 'rb'))
    
    print(f"Tables found: {list(tables.keys())}")
    
    # Expected: "North Region" and "South Region"
    assert "North Region" in tables
    assert "South Region" in tables
    
    # Check Content
    df_north = tables["North Region"]
    print(f"North Table:\n{df_north}")
    assert len(df_north) == 2 # Item A, Item B
    assert "Goal" in df_north.columns
    
    print("[PASS] Multi-table parsing successful.")

if __name__ == "__main__":
    try:
        test_multi_table()
        print("\nALL TABLE TESTS PASSED")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        exit(1)
