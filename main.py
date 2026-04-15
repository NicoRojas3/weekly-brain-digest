#### ––––––––––––––– START ––––––––––––––––– ####

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

# –––––––––––––––––––––––––––––––– #

## Configuration (IDs and API keys)

NOTION_TOKEN = "...XYZ..."
DATABASE_ID = "...ABC..."

notion = Client(auth=NOTION_TOKEN)

# –––––––––––––––––––––––––––––––– #

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

# –––––––––––––––––––––––––––––––– #

## Sorting & Selecting works and quotes

def get_blocks_recursive(block_id, depth=0):
    """Recursively fetches nested blocks from Notion to preserve hierarchy."""
    extracted = []
    try:
        # Notion paginates block children, so we loop to get all of them
        has_more = True
        start_cursor = None

        while has_more:
            response = notion.blocks.children.list(block_id=block_id, start_cursor=start_cursor)
            blocks = response.get("results", [])

            for block in blocks:
                block_type = block.get("type")
                text_content = ""

                valid_types = ["paragraph", "bulleted_list_item", "numbered_list_item", "toggle", "quote", "callout", "heading_1", "heading_2", "heading_3", "heading_4"]

                if block_type in valid_types:
                    rich_text = block.get(block_type, {}).get("rich_text", [])
                    if rich_text:
                        text_content = "".join([t.get("plain_text", "") for t in rich_text])

                if text_content:
                    # Save the text along with its current depth level
                    is_heading = block_type.startswith("heading") or block_type == "toggle"
                    extracted.append({
                        "text": text_content,
                        "depth": depth,
                        "is_heading": is_heading
                    })

                if block.get("has_children"):
                    extracted.extend(get_blocks_recursive(block["id"], depth + 1))

            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

    except Exception as e:
        print(f"Error crawling block {block_id}: {e}")

    return extracted

def get_page_content(page_id):
    return get_blocks_recursive(page_id, depth=0)

def extract_metadata(page):
    """Safely extracts book details, handling multi-select, select, or text Type columns."""
    props = page.get("properties", {})

    title_list = props.get("Name", {}).get("title", [])
    title = title_list[0].get("plain_text", "Untitled") if title_list else "Untitled"

    type_prop = props.get("Type", {})
    item_type = "none"

    if "multi_select" in type_prop and type_prop["multi_select"]:
        item_type = type_prop["multi_select"][0].get("name", "none").lower()
    elif "select" in type_prop and type_prop["select"]:
        item_type = type_prop["select"].get("name", "none").lower()
    elif "rich_text" in type_prop and type_prop["rich_text"]:
        item_type = type_prop["rich_text"][0].get("plain_text", "none").lower()

    tags = [t["name"].lower() for t in props.get("Tags", {}).get("multi_select", [])]

    idea_list = props.get("Core Idea", props.get("Core idea", {})).get("rich_text", [])
    core_idea = idea_list[0].get("plain_text", "No hay idea central.") if idea_list else "No hay idea central."

    cover = page.get("cover")
    cover_url = None
    if cover:
        cover_url = cover.get("external", {}).get("url") or cover.get("file", {}).get("url")

    return {"id": page["id"], "title": title, "item_type": item_type, "tags": tags, "core_idea": core_idea, "cover_url": cover_url}

def generate_weekly_plan(raw_results):
    print("--- BUILDING WEEKLY PLAN (WITH RECURSIVE DEPTH) ---")

    prof_pool = []
    pers_pool = []

    pages_by_tag = {
        "spy": [], "product": [], "literature": [],
        "colombia": [], "economics": [], "negotiation": []
    }

    for page in raw_results:
        data = extract_metadata(page)

        if data["item_type"] == "professional": prof_pool.append(data)
        elif data["item_type"] == "personal": pers_pool.append(data)

        for tag in data["tags"]:
            if tag in pages_by_tag:
                pages_by_tag[tag].append(data)

    random.shuffle(prof_pool)
    random.shuffle(pers_pool)

    final_plan = []
    daily_schedule = [
        ("Monday", "spy"), ("Tuesday", "product"), ("Wednesday", "literature"),
        ("Thursday", "colombia"), ("Friday", "economics"),
        ("Saturday", "negotiation"), ("Sunday", "literature")
    ]

    for day_name, daily_tag in daily_schedule:
        day_data = {"day": day_name, "daily_tag": daily_tag, "random_quote": None, "source_title": None}
        print(f"\nProcessing {day_name}...")

        for label, current_pool in [("professional", prof_pool), ("personal", pers_pool)]:
            if current_pool:
                selected = current_pool.pop(0).copy()
                selected["quotes"] = get_page_content(selected["id"])
                day_data[label] = selected
                current_pool.append(selected)
                print(f"  - Added {label.upper()}: {selected['title']}")
            else:
                day_data[label] = None

        if pages_by_tag[daily_tag]:
            random_page = random.choice(pages_by_tag[daily_tag])
            page_content = get_page_content(random_page["id"])

            valid_quotes = [q["text"] for q in page_content if len(q["text"].strip()) > 5 and not q["is_heading"]]

            if valid_quotes:
                day_data["random_quote"] = random.choice(valid_quotes)
                day_data["source_title"] = random_page["title"]
                print(f"  - Added random {daily_tag.upper()} quote from: {random_page['title']}")

        final_plan.append(day_data)

    print("\n Plan generated with custom daily tags.")
    return final_plan

# --- TRIGGER ---
if 'raw_results' in globals():
    weekly_plan = generate_weekly_plan(raw_results)
else:
    print("❌ Error: Run Block 3 first.")


# –––––––––––––––––––––––––––––––– #

## PDF Generation

from fpdf import FPDF
from google.colab import files

def sanitize_text(text):
    if not text:
        return ""
    replacements = {
        "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
        "\u2013": "-", "\u2014": "-", "\u2026": "..."
    }
    for search, replace in replacements.items():
        text = text.replace(search, replace)
    return text.encode('latin-1', 'ignore').decode('latin-1')

def create_pdf(weekly_plan):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20) # Increased margins for more "breathing room"

    print("--- 📄 GENERATING PREMIUM PDF FILE ---")

    for day_data in weekly_plan:
        pdf.add_page()

        pdf.set_fill_color(240, 244, 248)
        pdf.rect(0, 0, 210, 35, 'F')

        pdf.set_y(12)
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(70, 80, 90)
        pdf.cell(0, 10, f"{day_data['day'].upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(20) 

        for label in ["professional", "personal"]:
            item = day_data.get(label)
            if item:
                # 2. Subtle Category
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(160, 160, 160)
                pdf.cell(0, 4, f"{label.upper()} READ", new_x="LMARGIN", new_y="NEXT")

                # Main Title
                pdf.set_font("Helvetica", "B", 16)
                pdf.set_text_color(40, 40, 40)
                safe_title = sanitize_text(item['title'])
                pdf.cell(0, 8, safe_title, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(3)

                # Optional Cover Image
                if item.get('cover_url'):
                    try:
                        pdf.image(item['cover_url'], w=35)
                        pdf.ln(5)
                    except: pass

                # 3. Core Idea 
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(120, 130, 140)
                pdf.cell(0, 5, "CORE IDEA / IDEA CENTRAL", new_x="LMARGIN", new_y="NEXT")

                pdf.set_font("Helvetica", "", 11)
                pdf.set_text_color(60, 60, 60)
                pdf.set_draw_color(180, 190, 200) 
                pdf.set_line_width(0.3)

                safe_idea = sanitize_text(item['core_idea'])
                pdf.multi_cell(0, 7, f" {safe_idea} ", border=1, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(6)

                # 4. Highlights 
                if item.get('quotes'):
                    for quote_data in item['quotes']:
                        text = quote_data.get("text", "") if isinstance(quote_data, dict) else quote_data
                        depth = quote_data.get("depth", 0) if isinstance(quote_data, dict) else 0
                        is_heading = quote_data.get("is_heading", False) if isinstance(quote_data, dict) else False

                        safe_quote = sanitize_text(text)

                        base_x = 20
                        indent = depth * 8

                        if is_heading:
                            pdf.set_x(base_x + indent)
                            pdf.set_font("Helvetica", "B", 10)
                            pdf.set_text_color(50, 50, 50)
                            pdf.multi_cell(0, 6, safe_quote)
                        else:
                            # Draw bullet
                            bullet_x = base_x + indent + 1
                            bullet_y = pdf.get_y() + 2.5
                            pdf.set_fill_color(160, 180, 200)
                            pdf.rect(bullet_x, bullet_y, 1.5, 1.5, 'F')

                            # Print text next to bullet
                            pdf.set_x(base_x + indent + 5)
                            pdf.set_font("Helvetica", "", 10)
                            pdf.set_text_color(70, 70, 70)
                            pdf.multi_cell(0, 6, safe_quote)
                        pdf.ln(1)

                pdf.ln(8)

        # 5. Daily Random Quote Section 
        if day_data.get("random_quote"):
            pdf.ln(5)
            # Divider line
            pdf.set_draw_color(220, 220, 220)
            pdf.line(40, pdf.get_y(), 170, pdf.get_y())
            pdf.ln(8)

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 5, f"DAILY {day_data['daily_tag'].upper()} QUOTE", align="C", new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "I", 11)
            pdf.set_text_color(80, 80, 80)
            safe_daily_quote = sanitize_text(day_data["random_quote"])
            safe_source = sanitize_text(day_data["source_title"])

            pdf.multi_cell(0, 6, f'"{safe_daily_quote}"\n- {safe_source}', align="C")
            pdf.set_text_color(0, 0, 0)

    output_name = "Weekly_Brain_Digest.pdf"
    pdf.output(output_name)
    print(f"✅ SUCCESS: '{output_name}' created!")

    try:
        files.download(output_name)
    except Exception as e:
        print("Note: Could not auto-download. Please find the file in the left sidebar.")

# --- TRIGGER ---
if 'weekly_plan' in globals():
    create_pdf(weekly_plan)


#### ––––––––––––––– END ––––––––––––––––– ####

