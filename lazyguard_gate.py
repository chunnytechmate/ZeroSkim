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
    """Enforce that LazyGuard was called within the last 5 minutes."""
    # Resolve state file path to match lazyguard.py
    if session_id:
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '', session_id) or "default"
        state_file = os.path.join(BASE_STATE_DIR, f".lazyguard-state-session-{safe_id}.json")
    else:
        state_file = os.path.join(BASE_STATE_DIR, ".lazyguard-state.json")

    if not os.path.isfile(state_file):
        # Ensure directory exists before error (clean error message on fresh systems)
        _abort(skill_name, "No LazyGuard state found for this session.")

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
    except (json.JSONDecodeError, IOError):
        _abort(skill_name, "State file corrupt.")

    if skill_name not in state:
        _abort(skill_name, "Skill not found in read-cache. Run lazyguard first.")

    entry = state[skill_name]
    last_read = datetime.fromisoformat(entry.get("last_read", "1970-01-01T00:00:00"))
    age = datetime.now() - last_read

    if age > timedelta(minutes=MAX_AGE_MINUTES):
        _abort(skill_name, f"Read-cache EXPIRED ({int(age.total_seconds()/60)} mins ago).")

    lines = entry.get("lines", "?")
    print(f"✅ LazyGuard OK: '{skill_name}' active ({int(age.total_seconds())}s ago, {lines} lines).")


def _abort(skill: str, reason: str):
    print(f"❌ LAZYGUARD BLOCK: {reason}")
    print(f"   → Run: python3 lazyguard.py {skill}")
    sys.exit(1)
