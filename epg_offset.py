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
        "m3u": "http://m3u4u.com/m3u/4z2xnj6xk6t2mr4gnv15",
        "epg": "https://epg.pw/xmltv/epg_CN.xml",
        "offset": -13
    },
    # 可以在下面复制添加更多源...
    {
        "name": "香港频道",
        "m3u": "http://m3u4u.com/m3u/dqr6ywqveqsm1p54yx1w",
        "epg": "https://epg.pw/xmltv/epg_HK.xml",
        "offset": -13
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

def process_and_merge(source_conf, master_root, seen_channel_ids):
    """
    处理单个源，并将结果合并到 master_root 中
    :param source_conf: 单个源的配置字典
    :param master_root: 主 XML 根节点
    :param seen_channel_ids: 已添加过的频道 ID 集合 (用于去重)
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

    # 2. 获取 EPG
    epg_data = get_content(source_conf['epg'])
    if not epg_data:
        print("  - 跳过此源 (EPG 下载失败)")
        return

    print("  - 正在解析 XMLTV 数据...")
    try:
        # 有些 EPG 可能编码奇特，尝试容错
        try:
            epg_root = ET.fromstring(epg_data)
        except:
            epg_root = ET.fromstring(epg_data.decode('utf-8', errors='ignore'))
    except ET.ParseError as e:
        print(f"  - XML 解析失败: {e}")
        return

    offset_hours = source_conf.get('offset', 0)
    time_format = "%Y%m%d%H%M%S"
    
    added_channels = 0
    added_programmes = 0

    print(f"  - 正在合并数据 (时差偏移: {offset_hours} 小时)...")

    # 3. 遍历并合并
    for child in epg_root:
        # --- 处理频道信息 <channel> ---
        if child.tag == 'channel':
            c_id = child.get('id')
            # 只有当 ID 在 M3U 里，且之前没添加过这个频道信息，才添加
            if c_id in valid_ids:
                if c_id not in seen_channel_ids:
                    master_root.append(child)
                    seen_channel_ids.add(c_id)
                    added_channels += 1
                else:
                    # 如果频道 ID 已经存在，就不重复添加 <channel> 标签了
                    # 但不影响后面添加该频道的 <programme>
                    pass
        
        # --- 处理节目单 <programme> ---
        elif child.tag == 'programme':
            p_id = child.get('channel')
            if p_id in valid_ids:
                # 复制节点，以免修改原始对象影响内存（虽然这里是一次性的）
                # 这里直接修改 child 也可以
                
                # 修改 start 和 stop 时间
                modified_time = False
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
                                modified_time = True
                            except ValueError:
                                pass
                
                master_root.append(child)
                added_programmes += 1

    print(f"  - 本源处理完成: 新增频道 {added_channels} 个, 节目单 {added_programmes} 条")

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
