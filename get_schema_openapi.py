import os
import requests
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_ANON_KEY")

if not URL or not KEY:
    print("Missing credentials")
    exit(1)

# Supabase REST endpoint provides OpenApi description at the root
endpoint = f"{URL}/rest/v1/"
headers = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}"
}

try:
    response = requests.get(endpoint, headers=headers)
    if response.status_code == 200:
        schema = response.json()
        definitions = schema.get("definitions", {})
        ads_definition = definitions.get("ads", {})
        properties = ads_definition.get("properties", {})
        
        print("\n--- Schema for 'ads' table ---")
        if properties:
            for prop, details in properties.items():
                print(f"Prop: {prop}, Type: {details.get('format', details.get('type'))}")
        else:
            print("No properties found in OpenApi for 'ads'.")
            
        print("\n--- Schema for 'analytics_events' table ---")
        analytics_definition = definitions.get("analytics_events", {})
        properties_analytics = analytics_definition.get("properties", {})
        for prop, details in properties_analytics.items():
            print(f"Prop: {prop}, Type: {details.get('format', details.get('type'))}")
            
    else:
        print(f"Failed to fetch schema: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Error: {e}")
