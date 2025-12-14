import xml.etree.ElementTree as ET
import requests
import gzip
import re
from datetime import datetime, timedelta

# ================= 配置区域 =================

# 1. 你的 M3U 播放列表链接 (用来提取需要保留的频道 ID)
M3U_URL = "http://m3u4u.com/m3u/4z2xnj6xk6t2mr4gnv15"

# 2. 你的第三方 EPG 链接 (支持 .xml 或 .xml.gz)
EPG_URL = "https://epg.pw/xmltv/epg_CN.xml"

# 3. 你想要偏移的小时数 (例如 -5)
OFFSET_HOURS = -8

# 4. 输出文件名
OUTPUT_FILENAME = "slim_fixed_epg.xml"

# ===========================================

def get_content(url):
    """下载内容，自动处理 gzip"""
    print(f"正在下载: {url} ...")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        if url.endswith('.gz'):
            return gzip.decompress(response.content)
        else:
            return response.content
    except Exception as e:
        print(f"下载失败: {e}")
        return None

def extract_tvg_ids(m3u_content):
    """从 M3U 内容中提取所有的 tvg-id"""
    print("正在解析 M3U 播放列表...")
    text = m3u_content.decode('utf-8', errors='ignore')
    # 正则匹配 tvg-id="xxx"
    ids = set(re.findall(r'tvg-id="([^"]+)"', text))
    print(f"M3U 中共找到 {len(ids)} 个唯一的频道 ID (tvg-id)。")
    return ids

def process_epg(epg_content, valid_ids):
    """解析 EPG，过滤频道，并修改时间"""
    print("正在解析 XMLTV 数据 (这可能需要一点时间)...")
    try:
        original_root = ET.fromstring(epg_content)
    except ET.ParseError as e:
        print(f"XML 解析失败: {e}")
        return

    # 创建一个新的 XML 根节点
    new_root = ET.Element("tv")
    # 复制原始根节点的属性 (如 generator-info-name)
    for k, v in original_root.attrib.items():
        new_root.set(k, v)

    channel_count = 0
    programme_count = 0
    time_format = "%Y%m%d%H%M%S"

    print(f"正在过滤数据并应用 {OFFSET_HOURS} 小时偏移...")

    # 遍历原始 XML 的所有子节点
    for child in original_root:
        # 1. 处理频道定义 <channel id="...">
        if child.tag == 'channel':
            c_id = child.get('id')
            if c_id in valid_ids:
                new_root.append(child) # 直接复制节点
                channel_count += 1
        
        # 2. 处理节目单 <programme channel="...">
        elif child.tag == 'programme':
            p_id = child.get('channel')
            if p_id in valid_ids:
                # 只有 ID 在白名单里，才进行时间计算和保留
                
                # 修改 start 和 stop 时间
                modified = False
                for attr in ['start', 'stop']:
                    if attr in child.attrib:
                        original_time_str = child.attrib[attr]
                        # 提取前14位时间
                        time_part = original_time_str[:14]
                        timezone_part = original_time_str[14:]
                        
                        try:
                            dt = datetime.strptime(time_part, time_format)
                            new_dt = dt + timedelta(hours=OFFSET_HOURS)
                            # 硬写入新时间，保留原后缀
                            new_time_str = new_dt.strftime(time_format) + timezone_part
                            child.set(attr, new_time_str)
                            modified = True
                        except ValueError:
                            pass
                
                if modified:
                    new_root.append(child)
                    programme_count += 1

    print(f"处理完成！")
    print(f"保留频道数: {channel_count}")
    print(f"保留节目单条目: {programme_count}")

    # 保存文件
    tree = ET.ElementTree(new_root)
    tree.write(OUTPUT_FILENAME, encoding="UTF-8", xml_declaration=True)
    print(f"文件已生成: {OUTPUT_FILENAME}")

if __name__ == "__main__":
    # 1. 获取 M3U
    m3u_data = get_content(M3U_URL)
    
    if m3u_data:
        # 2. 提取白名单 ID
        valid_ids = extract_tvg_ids(m3u_data)
        
        if valid_ids:
            # 3. 获取 EPG
            epg_data = get_content(EPG_URL)
            
            if epg_data:
                # 4. 过滤 + 偏移 + 保存
                process_epg(epg_data, valid_ids)
