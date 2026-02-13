from storage import save_job, load_job, list_jobs
import os

def test_storage():
    print("Testing Storage Module...")
    
    job_id = "TEST-JOB-001"
    data = {
        "table_mapping": {"A": "B"},
        "col_mapping": {"Col1": "Col2"},
        "row_mapping": {"Row1": "Row2"}
    }
    
    # 1. Test Save
    print(f"Saving job '{job_id}'...")
    success, msg = save_job(job_id, data)
    if success:
        print("[PASS] Save successful")
    else:
        print(f"[FAIL] Save failed: {msg}")
        
    # 2. Test List
    print("Listing jobs...")
    jobs = list_jobs()
    if job_id in jobs:
        print(f"[PASS] Job '{job_id}' found in list: {jobs}")
    else:
        print(f"[FAIL] Job '{job_id}' NOT found in list: {jobs}")
        
    # 3. Test Load
    print(f"Loading job '{job_id}'...")
    loaded_data, err = load_job(job_id)
    if not err and loaded_data['table_mapping'] == data['table_mapping']:
        print("[PASS] Load successful and data matches")
    else:
        print(f"[FAIL] Load failed or mismatch. Err: {err}, Data: {loaded_data}")

    # Cleanup
    try:
        os.remove(f"jobs/{job_id}.json")
        print("Cleanup successful.")
    except:
        pass

if __name__ == "__main__":
    test_storage()
