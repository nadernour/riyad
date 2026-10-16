import sqlite3
import re
from bs4 import BeautifulSoup
import shutil
from collections import defaultdict
import json

# ==========================================
# CONFIGURATION
# ==========================================
DB_SOURCE = "riyad_salheen.db"
DB_TARGET = "..\\app\\src\\main\\assets\\databases\\riyad_salheen.db"

# ==========================================
# LOGGING AND UTILS
# ==========================================

def log_print(*args, **kwargs):
    with open("hadith_processing_log.txt", 'w', encoding='utf-8') as log_file:
        print(*args, **kwargs, file=log_file)

def add_column_if_not_exists(conn, table_name, column_name, column_type):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]
    if column_name not in columns:
        print(f"Column '{column_name}' not found in '{table_name}'. Adding it...")
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        print(f"Column '{column_name}' added successfully.")
    else:
        print(f"Column '{column_name}' already exists in '{table_name}'.")

def read_hadith_count(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM hadiths")
    count = cursor.fetchone()[0]
    return count

def find_all_colors_used(conn):
    cursor = conn.cursor()

    # 1. Add the new column for search-friendly text
    add_column_if_not_exists(conn, "hadiths", "hadith_normal", "TEXT")

    # 2. Fetch all hadiths that need processing
    cursor.execute("SELECT id, hadith, sharh FROM hadiths")
    all_hadiths = cursor.fetchall()
    
    total_hadiths = len(all_hadiths)
    print(f"\nFound {total_hadiths} hadiths to process.") 

    hadith_color_map = defaultdict(list)
    sharh_color_map = defaultdict(list)

    # Regex to find rgb(...) colors within a style attribute
    rgb_pattern = re.compile(
        r'(color:rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\))',
        re.IGNORECASE
    )

    # Process each HTML string in the input list
    for i, row in enumerate(all_hadiths):
        hadith_id, original_hadith, original_sharh = row
        print(f"Processing hadith {i + 1}/{total_hadiths} (ID: {hadith_id})... Done.")

        # Parse the HTML
        soup = BeautifulSoup(original_hadith, 'html.parser')
        for tag in soup.find_all('span', style=rgb_pattern):
            style_str = tag.get('style')
            found_colors = rgb_pattern.findall(style_str)
            if found_colors:
                content = tag.get_text(strip=True)
                if content:
                    for color in found_colors:
                        if not hadith_color_map[color] or len(hadith_color_map[color]) < 20:
                            hadith_color_map[color].append(content)

        soup = BeautifulSoup(original_sharh, 'html.parser')
        for tag in soup.find_all('span', style=rgb_pattern):
            style_str = tag.get('style')
            found_colors = rgb_pattern.findall(style_str)
            if found_colors:
                content = tag.get_text(strip=True)
                if content:
                    for color in found_colors:
                        if not sharh_color_map[color] or len(sharh_color_map[color]) < 20:
                            sharh_color_map[color].append(content)

    log_print(f"hadith_color_map:\n{json.dumps(hadith_color_map, indent = 4, ensure_ascii=False)}\nsharh_color_map:\n{json.dumps(sharh_color_map, indent = 4, ensure_ascii=False)}")
  
def test_process_and_print_hadith(conn):
    cursor = conn.cursor()

    # 1. Add the new column for search-friendly text
    add_column_if_not_exists(conn, "hadiths", "hadith_normal", "TEXT")

    # 2. Fetch all hadiths that need processing
    cursor.execute("SELECT id, hadith, sharh FROM hadiths")
    all_hadiths = cursor.fetchall()
    
    total_hadiths = len(all_hadiths)
    print(f"\nFound {total_hadiths} hadiths to process.")

    hadith_id, original_hadith, original_sharh = all_hadiths[1]
    cleaned_hadith = clean_html_text(original_hadith, "hadith")
    cleaned_sharh = clean_html_text(original_sharh, "sharh")
    hadith_normal = clean_and_normalize_text(cleaned_hadith)

    log_print(f"""
{original_hadith}
-----------------------------------------------------------------------------------------------------------
{cleaned_hadith}
-----------------------------------------------------------------------------------------------------------
{original_sharh}
-----------------------------------------------------------------------------------------------------------
{cleaned_sharh}""")

# ==========================================
# TEXT PROCESSING LOGIC
# ==========================================

def clean_html_text(html_content, textType):
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Define markers. We use text markers because get_text() will strip HTML tags.
    br_marker = "||BR||"
    bullet_marker = ("{{BULLET_MARKER}}", "<bullet>")
    # Define markers for each style
    style_markers = {
        'hadith':{
            'P0': {
                'markers': ("{{P0}}", "{{/P0}}"),
                'html_markers': ("<p0>", "</p0>"),
                'colors': ["color:rgb(0, 0, 255)", "color:rgb(255, 0, 0)"]
            },
            'P1': {
                'markers': ("{{P1}}", "{{/P1}}"),
                'html_markers': ("<p1>", "</p1>"),
                'colors': ["color:rgb(0, 128, 0)", "color:rgb(152, 0, 0)"]
            },
            'P2': {
                'markers': ("{{P2}}", "{{/P2}}"),
                'html_markers': ("<p2>", "</p2>"),
                'colors': ["color:rgb(128, 0, 0)", "color:rgb(128, 0, 128)", "color:rgb(106, 168, 79)",
                        "color:rgb(56, 118, 29)", "color:rgb(0, 0, 128)", "color:rgb(39, 78, 19)", 
                        "color:rgb(128, 128, 0)"]
            }
        },
        'sharh': {
            'P0': {
                'markers': ("{{P0}}", "{{/P0}}"),
                'html_markers': ("<p0>", "</p0>"),
                'colors': ["color:rgb(255, 0, 0)", "color:rgb(255, 255, 0)", "color:rgb(255, 7, 7)"]
            },
            'P1': {
                'markers': ("{{P1}}", "{{/P1}}"),
                'html_markers': ("<p1>", "</p1>"),
                'colors': [ "color:rgb(152, 0, 0)", "color:rgb(0, 0, 255)"]
            },
            'P2': {
                'markers': ("{{P2}}", "{{/P2}}"),
                'html_markers': ("<p2>", "</p2>"),
                'colors': ["color:rgb(0, 128, 0)", "color:rgb(48, 48, 48)", "color:rgb(34, 34, 34)",
                        "color:rgb(51, 51, 51)", "color:rgb(51, 51, 153)"]
            }
        }
    }

    markers = style_markers[textType]

    # Replace <br> tags with a marker
    for br in soup.find_all("br"):
        br.replace_with(br_marker)
    
    rgb_pattern = re.compile(
        r'(color:rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\))',
        re.IGNORECASE
    )

    for span in soup.find_all('span', style=rgb_pattern):
        style_str = span.get('style')
        found_colors = rgb_pattern.findall(style_str)
        content = span.get_text(strip=True)
        if found_colors and content and len(found_colors) > 0:
            color = found_colors[0]
            for key in markers:
                if color in markers[key]["colors"]:
                    new_text_node = (
                        f"{markers[key]['markers'][0]}"
                        f"{content}"
                        f"{markers[key]['markers'][1]}"
                    )
                    span.replace_with(new_text_node)
                    break

    text_parts = []
    # Find all major block-level elements that should be separated by newlines
    for element in soup.find_all(['p', 'li']):
        # If this element is nested inside another element we're already processing, skip it.
        if element.find_parent(['p', 'li']):
            continue
            
        # Get text from the element, replacing any internal tags with a space.
        # Our marker will be preserved.
        text = element.get_text(separator=' ', strip=True)
        
        # Consolidate whitespace, but protect the marker by removing spaces around it
        text = re.sub(r'\s*' + re.escape(br_marker) + r'\s*', br_marker, text)
        # Now collapse all other whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Finally, replace the marker with a newline
        text = text.replace(br_marker, '\n')

        # Add the cleaned text part if it's not empty
        if text:
            # For list items, we can add a bullet for clarity
            if element.name == 'li':
                text_parts.append(f"{bullet_marker[0]} {text}")
            else:
                text_parts.append(text)
    
    final_text = '\n'.join(text_parts)

    for key in markers:
        final_text = final_text.replace(markers[key]['markers'][0], markers[key]['html_markers'][0])
        final_text = final_text.replace(markers[key]['markers'][1], markers[key]['html_markers'][1])

    final_text = final_text.replace(bullet_marker[0], bullet_marker[1])

    # Join the parts with a single newline, which creates the desired paragraph structure
    return final_text

def clean_and_normalize_text(text):
    if not text:
        return ""
    
    marker_pattern = re.compile(r'<[^>]*>')
    text = re.sub(marker_pattern, ' ', text) # Replace with space to prevent word concatenation

    tashkeel_pattern = re.compile(r'[\u064B-\u0652\u0670]')
    text = re.sub(tashkeel_pattern, '', text)

    text = re.sub(r'\s+', ' ', text).strip()

    return text

# ==========================================
# EXPORT / IMPORT / INSERT
# ==========================================

def export_hadith_to_json(conn, hadith_id, output_filename="hadith_edit.json"):
    """
    Fetches a single hadith by ID and saves it to a JSON file.
    """
    conn.row_factory = sqlite3.Row # Access columns by name
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hadiths WHERE id = ?", (hadith_id,))
    row = cursor.fetchone()
    
    if row:
        data = dict(row)
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Hadith ID {hadith_id} exported to '{output_filename}'")
    else:
        print(f"Hadith ID {hadith_id} not found.")

def update_hadith_from_json(conn, json_filename):
    """
    Reads a JSON file, processes the text (cleaning/normalization),
    and UPDATES the existing record with the matching ID.
    """
    if not os.path.exists(json_filename):
        print(f"File {json_filename} not found.")
        return

    with open(json_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    hadith_id = data.get('id')
    raw_hadith = data.get('hadith', '')
    raw_sharh = data.get('sharh', '')
    
    # Apply processing logic
    cleaned_hadith = clean_html_text(raw_hadith, 'hadith')
    cleaned_sharh = clean_html_text(raw_sharh, 'sharh')
    hadith_normal = clean_and_normalize_text(cleaned_hadith)
    
    cursor = conn.cursor()
    
    # We only update content columns, not IDs or references usually
    query = """
    UPDATE hadiths 
    SET title = ?, hadith = ?, sharh = ?, hadith_normal = ?
    WHERE id = ?
    """
    
    try:
        cursor.execute(query, (data.get('title'), cleaned_hadith, cleaned_sharh, hadith_normal, hadith_id))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Successfully updated Hadith ID {hadith_id} from JSON.")
        else:
            print(f"No hadith found with ID {hadith_id} to update.")
    except sqlite3.Error as e:
        print(f"Error updating hadith: {e}")

def insert_hadith_from_json(conn, json_filename):
    """
    Reads a JSON file. 
    1. Checks if the ID exists. 
    2. If it exists, SHIFTS all subsequent IDs down by 1.
    3. INSERTS the new record after processing text.
    """
    if not os.path.exists(json_filename):
        print(f"File {json_filename} not found.")
        return

    with open(json_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    target_id = data.get('id')
    
    # Apply processing logic
    cleaned_hadith = clean_html_text(data.get('hadith', ''), 'hadith')
    cleaned_sharh = clean_html_text(data.get('sharh', ''), 'sharh')
    hadith_normal = clean_and_normalize_text(cleaned_hadith)

    cursor = conn.cursor()

    try:
        # 1. Check if ID exists
        cursor.execute("SELECT 1 FROM hadiths WHERE id = ?", (target_id,))
        exists = cursor.fetchone()

        if exists:
            print(f"ID {target_id} exists. Shifting subsequent records...")
            # Shift IDs to make room. 
            # IMPORTANT: Must do this in descending order to avoid unique constraint collision during update
            # But SQLite handles simple `UPDATE table SET id = id + 1` smartly usually, 
            # but standard SQL practice is careful.
            cursor.execute("UPDATE hadiths SET id = id + 1 WHERE id >= ?", (target_id,))
            print("Shift complete.")

        # 2. Insert
        columns = "id, book_id, door_id, title, hadith, sharh, hadith_normal"
        placeholders = "?, ?, ?, ?, ?, ?, ?"
        
        values = (
            target_id,
            data.get('book_id'),
            data.get('door_id'),
            data.get('title'),
            cleaned_hadith,
            cleaned_sharh,
            hadith_normal
        )

        cursor.execute(f"INSERT INTO hadiths ({columns}) VALUES ({placeholders})", values)
        conn.commit()
        print(f"Successfully inserted new Hadith at ID {target_id}.")

    except sqlite3.Error as e:
        print(f"Error inserting hadith: {e}")
        conn.rollback()

# ==========================================
# BATCH PROCESSING
# ==========================================
def process_and_update_hadiths(conn):
    cursor = conn.cursor()

    # 1. Add the new column for search-friendly text
    add_column_if_not_exists(conn, "hadiths", "hadith_normal", "TEXT")

    # 2. Fetch all hadiths that need processing
    cursor.execute("SELECT id, hadith, sharh FROM hadiths")
    all_hadiths = cursor.fetchall()
    
    total_hadiths = len(all_hadiths)
    print(f"\nFound {total_hadiths} hadiths to process.")

    # 3. Loop through, process, and update each hadith
    for i, row in enumerate(all_hadiths):
        hadith_id, original_hadith, original_sharh = row

        # Clean the HTML content
        cleaned_hadith = clean_html_text(original_hadith, 'hadith')
        cleaned_sharh = clean_html_text(original_sharh, 'sharh')
        
        # Create the search-friendly version without tashkeel
        hadith_normal = clean_and_normalize_text(cleaned_hadith)

        # Update the row in the database
        update_query = """
        UPDATE hadiths 
        SET hadith = ?, sharh = ?, hadith_normal = ? 
        WHERE id = ?
        """
        cursor.execute(update_query, (cleaned_hadith, cleaned_sharh, hadith_normal, hadith_id))
        
        # Print progress
        print(f"Processing hadith {i + 1}/{total_hadiths} (ID: {hadith_id})... Done.")

    # 4. Commit all changes to the database
    conn.commit()
    print("\nAll hadiths have been processed and the database has been updated successfully!")

def main():
    original_database_path = "riyad_salheen.db"
    target_database_path = "..\\app\\src\\main\\assets\\databases\\riyad_salheen.db"

    # try:
    #     print(f"Copying '{original_database_path}' to '{target_database_path}'...")
    #     shutil.copyfile(original_database_path, target_database_path)
    #     print("Copy complete.")
        
    # except IOError as e:
    #     print(f"Unable to copy file. Error: {e}")
    #     return
    # except Exception as e:
    #     print(f"An error occurred during copy: {e}")
    #     return
    
    conn = sqlite3.connect(target_database_path)
    try:
        # --- MODE SELECTION ---
        # Uncomment the function you want to run
        
        # A. Run the full cleanup on the whole DB
        # process_and_update_hadiths(conn)

        # B. Export a specific Hadith to JSON (to edit it)
        # export_hadith_to_json(conn, hadith_id=1, output_filename="edit_hadith_1.json")

        # C. Import (Update) an edited JSON back to DB
        # update_hadith_from_json(conn, json_filename="edit_hadith_1.json")

        # D. Insert a NEW Hadith at a specific Index (Shifting others)
        # insert_hadith_from_json(conn, json_filename="new_hadith.json")
        
        pass # Placeholder if everything above is commented out
    finally:
        if conn:
            conn.close()
            print("Processed database connection closed.")

if __name__ == '__main__':
    main()