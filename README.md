<div align="center">

# 🔍 DiskLens

**轻量级终端磁盘空间智能分析引擎**

*Lightweight Terminal Disk Space Intelligent Analysis Engine*

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey.svg)]()
[![Zero Dependencies](https://img.shields.io/badge/Zero-Dependencies-orange.svg)]()

[English](#english) | [简体中文](#简体中文) | [繁體中文](#繁體中文)

</div>

---

<a name="简体中文"></a>
## 🎉 项目介绍

**DiskLens** 是一款零依赖、轻量级的终端磁盘空间分析工具，帮助开发者快速识别磁盘空间占用情况，发现大文件、重复文件，并提供可视化的分析报告。

### 💡 灵感来源

在日常开发中，我们经常遇到磁盘空间不足的问题，但传统工具要么过于复杂，要么需要安装大量依赖。DiskLens 旨在提供一个**开箱即用、零配置、纯Python**的解决方案。

### ✨ 核心特性

- 🚀 **零依赖设计** - 纯Python标准库实现，无需安装任何第三方包
- 🎨 **彩色终端输出** - 基于文件大小的智能颜色编码，一目了然
- 📊 **可视化图表** - ASCII条形图展示目录和扩展名分布
- 🌲 **树形结构浏览** - 支持层级化目录展示，可配置深度和大小过滤
- 🔍 **重复文件检测** - 快速模式和深度Hash模式双重检测
- 📈 **JSON报告导出** - 支持导出详细分析报告供进一步处理
- ⚡ **多线程扫描** - 并行目录扫描，提升分析速度
- 🔧 **高度可配置** - 灵活的排除模式、大小阈值等配置选项

### 🚀 快速开始

#### 环境要求

- Python 3.7 或更高版本
- Linux / macOS / Windows

#### 安装

**方式一：直接下载使用**

```bash
# 克隆仓库
git clone https://github.com/gitstq/DiskLens.git
cd DiskLens

# 直接运行
python3 disklens.py
```

**方式二：通过 pip 安装**

```bash
pip install disklens
```

**方式三：系统级安装**

```bash
# 安装到系统
python3 setup.py install

# 或开发模式安装
pip install -e .
```

#### 基本使用

```bash
# 分析当前目录
disklens

# 分析指定目录
disklens /path/to/directory

# 显示前30个大文件
disklens -t 30 /home

# 树形结构显示（只显示大于1MB的文件/目录）
disklens --tree --tree-min-size 1M /var/log

# 查找重复文件
disklens --dupes ~/Downloads

# 深度重复检测（计算文件Hash）
disklens --deep-dupes ~/Documents

# 按扩展名分析
disklens --ext /projects

# 导出JSON报告
disklens --json report.json /data
```

### 📖 详细使用指南

#### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `path` | 要分析的目录路径 | `disklens /home` |
| `-t, --top` | 显示前N个大文件 | `disklens -t 50` |
| `--tree` | 以树形结构显示 | `disklens --tree` |
| `--tree-depth` | 树形显示最大深度 | `disklens --tree --tree-depth 5` |
| `--tree-min-size` | 树形显示最小大小 | `disklens --tree --tree-min-size 10M` |
| `--dupes` | 快速查找重复文件 | `disklens --dupes` |
| `--deep-dupes` | 深度重复检测 | `disklens --deep-dupes` |
| `--ext` | 按扩展名分析 | `disklens --ext` |
| `--json` | 导出JSON报告 | `disklens --json report.json` |
| `--no-color` | 禁用颜色输出 | `disklens --no-color` |
| `--exclude` | 排除模式 | `disklens --exclude node_modules .git` |

#### 输出示例

```
============================================================
  DiskLens v1.0.0 - 磁盘空间智能分析引擎
============================================================

📁 扫描目录: /home/user/projects

📊 扫描结果:
   总文件数: 1,234
   总大小:   2.45 GB
   平均大小: 2.03 MB

🔥 最大的 20 个文件:
    1. 512.50 MB     .../node_modules/package.zip
    2. 256.30 MB     .../build/output.bin
    ...

📎 按扩展名分析:

文件扩展名分布 (Top 15)
============================================================
.js (523 files)          │███████████████████ 1.23 GB
.zip (12 files)          │█████████████ 890.45 MB
.png (234 files)         │██████ 234.56 MB

📂 子目录大小 (Top 15):
node_modules             │███████████████████ 1.50 GB
build                    │█████████████ 800.45 MB
src                      │██████ 150.20 MB

============================================================
分析完成!
```

### 💡 设计思路与迭代规划

#### 技术选型

- **纯Python标准库**：确保零依赖，兼容所有Python环境
- **多线程扫描**：利用`concurrent.futures`实现并行目录扫描
- **ANSI颜色代码**：原生支持彩色终端输出
- **模块化设计**：功能拆分为独立函数，易于扩展

#### 后续迭代计划

- [ ] 交互式TUI界面（使用curses/rich）
- [ ] 实时监控模式（监听文件变化）
- [ ] 云存储分析（S3、OSS等）
- [ ] 磁盘清理建议（基于AI分析）
- [ ] Web可视化报告

### 📦 打包与部署

#### 构建可执行文件

```bash
# 使用 PyInstaller
pip install pyinstaller
pyinstaller --onefile --name disklens disklens.py

# 可执行文件将在 dist/ 目录生成
```

#### 创建系统包

```bash
# Debian/Ubuntu
dpkg-buildpackage -us -uc

# RPM 包
python3 setup.py bdist_rpm
```

### 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 📄 开源协议

本项目基于 [MIT](LICENSE) 协议开源。

---

<a name="繁體中文"></a>
## 🎉 專案介紹

**DiskLens** 是一款零依賴、輕量級的終端磁碟空間分析工具，幫助開發者快速識別磁碟空間佔用情況，發現大檔案、重複檔案，並提供視覺化的分析報告。

### ✨ 核心特性

- 🚀 **零依賴設計** - 純Python標準庫實現，無需安裝任何第三方套件
- 🎨 **彩色終端輸出** - 基於檔案大小的智慧顏色編碼，一目了然
- 📊 **視覺化圖表** - ASCII條形圖展示目錄和副檔名分布
- 🌲 **樹形結構瀏覽** - 支援層級化目錄展示，可配置深度和大小過濾
- 🔍 **重複檔案檢測** - 快速模式和深度Hash模式雙重檢測
- 📈 **JSON報告匯出** - 支援匯出詳細分析報告供進一步處理
- ⚡ **多執行緒掃描** - 並行目錄掃描，提升分析速度

### 🚀 快速開始

```bash
# 克隆倉庫
git clone https://github.com/gitstq/DiskLens.git
cd DiskLens

# 直接運行
python3 disklens.py

# 或安裝
pip install disklens
```

### 📖 使用範例

```bash
# 分析當前目錄
disklens

# 顯示前30個大檔案
disklens -t 30 /home

# 樹形結構顯示
disklens --tree /var/log

# 查找重複檔案
disklens --dupes ~/Downloads

# 匯出JSON報告
disklens --json report.json /data
```

---

<a name="english"></a>
## 🎉 Introduction

**DiskLens** is a zero-dependency, lightweight terminal disk space analysis tool that helps developers quickly identify disk space usage, discover large files and duplicates, and provide visual analysis reports.

### ✨ Key Features

- 🚀 **Zero Dependencies** - Pure Python standard library, no third-party packages required
- 🎨 **Colorful Terminal Output** - Smart color coding based on file size
- 📊 **Visual Charts** - ASCII bar charts for directory and extension distribution
- 🌲 **Tree Structure View** - Hierarchical directory display with configurable depth and size filters
- 🔍 **Duplicate Detection** - Fast mode and deep Hash mode for finding duplicates
- 📈 **JSON Report Export** - Export detailed analysis reports for further processing
- ⚡ **Multi-threaded Scanning** - Parallel directory scanning for improved performance

### 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/gitstq/DiskLens.git
cd DiskLens

# Run directly
python3 disklens.py

# Or install via pip
pip install disklens
```

### 📖 Usage Examples

```bash
# Analyze current directory
disklens

# Show top 30 largest files
disklens -t 30 /home

# Tree view
disklens --tree /var/log

# Find duplicate files
disklens --dupes ~/Downloads

# Export JSON report
disklens --json report.json /data
```

### 📄 License

This project is licensed under the [MIT](LICENSE) License.

---

<div align="center">

**Made with ❤️ by gitstq**

</div>
