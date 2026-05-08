#!/usr/bin/env python3
"""
skill_read_guard.py — บังคับอ่าน SKILL.md ทั้งหมดก่อนใช้งาน skill

วิธีทำงาน:
  - Track SHA256 hash ของแต่ละ SKILL.md
  - FRESH / CHANGED → พิมพ์ content ทั้งหมด + บันทึก hash ใหม่
  - UNCHANGED → แจ้ง metadata เท่านั้น (ไม่พิมพ์ content ลด token burn)

Usage:
  python3 skill_read_guard.py <skill_name>
  python3 skill_read_guard.py <skill_name> --force     # บังคับพิมพ์ content ไม่สน hash
  python3 skill_read_guard.py --list                    # แสดง skill ทั้งหมด + status

Examples:
  python3 skill_read_guard.py send-recording-line
  python3 skill_read_guard.py music-class-summarizer --force
  python3 skill_read_guard.py --list
"""

import sys
import os
import json
import hashlib
import tempfile
from datetime import datetime

STATE_FILE = os.path.expanduser("~/.openclaw/workspace/.skill-state.json")
SKILLS_DIRS = [
    os.path.expanduser("~/.openclaw/workspace/skills"),
    "/app/skills",
]


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


def load_state() -> dict:
    """Load skill read state. Returns {} on corrupt/missing file."""
    if not os.path.isfile(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        # Corrupt or unreadable — start fresh
        return {}


def save_state(state: dict):
    """Save skill read state with atomic write to prevent corruption."""
    try:
        state_dir = os.path.dirname(STATE_FILE)
        os.makedirs(state_dir, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(
            dir=state_dir, suffix=".json", prefix=".skill-state-"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, STATE_FILE)  # atomic on POSIX
        except BaseException:
            # Clean up temp file on any error
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except (IOError, OSError) as e:
        print(f"⚠️ Cannot save state: {e}", file=sys.stderr)
        # Non-fatal — state loss is acceptable


def list_skills():
    """List all discovered skills with read status."""
    state = load_state()
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

    print(f"{'Skill':<40} {'Status':<14} {'Last Read'}")
    print("-" * 80)
    for name, status, last_read in found:
        print(f"{name:<40} {status:<14} {last_read}")
    print(f"\nTotal: {len(found)} skills")


def read_skill(skill_name: str, force: bool = False):
    """Read a skill's SKILL.md, printing content only when needed."""
    # Find SKILL.md
    skill_path = find_skill_path(skill_name)
    if not skill_path:
        print(f"❌ SKILL.md not found for skill: {skill_name}")
        sys.exit(1)

    # Read content with error handling
    try:
        with open(skill_path, "r", encoding="utf-8") as f:
            content = f.read()
    except PermissionError:
        print(f"❌ Permission denied: {skill_path}")
        sys.exit(1)
    except UnicodeDecodeError:
        print(f"❌ Encoding error (not valid UTF-8): {skill_path}")
        sys.exit(1)
    except OSError as e:
        print(f"❌ Cannot read {skill_path}: {e}")
        sys.exit(1)

    current_hash = get_file_hash(skill_path)
    line_count = content.count("\n") + 1

    # Check state (skip hash check if --force)
    if not force:
        state = load_state()
        skill_state = state.get(skill_name, {})
        last_hash = skill_state.get("hash", "")

        if last_hash == current_hash and last_hash:
            # Already read and unchanged — just show metadata, skip content
            print(f"✅ UNCHANGED — already read ({line_count} lines)")
            print(f"📌 Path: {skill_path}")
            print(f"📖 Last read: {skill_state.get('last_read', 'unknown')}")
            print(f"🔑 Hash: {current_hash[:16]}...")
            print(f"📌 Action: ไม่ต้องอ่านซ้ำ — ใช้ความจำ session นี้ได้เลย")
            return

    # FRESH / CHANGED / --force → print full content
    state = load_state() if not force else {}
    skill_state = state.get(skill_name, {})
    last_hash = skill_state.get("hash", "")

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

    # Update state
    state[skill_name] = {
        "hash": current_hash,
        "last_read": datetime.now().isoformat(),
        "path": skill_path,
        "lines": line_count,
    }
    save_state(state)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 skill_read_guard.py <skill_name> [--force]")
        print("       python3 skill_read_guard.py --list")
        sys.exit(1)

    if sys.argv[1] == "--list":
        list_skills()
        return

    skill_name = sys.argv[1]
    force = "--force" in sys.argv

    read_skill(skill_name, force=force)


if __name__ == "__main__":
    main()
