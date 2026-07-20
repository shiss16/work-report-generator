"""Markdown 文件输出"""

import os


def save_to_local(content: str, output_path: str) -> str:
    """写入本地 MD 文件，自动创建目录，返回文件路径"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path