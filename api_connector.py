import requests
import io

def parse_forsta_url(url):
    """
    Helper to extract details from a Forsta/Decipher URL.
    Supports dashboard URLs like:
    https://emea.focusvision.com/apps/dashboard/selfserve/2e95/ge320:view/p42hq2c2ex5u
    """
    if not url:
        return {}
    
    url = url.strip()
    server = ""
    project_path = ""
    dashboard_id = ""
    
    # 1. Extract Server
    if "://" in url:
        server = url.split("://")[1].split("/")[0]
    else:
        server = url.split("/")[0]
        
    # 2. Extract Project Path and Dashboard ID
    if "/selfserve/" in url:
        # Standard Dashboard/Report Hub URL
        part = url.split("/selfserve/")[1]
        # part is e.g. "2e95/ge320:view/p42hq2c2ex5u" or "2e95/ge320/..."
        
        if ":view/" in part:
            project_path_part, dash_part = part.split(":view/")
            project_path = "selfserve/" + project_path_part.strip("/")
            dashboard_id = dash_part.split("/")[0] # Get first part before any queries
        else:
            # Fallback parsing
            segments = part.split("/")
            if len(segments) >= 2:
                # project_path is selfserve/2e95/ge320
                project_path = "selfserve/" + segments[0] + "/" + segments[1].split(":")[0]
                if len(segments) >= 3:
                     # Attempt to find if dashboard_id is buried in path
                     dashboard_id = segments[-1].split("?")[0]
    
    return {
        "server": server,
        "project_path": project_path,
        "dashboard_id": dashboard_id
    }

def fetch_forsta_dashboard_data(api_key, server, project_path, dashboard_id):
    """
    Fetches data from a specific Report Hub (Dashboard) view.
    API: GET /api/v1/rh/dashboards/{project_path}/{view_id}/export?format=xlsx
    """
    if not api_key or not server or not project_path or not dashboard_id:
        return None, "Missing API Key, Server, Project Path, or Dashboard ID."

    server = server.replace("https://", "").replace("http://", "").strip("/")
    project_path = project_path.strip("/")
    dashboard_id = dashboard_id.strip("/")
    
    # Endpoint for Report Hub export
    url = f"https://{server}/api/v1/rh/dashboards/{project_path}/{dashboard_id}/export"
    
    headers = {
        "x-apikey": api_key,
        "Content-Type": "application/json"
    }
    
    params = {
        "format": "xlsx"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, stream=True)
        
        if response.status_code == 200:
            return io.BytesIO(response.content), None
        elif response.status_code == 401:
            return None, "Unauthorized: Invalid API Key."
        elif response.status_code == 404:
            return None, "Dashboard not found. Check Project Path and Dashboard ID."
        else:
            return None, f"API Error ({response.status_code}): {response.text}"
            
    except Exception as e:
        return None, f"Connection Error: {str(e)}"

def fetch_decipher_data(api_key, server, project_path):
    """
    Fetches standard survey data from the Forsta/Decipher API.
    """
    if not api_key or not server or not project_path:
        return None, "Missing API Key, Server, or Project Path."

    server = server.replace("https://", "").replace("http://", "").strip("/")
    project_path = project_path.strip("/")
    
    url = f"https://{server}/API/v1/surveys/{project_path}/data"
    
    headers = {
        "x-apikey": api_key,
        "Content-Type": "application/json"
    }
    
    params = {
        "format": "xlsx",
        "layout": "flat"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, stream=True)
        
        if response.status_code == 200:
            return io.BytesIO(response.content), None
        elif response.status_code == 401:
            return None, "Unauthorized: Invalid API Key."
        elif response.status_code == 404:
            return None, "Project not found or Invalid URL."
        else:
            return None, f"API Error ({response.status_code}): {response.text}"
            
    except Exception as e:
        return None, f"Connection Error: {str(e)}"
