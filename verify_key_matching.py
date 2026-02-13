import pandas as pd
from utils import calculate_gap_analysis

def test_row_mapping():
    print("Testing Distinct Row Mapping (Male -> M)...")
    
    # Tables with diff keys
    t_data = {'Gender': ['Male', 'Female'], 'Value': [100, 200]}
    a_data = {'Sex': ['F', 'M'], 'Count': [180, 90]} 
    # Male -> M (90), Female -> F (180)
    
    df_t = pd.DataFrame(t_data)
    df_a = pd.DataFrame(a_data)
    
    t_tables = {'Demographics': df_t}
    a_tables = {'Demographics_Dash': df_a}
    
    t_map = {'Demographics': 'Demographics_Dash'}
    c_map = {'Value': 'Count'} 
    
    # Define Row Mapping
    # {Table: {TargetKey: DashKey}}
    r_map = {
        'Demographics': {
            'Male': 'M',
            'Female': 'F'
        }
    }
    
    results = calculate_gap_analysis(t_tables, a_tables, t_map, c_map, row_mapping=r_map)
    res = results[0]
    
    print("\nResult Table with Mapping:")
    print(res[['Row Label', 'Value (Target)', 'Value (Achieved)', 'Value (Remaining)']])
    
    # Check Male Row
    # Target Male: 100
    # Dashboard 'M' maps to Male: 90
    # Rem: 10
    row_m = res[res['Row Label'] == 'Male'].iloc[0]
    print(f"\nMale Row: T={row_m['Value (Target)']}, A={row_m['Value (Achieved)']}, Rem={row_m['Value (Remaining)']}")
    
    assert row_m['Value (Remaining)'] == 10
    print("[PASS] Row Mapping Male->M successful.")

if __name__ == "__main__":
    test_row_mapping()
