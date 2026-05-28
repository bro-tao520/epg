# 📺 IPTV EPG Slimmer & Auto-Updater

[![EPG Update](https://github.com/bro-tao520/epg/actions/workflows/update_epg.yml/badge.svg)](https://github.com/bro-tao520/epg/actions/workflows/update_epg.yml)
![License](https://img.shields.io/github/license/bro-tao520/epg?color=blue&style=flat-square)

A lightweight, automated EPG (Electronic Program Guide) generator and timezone fixer powered by Python and GitHub Actions.

## 💡 Why do you need this? (The Pain Point)

Public EPG XML files are usually massive (often containing thousands of channels and weighing tens of megabytes). Loading them directly into IPTV players like Tivimate, Perfect Player, or PotPlayer can cause:
- 🐌 Extremely slow loading times
- 💥 High memory usage and app crashes
- 🕒 Incorrect program schedules due to wrong timezones

**This script solves these problems by:**
1. **M3U-based Filtering**: It reads your personal M3U playlist and extracts **ONLY** the EPG data for the channels you actually have.
2. **Timezone Correction**: It automatically adjusts the time offset for specific sources to ensure your TV guide is perfectly synced.
3. **Ultra-Slim Output**: Generates a lightweight `slim_fixed_epg.xml` (usually just a few hundred KBs) for lightning-fast loading.

## 🚀 Features

- **Zero Server Cost**: Fully automated using GitHub Actions. No need to rent a VPS.
- **Tailored for You**: Extracts only what you need, discarding 99% of useless data.
- **Timezone Fixer**: Easily fix EPGs that are hours ahead or behind.
- **XMLTV Standard**: Fully compatible with almost all modern IPTV clients.

## 🛠️ How to build your own EPG service?

If you have your own M3U list and a public EPG source, you can set up your own auto-updating service in 3 simple steps:

### Step 1: Fork this repository
Click the `Fork` button at the top right of this page to copy this project to your own GitHub account.

### Step 2: Configure your sources
Edit the `epg_offset.py` file in your forked repository. Find the `SOURCES` array and replace it with your own M3U and EPG links:

```python
SOURCES = [
    {
        "name": "My Custom Channels",
        "m3u": "https://your-domain.com/your-playlist.m3u",  # Your M3U playlist link
        "epg": "https://epg.pw/xmltv/epg_CN.xml",            # The massive public EPG link
        "offset": -8                                         # Timezone offset (adjust as needed)
    }
]
```
*(Note: You can add multiple dictionaries to the `SOURCES` array to merge different EPGs.)*

### Step 3: Enable GitHub Actions
1. Go to the **Actions** tab in your repository.
2. Click **"I understand my workflows, go ahead and enable them"**.
3. The system will now automatically run every day (based on the cron schedule in `.github/workflows/update_epg.yml`) and generate your personalized, ultra-slim `slim_fixed_epg.xml`!

## 🔗 How to use the generated EPG?

Once the Action runs successfully, you can use the raw link of the generated XML file in your IPTV player. The link format is:

```text
https://raw.githubusercontent.com/<YOUR_GITHUB_USERNAME>/epg/main/slim_fixed_epg.xml
```
*(Replace `<YOUR_GITHUB_USERNAME>` with your actual GitHub username)*

## ⚙️ Tech Stack

- **Language**: Python 3.x
- **CI/CD**: GitHub Actions
- **Format**: XMLTV Standard

## 🤝 Contributing

Issues and Pull Requests are welcome! If you find this tool helpful in saving your IPTV player's memory, please give it a ⭐ **Star**!

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
