#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# LazyGuard — Gate Enforcement
# Copyright (c) 2026 Chunny (chunnytechmate). All rights reserved.
# Licensed under the MIT License.
# ---------------------------------------------------------------------------
"""
lazyguard_gate.py — Import this in every skill script to enforce LazyGuard pre-read.

Usage (add at top of any skill script):
  import sys, os
  scripts_dir = os.environ.get("OPENCLAW_SCRIPTS_DIR", os.path.expanduser("~/.openclaw/workspace/scripts"))
  if scripts_dir not in sys.path:
      sys.path.insert(0, scripts_dir)
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
        _abort(skill_name, "No LazyGuard state found for this session.", session_id)

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
    except (json.JSONDecodeError, IOError):
        _abort(skill_name, "State file corrupt.", session_id)

    if skill_name not in state:
        _abort(skill_name, "Skill not found in read-cache. Run lazyguard first.", session_id)

    entry = state[skill_name]
    last_read = datetime.fromisoformat(entry.get("last_read", "1970-01-01T00:00:00"))
    age = datetime.now() - last_read

    if age > timedelta(minutes=MAX_AGE_MINUTES):
        _abort(skill_name, f"Read-cache EXPIRED ({int(age.total_seconds()/60)} mins ago).", session_id)

    lines = entry.get("lines", "?")
    print(f"✅ LazyGuard OK: '{skill_name}' active ({int(age.total_seconds())}s ago, {lines} lines).")


def _abort(skill: str, reason: str, session_id: str | None = None):
    print(f"❌ LAZYGUARD BLOCK: {reason}")
    cmd = f"python3 lazyguard.py {skill}"
    if session_id:
        cmd += f" --session {session_id}"
    print(f"   → Run: {cmd}")
    sys.exit(1)
