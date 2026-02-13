import pandas as pd
from utils import calculate_gap_analysis

def test_tb_exclusion():
    print("Testing T&B Exclusion Logic...")
    
    # Data
    # Row 1: Normal (100 vs 90)
    # Row 2: T&B (Target="T&B", Achieved=50) -> Expect Remaining="T&B"
    
    t_data = {
        'Item': ['Normal', 'TB_Row'],
        'Value': [100, 'T&B']
    }
    a_data = {
        'Item': ['Normal', 'TB_Row'],
        'Count': [90, 50]
    }
    
    df_t = pd.DataFrame(t_data)
    df_a = pd.DataFrame(a_data)
    
    t_tables = {'Test': df_t}
    a_tables = {'Test_Dash': df_a}
    t_map = {'Test': 'Test_Dash'}
    c_map = {'Value': 'Count'}
    
    results = calculate_gap_analysis(t_tables, a_tables, t_map, c_map)
    res = results[0]
    
    print("\nResult:")
    print(res[['Row Label', 'Value (Target)', 'Value (Remaining)']])
    
    # Check Normal
    row_norm = res[res['Row Label'] == 'Normal'].iloc[0]
    assert row_norm['Value (Remaining)'] == 10
    print("[PASS] Normal row calculated correctly.")
    
    # Check T&B
    row_tb = res[res['Row Label'] == 'TB_Row'].iloc[0]
    rem_val = row_tb['Value (Remaining)']
    ach_val = row_tb['Value (Achieved)']
    print(f"T&B Row Remaining: {rem_val} (Expected {ach_val})")
    
    assert rem_val == ach_val
    print("[PASS] T&B row preserved Achieved Value in Remaining column.")
    
    # Generate Report to check tab existence
    from utils import generate_gap_report
    rep = generate_gap_report([res], t_tables, a_tables, t_map, c_map)
    with open("verify_summary_tab.xlsx", "wb") as f:
        f.write(rep)
        
    xl = pd.ExcelFile("verify_summary_tab.xlsx")
    assert "Gap Summary" in xl.sheet_names
    print("[PASS] Gap Summary tab exists.")

if __name__ == "__main__":
    test_tb_exclusion()
