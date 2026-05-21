#!/usr/bin/env python3
"""
ZeroSkim — Stop AI agents from skimming skill files.

Core module providing the ZeroSkim cache system and gate enforcement.
"""

import sys
import os
import json
import hashlib
import glob
import re
import time

# ---------------------------------------------------------------------------
# ZeroSkim: Smart SKILL.md cache (anti-skimming)
# ---------------------------------------------------------------------------

class ZeroSkim:
    """
    Forces AI agents to fully read SKILL.md files before execution.
    Tracks SHA256 hashes per session to prevent skimming.

    Usage:
        zs = ZeroSkim(workspace_dir="/path/to/workspace")
        result = zs.read("my-skill", session_id="abc123")
    """

    STATE_FILE_TEMPLATE = ".zeroskim-state.json"
    SESSION_STATE_TEMPLATE = ".zeroskim-state-{session_id}.json"
    MAX_CACHE_AGE_DAYS = 7

    def __init__(self, workspace_dir=None):
        self.workspace_dir = workspace_dir or os.environ.get(
            "OPENCLAW_WORKSPACE_DIR",
            os.path.expanduser("~/.openclaw/workspace")
        )
        self.skills_dir = os.path.join(self.workspace_dir, "skills")

    # --- State management ---

    def _state_path(self, session_id=None):
        if session_id:
            safe_id = re.sub(r'[^a-zA-Z0-9_-]', '', session_id)
            return os.path.join(self.workspace_dir, self.SESSION_STATE_TEMPLATE.format(session_id=safe_id))
        return os.path.join(self.workspace_dir, self.STATE_FILE_TEMPLATE)

    def _load_state(self, session_id=None):
        path = self._state_path(session_id)
        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_state(self, state, session_id=None):
        path = self._state_path(session_id)
        tmp = path + ".tmp"
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            os.replace(tmp, path)
        except IOError as e:
            print(f"[⚠️] Could not save state: {e}", file=sys.stderr)

    # --- Skill discovery ---

    def _find_skill_md(self, skill_name):
        """Find SKILL.md for a given skill name."""
        patterns = [
            os.path.join(self.skills_dir, skill_name, "SKILL.md"),
            os.path.join(self.skills_dir, skill_name.replace("-", "_"), "SKILL.md"),
            os.path.join(self.skills_dir, skill_name.replace("_", "-"), "SKILL.md"),
        ]
        for p in patterns:
            if os.path.isfile(p):
                return p
        # Try glob
        matches = glob.glob(os.path.join(self.skills_dir, "*", "SKILL.md"))
        for m in matches:
            dirname = os.path.basename(os.path.dirname(m))
            if skill_name.lower() in dirname.lower():
                return m
        return None

    def list_skills(self):
        """List all discovered skills."""
        skills = []
        if os.path.isdir(self.skills_dir):
            for entry in sorted(os.listdir(self.skills_dir)):
                md_path = os.path.join(self.skills_dir, entry, "SKILL.md")
                if os.path.isdir(os.path.join(self.skills_dir, entry)) and os.path.isfile(md_path):
                    skills.append({"name": entry, "path": md_path})
        return skills

    # --- Core read ---

    def read(self, skill_name, session_id=None, force=False):
        """
        Read a skill's SKILL.md with anti-skimming cache.

        Returns dict with:
            status: "FIRST_READ", "UNCHANGED", "CHANGED", "NOT_FOUND"
            content: full text (if FIRST_READ or CHANGED)
            path: file path
            hash: SHA256 hash
            lines: number of lines
            last_read: ISO timestamp
        """
        skill_path = self._find_skill_md(skill_name)
        if not skill_path:
            return {"status": "NOT_FOUND", "skill_name": skill_name}

        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()

        current_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        lines = content.count('\n') + 1
        state = self._load_state(session_id)

        entry = state.get(skill_name, {})
        cached_hash = entry.get("hash", "")

        now = time.strftime("%Y-%m-%dT%H:%M:%S")

        if force or cached_hash != current_hash:
            # Fresh read or changed
            state[skill_name] = {
                "hash": current_hash,
                "path": skill_path,
                "last_read": now,
                "lines": lines,
            }
            self._save_state(state, session_id)
            return {
                "status": "CHANGED" if cached_hash else "FIRST_READ",
                "content": content,
                "path": skill_path,
                "hash": current_hash,
                "lines": lines,
                "last_read": now,
            }
        else:
            # Unchanged — return metadata only
            return {
                "status": "UNCHANGED",
                "content": None,
                "path": skill_path,
                "hash": current_hash,
                "lines": lines,
                "last_read": entry.get("last_read", now),
            }

    # --- Garbage collection ---

    def gc(self):
        """Remove state files older than MAX_CACHE_AGE_DAYS."""
        removed = 0
        cutoff = time.time() - (self.MAX_CACHE_AGE_DAYS * 86400)
        for f in glob.glob(os.path.join(self.workspace_dir, ".zeroskim-state*.json")):
            if os.path.getmtime(f) < cutoff:
                try:
                    os.remove(f)
                    removed += 1
                except IOError:
                    pass
        return removed


# ---------------------------------------------------------------------------
# Gate enforcement (hard gate for skill scripts)
# ---------------------------------------------------------------------------

def require_zeroskim(skill_name, session_id=None, max_age_minutes=5):
    """
    Hard gate: blocks execution if ZeroSkim hasn't been run recently.

    Call this at the top of every skill script:

        from zeroskim import require_zeroskim
        require_zeroskim("my-skill")

    Raises SystemExit if the skill hasn't been read via ZeroSkim recently.
    """
    zs = ZeroSkim()
    state = zs._load_state(session_id)

    entry = state.get(skill_name)
    if not entry:
        print(f"❌ ZEROSKIM BLOCK: Skill '{skill_name}' not found in read-cache.", file=sys.stderr)
        print(f"   → Run: python3 zeroskim.py {skill_name}", file=sys.stderr)
        sys.exit(1)

    # Check freshness
    last_read = entry.get("last_read", "")
    if last_read:
        try:
            last_ts = time.mktime(time.strptime(last_read, "%Y-%m-%dT%H:%M:%S"))
            age_minutes = (time.time() - last_ts) / 60
            if age_minutes > max_age_minutes:
                print(f"❌ ZEROSKIM BLOCK: Read-cache EXPIRED ({age_minutes:.0f} mins ago).", file=sys.stderr)
                print(f"   → Run: python3 zeroskim.py {skill_name}", file=sys.stderr)
                sys.exit(1)
        except (ValueError, OverflowError):
            pass

    print(f"✅ ZeroSkim OK: '{skill_name}' active ({entry.get('last_read', '?')} ago, {entry.get('lines', '?')} lines).")


# ---------------------------------------------------------------------------
# Layer 2: Step Completion Gate (Convention-based)
# ---------------------------------------------------------------------------

def require_step_done(skill_name, step):
    """
    Convention-based hard gate: verify that a step was actually performed
    by checking if the step name appears in today's agent log.

    How it works:
    1. Find the skill's log directory (auto-discover)
    2. Read today's agent log file
    3. Search for the step name in the log
    4. If found → pass, if not → block

    Convention: agent writes entries like:
      | 12:30:00 | read-comments | detail |

    So searching for the step name in the log content is sufficient.

    Usage:
      require_step_done("hangyao-socialmedia", "read-comments")
      require_step_done("send-lesson-line", "fetch-student")
    """
    from datetime import datetime, timezone, timedelta as _td
    from pathlib import Path as _Path

    _TZ_BKK = timezone(_td(hours=7))
    today_str = datetime.now(_TZ_BKK).strftime("%Y-%m-%d")

    log_paths = _find_log_paths(skill_name, today_str)

    if not log_paths:
        _abort_step_done(skill_name, step,
            f"No log file found for today ({today_str}). "
            f"Run the step first, then try again.")

    for log_path in log_paths:
        try:
            content = log_path.read_text(encoding="utf-8")
        except (IOError, OSError):
            continue

        if _step_in_log(step, content):
            print(f"✅ Step OK: '{step}' found in {log_path.name}")
            return

    _abort_step_done(skill_name, step,
        f"Step '{step}' not found in today's logs ({today_str}). "
        f"Complete this step first before proceeding.")


def _find_log_paths(skill_name, today_str):
    """Auto-discover log file paths for a skill."""
    from pathlib import Path as _Path

    workspace = _Path(os.environ.get("OPENCLAW_STATE_DIR", os.path.expanduser("~/.openclaw/workspace")))
    bases = [workspace, workspace / "workspace"]

    try:
        script_dir = _Path(__file__).resolve().parent
        if (script_dir.parent / "skills").is_dir():
            bases.append(script_dir.parent)
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


def _step_in_log(step, content):
    """Check if step name appears in log content (flexible matching)."""
    step_lower = step.lower()
    content_lower = content.lower()

    if step_lower in content_lower:
        return True

    step_variants = [
        step_lower,
        step_lower.replace("-", "_"),
        step_lower.replace("-", " "),
        step_lower.replace("_", " "),
    ]

    return any(v in content_lower for v in step_variants)


def _abort_step_done(skill, step, reason):
    """Block execution with clear error message."""
    print(f"🛑 STEP BLOCK: {reason}", file=sys.stderr)
    print(f"   Skill: {skill}", file=sys.stderr)
    print(f"   Required step: {step}", file=sys.stderr)
    print(f"   Fix: Complete '{step}' and log it, then try again.", file=sys.stderr)
    sys.exit(1)
