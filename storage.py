import json
import os
from datetime import datetime

# Simple interface for saving/loading jobs
# In the future, this can be swapped for a database (e.g. Supabase)

JOBS_DIR = "jobs"

def _get_job_path(job_id):
    """Returns the file path for a given job ID."""
    if not os.path.exists(JOBS_DIR):
        os.makedirs(JOBS_DIR)
    # Sanitize job_id to prevent path traversal
    safe_id = "".join([c for c in job_id if c.isalnum() or c in ('-', '_')])
    return os.path.join(JOBS_DIR, f"{safe_id}.json")

def save_job(job_id, data):
    """
    Saves the job data (mappings) to a JSON file.
    data should be a dictionary containing:
    - table_mapping
    - col_mapping
    - row_mapping
    - internal_state (optional)
    """
    if not job_id:
        return False, "Job ID cannot be empty."
    
    try:
        filepath = _get_job_path(job_id)
        
        # Add metadata
        data['last_updated'] = datetime.now().isoformat()
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
            
        return True, f"Job '{job_id}' saved successfully."
    except Exception as e:
        return False, f"Error saving job: {str(e)}"

def load_job(job_id):
    """
    Loads the job data from a JSON file.
    Returns (data, error_message).
    If successful, error_message is None.
    """
    if not job_id:
        return None, "Job ID cannot be empty."
        
    filepath = _get_job_path(job_id)
    
    if not os.path.exists(filepath):
        return None, f"Job '{job_id}' not found."
        
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data, None
    except Exception as e:
        return None, f"Error loading job: {str(e)}"

def list_jobs():
    """Lists all available job IDs."""
    if not os.path.exists(JOBS_DIR):
        return []
    
    jobs = []
    for filename in os.listdir(JOBS_DIR):
        if filename.endswith(".json"):
            jobs.append(filename[:-5]) # Remove .json
    return jobs
