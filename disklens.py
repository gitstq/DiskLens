#!/usr/bin/env python3
"""
DiskLens - 轻量级终端磁盘空间智能分析引擎
Lightweight Terminal Disk Space Intelligent Analysis Engine

Author: gitstq
License: MIT
"""

import os
import sys
import argparse
import json
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

__version__ = "1.0.0"

# ANSI颜色代码
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"
    WHITE = "\033[97m"

# 文件大小阈值（用于颜色编码）
SIZE_THRESHOLDS = [
    (1024 ** 4, Colors.RED, "TB"),      # >= 1TB
    (1024 ** 3, Colors.MAGENTA, "GB"),  # >= 1GB
    (1024 ** 2, Colors.YELLOW, "MB"),   # >= 1MB
    (1024, Colors.GREEN, "KB"),         # >= 1KB
]


def format_size(size_bytes: int, use_color: bool = True) -> str:
    """将字节大小格式化为人类可读的字符串"""
    if size_bytes == 0:
        return "0 B"
    
    for threshold, color, unit in SIZE_THRESHOLDS:
        if size_bytes >= threshold:
            value = size_bytes / threshold
            formatted = f"{value:.2f} {unit}" if value < 100 else f"{value:.1f} {unit}"
            if use_color:
                return f"{color}{formatted}{Colors.RESET}"
            return formatted
    
    formatted = f"{size_bytes} B"
    if use_color and size_bytes > 0:
        return f"{Colors.GREEN}{formatted}{Colors.RESET}"
    return formatted


def get_size_color(size_bytes: int) -> str:
    """根据文件大小返回对应的颜色代码"""
    for threshold, color, _ in SIZE_THRESHOLDS:
        if size_bytes >= threshold:
            return color
    return Colors.GREEN


def scan_directory(path: str, exclude_patterns: List[str] = None, 
                   follow_symlinks: bool = False) -> Tuple[int, int, List[Dict]]:
    """
    扫描目录并返回总大小、文件数量和文件列表
    
    Returns:
        (total_size, file_count, file_list)
    """
    total_size = 0
    file_count = 0
    file_list = []
    
    exclude_patterns = exclude_patterns or []
    
    try:
        for root, dirs, files in os.walk(path, followlinks=follow_symlinks):
            # 过滤排除的目录
            dirs[:] = [d for d in dirs if not any(
                pattern in os.path.join(root, d) for pattern in exclude_patterns
            )]
            
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    
                    # 跳过符号链接
                    if not follow_symlinks and os.path.islink(file_path):
                        continue
                    
                    # 检查排除模式
                    if any(pattern in file_path for pattern in exclude_patterns):
                        continue
                    
                    stat = os.stat(file_path)
                    size = stat.st_size
                    total_size += size
                    file_count += 1
                    
                    file_list.append({
                        'path': file_path,
                        'size': size,
                        'name': file,
                        'dir': root
                    })
                    
                except (OSError, PermissionError, FileNotFoundError):
                    continue
                    
    except (OSError, PermissionError) as e:
        print(f"{Colors.RED}Error scanning {path}: {e}{Colors.RESET}", file=sys.stderr)
    
    return total_size, file_count, file_list


def scan_directory_parallel(path: str, max_workers: int = 4,
                            exclude_patterns: List[str] = None) -> Tuple[int, int, List[Dict]]:
    """并行扫描目录"""
    total_size = 0
    file_count = 0
    file_list = []
    
    exclude_patterns = exclude_patterns or []
    subdirs = []
    
    try:
        # 首先获取直接子目录
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_symlink():
                        continue
                    if entry.is_dir():
                        if not any(pattern in entry.path for pattern in exclude_patterns):
                            subdirs.append(entry.path)
                    elif entry.is_file():
                        stat = entry.stat()
                        size = stat.st_size
                        total_size += size
                        file_count += 1
                        file_list.append({
                            'path': entry.path,
                            'size': size,
                            'name': entry.name,
                            'dir': path
                        })
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError):
        pass
    
    # 并行扫描子目录
    if subdirs:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(scan_directory, subdir, exclude_patterns): subdir 
                      for subdir in subdirs}
            
            for future in as_completed(futures):
                try:
                    size, count, files = future.result()
                    total_size += size
                    file_count += count
                    file_list.extend(files)
                except Exception:
                    continue
    
    return total_size, file_count, file_list


def analyze_by_extension(file_list: List[Dict]) -> Dict[str, Tuple[int, int]]:
    """按文件扩展名分析"""
    ext_stats = defaultdict(lambda: [0, 0])  # [total_size, count]
    
    for file_info in file_list:
        ext = Path(file_info['path']).suffix.lower() or '(no extension)'
        ext_stats[ext][0] += file_info['size']
        ext_stats[ext][1] += 1
    
    return dict(ext_stats)


def find_duplicate_files(file_list: List[Dict], quick_mode: bool = True) -> Dict[str, List[str]]:
    """
    查找重复文件
    
    Args:
        quick_mode: 如果为True，只比较文件名和大小；否则比较文件内容hash
    """
    duplicates = defaultdict(list)
    
    if quick_mode:
        # 快速模式：按文件名+大小分组
        file_map = defaultdict(list)
        for file_info in file_list:
            key = (file_info['name'], file_info['size'])
            file_map[key].append(file_info['path'])
        
        for key, paths in file_map.items():
            if len(paths) > 1:
                duplicates[f"{key[0]} ({format_size(key[1], False)})"] = paths
    else:
        # 深度模式：计算文件hash
        size_map = defaultdict(list)
        for file_info in file_list:
            size_map[file_info['size']].append(file_info['path'])
        
        # 只处理大小相同的文件
        for size, paths in size_map.items():
            if len(paths) < 2:
                continue
            
            hash_map = defaultdict(list)
            for path in paths:
                try:
                    file_hash = hashlib.md5(open(path, 'rb').read()).hexdigest()
                    hash_map[file_hash].append(path)
                except (OSError, PermissionError):
                    continue
            
            for file_hash, dup_paths in hash_map.items():
                if len(dup_paths) > 1:
                    duplicates[f"Hash: {file_hash[:16]}... ({format_size(size, False)})"] = dup_paths
    
    return dict(duplicates)


def find_large_files(file_list: List[Dict], top_n: int = 20) -> List[Dict]:
    """查找最大的文件"""
    return sorted(file_list, key=lambda x: x['size'], reverse=True)[:top_n]


def analyze_directory_sizes(file_list: List[Dict]) -> Dict[str, int]:
    """分析各目录的大小"""
    dir_sizes = defaultdict(int)
    
    for file_info in file_list:
        dir_sizes[file_info['dir']] += file_info['size']
    
    return dict(dir_sizes)


def print_bar_chart(data: List[Tuple[str, int]], max_width: int = 50, 
                    title: str = "", use_color: bool = True):
    """打印ASCII条形图"""
    if not data:
        return
    
    if title:
        print(f"\n{Colors.BOLD}{title}{Colors.RESET}")
        print("=" * 60)
    
    max_value = max(v for _, v in data)
    max_label_len = max(len(str(k)) for k, _ in data)
    
    for label, value in data:
        bar_len = int((value / max_value) * max_width) if max_value > 0 else 0
        bar = "█" * bar_len
        
        if use_color:
            color = get_size_color(value)
            bar = f"{color}{bar}{Colors.RESET}"
        
        label_str = str(label).ljust(max_label_len)
        value_str = format_size(value, use_color)
        
        print(f"{label_str} │{bar} {value_str}")


def print_tree(path: str, prefix: str = "", max_depth: int = 3, 
               current_depth: int = 0, min_size: int = 1024*1024):
    """打印目录树形结构（只显示大于min_size的目录）"""
    if current_depth >= max_depth:
        return
    
    try:
        entries = []
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_symlink():
                        continue
                    if entry.is_dir():
                        size, _, _ = scan_directory(entry.path)
                        if size >= min_size:
                            entries.append((entry.name, size, True))
                    elif entry.is_file():
                        stat = entry.stat()
                        if stat.st_size >= min_size:
                            entries.append((entry.name, stat.st_size, False))
                except (OSError, PermissionError):
                    continue
        
        # 按大小排序
        entries.sort(key=lambda x: x[1], reverse=True)
        
        for i, (name, size, is_dir) in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            
            size_str = format_size(size, True)
            suffix = "/" if is_dir else ""
            
            print(f"{prefix}{connector}{name}{suffix} ({size_str})")
            
            if is_dir:
                extension = "    " if is_last else "│   "
                print_tree(os.path.join(path, name), prefix + extension, 
                          max_depth, current_depth + 1, min_size)
                          
    except (OSError, PermissionError):
        pass


def generate_json_report(file_list: List[Dict], output_path: str):
    """生成JSON格式的详细报告"""
    report = {
        'summary': {
            'total_files': len(file_list),
            'total_size': sum(f['size'] for f in file_list),
            'total_size_formatted': format_size(sum(f['size'] for f in file_list), False)
        },
        'largest_files': [
            {
                'path': f['path'],
                'size': f['size'],
                'size_formatted': format_size(f['size'], False)
            }
            for f in find_large_files(file_list, 50)
        ],
        'by_extension': {
            ext: {
                'size': size,
                'size_formatted': format_size(size, False),
                'count': count
            }
            for ext, (size, count) in analyze_by_extension(file_list).items()
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n{Colors.GREEN}✓ Report saved to: {output_path}{Colors.RESET}")


def main():
    parser = argparse.ArgumentParser(
        description="DiskLens - 轻量级终端磁盘空间智能分析引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  disklens                    # 分析当前目录
  disklens /path/to/dir       # 分析指定目录
  disklens -t 30 /home        # 显示前30个大文件
  disklens --tree /var        # 树形结构显示
  disklens --dupes ~/Downloads # 查找重复文件
  disklens --json report.json # 导出JSON报告
        """
    )
    
    parser.add_argument('path', nargs='?', default='.', 
                       help='要分析的目录路径 (默认: 当前目录)')
    parser.add_argument('-t', '--top', type=int, default=20,
                       help='显示前N个大文件 (默认: 20)')
    parser.add_argument('--tree', action='store_true',
                       help='以树形结构显示目录')
    parser.add_argument('--tree-depth', type=int, default=3,
                       help='树形显示的最大深度 (默认: 3)')
    parser.add_argument('--tree-min-size', type=str, default='1M',
                       help='树形显示的最小文件大小 (默认: 1M)')
    parser.add_argument('--dupes', '--duplicates', action='store_true',
                       help='查找重复文件')
    parser.add_argument('--deep-dupes', action='store_true',
                       help='深度查找重复文件（计算文件hash，较慢）')
    parser.add_argument('--ext', '--extensions', action='store_true',
                       help='按文件扩展名分析')
    parser.add_argument('--json', metavar='FILE',
                       help='导出JSON报告到指定文件')
    parser.add_argument('--no-color', action='store_true',
                       help='禁用颜色输出')
    parser.add_argument('--exclude', nargs='+', default=[],
                       help='排除的模式（如: node_modules .git）')
    parser.add_argument('-v', '--version', action='version', 
                       version=f'DiskLens {__version__}')
    
    args = parser.parse_args()
    
    # 禁用颜色
    if args.no_color:
        global Colors
        for attr in dir(Colors):
            if not attr.startswith('_'):
                setattr(Colors, attr, '')
    
    # 解析最小大小
    min_size = 1024 * 1024  # 默认1MB
    size_str = args.tree_min_size.upper()
    if size_str.endswith('K'):
        min_size = int(size_str[:-1]) * 1024
    elif size_str.endswith('M'):
        min_size = int(size_str[:-1]) * 1024 * 1024
    elif size_str.endswith('G'):
        min_size = int(size_str[:-1]) * 1024 * 1024 * 1024
    else:
        try:
            min_size = int(size_str)
        except ValueError:
            pass
    
    target_path = os.path.abspath(args.path)
    
    if not os.path.exists(target_path):
        print(f"{Colors.RED}Error: Path does not exist: {target_path}{Colors.RESET}", 
              file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isdir(target_path):
        print(f"{Colors.RED}Error: Not a directory: {target_path}{Colors.RESET}", 
              file=sys.stderr)
        sys.exit(1)
    
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  DiskLens v{__version__} - 磁盘空间智能分析引擎{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"\n📁 扫描目录: {Colors.BOLD}{target_path}{Colors.RESET}")
    print(f"⏳ 正在扫描...", end='', flush=True)
    
    # 扫描目录
    exclude_patterns = args.exclude + ['.git', 'node_modules', '__pycache__', '.venv']
    total_size, file_count, file_list = scan_directory(target_path, exclude_patterns)
    
    print(f"\r{' '*20}\r", end='')
    
    # 基本信息
    print(f"\n{Colors.BOLD}📊 扫描结果:{Colors.RESET}")
    print(f"   总文件数: {Colors.CYAN}{file_count:,}{Colors.RESET}")
    print(f"   总大小:   {Colors.CYAN}{format_size(total_size)}{Colors.RESET}")
    
    if file_count > 0:
        avg_size = total_size / file_count
        print(f"   平均大小: {format_size(int(avg_size))}")
    
    # 树形显示
    if args.tree:
        print(f"\n{Colors.BOLD}🌲 目录结构 (>{args.tree_min_size}):{Colors.RESET}")
        print(f"{Colors.GRAY}{target_path}{Colors.RESET}")
        print_tree(target_path, max_depth=args.tree_depth, min_size=min_size)
    
    # 大文件分析
    if args.top > 0 and file_list:
        print(f"\n{Colors.BOLD}🔥 最大的 {args.top} 个文件:{Colors.RESET}")
        large_files = find_large_files(file_list, args.top)
        for i, file_info in enumerate(large_files, 1):
            size_str = format_size(file_info['size'])
            path_display = file_info['path']
            if len(path_display) > 50:
                path_display = "..." + path_display[-47:]
            print(f"   {i:2d}. {size_str:<15} {path_display}")
    
    # 扩展名分析
    if args.ext:
        print(f"\n{Colors.BOLD}📎 按扩展名分析:{Colors.RESET}")
        ext_stats = analyze_by_extension(file_list)
        sorted_exts = sorted(ext_stats.items(), key=lambda x: x[1][0], reverse=True)[:15]
        
        chart_data = []
        for ext, (size, count) in sorted_exts:
            label = f"{ext} ({count} files)"
            chart_data.append((label, size))
        
        print_bar_chart(chart_data, title="文件扩展名分布 (Top 15)")
    
    # 目录大小分析
    if not args.tree:
        print(f"\n{Colors.BOLD}📂 子目录大小 (Top 15):{Colors.RESET}")
        dir_sizes = analyze_directory_sizes(file_list)
        sorted_dirs = sorted(dir_sizes.items(), key=lambda x: x[1], reverse=True)[:15]
        
        chart_data = []
        for dir_path, size in sorted_dirs:
            rel_path = os.path.relpath(dir_path, target_path)
            if rel_path == '.':
                rel_path = '(root)'
            if len(rel_path) > 30:
                rel_path = rel_path[:27] + "..."
            chart_data.append((rel_path, size))
        
        print_bar_chart(chart_data)
    
    # 重复文件检测
    if args.dupes or args.deep_dupes:
        print(f"\n{Colors.BOLD}🔍 查找重复文件...{Colors.RESET}")
        duplicates = find_duplicate_files(file_list, quick_mode=not args.deep_dupes)
        
        if duplicates:
            print(f"\n{Colors.YELLOW}⚠️ 发现 {len(duplicates)} 组重复文件:{Colors.RESET}")
            for key, paths in list(duplicates.items())[:10]:  # 只显示前10组
                print(f"\n   {Colors.CYAN}{key}{Colors.RESET}")
                for path in paths:
                    print(f"      - {path}")
            
            if len(duplicates) > 10:
                print(f"\n   ... 还有 {len(duplicates) - 10} 组重复文件")
            
            # 计算可节省空间
            wasted_space = sum(
                sum(os.path.getsize(p) for p in paths[1:])
                for paths in duplicates.values()
            )
            print(f"\n{Colors.GREEN}💡 删除重复文件可节省: {format_size(wasted_space)}{Colors.RESET}")
        else:
            print(f"\n{Colors.GREEN}✓ 未发现重复文件{Colors.RESET}")
    
    # 导出JSON报告
    if args.json:
        generate_json_report(file_list, args.json)
    
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.GRAY}分析完成!{Colors.RESET}")


if __name__ == '__main__':
    main()
