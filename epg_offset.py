import xml.etree.ElementTree as ET
import requests
import gzip
import re
from datetime import datetime, timedelta

# ================= 配置区域 =================

# 在这里配置你的多个来源
# 格式：{"m3u": "M3U链接", "epg": "EPG链接", "offset": 时差偏移}
SOURCES = [
    {
        "name": "大陆频道",  # 方便看日志的名字
        "m3u": "https://www.dropbox.com/scl/fi/5vio2bkhbnbsaa1naousm/TV-List_CN.m3u?rlkey=q8ynpyirdhgr1xuwnyjy4u96a&raw=1",
        "epg": "https://epg.112114.xyz/pp.xml",
        "offset": 0
    },
    {
        "name": "香港频道",
        "m3u": "https://www.dropbox.com/scl/fi/b1w8njm0v68muuxaq0bs4/TV-List_HK.m3u?rlkey=xjkoez8vq0xolm5qqcoqmalmz&raw=1",
        "epg": "https://epg.pw/xmltv/epg_HK.xml",
        "offset": -8
    },
    {
        "name": "台湾频道",
        "m3u": "https://www.dropbox.com/scl/fi/qn06cpz5wecrswxtpvf5a/TV-List_TW.m3u?rlkey=f5hdt4hsx3ai6gbeqw52qijef&raw=1",
        "epg": "https://epg.pw/xmltv/epg_TW.xml",
        "offset": -8
    },
    {
        "name": "英文频道",
        "m3u": "https://www.dropbox.com/scl/fi/bmi02o7w4k4ss70mykji3/TV-List.m3u?rlkey=17oixu3vi7iyir2jad1eowsne&raw=1",
        "epg": "tvg-id",
        "offset": 0
    },
]

# 输出文件名
OUTPUT_FILENAME = "slim_fixed_epg.xml"

# ===========================================

def get_content(url):
    """下载内容，自动处理 gzip"""
    print(f"正在下载: {url} ...")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        if url.endswith('.gz') or url.endswith('.GZ'):
            return gzip.decompress(response.content)
        else:
            return response.content
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return None

def extract_tvg_ids(m3u_content):
    """从 M3U 内容中提取所有的 tvg-id"""
    if not m3u_content:
        return set()
    text = m3u_content.decode('utf-8', errors='ignore')
    # 正则匹配 tvg-id="xxx"
    ids = set(re.findall(r'tvg-id="([^"]+)"', text))
    print(f"  - M3U 中共找到 {len(ids)} 个唯一的频道 ID (tvg-id)。")
    return ids

def merge_epg_data(epg_root, valid_ids, seen_channel_ids, master_root, offset_hours):
    """提取出的公共合并逻辑，处理 XML 节点与时间偏移"""
    time_format = "%Y%m%d%H%M%S"
    added_channels = 0
    added_programmes = 0

    for child in epg_root:
        # --- 处理频道信息 <channel> ---
        if child.tag == 'channel':
            c_id = child.get('id')
            if c_id in valid_ids:
                if c_id not in seen_channel_ids:
                    master_root.append(child)
                    seen_channel_ids.add(c_id)
                    added_channels += 1
        
        # --- 处理节目单 <programme> ---
        elif child.tag == 'programme':
            p_id = child.get('channel')
            if p_id in valid_ids:
                if offset_hours != 0:
                    for attr in ['start', 'stop']:
                        if attr in child.attrib:
                            original_time_str = child.attrib[attr]
                            # 提取前14位时间 (YYYYMMDDHHMMSS)
                            time_part = original_time_str[:14]
                            timezone_part = original_time_str[14:] # 保留 +0000 或其他后缀
                            
                            try:
                                dt = datetime.strptime(time_part, time_format)
                                new_dt = dt + timedelta(hours=offset_hours)
                                # 写入新时间
                                new_time_str = new_dt.strftime(time_format) + timezone_part
                                child.set(attr, new_time_str)
                            except ValueError:
                                pass
                master_root.append(child)
                added_programmes += 1

    return added_channels, added_programmes

def process_and_merge(source_conf, master_root, seen_channel_ids):
    """
    处理单个源，并将结果合并到 master_root 中
    """
    print(f"\n>>> 开始处理: {source_conf['name']}")
    
    # 1. 获取 M3U 并提取 ID
    m3u_data = get_content(source_conf['m3u'])
    if not m3u_data:
        print("  - 跳过此源 (M3U 下载失败)")
        return
    
    valid_ids = extract_tvg_ids(m3u_data)
    if not valid_ids:
        print("  - 跳过此源 (未找到有效 tvg-id)")
        return

    offset_hours = source_conf.get('offset', 0)
    total_added_channels = 0
    total_added_programmes = 0

    # 2. 获取 EPG (区分常规模式和 tvg-id 逐个抓取模式)
    if source_conf['epg'] == "tvg-id":
        print("  - 检测到 epg 为 'tvg-id'，开始逐个频道抓取...")
        today_str = datetime.now().strftime("%Y%m%d")
        
        for c_id in valid_ids:
            # 拼接 API 链接
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
                print(f"  - XML 解析失败 ({c_id}): {e}")
                continue
            
            # 合并当前频道的数据
            c, p = merge_epg_data(epg_root, valid_ids, seen_channel_ids, master_root, offset_hours)
            total_added_channels += c
            total_added_programmes += p

    else:
        epg_data = get_content(source_conf['epg'])
        if not epg_data:
            print("  - 跳过此源 (EPG 下载失败)")
            return

        print("  - 正在解析 XMLTV 数据...")
        try:
            try:
                epg_root = ET.fromstring(epg_data)
            except:
                epg_root = ET.fromstring(epg_data.decode('utf-8', errors='ignore'))
        except ET.ParseError as e:
            print(f"  - XML 解析失败: {e}")
            return

        print(f"  - 正在合并数据 (时差偏移: {offset_hours} 小时)...")
        c, p = merge_epg_data(epg_root, valid_ids, seen_channel_ids, master_root, offset_hours)
        total_added_channels += c
        total_added_programmes += p

    print(f"  - 本源处理完成: 新增频道 {total_added_channels} 个, 节目单 {total_added_programmes} 条")

if __name__ == "__main__":
    # 初始化主 XML 结构
    master_root = ET.Element("tv")
    master_root.set("generator-info-name", "EPG-Merger-Bot")
    master_root.set("generator-info-url", "https://github.com/")
    
    # 用于记录所有已添加的频道 ID，防止重复定义 <channel>
    all_seen_ids = set()

    # 循环处理每个源
    for conf in SOURCES:
        process_and_merge(conf, master_root, all_seen_ids)

    # 保存最终文件
    if len(master_root) > 0:
        print(f"\n正在保存合并后的文件: {OUTPUT_FILENAME} ...")
        tree = ET.ElementTree(master_root)
        tree.write(OUTPUT_FILENAME, encoding="UTF-8", xml_declaration=True)
        print("✅ 所有任务完成！")
    else:
        print("\n⚠️ 警告: 生成的内容为空，未保存文件。")
