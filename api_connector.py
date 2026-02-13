import requests
import pandas as pd
import io

def fetch_decipher_data(api_key, server, project_path):
    """
    Fetches survey data from the Forsta/Decipher API.
    
    Args:
        api_key (str): The API Key for authentication.
        server (str): The server hostname (e.g. 'emea.focusvision.com').
        project_path (str): The project path (e.g. 'selfserve/2e95/ge320').
        
    Returns:
        (file_obj, error_msg): Returns a file-like object containing the data if successful,
                               or an error message string if failed.
    """
    if not api_key or not server or not project_path:
        return None, "Missing API Key, Server, or Project Path."

    # Construct URL
    # Documentation varies, but typically: https://{server}/API/v1/surveys/{project}/data?format=xlsx
    # Or strict path: https://{server}/API/v1/surveys/{project_path}/data
    
    # Clean inputs
    server = server.replace("https://", "").replace("http://", "").strip("/")
    project_path = project_path.strip("/")
    
    url = f"https://{server}/API/v1/surveys/{project_path}/data"
    
    headers = {
        "x-apikey": api_key,
        "Content-Type": "application/json"
    }
    
    params = {
        "format": "xlsx",  # Request Excel format
        "layout": "flat"   # Optional: 'flat' or 'stacked', defaults usually fine
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, stream=True)
        
        if response.status_code == 200:
            # Check content type if possible, or just try to load it
            return io.BytesIO(response.content), None
        elif response.status_code == 401:
            return None, "Unauthorized: Invalid API Key."
        elif response.status_code == 404:
            return None, "Project not found or Invalid URL."
        else:
            return None, f"API Error ({response.status_code}): {response.text}"
            
    except Exception as e:
        return None, f"Connection Error: {str(e)}"
