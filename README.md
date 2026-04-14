# weekly-brain-digest
Automated system to sync Notion highlights and generate a curated weekly PDF digest for active recall.

## How it Works
Source: I manually add quotes and highlights to a Notion database once a week.
Algorithm: Every day, the script selects:
One Professional insight.
One Personal (Spy/Literature) insight.
A Categorized Random quote based on the day of the week (e.g., Wednesdays are for Literature).
Constraint: It includes logic to ensure no quote is repeated within the same calendar week.
Output: Generates a "Premium" PDF with clean formatting for easy reading on my tablet or phone.

## Technical Stack
Environment: Developed and run entirely in Google Colab.
Database: Notion API.
PDF Engine: fpdf2 for custom layouts.
