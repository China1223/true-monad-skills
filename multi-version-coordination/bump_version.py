#!/usr/bin/env python3
"""版本号递增工具（双文件模式）—— Skills 共享版 V3。

本脚本同时存在于以下位置（内容完全相同）：
  .trae/skills/multi-version-coordination/bump_version.py
  deploy/maintenance/bump_version.py

加载 Skill 时，脚本自动同步到 deploy/maintenance/bump_version.py（仅高版本覆盖低版本）。
deploy/maintenance/version_counter.txt 是项目数据，不随 Skill 迁移。

## 双文件模式（V3 核心变更）

V2 使用单一 VERSION 文件，Git 和 Release 共写，容易冲突。
V3 拆分为两个文件，互不干扰：

  VERSION         — Git 代码版本号（--git 写入）
  RELEASE_VERSION — Release 发行版本号（--release 写入）

## 版本号格式

  VERSION 文件：
    v{major}.{minor}.{patch}-{Git日期MMDD}-{全局序号NNNN}
    示例：v8.0.4-0722-0042

  RELEASE_VERSION 文件：
    v{major}.{minor}.{patch}-{Git日期MMDD}-{全局序号NNNN}-{Release日期MMDD}{字母}
    示例：v8.0.4-0722-0042-0722A

规则：
- Git 日期和序号来自 VERSION 文件（--git 递增）
- Release 日期为当天，字母 A/B/C.../AA/AB...
- 新 Git 提交后，RELEASE_VERSION 旧值保留（不再追加）
- /api/version 优先返回 RELEASE_VERSION（若存在），否则返回 VERSION

用法：
  python bump_version.py --git --base 8.0.4        # Git：VERSION 序号+1
  python bump_version.py --release --base 8.0.4      # Release：写 RELEASE_VERSION
  python bump_version.py --show                       # 显示 VERSION + RELEASE_VERSION
  python bump_version.py --script-version             # 显示脚本版本号
"""

# ====================================================================
# 脚本版本号（固定位置，供同步逻辑读取比较）
# 格式：主.次.修订，如 "3.0.0"
# 修改脚本逻辑时递增此版本号，确保高版本自动同步到 deploy/maintenance/
# ====================================================================
SCRIPT_VERSION = "3.0.0"

import argparse
import shutil
import string
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# 自动判断运行位置，动态计算项目根目录
# 位置1: .trae/skills/multi-version-coordination/  → 上 3 级
# 位置2: deploy/maintenance/                       → 上 2 级
if SCRIPT_DIR.parent.name == "skills" and SCRIPT_DIR.parent.parent.name == ".trae":
    ROOT_DIR = SCRIPT_DIR.parent.parent.parent  # skill 目录
else:
    ROOT_DIR = SCRIPT_DIR.parent.parent  # deploy/maintenance/ 目录

VERSION_FILE = ROOT_DIR / "VERSION"
RELEASE_VERSION_FILE = ROOT_DIR / "RELEASE_VERSION"
MAINTENANCE_DIR = ROOT_DIR / "deploy" / "maintenance"
COUNTER_FILE = MAINTENANCE_DIR / "version_counter.txt"
TARGET_SCRIPT = MAINTENANCE_DIR / "bump_version.py"

# config.py 读取 v8.0.x/VERSION，需同步更新
_VERSION_DIRS = sorted(ROOT_DIR.glob("v8.0.*/VERSION"), key=lambda p: str(p))
# 同步 RELEASE_VERSION 到子版本目录
_RELEASE_VERSION_DIRS = sorted(ROOT_DIR.glob("v8.0.*/RELEASE_VERSION"), key=lambda p: str(p))


# ---- 脚本版本比较与自动同步 ----

def _parse_script_version(filepath: Path) -> tuple[int, ...]:
    """从脚本文件前 30 行中读取 SCRIPT_VERSION，返回 (major, minor, patch) 元组。

    读取失败返回 (0, 0, 0)。
    """
    if not filepath.exists():
        return (0, 0, 0)
    try:
        for line in filepath.read_text(encoding="utf-8").splitlines()[:30]:
            stripped = line.strip()
            if stripped.startswith("SCRIPT_VERSION"):
                val = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                return tuple(int(x) for x in val.split("."))
    except Exception:
        pass
    return (0, 0, 0)


def _version_gt(v1: tuple[int, ...], v2: tuple[int, ...]) -> bool:
    """v1 > v2 ?"""
    for a, b in zip(v1, v2):
        if a > b:
            return True
        if a < b:
            return False
    return len(v1) > len(v2)


def sync_to_maintenance() -> bool:
    """若自身脚本版本高于 deploy/maintenance/bump_version.py，则复制自身过去。

    若自身已在 deploy/maintenance/ 目录（同路径），跳过复制。

    Returns:
        True 表示执行了复制，False 表示未复制。
    """
    self_path = Path(__file__).resolve()
    if self_path == TARGET_SCRIPT:
        return False  # 已在目标位置，无需复制

    self_ver = tuple(int(x) for x in SCRIPT_VERSION.split("."))
    target_ver = _parse_script_version(TARGET_SCRIPT)

    if _version_gt(self_ver, target_ver):
        MAINTENANCE_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self_path, TARGET_SCRIPT)
        return True
    return False


# ---- Release 字母工具 ----

def _num_to_letters(n: int) -> str:
    """数字转为字母序列：1→A, 2→B, ..., 26→Z, 27→AA, 28→AB, ...

    与 Excel 列号逻辑相同。n 从 1 开始。
    """
    if n < 1:
        return ""
    result = []
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result.append(string.ascii_uppercase[rem])
    return "".join(reversed(result))


def _letters_to_num(letters: str) -> int:
    """字母序列转为数字：A→1, B→2, ..., Z→26, AA→27, AB→28, ..."""
    if not letters:
        return 0
    n = 0
    for ch in letters.upper():
        if ch not in string.ascii_uppercase:
            return 0
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n


# ---- 版本号读写 ----

def read_version() -> str:
    """读取 VERSION 文件（Git 代码版本号）。"""
    if not VERSION_FILE.exists():
        return ""
    return VERSION_FILE.read_text(encoding="utf-8").strip()

def read_release_version() -> str:
    """读取 RELEASE_VERSION 文件（发行版本号）。"""
    if not RELEASE_VERSION_FILE.exists():
        return ""
    return RELEASE_VERSION_FILE.read_text(encoding="utf-8").strip()


def read_effective_version() -> str:
    """读取生效版本号：优先 RELEASE_VERSION，不存在则用 VERSION。"""
    rv = read_release_version()
    if rv:
        return rv
    return read_version()


def parse_version(ver: str) -> tuple[str, str, str, str, str] | None:
    """解析 Git 版本号（VERSION 文件格式）。

    支持：
      v8.0.3-0706-0001  → ('8.0.3', '0706', '0001', '', 'v8.0.3-0706-0001')

    Returns:
        (base, date_str, seq_str, '', full_version) 或 None
    """
    if not ver:
        return None
    ver = ver.strip()
    if not ver.startswith("v"):
        return None
    parts = ver[1:].split("-")
    if len(parts) < 3:
        return None
    base, date_str, seq_str = parts[0], parts[1], parts[2]
    return base, date_str, seq_str, "", ver


def parse_release_version(ver: str) -> tuple[str, str, str, str, str, str] | None:
    """解析 Release 版本号（RELEASE_VERSION 文件格式）。

    支持：
      v8.0.4-0722-0042-0722A
      → ('8.0.4', '0722', '0042', '0722', 'A', 'v8.0.4-0722-0042-0722A')

    Returns:
        (base, git_date, git_seq, release_date, release_letter, full_version) 或 None
    """
    if not ver:
        return None
    ver = ver.strip()
    if not ver.startswith("v"):
        return None
    parts = ver[1:].split("-")
    if len(parts) < 4:
        return None
    base = parts[0]
    git_date = parts[1]
    git_seq = parts[2]
    release_part = parts[3]  # 如 0722A

    # 分离日期和字母
    release_date = ""
    release_letter = ""
    for i, ch in enumerate(release_part):
        if ch.isalpha():
            release_date = release_part[:i]
            release_letter = release_part[i:]
            break
    else:
        release_date = release_part

    return base, git_date, git_seq, release_date, release_letter, ver


def read_counter() -> int:
    """读取全局序号计数器"""
    if not COUNTER_FILE.exists():
        return 0
    try:
        return int(COUNTER_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, IOError):
        return 0


def write_counter(val: int) -> None:
    """写入全局序号计数器"""
    COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    COUNTER_FILE.write_text(str(val) + "\n", encoding="utf-8")


def _sync_counter_from_remote() -> None:
    """检测远程 VERSION 文件中的序号是否高于本地 counter，若高则自动同步。

    多 AI 并行开发时，其他 AI 可能已 push 了更高的版本号但本地未 pull。
    此函数通过 git show 读取远程 master 分支的 VERSION 文件，
    如果远程序号 > 本地 counter，则更新本地 counter 并打印警告。
    """
    try:
        result = subprocess.run(
            ["git", "show", "origin/master:VERSION"],
            capture_output=True, text=True, timeout=10,
            cwd=str(ROOT_DIR),
        )
        if result.returncode != 0:
            return  # 远程不存在或无网络，静默跳过

        remote_ver = result.stdout.strip()
        parsed = parse_version(remote_ver)
        if not parsed:
            return

        remote_seq = int(parsed[2])
        local_seq = read_counter()

        if remote_seq > local_seq:
            write_counter(remote_seq)
            print(f"⚠️  检测到远程版本号更高：远程 seq={remote_seq} > 本地 seq={local_seq}")
            print(f"    已自动同步 version_counter.txt 为 {remote_seq}")
            print(f"    远程版本：{remote_ver}")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass  # git 不可用或超时，静默跳过


def _write_version_files(new_version: str, base: str) -> None:
    """写入根 VERSION 文件和匹配的子版本 VERSION 文件"""
    VERSION_FILE.write_text(new_version + "\n", encoding="utf-8")
    for vf in _VERSION_DIRS:
        if vf.parent.name == f"v{base}":
            vf.write_text(new_version + "\n", encoding="utf-8")


def _write_release_version_files(new_version: str, base: str) -> None:
    """写入根 RELEASE_VERSION 文件和匹配的子版本 RELEASE_VERSION 文件"""
    RELEASE_VERSION_FILE.write_text(new_version + "\n", encoding="utf-8")
    for vf in _RELEASE_VERSION_DIRS:
        if vf.parent.name == f"v{base}":
            vf.write_text(new_version + "\n", encoding="utf-8")


def bump_git(base_override: str | None = None) -> str:
    """Git 管理递增：VERSION 序号 +1，不动 RELEASE_VERSION。

    读取当前 VERSION 文件，序号+1，写入 VERSION。
    RELEASE_VERSION 文件不受影响（保留旧值或不存在）。
    """
    _sync_counter_from_remote()  # 防御：同步远程更高的 counter
    current = read_version()
    today_mmdd = datetime.now().strftime("%m%d")

    if base_override:
        base = base_override
    elif current:
        parsed = parse_version(current)
        if parsed:
            base = parsed[0]
        else:
            base = "8.0.3"
    else:
        base = "8.0.3"

    current_seq = read_counter()
    new_seq = current_seq + 1
    write_counter(new_seq)

    new_version = f"v{base}-{today_mmdd}-{new_seq:04d}"
    _write_version_files(new_version, base)
    return new_version


def bump_release(base_override: str | None = None) -> str:
    """Release 部署递增：读 VERSION，追加 Release 标记，写入 RELEASE_VERSION。

    格式：v{base}-{git_date}-{git_seq}-{release_date}{letter}

    - 首次 Release：追加 -{today}A
    - 同日再次 Release：A→B→C...
    - 跨日 Release：新日期从 A 开始
    - 新 Git 提交后（VERSION 已变）：从 A 开始
    """
    _sync_counter_from_remote()  # 防御：同步远程更高的 counter
    git_version = read_version()
    today_mmdd = datetime.now().strftime("%m%d")

    if not git_version:
        print("错误：VERSION 文件不存在，请先执行 --git")
        sys.exit(1)

    parsed = parse_version(git_version)
    if not parsed:
        print(f"错误：VERSION 文件格式无效：{git_version}")
        sys.exit(1)

    base = parsed[0]
    git_date = parsed[1]
    git_seq = parsed[2]

    # 读取当前 RELEASE_VERSION，判断是否需要递增字母
    current_release = read_release_version()
    current_rp = parse_release_version(current_release) if current_release else None

    if current_rp:
        cur_base = current_rp[0]
        cur_git_seq = current_rp[2]
        cur_release_date = current_rp[3]
        cur_letter = current_rp[4]

        if cur_git_seq == git_seq and cur_release_date == today_mmdd and cur_letter:
            # 同一 Git 版本、同一天、有字母 → 递增字母
            letter_num = _letters_to_num(cur_letter)
            new_letter = _num_to_letters(letter_num + 1)
        else:
            # 不同 Git 版本或不同日期 → 从 A 开始
            new_letter = "A"
    else:
        # 没有 RELEASE_VERSION → 首次 Release
        new_letter = "A"

    new_version = f"v{base}-{git_date}-{git_seq}-{today_mmdd}{new_letter}"
    _write_release_version_files(new_version, base)
    return new_version


if __name__ == "__main__":
    # 启动时自动同步到 deploy/maintenance/
    sync_to_maintenance()

    parser = argparse.ArgumentParser(
        description="版本号递增工具 V3（双文件模式：VERSION + RELEASE_VERSION）"
    )
    parser.add_argument("--git", action="store_true",
                        help="Git 管理：VERSION 序号+1，不动 RELEASE_VERSION")
    parser.add_argument("--release", action="store_true",
                        help="Release 部署：读 VERSION，追加 Release 标记，写入 RELEASE_VERSION")
    parser.add_argument("--show", action="store_true",
                        help="显示当前 VERSION 和 RELEASE_VERSION")
    parser.add_argument("--script-version", action="store_true",
                        help="显示脚本自身版本号")
    parser.add_argument("--base", type=str,
                        help="指定大版本号（如 8.0.4），覆盖 VERSION 文件中的 base")
    args = parser.parse_args()

    if args.script_version:
        print(SCRIPT_VERSION)
    elif args.show:
        print(f"VERSION:         {read_version()}")
        rv = read_release_version()
        print(f"RELEASE_VERSION: {rv or '(未设置)'}")
        print(f"生效版本:         {read_effective_version()}")
    elif args.git:
        new_ver = bump_git(base_override=args.base)
        print(f"VERSION 已更新: {new_ver}")
        print(f"RELEASE_VERSION: {read_release_version() or '(未设置)'}")
    elif args.release:
        new_ver = bump_release(base_override=args.base)
        print(f"RELEASE_VERSION 已更新: {new_ver}")
        print(f"VERSION:                {read_version()}")
    else:
        # 默认行为：显示当前版本号
        print(f"VERSION:         {read_version()}")
        print(f"RELEASE_VERSION: {read_release_version() or '(未设置)'}")
        print(f"生效版本:         {read_effective_version()}")
        print("提示：请使用 --git 或 --release 指定操作类型")
