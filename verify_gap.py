import pandas as pd
from utils import get_fuzzy_suggestions, calculate_gap_analysis, generate_gap_report
import os

def test_gap_analysis():
    print("Testing Multi-Table Gap Analysis...")
    
    # Mock DataFrames
    df_t = pd.DataFrame({
        'Item': ['A', 'B'],
        'Sales': [100, 200]
    })
    df_a = pd.DataFrame({
        'SKU': ['A', 'B'],
        'Revenue': [80, 210]
    })
    
    t_tables = {'North': df_t}
    a_tables = {'North_Dash': df_a}
    
    t_map = {'North': 'North_Dash'}
    c_map = {'Sales': 'Revenue'}
    
    results = calculate_gap_analysis(t_tables, a_tables, t_map, c_map)
    
    assert len(results) == 1
    res = results[0]
    
    print(res.head())
    
    # Check Item A: 100 - 80 = 20
    row_a = res[res['Row Label'] == 'A'].iloc[0]
    assert row_a['Sales (Remaining)'] == 20
    
    # Check Item B: 200 - 210 = -10
    row_b = res[res['Row Label'] == 'B'].iloc[0]
    assert row_b['Sales (Remaining)'] == -10
    
    print("[PASS] Subtraction logic correct.")
    
    print("\nGenerating Report...")
    report_bytes = generate_gap_report(results, t_tables, a_tables, t_map, c_map)
    with open('gap_report_multi_test.xlsx', 'wb') as f:
        f.write(report_bytes)
    print(f"[PASS] Report generated: gap_report_multi_test.xlsx ({len(report_bytes)} bytes)")
    
    # Optional: Check sheets?
    xl = pd.ExcelFile('gap_report_multi_test.xlsx')
    print(f"Sheets found: {xl.sheet_names}")
    assert 'Gap Analysis' in xl.sheet_names
    assert 'Mapping Keys' in xl.sheet_names
    assert 'Source - Target' in xl.sheet_names
    assert 'Source - Dashboard' in xl.sheet_names

if __name__ == "__main__":
    try:
        test_gap_analysis()
        print("\nALL GAP TESTS PASSED")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        exit(1)
