import argparse
import requests
import json
import pandas as pd
from datetime import datetime, timezone
import pytz
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Load tokens
load_dotenv()
GOAL_ACCESS_TOKEN = os.getenv('GOAL_ACCESS_TOKEN')
ACCOUNT_ACCESS_TOKEN = os.getenv('ACCOUNT_ACCESS_TOKEN')
GG_SCRIPT_URL = os.getenv('GG_SCRIPT_URL')

def get_cycle_list() -> List[Dict]:
    """Get list of OKR cycles from API"""
    url = "https://goal.base.vn/extapi/v1/cycle/list"
    data = {'access_token_v2': GOAL_ACCESS_TOKEN}
    try:
        response = requests.post(url, data=data, timeout=30)
        if response.status_code != 200:
            return []
        
        cycles_data = response.json()
        quarterly_cycles = []
        
        for cycle in cycles_data.get('cycles', []):
            if cycle.get('metatype') == 'quarterly':
                try:
                    start_time = datetime.fromtimestamp(float(cycle['start_time']))
                    end_time = datetime.fromtimestamp(float(cycle['end_time']))
                    quarterly_cycles.append({
                        'name': cycle['name'],
                        'path': cycle['path'],
                        'start_time': start_time,
                        'end_time': end_time,
                        'formatted_start_time': start_time.strftime('%d/%m/%Y'),
                        'formatted_end_time': end_time.strftime('%d/%m/%Y')
                    })
                except:
                    continue
        
        return sorted(quarterly_cycles, key=lambda x: x['start_time'], reverse=True)
    except Exception as e:
        print(f"Error fetching cycles: {e}")
        return []

def get_checkins_data(cycle_path: str) -> List[Dict]:
    """Get all checkins for a cycle"""
    url = "https://goal.base.vn/extapi/v1/cycle/checkins"
    all_checkins = []
    
    print(f"Starting to fetch checkins for cycle: {cycle_path}")
    
    max_pages = 50
    for page in range(1, max_pages + 1):
        data = {"access_token_v2": GOAL_ACCESS_TOKEN, "path": cycle_path, "page": page}
        try:
            response = requests.post(url, data=data, timeout=30)
            if response.status_code != 200:
                break
            
            response_data = response.json()
            if isinstance(response_data, list) and len(response_data) > 0:
                response_data = response_data[0]
            
            checkins = response_data.get('checkins', [])
            if not checkins:
                break
            
            all_checkins.extend(checkins)
            print(f"Fetched page {page}, total checkins: {len(all_checkins)}")
                
            if len(checkins) < 10:
                break
        except Exception as e:
            print(f"Error page {page}: {e}")
            break
            
    return all_checkins

def get_user_map() -> Dict[str, str]:
    """Fetch all users and return id->name map"""
    url = "https://account.base.vn/extapi/v1/users"
    data = {'access_token_v2': ACCOUNT_ACCESS_TOKEN}
    user_map = {}
    try:
        response = requests.post(url, data=data, timeout=30)
        if response.status_code == 200:
            json_response = response.json()
            # Handle potential list or dict response structure
            users = []
            if isinstance(json_response, list):
                users = json_response
            elif isinstance(json_response, dict):
                users = json_response.get('users', [])
                
            for u in users:
                u_id = str(u.get('id', ''))
                u_name = u.get('name', '')
                if u_id:
                    user_map[u_id] = u_name
    except Exception as e:
        print(f"Error fetching users: {e}")
    return user_map

def get_krs_only(cycle_path: str) -> List[Dict]:
    """Fetch KRs only (paginated)"""
    krs_url = "https://goal.base.vn/extapi/v1/cycle/krs"
    all_krs = []
    
    print("Fetching KRs...")
    for page in range(1, 20):
        krs_data = {"access_token_v2": GOAL_ACCESS_TOKEN, "path": cycle_path, "page": page}
        res = requests.post(krs_url, data=krs_data, timeout=30)
        if res.status_code != 200: break
        
        kd = res.json()
        if isinstance(kd, list) and kd: kd = kd[0]
        
        krs = kd.get("krs", [])
        if not krs: break
        all_krs.extend(krs)
        if len(krs) < 20: break
    return all_krs

def get_cycle_info(cycle_arg: str = None):
    """Resolve cycle arg to full cycle info (name, path)"""
    cycles = get_cycle_list()
    if not cycles: return None
    
    selected_cycle = None
    if not cycle_arg:
        selected_cycle = cycles[0]
    else:
        lower_arg = cycle_arg.lower().strip()
        try:
             query_date = None
             if '/' in lower_arg:
                parts = lower_arg.split('/')
                if len(parts) == 2: query_date = datetime(int(parts[1]), int(parts[0]), 15)
             elif '-' in lower_arg:
                 parts = lower_arg.split('-')
                 if len(parts) == 2: query_date = datetime(int(parts[0]), int(parts[1]), 15)
             
             if query_date:
                for c in cycles:
                    if c['start_time'] <= query_date <= c['end_time']:
                        selected_cycle = c
                        break
        except: pass
        
        if not selected_cycle:
            for c in cycles:
                if lower_arg in c['name'].lower():
                    selected_cycle = c
                    break
    
    if not selected_cycle: selected_cycle = cycles[0]
    return selected_cycle

def fetch_okr_data(cycle_arg: str = None) -> List[Dict]:
    """Core logic to get simplified checkin data"""
    try:
        print("Starting data fetch...")
        cycle_info = get_cycle_info(cycle_arg)
        if not cycle_info: return [{"error": "No OKR cycles found"}]
        
        cycle_path = cycle_info['path']
        print(f"Resolved cycle: {cycle_info['name']} ({cycle_path})")
        
        # 1. Fetch KRs for ID->Name mapping
        krs = get_krs_only(cycle_path)
        kr_map = {str(k['id']): k.get('name', '') for k in krs}

        # 2. Fetch Users for ID->Name mapping
        user_map = get_user_map()

        # 3. Fetch Checkins
        checkins = get_checkins_data(cycle_path)
        
        full_data = []

        def extract_form_value(form_array, field_name):
            if not form_array or not isinstance(form_array, list):
                return ""
            for item in form_array:
                if item.get('name') == field_name:
                    return item.get('value', item.get('display', ""))
            return ""

        def convert_time(ts):
            if not ts: return ''
            try:
                dt_utc = datetime.fromtimestamp(int(ts), tz=timezone.utc)
                tz_hcm = pytz.timezone('Asia/Ho_Chi_Minh')
                return dt_utc.astimezone(tz_hcm).strftime('%Y-%m-%d %H:%M:%S')
            except:
                return ''

        for c in checkins:
            obj_export = c.get('obj_export', {})
            kr_id = str(obj_export.get('id', ''))
            
            # Lookup KR Name (since checkin is logically on a KR/Objective)
            # If not in map, fallback to obj_export name or empty
            kr_name = kr_map.get(kr_id, obj_export.get('name', ''))
            
            checkin_ts = c.get('since', '')
            c_form = c.get('form', [])
            user_id = str(c.get('user_id', ''))
            
            row = {
                'checkin_id': str(c.get('id', '')),
                'checkin_name': c.get('name', ''),
                'checkin_user_id': user_id,
                'checkin_user_name': user_map.get(user_id, f"User_{user_id}"),
                'checkin_since': convert_time(checkin_ts),
                'checkin_since_timestamp': checkin_ts,
                'cong_viec_tiep_theo': extract_form_value(c_form, 'Công việc tiếp theo') or extract_form_value(c_form, 'Mô tả tiến độ') or extract_form_value(c_form, 'Những công việc quan trọng, trọng yếu, điểm nhấn thực hiện trong Tuần để đạt được kết quả (không phải công việc giải quyết hàng ngày)') or '', 
                'checkin_target_name': obj_export.get('name', ''), 
                'checkin_kr_current_value': c.get('current_value', 0),
                'kr_name': kr_name,
                'next_action_score': '' # Placeholder for AI scoring
            }
            full_data.append(row)
                    
        return full_data
        
    except Exception as e:
        print(f"Error generating data: {e}")
        return [{"error": str(e)}]


def sync_to_sheet(cycle_arg, web_app_url):
    print(f"Fetching data for cycle: {cycle_arg}...")
    
    # 1. Fetch data from LOCAL logic (no server import)
    raw_data = fetch_okr_data(cycle_arg)
    
    if not raw_data:
        print("No data found.")
        return
        
    if isinstance(raw_data, list) and len(raw_data) > 0 and 'error' in raw_data[0]:
        print(f"Error fetching data: {raw_data[0]['error']}")
        return

    print(f"Found {len(raw_data)} records. Preparing payload...")

    # 2. Convert to list of lists (Sheet format)
    df = pd.DataFrame(raw_data)
    df = df.astype(str)
    
    headers = df.columns.tolist()
    values = df.values.tolist()
    
    payload_data = [headers] + values
    
    # 4. Resolve Sheet Name
    cycle_info = get_cycle_info(cycle_arg)
    sheet_name = cycle_info['name'] if cycle_info else "OKR_Data"
    print(f"Target Sheet Name: {sheet_name}")

    # 3. Post to Google Apps Script
    payload = {
        'data': payload_data,
        'sheet_name': sheet_name
    }
    
    print(f"Uploading to Google Sheet ({web_app_url})...")
    try:
        response = requests.post(web_app_url, json=payload)
        
        if response.status_code == 200:
            print("Response:", response.text)
        else:
            print(f"Failed. Status: {response.status_code}, Response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync OKR Data to Google Sheet")
    parser.add_argument("--cycle", required=False, help="Cycle name or date (e.g. '11/2025' or 'Quý IV/2025'). Defaults to current cycle.")
    parser.add_argument("--url", required=False, help="Google Apps Script Web App URL (Optional if GG_SCRIPT_URL env is set)")
    
    args = parser.parse_args()
    
    script_url = args.url or GG_SCRIPT_URL
    if not script_url:
        print("Error: No Google Script URL provided. Set GG_SCRIPT_URL in .env or pass --url argument.")
        exit(1)
    
    sync_to_sheet(args.cycle, script_url)
