## Libraries and packages
!pip install notion-client fpdf2 requests

import os
import random
from datetime import datetime, timedelta
from notion_client import Client
from fpdf import FPDF
import requests
import requests
import json

––––––––

## Configuration (IDs and API keys)

NOTION_TOKEN = "...XYZ..."
DATABASE_ID = "...ABC..."

notion = Client(auth=NOTION_TOKEN)

––––––––

## Fetching the data

def fetch_entries_manual():

    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    try:
        response = requests.post(url, headers=headers, json={})

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            print(f"✅ SUCCESS! Found {len(results)} rows.")

            # --- PEEK LOGIC ---
            if results:
                print("\n Data Preview (First 3 rows):")
                for i in range(min(3, len(results))):
                    name = results[i]["properties"]["Name"]["title"][0]["plain_text"]
                    tags = [t["name"] for t in results[i]["properties"].get("Tags", {}).get("multi_select", [])]
                    print(f" - Item: {name} | Tags: {tags}")
            return results

        else:
            print(f"❌ ERROR {response.status_code}: {response.text}")
            return []

    except Exception as e:
        print(f"💥 CONNECTION ERROR: {e}")
        return []

raw_results = fetch_entries_manual()

