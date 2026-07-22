#!/usr/bin/env python3
"""版本号递增工具（全局递增序号 + Release 字母版）—— Skills 共享版 V2。

本脚本同时存在于以下位置（内容完全相同）：
  .trae/skills/multi-version-coordination/bump_version.py
  deploy/maintenance/bump_version.py

加载 Skill 时，脚本自动同步到 deploy/maintenance/bump_version.py（仅高版本覆盖低版本）。
deploy/maintenance/version_counter.txt 是项目数据，不随 Skill 迁移。

版本号格式：v{major}.{minor}.{patch}-{MMDD}-{seq}{release_letter}
示例：
  Git 管理：v8.0.4-0717-0107        （纯数字，无字母）
  Release ：v8.0.4-0717-0107A       （首次部署追加 A）
  Release ：v8.0.4-0717-0107B       （第二次部署追加 B）
  Git 管理：v8.0.4-0717-0108        （序号递增，字母清空）

规则：
- MMDD 为当天日期（自动计算）
- seq 为全局递增序号（4位），从 0001 开始，永不重置
- release_letter 为部署标记（仅 --release 时追加）
  - 首次部署加 A，第二次 B ... Z，超过 26 次用 AA、AB ...
  - Git 管理时清空字母（新序号不带字母）
- 序号存储在 deploy/maintenance/version_counter.txt

用法：
  python bump_version.py --git --base 8.0.4       # Git 管理：序号+1，无字母
  python bump_version.py --release --base 8.0.4    # Release：追加/递增字母
  python bump_version.py --show                     # 显示当前版本号
  python bump_version.py --script-version           # 显示脚本自身版本号
"""

# ====================================================================
# 脚本版本号（固定位置，供同步逻辑读取比较）
# 格式：主.次.修订，如 "2.0.0"
# 修改脚本逻辑时递增此版本号，确保高版本自动同步到 deploy/maintenance/
# ====================================================================
SCRIPT_VERSION = "2.1.0"

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
MAINTENANCE_DIR = ROOT_DIR / "deploy" / "maintenance"
COUNTER_FILE = MAINTENANCE_DIR / "version_counter.txt"
TARGET_SCRIPT = MAINTENANCE_DIR / "bump_version.py"

# config.py 读取 v8.0.x/VERSION，需同步更新
_VERSION_DIRS = sorted(ROOT_DIR.glob("v8.0.*/VERSION"), key=lambda p: str(p))


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
        try:
            shutil.copy2(self_path, TARGET_SCRIPT)
            return True
        except (SameFileError, OSError):
            return False
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
    if not VERSION_FILE.exists():
        return ""
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def parse_version(ver: str) -> tuple[str, str, str, str, str] | None:
    """解析版本号。

    支持：
      v8.0.3-0706-0001       → ('8.0.3', '0706', '0001', '', 'v8.0.3-0706-0001')
      v8.0.3-0706-0001A      → ('8.0.3', '0706', '0001', 'A', 'v8.0.3-0706-0001A')

    Returns:
        (base, date_str, seq_str, release_letter, full_version) 或 None
    """
    if not ver:
        return None
    ver = ver.strip()
    if not ver.startswith("v"):
        return None
    parts = ver[1:].split("-")
    if len(parts) != 3:
        return None
    base, date_str, seq_and_letter = parts

    # 分离数字部分和字母部分
    release_letter = ""
    seq_str = seq_and_letter
    for i, ch in enumerate(seq_and_letter):
        if ch.isalpha():
            release_letter = seq_and_letter[i:]
            seq_str = seq_and_letter[:i]
            break

    return base, date_str, seq_str, release_letter, ver


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


def bump_git(base_override: str | None = None) -> str:
    """Git 管理递增：序号 +1，无字母。

    如果当前版本有字母（如 0107B），新版本号字母清空（0108）。
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
    """Release 部署递增：序号不变，追加/递增字母。

    如果当前版本无字母（如 0107），变为 0107A。
    如果当前版本有字母（如 0107A），变为 0107B。
    如果当前版本的序号与 counter 不匹配（如 Git 管理后 counter 已递增），
    则用 counter 的序号，字母从 A 开始。
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

    # 解析当前版本号的序号和字母
    current_parsed = parse_version(current) if current else None
    current_seq_str = current_parsed[2] if current_parsed else "0"
    current_letter = current_parsed[3] if current_parsed else ""

    try:
        ver_seq = int(current_seq_str)
    except ValueError:
        ver_seq = 0

    if ver_seq == current_seq and current_letter:
        # 同一序号，字母递增
        letter_num = _letters_to_num(current_letter)
        new_letter = _num_to_letters(letter_num + 1)
        new_version = f"v{base}-{today_mmdd}-{current_seq:04d}{new_letter}"
    elif ver_seq == current_seq and not current_letter:
        # 同一序号，首次加字母
        new_version = f"v{base}-{today_mmdd}-{current_seq:04d}A"
    else:
        # 序号不匹配（Git 已递增或新日期），从 A 开始
        new_version = f"v{base}-{today_mmdd}-{current_seq:04d}A"

    _write_version_files(new_version, base)
    return new_version


if __name__ == "__main__":
    # 启动时自动同步到 deploy/maintenance/
    sync_to_maintenance()

    parser = argparse.ArgumentParser(
        description="版本号递增工具（Git 序号 + Release 字母）"
    )
    parser.add_argument("--git", action="store_true",
                        help="Git 管理：序号+1，无字母")
    parser.add_argument("--release", action="store_true",
                        help="Release 部署：追加/递增字母")
    parser.add_argument("--show", action="store_true",
                        help="仅显示当前版本号")
    parser.add_argument("--script-version", action="store_true",
                        help="显示脚本自身版本号")
    parser.add_argument("--base", type=str,
                        help="指定大版本号（如 8.0.3），覆盖 VERSION 文件中的 base")
    args = parser.parse_args()

    if args.script_version:
        print(SCRIPT_VERSION)
    elif args.show:
        print(read_version())
    elif args.git:
        new_ver = bump_git(base_override=args.base)
        print(new_ver)
    elif args.release:
        new_ver = bump_release(base_override=args.base)
        print(new_ver)
    else:
        # 默认行为：显示当前版本号（防止误操作）
        print(read_version())
        print("提示：请使用 --git 或 --release 指定操作类型")
