"""
skill_check.py — Import this in every skill script to enforce skill_read_guard pre-read.

Usage (add at top of any skill script):
  import sys, os
  sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/scripts"))
  from skill_check import require_skill_read

  # Call before any real work
  require_skill_read("send-recording-line")
"""

import os
import sys
import json
from datetime import datetime, timedelta

STATE_FILE = os.path.expanduser("~/.openclaw/workspace/.skill-state.json")
MAX_AGE_MINUTES = 5

def require_skill_read(skill_name: str):
    """
    Check that lazyguard.py was called for this skill within MAX_AGE_MINUTES.
    If not, print error and exit with code 1.
    """
    if not os.path.isfile(STATE_FILE):
        print(f"❌ SKILL GUARD NOT RUN: lazyguard.py has never been called for '{skill_name}'")
        print(f"   → Run: python3 ~/.openclaw/workspace/scripts/lazyguard.py {skill_name}")
        sys.exit(1)

    with open(STATE_FILE, "r") as f:
        state = json.load(f)

    if skill_name not in state:
        print(f"❌ SKILL GUARD NOT RUN: '{skill_name}' not found in state file")
        print(f"   → Run: python3 ~/.openclaw/workspace/scripts/lazyguard.py {skill_name}")
        sys.exit(1)

    entry = state[skill_name]
    last_read_str = entry.get("last_read", "")
    if not last_read_str:
        print(f"❌ SKILL GUARD: No last_read timestamp for '{skill_name}'")
        print(f"   → Run: python3 ~/.openclaw/workspace/scripts/lazyguard.py {skill_name}")
        sys.exit(1)

    # Parse timestamp
    try:
        last_read = datetime.fromisoformat(last_read_str)
    except ValueError:
        print(f"❌ SKILL GUARD: Invalid timestamp for '{skill_name}'")
        sys.exit(1)

    now = datetime.now()
    age = now - last_read

    if age > timedelta(minutes=MAX_AGE_MINUTES):
        print(f"❌ SKILL GUARD EXPIRED: '{skill_name}' was read {int(age.total_seconds()/60)} minutes ago (max {MAX_AGE_MINUTES} min)")
        print(f"   → Re-run: python3 ~/.openclaw/workspace/scripts/lazyguard.py {skill_name}")
        sys.exit(1)

    # All good
    lines = entry.get("lines", "?")
    print(f"✅ Skill guard OK: '{skill_name}' read {int(age.total_seconds())}s ago ({lines} lines)")
