import xml.etree.ElementTree as ET
import requests
import gzip
import re
from datetime import datetime, timedelta

# ================= Configuration Area =================

# Configure your multiple sources here
# Format: {"m3u": "M3U Link", "epg": "EPG Link", "offset": Timezone offset in hours}
SOURCES = [
    {
        "name": "Mainland Channels",  # Name for easy log reading
        "m3u": "https://www.dropbox.com/scl/fi/5vio2bkhbnbsaa1naousm/TV-List_CN.m3u?rlkey=q8ynpyirdhgr1xuwnyjy4u96a&raw=1",
        "epg": "https://epg.pw/xmltv/epg_CN.xml",
        "offset": -8
    },
    {
        "name": "Hong Kong Channels",
        "m3u": "https://www.dropbox.com/scl/fi/b1w8njm0v68muuxaq0bs4/TV-List_HK.m3u?rlkey=xjkoez8vq0xolm5qqcoqmalmz&raw=1",
        "epg": "https://epg.pw/xmltv/epg_HK.xml",
        "offset": -8
    },
    {
        "name": "Taiwan Channels",
        "m3u": "https://www.dropbox.com/scl/fi/qn06cpz5wecrswxtpvf5a/TV-List_TW.m3u?rlkey=f5hdt4hsx3ai6gbeqw52qijef&raw=1",
        "epg": "https://epg.pw/xmltv/epg_TW.xml",
        "offset": -8
    },
    {
        "name": "English Channels",
        "m3u": "https://www.dropbox.com/scl/fi/bmi02o7w4k4ss70mykji3/TV-List.m3u?rlkey=17oixu3vi7iyir2jad1eowsne&raw=1",
        "epg": "tvg-id",
        "offset": 0
    },
]

# Output filename
OUTPUT_FILENAME = "slim_fixed_epg.xml"

# ===========================================

def get_content(url):
    """Download content and automatically handle gzip"""
    print(f"Downloading: {url} ...")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        if url.endswith('.gz') or url.endswith('.GZ'):
            return gzip.decompress(response.content)
        else:
            return response.content
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

def extract_tvg_ids(m3u_content):
    """Extract all tvg-id from M3U content"""
    if not m3u_content:
        return set()
    text = m3u_content.decode('utf-8', errors='ignore')
    # Regex match tvg-id="xxx"
    ids = set(re.findall(r'tvg-id="([^"]+)"', text))
    print(f"  - Found {len(ids)} unique channel IDs (tvg-id) in M3U.")
    return ids

def merge_epg_data(epg_root, valid_ids, seen_channel_ids, master_root, offset_hours):
    """Extracted common merge logic to process XML nodes and time offsets"""
    time_format = "%Y%m%d%H%M%S"
    added_channels = 0
    added_programmes = 0

    for child in epg_root:
        # --- Process channel info <channel> ---
        if child.tag == 'channel':
            c_id = child.get('id')
            if c_id in valid_ids:
                if c_id not in seen_channel_ids:
                    master_root.append(child)
                    seen_channel_ids.add(c_id)
                    added_channels += 1
        
        # --- Process program guide <programme> ---
        elif child.tag == 'programme':
            p_id = child.get('channel')
            if p_id in valid_ids:
                if offset_hours != 0:
                    for attr in ['start', 'stop']:
                        if attr in child.attrib:
                            original_time_str = child.attrib[attr]
                            # Extract the first 14 characters of time (YYYYMMDDHHMMSS)
                            time_part = original_time_str[:14]
                            timezone_part = original_time_str[14:] # Keep +0000 or other suffixes
                            
                            try:
                                dt = datetime.strptime(time_part, time_format)
                                new_dt = dt + timedelta(hours=offset_hours)
                                # Write new time
                                new_time_str = new_dt.strftime(time_format) + timezone_part
                                child.set(attr, new_time_str)
                            except ValueError:
                                pass
                master_root.append(child)
                added_programmes += 1

    return added_channels, added_programmes

def process_and_merge(source_conf, master_root, seen_channel_ids):
    """
    Process a single source and merge the results into master_root
    """
    print(f"\n>>> Start processing: {source_conf['name']}")
    
    # 1. Get M3U and extract IDs
    m3u_data = get_content(source_conf['m3u'])
    if not m3u_data:
        print("  - Skip this source (M3U download failed)")
        return
    
    valid_ids = extract_tvg_ids(m3u_data)
    if not valid_ids:
        print("  - Skip this source (No valid tvg-id found)")
        return

    offset_hours = source_conf.get('offset', 0)
    total_added_channels = 0
    total_added_programmes = 0

    # 2. Get EPG (Distinguish between normal mode and tvg-id fetch-one-by-one mode)
    if source_conf['epg'] == "tvg-id":
        print("  - Detected epg as 'tvg-id', starting to fetch channel by channel...")
        today_str = datetime.now().strftime("%Y%m%d")
        
        for c_id in valid_ids:
            # Construct API link
            url = f"https://epg.pw/api/epg.xml?lang=en&date={today_str}&channel_id={c_id}"
            epg_data = get_content(url)
            if not epg_data:
                continue
            
            try:
                try:
                    epg_root = ET.fromstring(epg_data)
                except:
                    epg_root = ET.fromstring(epg_data.decode('utf-8', errors='ignore'))
            except ET.ParseError as e:
                print(f"  - XML parsing failed ({c_id}): {e}")
                continue
            
            # Merge data for current channel
            c, p = merge_epg_data(epg_root, valid_ids, seen_channel_ids, master_root, offset_hours)
            total_added_channels += c
            total_added_programmes += p

    else:
        epg_data = get_content(source_conf['epg'])
        if not epg_data:
            print("  - Skip this source (EPG download failed)")
            return

        print("  - Parsing XMLTV data...")
        try:
            try:
                epg_root = ET.fromstring(epg_data)
            except:
                epg_root = ET.fromstring(epg_data.decode('utf-8', errors='ignore'))
        except ET.ParseError as e:
            print(f"  - XML parsing failed: {e}")
            return

        print(f"  - Merging data (Timezone offset: {offset_hours} hours)...")
        c, p = merge_epg_data(epg_root, valid_ids, seen_channel_ids, master_root, offset_hours)
        total_added_channels += c
        total_added_programmes += p

    print(f"  - Source processing completed: Added {total_added_channels} channels, {total_added_programmes} programs")

if __name__ == "__main__":
    # Initialize main XML structure
    master_root = ET.Element("tv")
    master_root.set("generator-info-name", "EPG-Merger-Bot")
    master_root.set("generator-info-url", "https://github.com/")
    
    # Used to record all added channel IDs to prevent duplicate <channel> definitions
    all_seen_ids = set()

    # Loop through each source
    for conf in SOURCES:
        process_and_merge(conf, master_root, all_seen_ids)

    # Save final file
    if len(master_root) > 0:
        print(f"\nSaving merged file: {OUTPUT_FILENAME} ...")
        tree = ET.ElementTree(master_root)
        tree.write(OUTPUT_FILENAME, encoding="UTF-8", xml_declaration=True)
        print("✅ All tasks completed!")
    else:
        print("\n⚠️ Warning: Generated content is empty, file not saved.")
