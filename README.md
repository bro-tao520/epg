# IPTV / XMLTV EPG 自动更新服务

[![EPG Update](https://github.com/bro-tao520/epg/actions/workflows/update_epg.yml/badge.svg)](https://github.com/bro-tao520/epg/actions/workflows/update_epg.yml)
![License](https://img.shields.io/github/license/bro-tao520/epg?color=blue&style=flat-square)

本项目是一个基于 GitHub Actions 的自动 EPG（电子节目指南）生成与更新工具。通过 Python 脚本自动获取、调整时区偏移并精简 EPG 数据，为 IPTV 播放器（如 Tivimate、Perfect Player、PotPlayer 等）提供稳定、准确的 XMLTV 格式节目单。

## 🚀 项目特点

- **自动化运行**：利用 GitHub Actions 定时自动更新，无需自备服务器。
- **时区修正**：内置 `epg_offset.py` 脚本，支持对节目时间进行偏移调整（解决部分源时区不对、节目对不上的问题）。
- **精简高效**：生成 `slim_fixed_epg.xml` 紧凑版文件，剔除冗余信息，加载速度更快，节省播放器流量。
- **即拿即用**：直接提供可供 IPTV 客户端订阅的 XML 链接。

## 📁 文件结构说明

- **`.github/workflows/update_epg.yml`**：GitHub Actions 工作流配置文件，负责定时唤醒并执行更新任务。
- **`epg_offset.py`**：核心 Python 脚本，用于下载原始 EPG 数据、计算/修正时间偏差，并过滤精简数据。
- **`slim_fixed_epg.xml`**：最终生成的 XMLTV 格式电子节目指南文件（订阅源）。

## 🛠️ 使用方法

### 1. 直接订阅（推荐）
如果你只需要使用现成的 EPG 节目单，可以直接在支持 XMLTV 的 IPTV 播放器中导入以下链接：

```text
https://raw.githubusercontent.com/bro-tao520/epg/main/slim_fixed_epg.xml
```
*(注：如果国内网络访问 raw.githubusercontent 困难，可使用 jsDelivr 等 CDN 加速)*

### 2. 自行 Fork 部署修改
如果你想修改数据源或调整时区偏移参数：

1. **Fork 本仓库** 到你自己的 GitHub 账号下。
2. **修改脚本**：根据需求修改 `epg_offset.py` 中的数据源 URL 或时间偏移量（Offset）。
3. **启用 Actions**：在你的仓库页面，点击 `Actions` 标签页，手动允许工作流运行。
4. **定时更新**：工作流将按照 `update_epg.yml` 中配置的 Cron 定时任务自动运行，并将最新的 `slim_fixed_epg.xml` 推送到你的仓库。

## ⚙️ 技术栈

- **Language**: Python 3.x
- **CI/CD**: GitHub Actions
- **Format**: XMLTV 标准

## 🤝 贡献与反馈

欢迎提交 Issue 或 Pull Request 来完善此项目！如果你觉得这个项目对你有帮助，请给它点一个 ⭐ **Star**！
