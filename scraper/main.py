import os
import time
import json
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
api_token = os.getenv("BRIGHTDATA_API_KEY")
collector_id = os.getenv("COLLECTOR_ID")

if not api_token or not collector_id:
    raise ValueError("Missing API credentials. Please check your .env file.")

# Define target place and URL
target_place = "chennai"
target_url = f"https://veggies-api-test-website.onrender.com/" # <--------- Modifyable Target

# Endpoints and Headers
trigger_url = f"https://api.brightdata.com/dca/trigger?collector={collector_id}"
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}
payload = [{"url": target_url}]

# --- STEP 1: Trigger the Scraper ---
print(f"Triggering the scraper for {target_place}...")
trigger_response = requests.post(trigger_url, headers=headers, json=payload)
trigger_response.raise_for_status()

# Capture the triggered collection run ID without overwriting collector_id
trigger_data = trigger_response.json()
collection_id = trigger_data.get("collection_id")
print(f"Job triggered successfully. Run ID: {collection_id}")

# --- STEP 2: Poll the Dataset Endpoint ---
dataset_url = f"https://api.brightdata.com/dca/dataset?id={collection_id}"
auth_header_only = {"Authorization": f"Bearer {api_token}"}

max_retries = 15
retry_interval = 10  # Seconds between polling requests

print("Polling for results...")

for attempt in range(1, max_retries + 1):
    dataset_response = requests.get(dataset_url, headers=auth_header_only)
    
    if dataset_response.status_code == 200:
        print("Data retrieved successfully!")
        data = dataset_response.json()
        
        # --- STEP 3: Create Date-Based Directory and Save File ---
        today_str = datetime.now().strftime("%d-%m-%Y")

        # Get the absolute path of the directory containing this script (scraper/)
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Path relative to the script's location
        output_dir = os.path.join(script_dir, "..", "veggies-api", "data", today_str)
        
        # Create 'data/DD-MM-YYYY' directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Define path: data/DD-MM-YYYY/chennai.json
        file_path = os.path.join(output_dir, f"{target_place}.json")
        
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
            
        print(f"✅ Data successfully saved to: {file_path}")
        break
        
    elif dataset_response.status_code == 202:
        print(f"[{attempt}/{max_retries}] Job still processing... waiting {retry_interval}s.")
        time.sleep(retry_interval)
        
    else:
        print(f"Failed to fetch data. Status: {dataset_response.status_code}")
        print(dataset_response.text)
        break
else:
    print("Max retries reached. The job took too long to complete.")