#!/usr/bin/env python3
"""
skill_read_guard.py — บังคับอ่าน SKILL.md ทั้งหมดก่อนใช้งาน skill (รองรับ Session แยก)

วิธีทำงาน:
  - Track SHA256 hash ของแต่ละ SKILL.md **แยกตาม Session ID**
  - FRESH / CHANGED → พิมพ์ content ทั้งหมด + บันทึก hash ใหม่
  - UNCHANGED → แจ้ง metadata เท่านั้น (ลด token burn)
  - **Session-aware**: session เปลี่ยน → ถือว่ายังไม่เคยอ่าน → ต้องอ่านใหม่

Usage:
  python3 skill_read_guard.py <skill_name> [--session <session_id>]
  python3 skill_read_guard.py <skill_name> --force
  python3 skill_read_guard.py --list [--session <session_id>]

Examples:
  python3 skill_read_guard.py send-recording-line
  python3 skill_read_guard.py send-recording-line --session abc123
  python3 skill_read_guard.py music-class-summarizer --force
  python3 skill_read_guard.py --list
"""

import sys
import os
import json
import hashlib
import tempfile
import argparse
import re
import glob
from datetime import datetime, timedelta

# รองรับ Environment Variable สำหรับรันใน Docker
BASE_STATE_DIR = os.environ.get(
    "OPENCLAW_STATE_DIR",
    os.path.expanduser("~/.openclaw/workspace"),
)
SKILLS_DIRS = [
    os.path.expanduser("~/.openclaw/workspace/skills"),
    "/app/skills",
]


def get_state_file(session_id: str | None) -> str:
    """คืนค่า Path ของไฟล์ State โดยแยกตาม Session ID และป้องกัน Path Traversal"""
    if session_id:
        # กรองเอาเฉพาะตัวอักษร ตัวเลข ขีดกลาง และขีดล่าง เท่านั้น
        safe_session = re.sub(r'[^a-zA-Z0-9_-]', '', session_id)
        if not safe_session:
            safe_session = "default"
        filename = f".skill-state-session-{safe_session}.json"
    else:
        filename = ".skill-state.json"
    return os.path.join(BASE_STATE_DIR, filename)


def gc_stale_session_states(max_age_days: int = 7):
    """ลบ session state files ที่เก่าเกิน max_age_days วัน (Garbage Collection)"""
    if not os.path.isdir(BASE_STATE_DIR):
        return 0
    pattern = os.path.join(BASE_STATE_DIR, ".skill-state-session-*.json")
    cutoff = datetime.now() - timedelta(days=max_age_days)
    removed = 0
    for filepath in glob.glob(pattern):
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if mtime < cutoff:
                os.remove(filepath)
                removed += 1
        except OSError:
            pass
    return removed


def find_skill_path(skill_name: str) -> str | None:
    """Find SKILL.md path for a given skill name."""
    candidates = [
        skill_name,
        skill_name.replace("-", "_"),
        skill_name.replace("_", "-"),
    ]

    for base_dir in SKILLS_DIRS:
        for candidate in candidates:
            skill_path = os.path.join(base_dir, candidate, "SKILL.md")
            if os.path.isfile(skill_path):
                return skill_path

    return None


def get_file_hash(filepath: str) -> str:
    """Calculate SHA256 hash of a file (chunked read)."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_state(state_file: str) -> dict:
    """Load skill read state. Returns {} on corrupt/missing file."""
    if not os.path.isfile(state_file):
        return {}
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        return {}


def save_state(state_file: str, state: dict):
    """Save skill read state with atomic write to prevent corruption."""
    try:
        state_dir = os.path.dirname(state_file)
        os.makedirs(state_dir, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            dir=state_dir, suffix=".json", prefix=".skill-state-"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, state_file)  # atomic on POSIX
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except (IOError, OSError) as e:
        print(f"⚠️ Cannot save state: {e}", file=sys.stderr)


def list_skills(state_file: str):
    """List all discovered skills with read status."""
    state = load_state(state_file)
    found = []

    for base_dir in SKILLS_DIRS:
        if not os.path.isdir(base_dir):
            continue
        for entry in sorted(os.listdir(base_dir)):
            skill_path = os.path.join(base_dir, entry, "SKILL.md")
            if not os.path.isfile(skill_path):
                continue
            skill_state = state.get(entry, {})
            last_hash = skill_state.get("hash", "")
            try:
                current_hash = get_file_hash(skill_path)
            except OSError:
                current_hash = ""

            if last_hash == current_hash and last_hash:
                status = "✅ read"
            elif last_hash:
                status = "⚠️ changed"
            else:
                status = "📖 unread"
            found.append((entry, status, skill_state.get("last_read", "-")))

    if not found:
        print("No skills found.")
        return

    print(f"[{os.path.basename(state_file)}]")
    print(f"{'Skill':<40} {'Status':<14} {'Last Read'}")
    print("-" * 80)
    for name, status, last_read in found:
        print(f"{name:<40} {status:<14} {last_read}")
    print(f"\nTotal: {len(found)} skills")


def read_skill(skill_name: str, state_file: str, force: bool = False):
    """Read a skill's SKILL.md, printing content only when needed."""
    skill_path = find_skill_path(skill_name)
    if not skill_path:
        print(f"❌ SKILL.md not found for skill: {skill_name}")
        sys.exit(1)

    try:
        with open(skill_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Read error ({skill_path}): {e}")
        sys.exit(1)

    current_hash = get_file_hash(skill_path)
    line_count = content.count("\n") + 1
    state = load_state(state_file) if not force else {}
    skill_state = state.get(skill_name, {})
    last_hash = skill_state.get("hash", "")

    if not force and last_hash == current_hash and last_hash:
        # Already read and unchanged — update timestamp, skip content
        state[skill_name] = {
            "hash": current_hash,
            "last_read": datetime.now().isoformat(),
            "path": skill_path,
            "lines": line_count,
        }
        save_state(state_file, state)
        print(f"✅ UNCHANGED — already read ({line_count} lines)")
        print(f"📌 Path: {skill_path}")
        print(f"📖 Last read: {skill_state.get('last_read', 'unknown')}")
        print(f"🔑 Hash: {current_hash[:16]}...")
        print(f"📌 Action: ไม่ต้องอ่านซ้ำ — ใช้ความจำ session นี้ได้เลย")
        return

    # FRESH / CHANGED / --force → print full content
    if force:
        label = "📖 FORCE READ"
    elif last_hash:
        label = "⚠️ CHANGED — must re-read!"
    else:
        label = f"📖 FIRST READ ({line_count} lines)"

    print(label)
    print(f"📌 Path: {skill_path}")
    print(f"\n--- SKILL.md CONTENT ---\n")
    print(content)
    print(f"\n--- END ({line_count} lines) ---")
    print("⚠️ SYSTEM DIRECTIVE: You MUST read and strictly follow ALL rules and formats specified above before proceeding.")

    # Update state (load fresh if --force skipped loading earlier)
    if force:
        state = load_state(state_file)
    state[skill_name] = {
        "hash": current_hash,
        "last_read": datetime.now().isoformat(),
        "path": skill_path,
        "lines": line_count,
    }
    save_state(state_file, state)


def main():
    parser = argparse.ArgumentParser(
        description="Skill Read Guard — hash-based read gate for AI agent skill files"
    )
    parser.add_argument("skill_name", nargs="?", help="Name of the skill to read")
    parser.add_argument("--list", action="store_true", help="List all skills and status")
    parser.add_argument("--force", action="store_true", help="Force read content ignoring hash")
    parser.add_argument("--session", type=str, default=None, help="Session ID to isolate cache context")

    args = parser.parse_args()

    if not args.skill_name and not args.list:
        parser.print_help()
        sys.exit(1)

    state_file = get_state_file(args.session)

    if args.list:
        list_skills(state_file)
    else:
        # GC: ลบ session state files เก่าๆ (เฉพาะตอนใช้งานปกติ ไม่ใช่ --list)
        removed = gc_stale_session_states(max_age_days=7)
        if removed:
            print(f"🧹 GC: removed {removed} stale session state file(s)", file=sys.stderr)

        read_skill(args.skill_name, state_file, force=args.force)


if __name__ == "__main__":
    main()
