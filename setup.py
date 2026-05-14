#!/usr/bin/env python3
"""
DiskLens - 轻量级终端磁盘空间智能分析引擎
Setup script
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="disklens",
    version="1.0.0",
    author="gitstq",
    author_email="",
    description="轻量级终端磁盘空间智能分析引擎 - Lightweight Terminal Disk Space Intelligent Analysis Engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gitstq/DiskLens",
    py_modules=["disklens"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "disklens=disklens:main",
            "dl=disklens:main",
        ],
    },
    keywords="disk usage analyzer cli terminal tool storage cleanup",
    project_urls={
        "Bug Reports": "https://github.com/gitstq/DiskLens/issues",
        "Source": "https://github.com/gitstq/DiskLens",
    },
)
