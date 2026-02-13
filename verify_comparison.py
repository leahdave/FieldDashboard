import pandas as pd
from utils import compare_dataframes, generate_excel_report
import os

def test_comparison():
    print("Loading data...")
    df_ref = pd.read_csv('data/ref.csv')
    df_target = pd.read_csv('data/target.csv')
    
    print("Comparing with key=['id']...")
    result = compare_dataframes(df_ref, df_target, key_columns=['id'])
    
    summary = result['summary']
    print("\nSummary:")
    print(summary)
    
    # Expected results:
    # Ref: 4 rows
    # Target: 4 rows
    # Matching keys: 1, 2, 4 (3 matching)
    # Added keys: 5 (1 added)
    # Removed keys: 3 (1 removed)
    # Modified rows: 1 (Alice)
    
    assert summary['total_ref'] == 4
    assert summary['total_target'] == 4
    assert summary['matching_keys'] == 3
    assert summary['added_keys'] == 1
    assert summary['removed_keys'] == 1
    assert summary['modified_rows'] == 1
    
    print("\n[PASS] Assertion passed: Summary metrics are correct.")
    
    # Check details
    # Alice (id 1) changed
    mod_row = result['details']['modified'].iloc[0]
    assert mod_row['id'] == 1
    # Check if 'role' and 'salary' are in changed columns
    # Note: 'changed_columns' is a list of col names.
    print(f"Alice changes: {mod_row['changed_columns']}")
    assert 'role' in mod_row['changed_columns']
    assert 'salary' in mod_row['changed_columns']
    
    print("[PASS] Assertion passed: Modified row details are correct.")

    # Test report generation
    print("\nGenerating report...")
    report_bytes = generate_excel_report(result)
    with open('comparison_report_test.xlsx', 'wb') as f:
        f.write(report_bytes)
    
    print(f"[PASS] Report generated: comparison_report_test.xlsx ({len(report_bytes)} bytes)")

if __name__ == "__main__":
    try:
        test_comparison()
        print("\nALL TESTS PASSED")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        exit(1)
