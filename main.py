import requests
from datetime import datetime
from typing import List, Dict, Optional, NamedTuple
import json
import os
from dotenv import load_dotenv

class ServerAvailability(NamedTuple):
    plan_name: str
    plan_code: str
    is_available: bool

def get_ovh_availability(plan_codes: Dict[str, str], datacenters: Optional[List[str]] = None) -> Dict[str, List[ServerAvailability]]:
    """
    Get availability information for OVH dedicated servers.
    
    Args:
        plan_codes (Dict[str,str]): Dictionary mapping plan names to plan codes
        datacenters (Optional[List[str]]): List of specific datacenters to check (e.g. ['bhs', 'rbx']). 
                                         If None, returns all datacenters
        
    Returns:
        Dict[str, List[ServerAvailability]]: Dictionary mapping datacenters to list of server availabilities
    """
    results: Dict[str, List[ServerAvailability]] = {}
    for plan_name, plan_code in plan_codes.items():
        url = f"https://ca.api.ovh.com/v1/dedicated/server/datacenter/availabilities?planCode={plan_code}"
        response = requests.get(url)
        data = response.json()[0]
        availability_list = data['datacenters']
        
        dc_list = datacenters if datacenters else list(availability_list.keys())
        
        for datacenter in dc_list:
            if datacenter not in results:
                results[datacenter] = []
                
            if datacenter in availability_list:
                is_available = availability_list[datacenter]['availability'] != 'unavailable'
            else:
                is_available = False
                
            results[datacenter].append(ServerAvailability(
                plan_name=plan_name,
                plan_code=plan_code,
                is_available=is_available
            ))
            
    return results

def load_previous_status() -> Dict[str, Dict[str, bool]]:
    if not os.path.exists('server_status.json'):
        return {}
    try:
        with open('server_status.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def save_current_status(status: Dict[str, Dict[str, bool]]) -> None:
    data = {
        'last_updated': datetime.now().isoformat(),
        'status': status
    }
    with open('server_status.json', 'w') as f:
        json.dump(data, f)

def send_discord_message(avail: Dict[str, List[ServerAvailability]]) -> None:    
    previous_status = load_previous_status()
    previous_server_status = previous_status.get('status', {})
    current_status: Dict[str, Dict[str, bool]] = {}
    
    for datacenter, servers in avail.items():
        if datacenter not in current_status:
            current_status[datacenter] = {}
            
        for server in servers:
            server_key = f"{server.plan_name}_{server.plan_code}"
            current_status[datacenter][server_key] = server.is_available
            
            # Get previous status, default to None if not found
            prev_available = previous_server_status.get(datacenter, {}).get(server_key)
            
            # Only send notification if status changed
            if prev_available is None or prev_available != server.is_available:
                status_msg = "now available" if server.is_available else "no longer available"
                message: Dict[str, str] = {
                    "content": f"🚨  Server plan {server.plan_name} ({server.plan_code}) is {status_msg} in datacenter {datacenter}!  🚨"
                }
                requests.post(os.getenv('DISCORD_WEBHOOK_URL'), json=message)
    
    # Save current status for next run
    save_current_status(current_status)

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    plan_codes: Dict[str, str] = {
        'KS-A': '24ska01',
    }
    
    avail = get_ovh_availability(plan_codes, datacenters=["bhs"])
    send_discord_message(avail)
