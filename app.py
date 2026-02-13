import streamlit as st
import pandas as pd
from utils import load_data, get_fuzzy_suggestions, get_smart_unique_matches, calculate_gap_analysis, generate_gap_report
from storage import save_job, load_job, list_jobs
from api_connector import fetch_decipher_data

st.set_page_config(page_title="Multi-Table Gap Analysis", layout="wide")

st.title("Gap Analysis & Comparison Tool")
st.markdown("Compare **Target (Goal)** vs **Dashboard (Achieved)** files with multiple tables.")
st.caption("Matches tables by header name, then rows by first column.")

# -- SIDEBAR: JOB MANAGEMENT --
with st.sidebar:
    st.header("Job Management")
    st.info("Save your mappings to reload them later.")
    
    # 1. Select or Create Job ID
    existing_jobs = list_jobs()
    job_mode = st.radio("Mode", ["New Job", "Load Job"], horizontal=True)
    
    if job_mode == "Load Job":
        job_id = st.selectbox("Select Job ID", existing_jobs if existing_jobs else ["No jobs found"])
    else:
        job_id = st.text_input("Enter Job ID (e.g. PROJECT-123)")
    
    # 2. Load Button
    if st.button("Load Job Configuration"):
        if job_mode == "Load Job" and (not job_id or job_id == "No jobs found"):
            st.error("Please select a valid job.")
        elif not job_id:
            st.error("Please enter a Job ID.")
        else:
            data, err = load_job(job_id)
            if err:
                st.error(err)
            else:
                # Restore State
                # We need to populate st.session_state keys matching our widgets
                
                # 1. Table Mappings: key = f"tbl_{t_name}"
                for t_name, val in data.get('table_mapping', {}).items():
                    st.session_state[f"tbl_{t_name}"] = val
                    
                # 2. Col Mappings: key = f"col_{col}"
                for col, val in data.get('col_mapping', {}).items():
                    st.session_state[f"col_{col}"] = val
                    
                # 3. Row Mappings: key = f"row_{t_table}_{uk}"
                # stored as { table: { row_key: val } }
                for t_table, row_map in data.get('row_mapping', {}).items():
                    for uk, val in row_map.items():
                        st.session_state[f"row_{t_table}_{uk}"] = val
                
                st.toast(f"Loaded configuration for '{job_id}'!", icon="✅")
                st.session_state['current_job_id'] = job_id
                
                # Force refresh to populate widgets
                st.rerun()


# -- STEP 1: LOAD FILES --
col1, col2 = st.columns(2)

target_tables = {}
achieved_tables = {}

with col1:
    st.header("1. Target File")
    t_file = st.file_uploader("Upload Target File", type=['xlsx', 'csv'], key='t')
    if t_file:
        try:
            # Target uses standard parsing
            target_tables = load_data(t_file, parse_mode='standard')
            st.success(f"Found {len(target_tables)} tables.")
            with st.expander("View Tables"):
                for name, df in target_tables.items():
                    st.write(f"**{name}** ({df.shape[0]} rows)")
                    st.dataframe(df.head(2))
        except Exception as e:
            st.error(f"Error: {e}")

with col2:
    st.header("2. Dashboard File")
    
    # Check if 'source_type' is in session state (restored from job?) 
    # Actually, we don't save source type in job currently, but we could later.
    source_type = st.radio("Source:", ["Upload File", "Forsta API"], horizontal=True)
    
    if source_type == "Upload File":
        a_file = st.file_uploader("Upload Dashboard File", type=['xlsx', 'csv'], key='a')
        if a_file:
            try:
                # Dashboard uses new complex parsing
                achieved_tables = load_data(a_file, parse_mode='dashboard')
                st.success(f"Found {len(achieved_tables)} tables.")
                with st.expander("View Tables"):
                    for name, df in achieved_tables.items():
                        st.write(f"**{name}** ({df.shape[0]} rows)")
                        st.caption(f"Columns: {list(df.columns)}")
                        st.dataframe(df.head(2))
            except Exception as e:
                st.error(f"Error: {e}")
                
    else: # Forsta API
        st.caption("Connect to Decipher/Forsta Survey Data")
        
        # Inputs
        # Default Server
        api_server = st.text_input("Server", value="emea.focusvision.com")
        # Default Project Path logic: try to parse from input if they paste a whole link? 
        # For now just simple text input
        api_project = st.text_input("Project Path", placeholder="selfserve/2e95/ge320")
        api_key = st.text_input("API Key", type="password")
        
        if st.button("Fetch Data"):
            if not api_key or not api_project:
                st.error("Please provide API Key and Project Path.")
            else:
                with st.spinner("Connecting to Forsta..."):
                    file_obj, err = fetch_decipher_data(api_key, api_server, api_project)
                    
                    if err:
                        st.error(err)
                    else:
                        try:
                            # Load data from the returned file object
                            achieved_tables = load_data(file_obj, parse_mode='dashboard')
                            st.success(f"Successfully fetched! Found {len(achieved_tables)} tables.")
                            
                            with st.expander("View Tables"):
                                for name, df in achieved_tables.items():
                                    st.write(f"**{name}** ({df.shape[0]} rows)")
                                    st.caption(f"Columns: {list(df.columns)}")
                                    st.dataframe(df.head(2))
                                    
                        except Exception as e:
                            st.error(f"Error parsing API data: {e}")


if target_tables and achieved_tables:
    st.divider()
    
    # -- STEP 2: MAP TABLES --
    st.header("3. Map Tables")
    st.info("Match Target tables (Left) to Dashboard tables (Right). Duplicates are NOT allowed.")
    
    table_mapping = {}
    
    # Suggest matches
    t_names = list(target_tables.keys())
    a_names = list(achieved_tables.keys())
    table_suggestions = get_fuzzy_suggestions(t_names, a_names)
    
    # Track selected values for validation
    selected_dashboard_tables = []
    
    for t_name in t_names:
        c1, c2, c3 = st.columns([2, 2, 1]) # Added column for % match
        with c1:
            st.markdown(f"**{t_name}**")
        with c2:
            match, score = table_suggestions.get(t_name, (None, 0))
            opts = ["(Skip)"] + a_names
            idx = 0
            
            # Check if we have a saved value in session state (from Load Job)
            # If so, we trust the key to drive the selection.
            # Only if NOT in session state do we try smart defaults.
            saved_val = st.session_state.get(f"tbl_{t_name}")
            
            if not saved_val and match and score > 60:
                 try:
                    idx = opts.index(match)
                 except:
                    pass
            
            sel = st.selectbox(f"Matches:", opts, index=idx, key=f"tbl_{t_name}", label_visibility="collapsed")
            if sel != "(Skip)":
                table_mapping[t_name] = sel
                selected_dashboard_tables.append(sel)
        
        with c3:
            if sel != "(Skip)" and sel == match:
                color = "green" if score > 80 else "orange"
                st.markdown(f":{color}[{score}%]")
            elif sel != "(Skip)":
                st.markdown(":grey[Manual]")

    # Check for duplicates
    has_duplicates = len(selected_dashboard_tables) != len(set(selected_dashboard_tables))
    if has_duplicates:
        st.error("⛔ Error: You have selected the same Dashboard table more than once. Please ensure each Target table maps to a unique Dashboard table.")
    
    if table_mapping and not has_duplicates:
        st.divider()
        st.header("4. Map Columns")
        st.caption("Define which columns to compare. These settings apply to all mapped tables.")
        
        # Assumption: Consistent schema. Grab columns from the first mapped target table.
        first_t = list(table_mapping.keys())[0]
        first_a = table_mapping[first_t]
        
        # We need validation that dependencies exist
        if first_t in target_tables and first_a in achieved_tables:
            df_t_sample = target_tables[first_t]
            df_a_sample = achieved_tables[first_a]
            
            # cols to map (exclude Key Col 0)
            t_cols = [c for c in df_t_sample.columns if c != df_t_sample.columns[0]]
            a_cols = [c for c in df_a_sample.columns if c != df_a_sample.columns[0]]
            
            # Use Smart Unique Matching for Columns too
            col_smart_defaults = get_smart_unique_matches(t_cols, a_cols)
            col_mapping = {}
            
            for col in t_cols:
                c1, c2, c3 = st.columns([2,2,1])
                with c1:
                    st.write(f"Target: **{col}**")
                with c2:
                    # Top match from smart suggestions
                    match_info = col_smart_defaults.get(col)
                    
                    opts = ["(Skip)"] + a_cols
                    idx = 0
                    
                    saved_val = st.session_state.get(f"col_{col}")

                    # Default selection
                    if not saved_val and match_info:
                        match_val, score, alts = match_info
                        try:
                            idx = opts.index(match_val)
                        except: 
                            pass
                    
                    sel = st.selectbox(f"Matches:", opts, index=idx, key=f"col_{col}", label_visibility="collapsed")
                    if sel != "(Skip)":
                        col_mapping[col] = sel
                with c3:
                    # Show score and alternative if current selection matches the smart suggestion
                    if match_info and sel == match_info[0]:
                        score = match_info[1]
                        alts = match_info[2]
                        st.caption(f"Match {score}%")
                        if alts:
                            st.caption(f":grey[Next best: {alts[0][0]} ({alts[0][1]}%)]")
                    elif match_info:
                        pass

            if col_mapping:
                st.divider()
                st.header("5. Review Rows")
                st.caption("We automatically matched rows that have the exact same ID. Review mismatched rows below.")
                
                row_mapping = {}
                has_row_duplicates = False
                
                # Iterate mapped tables to find mismatches
                for t_table, a_table in table_mapping.items():
                    df_t = target_tables[t_table]
                    df_a = achieved_tables[a_table]
                    
                    # Get Keys (Col A)
                    t_keys = df_t.iloc[:, 0].astype(str).str.strip().unique()
                    a_keys = df_a.iloc[:, 0].astype(str).str.strip().unique()
                    
                    # Find Unmatched Target Keys
                    unmatched_t = [k for k in t_keys if k not in a_keys]
                    
                    if unmatched_t:
                        with st.expander(f"**{t_table}**: {len(unmatched_t)} Unmatched Rows", expanded=True):
                            st.info(f"Target table '{t_table}' has rows not found in Dashboard table '{a_table}'. Map them manually if needed.")
                            
                            table_row_map = {}
                            used_a_keys = []
                            
                            cols = st.columns(2)
                            cols[0].markdown("**Target Row (Unmatched)**")
                            cols[1].markdown("**Map to Dashboard Row**")
                            
                            # Smart Unique Matches
                            smart_defaults = get_smart_unique_matches(unmatched_t, list(a_keys))
                            
                            for uk in unmatched_t:
                                c1, c2 = st.columns(2)
                                c1.write(uk)
                                
                                opts = ["(Unmapped)"] + list(a_keys)
                                
                                # Determine default index
                                idx = 0
                                match_info = smart_defaults.get(uk)
                                
                                saved_val = st.session_state.get(f"row_{t_table}_{uk}")
                                
                                if not saved_val and match_info:
                                    match_val, score, alts = match_info
                                    try:
                                        idx = opts.index(match_val)
                                    except:
                                        pass
                                        
                                sel_row = c2.selectbox(f"Map '{uk}' to:", opts, index=idx, key=f"row_{t_table}_{uk}", label_visibility="collapsed")
                                
                                if sel_row != "(Unmapped)":
                                    table_row_map[uk] = sel_row
                                    used_a_keys.append(sel_row)
                                    
                                # Optional: Show score if using default
                                if idx > 0 and match_info and sel_row == match_info[0]:
                                    c2.caption(f"Best unique match: {match_info[1]}%")
                                    if match_info[2]:
                                        c2.caption(f":grey[Next best: {match_info[2][0][0]} ({match_info[2][0][1]}%)]")
                                    
                            if table_row_map:
                                row_mapping[t_table] = table_row_map
                                
                            # Check local duplicates for this table
                            if len(used_a_keys) != len(set(used_a_keys)):
                                st.error(f"⛔ Error in {t_table}: You mapped multiple Target rows to the same Dashboard row.")
                                has_row_duplicates = True
                
                # -- ACTIONS --
                st.divider()
                ac1, ac2 = st.columns([1, 4])
                
                with ac1:
                    # Save Job Logic
                    if st.button("💾 Save Job Config"):
                        if not job_id or job_id == "No jobs found":
                            st.error("Please enter a valid Job ID in the sidebar to save.")
                        else:
                            job_data = {
                                "table_mapping": table_mapping,
                                "col_mapping": col_mapping,
                                "row_mapping": row_mapping
                            }
                            # Call external storage function
                            success, msg = save_job(job_id, job_data)
                            if success:
                                st.toast(msg, icon="✅")
                                st.success(f"Saved to '{job_id}'")
                            else:
                                st.error(msg)
                
                with ac2:
                    if st.button("Calculate Gap Analysis", type="primary", disabled=has_row_duplicates):
                        if not col_mapping:
                            st.error("Please map at least one column.")
                        else:
                            try:
                                results = calculate_gap_analysis(target_tables, achieved_tables, 
                                                               table_mapping, col_mapping, row_mapping)
                                
                                st.success("Calculation Complete!")
                                
                                # Preview
                                for res_df in results:
                                    st.subheader(res_df['Table Pair'].iloc[0])
                                    st.dataframe(res_df.head(), use_container_width=True)
                                    
                                # Download
                                report_bytes = generate_gap_report(results, target_tables, achieved_tables, 
                                                                 table_mapping, col_mapping, row_mapping)
                                st.download_button("Download Report", report_bytes, "gap_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                                
                            except Exception as e:
                                st.error(f"Error during calculation: {e}")
