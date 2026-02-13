import pandas as pd
import numpy as np
from thefuzz import process, fuzz
import re

def load_data(file, parse_mode='standard'):
    """
    Load data from an uploaded file.
    Args:
        file: The file object.
        parse_mode: 'standard' or 'dashboard'. 
                    'dashboard' enables skipping specific rows (TOTAL/COUNT) and 
                    aligns headers based on specific offset rules.
    Returns: A dictionary of {Table Name: DataFrame}.
    """
    try:
        raw_df = None
        # Handle cases where file is BytesIO (from API) and has no .name
        filename = getattr(file, 'name', 'api_result.xlsx').lower()

        if filename.endswith('.csv'):
            encodings = ['utf-8', 'cp1252', 'latin1']
            col_names = range(100)
            for encoding in encodings:
                try:
                    file.seek(0)
                    raw_df = pd.read_csv(file, encoding=encoding, header=None, names=col_names, on_bad_lines='skip', skip_blank_lines=False)
                    break
                except:
                    continue
            if raw_df is None:
                file.seek(0)
                raw_df = pd.read_csv(file, encoding='latin1', header=None, names=col_names, on_bad_lines='skip', skip_blank_lines=False)
        else:
             try:
                file.seek(0)
                raw_df = pd.read_excel(file, header=None)
             except:
                try:
                    file.seek(0)
                    raw_df = pd.read_excel(file, engine='calamine', header=None)
                except Exception as ex:
                    # If Excel fails, maybe it IS a CSV after all? (Fallback)
                    try:
                        file.seek(0)
                        raw_df = pd.read_csv(file, header=None, names=range(100), on_bad_lines='skip')
                    except:
                        raise ex
    
    except Exception as e:
        raise ValueError(f"Could not read file: {e}")


    if raw_df is None or raw_df.empty:
        return {}

    tables = {}
    current_block_rows = []
    
    for _, row in raw_df.iterrows():
        # Check if empty
        if row.dropna().empty or all(str(x).strip() == "" for x in row if pd.notna(x)):
            if current_block_rows:
                _process_block(current_block_rows, tables, parse_mode)
                current_block_rows = []
        else:
            current_block_rows.append(row.values)
    
    if current_block_rows:
        _process_block(current_block_rows, tables, parse_mode)
        
    return tables

def _process_block(rows, tables, parse_mode='standard'):
    if not rows:
        return
    
    # 1. Table Name (Always first row, first cell)
    header_row = rows[0]
    table_name = str(header_row[0]).strip()
    if not table_name or table_name.lower() == 'nan':
         table_name = f"Table_{len(tables)+1}"

    # 2. Determine Column Headers and Data Start
    # Standard: Row 1 is headers (merged with Table Name row? No, usually Table Name is own row).
    # Actually, previous implementation assumed Row 0 contained Table Name AND Col Headers.
    # User says for Dashboard: "header is A4 [Name], but cols are B5...".
    # So for Dashboard:
    #   Row 0: Table Name
    #   Row 1: Column Headers
    #   Row 2+: Check for 'TOTAL'/'COUNT' to skip.
    
    columns = []
    data_rows = []
    
    if parse_mode == 'dashboard':
        # Dashboard Logic
        if len(rows) > 1:
            # Row 1 has headers
            col_row = rows[1]
            # Headers are often starting from Col B? User said "cols are B5,C5...".
            # The regex/logic should be: take the row, treat as headers. 
            # If Col A is empty or matches Table Name, ignore?
            # Let's just take the whole row as headers for simplicity, handling "Unnamed".
            for i, x in enumerate(col_row):
                val = str(x).strip() if pd.notna(x) else f"Unnamed_{i}"
                columns.append(val)
            
            # Data starts after Row 1, but we must skip "COUNT"/"TOTAL" rows
            for r in rows[2:]:
                # Check for "TOTAL" in first cell or "COUNT" in row
                row_str = " ".join([str(x).upper() for x in r])
                first_cell = str(r[0]).strip().upper()
                
                if "TOTAL" in first_cell or "COUNT" in row_str:
                    continue
                
                data_rows.append(r)
        else:
            # Just one row? weird table.
            columns = [f"Col_{i}" for i in range(len(header_row))]
            
    else:
        # Standard Logic (Target file)
        # Assume Row 0 has "Table Name" in Col A, and "Col Header 1" in Col B?
        # Or Row 0 is Name, Row 1 is Headers?
        # Previous implementation: Row 0 is headers.
        # Let's stick to: Row 0 is headers for Standard, unless we want to support Name row.
        # User said "col headers can be found on the same line of the table header [for Target?]".
        # "in 1 sheet, the col headers will be consistent...".
        # Let's assume Standard = Row 0 is headers (and Col A is Name/Key info).
        
        # Actually, for the "Target" file, if it has multiple tables, it likely has "Table Name" rows too?
        # Let's try to detect.
        # If Row 0 has "Table Name" in A, and B is empty? Then Row 1 is headers.
        # If Row 0 has "Table Name" in A, and "Sales" in B? Then Row 0 is headers.
        
        # Let's use the Dashboard logic of Row 0=Name, Row 1=Headers IF Row 0 seems to be a title (mostly empty).
        is_title_row = False
        non_empty_cells = sum(1 for x in header_row if pd.notna(x) and str(x).strip() != "")
        if non_empty_cells == 1:
            is_title_row = True
            
        if is_title_row and len(rows) > 1:
            # Row 0 is Title. Row 1 is Headers.
            # Update generic logic to match valid table structure
            col_row = rows[1]
            data_rows = rows[2:]
            for i, x in enumerate(col_row):
                val = str(x).strip() if pd.notna(x) else f"Unnamed_{i}"
                columns.append(val)
        else:
            # Row 0 is Headers
            for i, x in enumerate(header_row):
                val = str(x).strip() if pd.notna(x) else f"Unnamed_{i}"
                columns.append(val)
            data_rows = rows[1:]

    # Create DF
    if data_rows:
        df = pd.DataFrame(data_rows, columns=columns)
    else:
        df = pd.DataFrame(columns=columns)

    # 3. Add to tables
    if table_name in tables:
        count = 1
        while f"{table_name}_{count}" in tables:
            count += 1
        table_name = f"{table_name}_{count}"
        
    tables[table_name] = df


def get_fuzzy_suggestions(target_cols, candidate_cols):
    """
    For each column in target_cols, find the best match in candidate_cols.
    Returns a dict: {target_col: (best_match_col, score)}
    """
    suggestions = {}
    for col in target_cols:
        # process.extractOne returns (match, score)
        # We assume columns are strings
        match, score = process.extractOne(col, candidate_cols)
        suggestions[col] = (match, score)
    return suggestions

    return suggestions

def _calculate_weighted_score(s1, s2):
    """
    Custom scorer that heavily prioritizes the 'Prefix Key'.
    e.g. "Cell 1..." vs "Cell 2..." should differ significantly.
    """
    s1_clean = str(s1).strip()
    s2_clean = str(s2).strip()
    
    # Base score
    base_score = fuzz.token_sort_ratio(s1_clean, s2_clean)
    
    # Extract "Prefix Key" (First 2 tokens usually capture "Cell 1", "Item A")
    # precise logic: 
    # 1. Split by non-alphanumeric (space, colon, etc)
    # 2. Compare first token. If equal, compare second.
    import re
    tokens1 = [t for t in re.split(r'[^a-zA-Z0-9]', s1_clean) if t]
    tokens2 = [t for t in re.split(r'[^a-zA-Z0-9]', s2_clean) if t]
    
    if not tokens1 or not tokens2:
        return base_score
        
    # Check 1st Token (Major Group, e.g. "Cell", "Brand")
    if tokens1[0].lower() != tokens2[0].lower():
        # Major mismatch (e.g. "Brand" vs "Cell")
        # Keep base score (might be low anyway)
        return base_score
    
    # Check 2nd Token (ID, e.g. "1", "2", "A", "B")
    # Only if both have a 2nd token
    if len(tokens1) > 1 and len(tokens2) > 1:
        t1_second = tokens1[1].lower()
        t2_second = tokens2[1].lower()
        
        if t1_second == t2_second:
            # "Cell 1" vs "Cell 1" -> Massive Boost
            return min(100, base_score + 40)
        else:
            # "Cell 1" vs "Cell 2" -> Massive Penalty
            # This is the critical fix for the user
            return max(0, base_score - 50)
            
    return base_score

def get_smart_unique_matches(target_items, candidate_items, threshold=60):
    """
    Greedily assign best unique matches using Prefix Bias.
    Returns dict: {target_item: (best_match_item, score)}
    """
    # 1. Calculate all possible scores
    all_matches = []
    for t in target_items:
        # Custom loop through ALL candidates to ensure our custom scorer is the only judge
        # process.extract is too limiting if the base score is low
        for c in candidate_items:
            # Optimize: Skip if lengths are wild diff? No, stick to robust.
            score = _calculate_weighted_score(t, c)
            if score >= threshold:
                all_matches.append((score, t, c))
                
    # 2. Sort by score descending
    all_matches.sort(key=lambda x: x[0], reverse=True)
    
    # 3. Greedy assignment
    assignments = {} # target -> (candidate, score, alternatives)
    used_candidates = set()
    assigned_targets = set()
    
    # Store all scores per target for the UI to show alternatives
    scores_per_target = {}
    for score, t, c in all_matches:
        if t not in scores_per_target:
            scores_per_target[t] = []
        scores_per_target[t].append((c, score))

    for score, t, c in all_matches:
        if t not in assigned_targets and c not in used_candidates:
            # Found best unique match
            # Get alternatives (remaining candidates for this target)
            alts = [x for x in scores_per_target.get(t, []) if x[0] != c and x[0] not in used_candidates]
            assignments[t] = (c, score, alts)
            assigned_targets.add(t)
            used_candidates.add(c)
            
    return assignments


def calculate_gap_analysis(target_tables, achieved_tables, 
                           table_mapping, column_mapping, row_mapping=None):
    """
    Perform gap analysis across multiple tables.
    
    Args:
        target_tables: Dict {Table Name: DF}
        achieved_tables: Dict {Table Name: DF}
        table_mapping: Dict {Target Table Name: Achieved Table Name}
        column_mapping: Dict {Target Col Name: Achieved Col Name} (Global mapping)
        row_mapping: Dict {Target Table Name: {Target Row Label: Achieved Row Label}}
    """
    all_results = []
    if row_mapping is None:
        row_mapping = {}
    
    for t_name, a_name in table_mapping.items():
        if not a_name or t_name not in target_tables or a_name not in achieved_tables:
            continue
            
        df_t = target_tables[t_name].copy()
        df_a = achieved_tables[a_name].copy()
        
        # Determine Keys (Col A)
        if df_t.empty or df_a.empty:
            continue

        key_col_t = df_t.columns[0]
        key_col_a = df_a.columns[0] 
        
        # Ensure keys are string
        df_t[key_col_t] = df_t[key_col_t].astype(str).str.strip()
        df_a[key_col_a] = df_a[key_col_a].astype(str).str.strip()
        
        # Apply Row Mapping (Rename Dashboard Keys to match Target)
        # This effectively "Aligns" them before merge
        if t_name in row_mapping:
            specific_map = row_mapping[t_name] # {TargetKey: DashKey}
            # We want to replace DashKey with TargetKey in df_a
            # Invert: {DashKey: TargetKey}
            # Note: DashKey must be unique in this map for this to work perfectly. 
            # User constraint "dropdowns unique" ensures this.
            
            # Create replacement dict
            # We only want to replace the specific rows being mapped.
            replace_dict = {v: k for k, v in specific_map.items()}
            
            # Apply replacement to Key Column
            df_a[key_col_a] = df_a[key_col_a].replace(replace_dict)
        
        # Merge - Preserve Target Order
        # Add a temporary index to Target to restore its order after outer merge
        df_t['_target_order'] = range(len(df_t))
        
        merged = pd.merge(df_t, df_a, left_on=key_col_t, right_on=key_col_a, how='outer', suffixes=('_T', '_A'))
        
        # Sort back to Target order. New rows from Dashboard (not in Target) will go to the end.
        merged = merged.sort_values(by='_target_order').drop(columns=['_target_order']).reset_index(drop=True)
        
        # Row Label
        merged['Row Label'] = merged[key_col_t].combine_first(merged[key_col_a])
        
        # Add metadata
        merged['Table Pair'] = f"{t_name} vs {a_name}"
        
        # Calculations
        cols_to_keep = ['Table Pair', 'Row Label']
        
        for t_col, a_col in column_mapping.items():
            # Check availability in this specific table
            if t_col not in df_t.columns:
                continue 
            
            real_t = t_col
            if t_col in df_a.columns:
                 real_t = f"{t_col}_T"
            
            real_a = a_col
            if a_col in df_t.columns:
                 real_a = f"{a_col}_A"
                 
            # Extract data
            remaining_series = []
            target_series = []
            
            # Iterate rows
            for idx, row in merged.iterrows():
                r_t = row.get(real_t, 0)
                # Check for T&B
                if str(r_t).strip().upper() in ["T&B", "TB", "TRACK & BALANCE"]:
                    val_t = "T&B"
                    val_a = pd.to_numeric(row.get(real_a, 0), errors='coerce')
                    if pd.isna(val_a): val_a = 0
                    
                    remaining = val_a 
                else:
                    # Numeric calc
                    val_t = pd.to_numeric(r_t, errors='coerce')
                    if pd.isna(val_t): val_t = 0
                    
                    val_a = row.get(real_a, 0)
                    val_a = pd.to_numeric(val_a, errors='coerce')
                    if pd.isna(val_a): val_a = 0
                    
                    remaining = val_t - val_a
                
                target_series.append(val_t)
                remaining_series.append(remaining)
            
            # Update DataFrame
            merged[f"{t_col} (Target)"] = target_series
            merged[f"{t_col} (Achieved)"] = pd.to_numeric(merged.get(real_a, 0), errors='coerce').fillna(0)
            merged[f"{t_col} (Remaining)"] = remaining_series
            
            cols_to_keep.extend([f"{t_col} (Target)", f"{t_col} (Achieved)", f"{t_col} (Remaining)"])
            
        # Append relevant slice
        if len(cols_to_keep) > 2: # Only if we actually found columns
            all_results.append(merged[cols_to_keep].copy())
        
    return all_results

def generate_gap_report(df_results, target_tables, achieved_tables, table_mapping, column_mapping, row_mapping=None):
    """
    Generate styled Excel report with multiple tabs:
    1. Gap Analysis ( Consolidated Results )
    2. Mapping Keys ( Config )
    3. Source - Target ( Raw Data )
    4. Source - Dashboard ( Raw Data )
    """
    if row_mapping is None:
        row_mapping = {}
        
    from io import BytesIO
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # --- 1. Gap Analysis ---
        sheet_name = 'Gap Analysis'
        workbook.add_worksheet(sheet_name)
        worksheet = writer.sheets[sheet_name]
        
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        neg_fmt = workbook.add_format({'font_color': '#9C0006', 'bg_color': '#FFC7CE'})
        tb_fmt = workbook.add_format({'italic': True, 'font_color': '#808080'})
        
        start_row = 0
        for df in df_results:
            df.to_excel(writer, sheet_name=sheet_name, startrow=start_row, index=False)
            
            # Header formatting
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(start_row, col_num, value, header_fmt)
                worksheet.set_column(col_num, col_num, 20)
                
                # Conditional formatting for Remaining negatives
                if "(Remaining)" in str(value):
                     worksheet.conditional_format(start_row+1, col_num, start_row+len(df), col_num, {
                        'type': 'cell', 'criteria': '<', 'value': 0, 'format': neg_fmt
                     })

            # Check for T&B rows for styling
            t_cols = [c for c in df.columns if "(Target)" in c]
            for r_pos, (idx, row) in enumerate(df.iterrows()):
                for t_col in t_cols:
                    if str(row[t_col]) == "T&B":
                        base_col = t_col.replace(" (Target)", "")
                        rem_col_name = f"{base_col} (Remaining)"
                        
                        if rem_col_name in df.columns:
                            c_idx = df.columns.get_loc(rem_col_name)
                            # Write formatted value to correct Excel row using r_pos
                            val_to_write = row[rem_col_name]
                            worksheet.write(start_row + 1 + r_pos, c_idx, val_to_write, tb_fmt)

            start_row += len(df) + 3

        # --- 2. Gap Summary ---
        sheet_name_sum = 'Gap Summary'
        workbook.add_worksheet(sheet_name_sum)
        ws_sum = writer.sheets[sheet_name_sum]
        
        sum_row = 0
        for df in df_results:
            # Table Pair Header
            pair_name = df['Table Pair'].iloc[0]
            ws_sum.merge_range(sum_row, 0, sum_row, 1, pair_name, header_fmt)
            sum_row += 1
            
            # Columns: Row Label + Remaining
            cols_rem = [c for c in df.columns if "(Remaining)" in c]
            
            # Detect if this table has T&B rows
            # We look at any (Target) column in this df
            t_cols = [c for c in df.columns if "(Target)" in c]
            is_tb_table = False
            for tc in t_cols:
                if "T&B" in df[tc].astype(str).values:
                    is_tb_table = True
                    break
            
            header_text = "track & balance - currently achieved values" if is_tb_table else ""
            clean_headers = [header_text] + [c.replace(" (Remaining)", "") for c in cols_rem]
            
            # Write Headers
            for i, h in enumerate(clean_headers):
                ws_sum.write(sum_row, i, h, header_fmt)
                ws_sum.set_column(i, i, 20)
            sum_row += 1

            
            # Write Data - Use enumeration (r_pos) for Excel positioning
            for r_pos, (idx, row) in enumerate(df.iterrows()):
                ws_sum.write(sum_row + r_pos, 0, row['Row Label'])
                
                for c_idx, col_name in enumerate(cols_rem):
                    val = row[col_name]
                    target_col_name = col_name.replace("(Remaining)", "(Target)")
                    is_tb = str(row[target_col_name]) == "T&B"
                    
                    cell_fmt = None
                    if is_tb:
                        cell_fmt = tb_fmt
                    elif isinstance(val, (int, float)) and val < 0:
                        cell_fmt = neg_fmt
                        
                    ws_sum.write(sum_row + r_pos, c_idx + 1, val, cell_fmt)
            
            sum_row += len(df) + 2

            
            
        # --- 3. Mapping Keys ---
        # Create a dataframe for Table Mapping
        t_map_df = pd.DataFrame(list(table_mapping.items()), columns=['Target Table', 'Dashboard Table'])
        # Create a dataframe for Column Mapping
        c_map_df = pd.DataFrame(list(column_mapping.items()), columns=['Target Column', 'Dashboard Column'])
        
        t_map_df.to_excel(writer, sheet_name='Mapping Keys', startrow=0, startcol=0, index=False)
        c_map_df.to_excel(writer, sheet_name='Mapping Keys', startrow=0, startcol=4, index=False) # Offset
        
        mk_sheet = writer.sheets['Mapping Keys']
        mk_sheet.write(0, 0, 'Target Table', header_fmt)
        mk_sheet.write(0, 1, 'Dashboard Table', header_fmt)
        mk_sheet.write(0, 4, 'Target Column', header_fmt)
        mk_sheet.write(0, 5, 'Dashboard Column', header_fmt)
        mk_sheet.set_column(0, 1, 25)
        mk_sheet.set_column(4, 5, 25)

        # New: Row Mappings (Matched Rows)
        row_mk_start = 0
        mk_sheet.write(0, 8, 'Matched Rows (Target -> Dashboard)', header_fmt)
        mk_sheet.set_column(8, 9, 30)
        row_mk_row = 1
        
        for t_table, r_map in row_mapping.items():
            if r_map:
                mk_sheet.write(row_mk_row, 8, f"Table: {t_table}", workbook.add_format({'bold': True, 'italic': True}))
                row_mk_row += 1
                for t_row, a_row in r_map.items():
                    mk_sheet.write(row_mk_row, 8, t_row)
                    mk_sheet.write(row_mk_row, 9, a_row)
                    row_mk_row += 1
                row_mk_row += 1 # Spacer

        # --- 3. Source - Target ---
        st_row = 0
        workbook.add_worksheet('Source - Target')
        st_sheet = writer.sheets['Source - Target']
        for name, df in target_tables.items():
            st_sheet.write(st_row, 0, f"Table: {name}", header_fmt)
            df.to_excel(writer, sheet_name='Source - Target', startrow=st_row+1, index=False)
            st_row += len(df) + 4
            
        # --- 4. Source - Dashboard ---
        sd_row = 0
        workbook.add_worksheet('Source - Dashboard')
        sd_sheet = writer.sheets['Source - Dashboard']
        for name, df in achieved_tables.items():
            sd_sheet.write(sd_row, 0, f"Table: {name}", header_fmt)
            df.to_excel(writer, sheet_name='Source - Dashboard', startrow=sd_row+1, index=False)
            sd_row += len(df) + 4
                
    return output.getvalue()
