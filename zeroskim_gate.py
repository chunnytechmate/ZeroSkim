#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ZeroSkim — Gate Enforcement
# Copyright (c) 2026 Chunny (chunnytechmate). All rights reserved.
# Licensed under the MIT License.
# ---------------------------------------------------------------------------
"""
zeroskim_gate.py — Import this in every skill script to enforce ZeroSkim pre-read.

Usage (add at top of any skill script):
  import sys, os
  scripts_dir = os.environ.get("OPENCLAW_SCRIPTS_DIR", os.path.expanduser("~/.openclaw/workspace/scripts"))
  if scripts_dir not in sys.path:
      sys.path.insert(0, scripts_dir)
  from zeroskim_gate import require_zeroskim, require_step_done

  # Layer 1: File read gate (original ZeroSkim)
  require_zeroskim("send-recording-line", session_id=os.environ.get("OPENCLAW_SESSION_ID"))

  # Layer 2: Step completion gate (convention-based)
  require_step_done("hangyao-socialmedia", "read-comments")
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_STATE_DIR = os.environ.get(
    "OPENCLAW_STATE_DIR",
    os.path.expanduser("~/.openclaw/workspace")
)
MAX_AGE_MINUTES = 15  # เพิ่มจาก 5 → 15 สำหรับ long tasks (หางยาวโซเชียล, video pipeline)
TZ_BKK = timezone(timedelta(hours=7))


# ═══════════════════════════════════════════════════════════════════════
# Layer 1: File Read Gate (original ZeroSkim)
# ═══════════════════════════════════════════════════════════════════════

def require_zeroskim(skill_name: str, session_id: str | None = None):
    """Enforce that ZeroSkim was called within the last N minutes."""
    # Resolve state file path to match zeroskim.py
    if session_id:
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '', session_id) or "default"
        state_file = os.path.join(BASE_STATE_DIR, f".zeroskim-state-session-{safe_id}.json")
    else:
        state_file = os.path.join(BASE_STATE_DIR, ".zeroskim-state.json")

    if not os.path.isfile(state_file):
        _abort(skill_name, "No ZeroSkim state found for this session.", session_id)

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
    except (json.JSONDecodeError, IOError):
        _abort(skill_name, "State file corrupt.", session_id)

    if skill_name not in state:
        _abort(skill_name, "Skill not found in read-cache. Run zeroskim first.", session_id)

    entry = state[skill_name]
    last_read = datetime.fromisoformat(entry.get("last_read", "1970-01-01T00:00:00"))
    age = datetime.now() - last_read

    # Allow per-skill override via env: ZEROSKIM_MAX_AGE_<SKILLNAME>=<minutes>
    max_age = MAX_AGE_MINUTES
    env_key = f"ZEROSKIM_MAX_AGE_{skill_name.upper().replace('-', '_')}"
    env_val = os.environ.get(env_key)
    if env_val:
        try:
            max_age = int(env_val)
        except ValueError:
            pass

    if age > timedelta(minutes=max_age):
        _abort(skill_name, f"Read-cache EXPIRED ({int(age.total_seconds()/60)} mins ago).", session_id)

    lines = entry.get("lines", "?")
    print(f"✅ ZeroSkim OK: '{skill_name}' active ({int(age.total_seconds())}s ago, {lines} lines).")


# ═══════════════════════════════════════════════════════════════════════
# Layer 2: Step Completion Gate (Convention-based)
# ═══════════════════════════════════════════════════════════════════════

def require_step_done(skill_name: str, step: str):
    """
    Convention-based hard gate: verify that a step was actually performed
    by checking if the step name appears in today's agent log.

    How it works:
    1. Find the skill's log directory (auto-discover)
    2. Read today's agent log file
    3. Search for the step name in the log
    4. If found → pass, if not → block

    Convention: agent_log.py writes entries like:
      | 12:30:00 | read-comments | อ่าน comments ของ tweet X |

    So searching for the step name in the log content is sufficient.

    Usage:
      require_step_done("hangyao-socialmedia", "read-comments")
      require_step_done("send-lesson-line", "fetch-student")
    """
    today_str = datetime.now(TZ_BKK).strftime("%Y-%m-%d")

    # Auto-discover log directory: check common locations
    log_paths = _find_log_paths(skill_name, today_str)

    if not log_paths:
        _abort_step_done(skill_name, step,
            f"No log file found for today ({today_str}). "
            f"Run the step first, then try again.")

    # Search all possible log files
    for log_path in log_paths:
        try:
            content = log_path.read_text(encoding="utf-8")
        except (IOError, OSError):
            continue

        # Convention: step name appears in the log
        # Check multiple formats: markdown table, JSON, plain text
        if _step_in_log(step, content):
            print(f"✅ Step OK: '{step}' found in {log_path.name}")
            return

    _abort_step_done(skill_name, step,
        f"Step '{step}' not found in today's logs ({today_str}). "
        f"Complete this step first before proceeding.")


def _find_log_paths(skill_name: str, today_str: str) -> list[Path]:
    """Auto-discover log file paths for a skill.

    Search order:
    1. skills/<skill_name>/data/agent_logs/YYYY-MM-DD.md  (skill-specific)
    2. skills/<skill_name>/logs/YYYY-MM-DD.md              (alternative)
    3. workspace/data/agent_logs/YYYY-MM-DD.md             (global)

    Also searches from script location (for when called from within a skill).
    """
    # Try multiple base directories
    bases = []
    base_env = Path(BASE_STATE_DIR)
    bases.append(base_env)
    # Common: BASE_STATE_DIR might be ~/.openclaw, workspace is ~/.openclaw/workspace
    bases.append(base_env / "workspace")
    # Try relative to this script's location
    try:
        script_dir = Path(__file__).resolve().parent
        # If script is in workspace/scripts, go up to workspace
        if script_dir.name == "scripts":
            bases.append(script_dir.parent)
        # If script is in a skill's scripts/ dir, go up to workspace
        if (script_dir.parent / "skills").is_dir():
            bases.append(script_dir.parent)
        if (script_dir.parent.parent / "skills").is_dir():
            bases.append(script_dir.parent.parent)
    except Exception:
        pass

    seen = set()
    candidates = []
    for base in bases:
        for pattern in [
            base / "skills" / skill_name / "data" / "agent_logs" / f"{today_str}.md",
            base / "skills" / skill_name / "logs" / f"{today_str}.md",
            base / "data" / "agent_logs" / f"{today_str}.md",
        ]:
            if pattern not in seen and pattern.is_file():
                candidates.append(pattern)
                seen.add(pattern)
    return candidates


def _step_in_log(step: str, content: str) -> bool:
    """Check if step name appears in log content (flexible matching).

    Supports multiple log formats:
    - Markdown table: | 12:30 | read-comments | detail |
    - Plain text: read-comments detail
    - JSON: {"action": "read-comments", ...}
    """
    # Normalize step name for matching
    step_lower = step.lower()
    content_lower = content.lower()

    # Direct match
    if step_lower in content_lower:
        return True

    # Handle hyphen/underscore/space variants
    step_variants = [
        step_lower,
        step_lower.replace("-", "_"),
        step_lower.replace("-", " "),
        step_lower.replace("_", " "),
    ]

    return any(v in content_lower for v in step_variants)


def _abort_step_done(skill: str, step: str, reason: str):
    """Block execution with clear error message."""
    print(f"🛑 STEP BLOCK: {reason}")
    print(f"   Skill: {skill}")
    print(f"   Required step: {step}")
    print(f"   Fix: Complete '{step}' and log it with agent_log.py, then try again.")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════
# Shared abort function
# ═══════════════════════════════════════════════════════════════════════

def _abort(skill: str, reason: str, session_id: str | None = None):
    print(f"❌ ZEROSKIM BLOCK: {reason}")
    cmd = f"python3 zeroskim.py {skill}"
    if session_id:
        cmd += f" --session {session_id}"
    print(f"   → Run: {cmd}")
    sys.exit(1)
