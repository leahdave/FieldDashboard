import json
import os
import pandas as pd
from datetime import datetime

# Simple interface for saving/loading jobs
# Supports local JSON files and Google Sheets via st-gsheets-connection

JOBS_DIR = "jobs"
SHEET_NAME = "Jobs" # Default tab name in Google Sheets

def _get_local_job_path(job_id):
    """Returns the file path for a given local job ID."""
    if not os.path.exists(JOBS_DIR):
        os.makedirs(JOBS_DIR)
    safe_id = "".join([c for c in job_id if c.isalnum() or c in ('-', '_')])
    return os.path.join(JOBS_DIR, f"{safe_id}.json")

def save_job(job_id, data, gsheets_conn=None):
    """
    Saves the job data (mappings) to local storage and optional Google Sheets.
    """
    if not job_id:
        return False, "Job ID cannot be empty."
    
    try:
        # 1. Update metadata
        data['last_updated'] = datetime.now().isoformat()
        
        # 2. Save locally (Always do this as a backup/cache)
        local_path = _get_local_job_path(job_id)
        with open(local_path, 'w') as f:
            json.dump(data, f, indent=4)
            
        # 3. Save to Google Sheets if connection provided
        if gsheets_conn:
            try:
                # Read existing jobs from sheet
                df = gsheets_conn.read(worksheet=SHEET_NAME, ttl=0)
                if df is None or df.empty:
                    df = pd.DataFrame(columns=['job_id', 'config_json', 'last_updated'])
                
                # Update or Append
                config_str = json.dumps(data)
                new_row = {'job_id': job_id, 'config_json': config_str, 'last_updated': data['last_updated']}
                
                if job_id in df['job_id'].values:
                    df.loc[df['job_id'] == job_id, ['config_json', 'last_updated']] = [config_str, data['last_updated']]
                else:
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                
                gsheets_conn.update(worksheet=SHEET_NAME, data=df)
            except Exception as ge:
                return True, f"Job '{job_id}' saved locally, but Google Sheets error: {str(ge)}"

        return True, f"Job '{job_id}' saved successfully."
    except Exception as e:
        return False, f"Error saving job: {str(e)}"

def load_job(job_id, gsheets_conn=None):
    """
    Loads the job data. Checks local storage first, then Google Sheets if missing.
    """
    if not job_id:
        return None, "Job ID cannot be empty."
        
    # 1. Try local cache first
    local_path = _get_local_job_path(job_id)
    if os.path.exists(local_path):
        try:
            with open(local_path, 'r') as f:
                return json.load(f), None
        except:
            pass # Fall through to Sheets if local fails
            
    # 2. Try Google Sheets if missing locally
    if gsheets_conn:
        try:
            df = gsheets_conn.read(worksheet=SHEET_NAME, ttl=0)
            if df is not None and not df.empty and job_id in df['job_id'].values:
                config_str = df.loc[df['job_id'] == job_id, 'config_json'].values[0]
                data = json.loads(config_str)
                # Cache it locally for next time
                save_job(job_id, data) 
                return data, None
        except Exception as e:
            return None, f"Error loading from Google Sheets: {str(e)}"
            
    return None, f"Job '{job_id}' not found locally or in cloud."

def list_jobs(gsheets_conn=None):
    """Lists all available job IDs from both local and Google Sheets."""
    jobs = set()
    
    # 1. Local jobs
    if os.path.exists(JOBS_DIR):
        for filename in os.listdir(JOBS_DIR):
            if filename.endswith(".json"):
                jobs.add(filename[:-5])
    
    # 2. Cloud jobs
    if gsheets_conn:
        try:
            df = gsheets_conn.read(worksheet=SHEET_NAME, ttl=0)
            if df is not None and not df.empty and 'job_id' in df.columns:
                for j_id in df['job_id'].tolist():
                    jobs.add(str(j_id))
        except:
            pass
            
    return sorted(list(jobs))
