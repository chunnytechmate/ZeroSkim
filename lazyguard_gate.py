"""
lazyguard_gate.py — Import this in every skill script to enforce LazyGuard pre-read.

Usage (add at top of any skill script):
  import sys, os
  sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/scripts"))
  from lazyguard_gate import require_lazyguard

  # Call before any real work.
  # If your agent uses sessions, pass the session_id!
  require_lazyguard("send-recording-line", session_id=os.environ.get("OPENCLAW_SESSION_ID"))
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta

BASE_STATE_DIR = os.environ.get(
    "OPENCLAW_STATE_DIR",
    os.path.expanduser("~/.openclaw/workspace")
)
MAX_AGE_MINUTES = 5


def require_lazyguard(skill_name: str, session_id: str | None = None):
    """
    Check that lazyguard.py was called for this skill within MAX_AGE_MINUTES.
    If not, print error and exit with code 1.
    """
    # 1. Resolve state file path to match lazyguard.py
    if session_id:
        safe_session = re.sub(r'[^a-zA-Z0-9_-]', '', session_id) or "default"
        state_file = os.path.join(BASE_STATE_DIR, f".lazyguard-state-session-{safe_session}.json")
        cmd_hint = f"python3 ~/.openclaw/workspace/scripts/lazyguard.py {skill_name} --session {safe_session}"
    else:
        state_file = os.path.join(BASE_STATE_DIR, ".lazyguard-state.json")
        cmd_hint = f"python3 ~/.openclaw/workspace/scripts/lazyguard.py {skill_name}"

    # 2. Check state file exists
    if not os.path.isfile(state_file):
        print(f"❌ LAZYGUARD NOT RUN: No state file found for this session.")
        print(f"   → Run: {cmd_hint}")
        sys.exit(1)

    # 3. Load JSON (handle corrupt files)
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
    except (json.JSONDecodeError, IOError):
        print(f"❌ LAZYGUARD STATE CORRUPT: Cannot read state file.")
        print(f"   → Run: {cmd_hint}")
        sys.exit(1)

    # 4. Check if this skill was read
    if skill_name not in state:
        print(f"❌ LAZYGUARD NOT RUN: '{skill_name}' not found in state file.")
        print(f"   → Run: {cmd_hint}")
        sys.exit(1)

    entry = state[skill_name]
    last_read_str = entry.get("last_read", "")
    if not last_read_str:
        print(f"❌ LAZYGUARD: No timestamp found for '{skill_name}'")
        print(f"   → Run: {cmd_hint}")
        sys.exit(1)

    # 5. Check age (timeout 5 minutes)
    try:
        last_read = datetime.fromisoformat(last_read_str)
    except ValueError:
        print(f"❌ LAZYGUARD: Invalid timestamp for '{skill_name}'")
        sys.exit(1)

    age = datetime.now() - last_read

    if age > timedelta(minutes=MAX_AGE_MINUTES):
        print(f"❌ LAZYGUARD EXPIRED: '{skill_name}' was read {int(age.total_seconds()/60)} minutes ago (max {MAX_AGE_MINUTES} min)")
        print(f"   → Re-run: {cmd_hint}")
        sys.exit(1)

    # All good
    lines = entry.get("lines", "?")
    print(f"✅ LazyGuard OK: '{skill_name}' read {int(age.total_seconds())}s ago ({lines} lines)")
