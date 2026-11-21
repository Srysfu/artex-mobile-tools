#!/usr/bin/env python3
"""扫描 bin/ 目录，生成 tools.json。

换工具或换版本后重跑本脚本，再把 tools.json 和 bin/ 一起提交。
url 里的 tag 需要和实际 Release 的 tag 对上。
"""
import hashlib
import json
import os
import sys

TAG = sys.argv[1] if len(sys.argv) > 1 else "tools-v1"
REPO = "Srysfu/artex-mobile-tools"

# name -> (version, description, category)
META = {}


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_dir = os.path.join(root, "bin")
    if not os.path.isdir(bin_dir):
        sys.exit(f"找不到 {bin_dir}")

    tools = []
    for name in sorted(os.listdir(bin_dir)):
        path = os.path.join(bin_dir, name)
        if not os.path.isfile(path):
            continue
        ver, desc, cat = META.get(name, ("", "", "other"))
        tools.append({
            "name": name,
            "version": ver,
            "description": desc,
            "category": cat,
            "size": os.path.getsize(path),
            "sha256": sha256_of(path),
            "url": f"https://github.com/{REPO}/releases/download/{TAG}/{name}",
        })

    out = {
        "version": 1,
        "updated": "2026-11-21",
        "note": "AArch64 静态 ELF，直接放 PATH 可执行。sha256 用于下载后完整性校验。",
        "tools": tools,
    }
    dest = os.path.join(root, "tools.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"已生成 {dest}：{len(tools)} 个工具，tag={TAG}")


if __name__ == "__main__":
    main()
