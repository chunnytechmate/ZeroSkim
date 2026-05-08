# LazyGuard

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)

**A strict gatekeeper that forces lazy AI agents to fully read and cache SKILL.md before execution — preventing costly mistakes in production AI systems.**

---

## The Problem

AI agents that use skill-based architectures (OpenClaw, Claude, GPT, etc.) face a dilemma every time they wake up in a new session:

- **Read nothing** → Miss critical details — wrong parameters, skipped steps, broken workflows.
- **Read everything** → Burn thousands of tokens re-reading files that haven't changed.
- **Partial reads** → Even worse — silent failures from incomplete context.
- **Fake memory** → Agent claims it remembers the rules, but its memory was just wiped (hallucination).

When you have dozens of skills with 200+ line manuals each, the token cost adds up fast.

## The Solution — 2-Layer Protection

### Layer 1: Soft Gate (Agent Discipline)

`lazyguard.py` acts as a smart cache between your agent and its skill files:

1. **First read** → Outputs the full file content and records a SHA256 fingerprint.
2. **File unchanged** → Outputs only a 5-line metadata summary — **~97% fewer tokens**.
3. **File changed** → Outputs the full content again and updates the fingerprint.
4. **Session-aware** (`--session <id>`) → Separate cache per session, prevents hallucination after chat clear.
5. **Force flag** (`--force`) → Always outputs full content, ignoring the cache.

### Layer 2: Hard Gate (Script Enforcement)

If the agent skips LazyGuard and tries to run a skill script directly, the script **blocks execution**:

```
❌ LAZYGUARD BLOCK: Skill not found in read-cache. Run lazyguard first.
 → Run: python3 lazyguard.py send-recording-line
```

**Why both layers?**
- Layer 1 depends on the agent reading `AGENTS.md` — if the agent is lazy and skips it, Layer 1 is bypassed.
- Layer 2 is a hard block inside the script itself — even if the agent skips everything, it **cannot run the skill** without LazyGuard.

## Quick Start

```
$ python3 lazyguard.py music-class-summarizer
📖 FIRST READ (219 lines)
📌 Path: /skills/music-class-summarizer/SKILL.md

--- SKILL.md CONTENT ---
(full content here...)
--- END (219 lines) ---
⚠️ SYSTEM DIRECTIVE: You MUST read and strictly follow ALL rules and formats specified above before proceeding.
```

```
$ python3 lazyguard.py music-class-summarizer
✅ UNCHANGED — already read (219 lines)
📌 Path: /skills/music-class-summarizer/SKILL.md
📖 Last read: 2026-05-08T12:45:11
🔑 Hash: f74e5050ca0cbc8a...
📌 Action: No re-read needed — use session memory
```

## Usage

```bash
# Read a skill (auto-detects if content has changed)
python3 lazyguard.py <skill_name>

# Force a full re-read regardless of cache
python3 lazyguard.py <skill_name> --force

# Session-aware cache (prevents hallucination after chat clear)
python3 lazyguard.py <skill_name> --session <session_id>

# List all discovered skills and their read status
python3 lazyguard.py --list
```

---

## Installation & Setup

### 1. The Main Script

Place `lazyguard.py` in your agent's workspace (e.g., `~/.openclaw/workspace/scripts/`).

### 2. The Hard Gate Enforcement

Create a file named `lazyguard_gate.py` in the same directory. This script ensures the agent's memory is fresh (within 5 minutes).

```python
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
    if session_id:
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '', session_id) or "default"
        state_file = os.path.join(BASE_STATE_DIR, f".lazyguard-state-session-{safe_id}.json")
    else:
        state_file = os.path.join(BASE_STATE_DIR, ".lazyguard-state.json")

    if not os.path.isfile(state_file):
        _abort(skill_name, "No LazyGuard state found for this session.")

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
    except:
        _abort(skill_name, "State file corrupt.")

    if skill_name not in state:
        _abort(skill_name, "Skill not found in read-cache. Run lazyguard first.")

    entry = state[skill_name]
    last_read = datetime.fromisoformat(entry.get("last_read", "1970-01-01T00:00:00"))
    age = datetime.now() - last_read

    if age > timedelta(minutes=MAX_AGE_MINUTES):
        _abort(skill_name, f"Read-cache EXPIRED ({int(age.total_seconds()/60)} mins ago).")

    print(f"✅ LazyGuard OK: '{skill_name}' active ({int(age.total_seconds())}s ago).")

def _abort(skill, reason):
    print(f"❌ LAZYGUARD BLOCK: {reason}\n → Run: python3 lazyguard.py {skill}")
    sys.exit(1)
```

### 3. Protecting Your Skills

Add this to the top of every skill script:

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/scripts"))
from lazyguard_gate import require_lazyguard

# This will block execution if LazyGuard hasn't been run recently
require_lazyguard("your-skill-name", session_id=os.environ.get("OPENCLAW_SESSION_ID"))
```

---

## 🚀 One-Prompt Install for AI Agents

Copy this to your `AGENTS.md` or System Prompt:

```markdown
## ⚠️ LazyGuard — Mandatory Skill Read System

You MUST follow these rules. No exceptions.

### Rule 1: Always use lazyguard.py before using any skill
Before using ANY skill, always run:
  python3 ~/.openclaw/workspace/scripts/lazyguard.py <skill_name> [--session <id>]

- NEVER read SKILL.md directly with the `read` tool — always go through lazyguard.py.
- If the output includes full content, read it carefully before proceeding.
- If the output says UNCHANGED, you already have the context in this session.

### Rule 2: The 5-Minute Enforcement
You must have called LazyGuard within the last 5 minutes to run a skill. If you wait too long, the script will BLOCK you. Re-run LazyGuard to refresh your context.

### Rule 3: No Bypassing
Skill scripts will hard-block execution if Rule 1 and Rule 2 are not met. Run lazyguard first. Always.
```

---

## How It Works

| Scenario | Behavior |
|----------|----------|
| First read ever | Print full content + save hash |
| File unchanged since last read | Print 5-line summary only |
| File modified since last read | Print full content + update hash |
| `--force` flag | Always print full content |
| `--session <id>` | Separate state file per session |
| New session (no cache) | Print full content (first read) |
| Corrupt state file | Auto-recover — starts fresh |
| Skill file not found | Print error, exit with code 1 |

### Safety & Auto-Maintenance

- **SHA256 Fingerprinting** — Automatically detects any changes in your SKILL.md files.
- **Session-aware Cache** — Prevents hallucination after a chat clear by isolating context per session.
- **Auto Garbage Collection (GC)** — Removes session state files older than 7 days automatically.
- **Atomic Writes** — Prevents state file corruption during crashes using `os.replace()`.
- **Path Traversal Protection** — Sanitizes session IDs to `[a-zA-Z0-9_-]` only.

### File Structure

```
LazyGuard/
├── lazyguard.py                          # Main script
├── lazyguard_gate.py                     # Hard gate enforcement (import in skill scripts)
├── .lazyguard-state.json                 # Global hash cache (gitignored)
├── .lazyguard-state-session-<id>.json    # Per-session cache (gitignored, auto-GC)
└── README.md
```

## Requirements

- **Python 3.10+** (uses `str | None` union syntax)
- **No external dependencies** — standard library only

## Architecture Diagram

```
  AI Agent
     │
     ▼
  ┌──────────────────────────────────┐
  │  AGENTS.md (Layer 1: Soft Gate)  │
  │  "Run lazyguard.py before skill" │
  └──────────────┬───────────────────┘
                 │
                 ▼
  ┌──────────────────────────────────┐
  │         lazyguard.py             │
  │  - Check hash cache              │
  │  - Print content if FRESH/CHANGED│
  │  - Print summary if UNCHANGED    │
  └──────────────┬───────────────────┘
                 │
                 ▼
  ┌──────────────────────────────────┐
  │  skill script (Layer 2: Hard)    │
  │  require_lazyguard() ← BLOCKS    │
  │  if not read in < 5 minutes      │
  └──────────────────────────────────┘
```

## License

MIT

---

# 🇹🇭 LazyGuard (ภาษาไทย)

**ผู้คุมกฎสุดเข้มงวดที่ดัดนิสัย AI agent ขี้เกียจ บังคับให้อ่านกฎ (SKILL.md) ให้จบก่อนเริ่มงาน — ป้องกันข้อผิดพลาดที่ราคาแพงในระบบ Production**

## ปัญหา

AI agent มักจะเจอปัญหาเดิมๆ ทุกครั้งที่เริ่ม session ใหม่:

- **ไม่อ่านกฎเลย** → พลาดรายละเอียดสำคัญ, ใส่ parameter ผิด, ข้ามขั้นตอน
- **อ่านหมดทุกอย่างซ้ำๆ** → เสีย Token มหาศาลไปกับไฟล์ที่ไม่ได้เปลี่ยน
- **แกล้งจำได้** → เกิดอาการ AI "หลอน" (Hallucination) ว่าจำกฎได้ทั้งที่เพิ่งล้างความจำ

## วิธีแก้ — ระบบป้องกัน 2 ชั้น

### ชั้นที่ 1: Soft Gate (สร้างวินัย)

`lazyguard.py` ทำหน้าที่เป็นแคชอัจฉริยะ:

- **รันครั้งแรก**: พิมพ์เนื้อหาเต็ม + บันทึก SHA256 Hash
- **ไฟล์ไม่เปลี่ยน**: พิมพ์สรุป 5 บรรทัด (ประหยัด Token ~97%)
- **แยกตาม Session**: ป้องกันการสับสนระหว่างแชทเก่าและแชทใหม่

### ชั้นที่ 2: Hard Gate (บล็อกในโค้ด)

ใช้ `lazyguard_gate.py` ใส่ไว้ในทุก Skill Script:

- **กฎ 5 นาที**: AI จะต้องรัน LazyGuard มาไม่เกิน 5 นาทีก่อนรันงานจริง มิฉะนั้นสคริปต์จะ **บล็อกการทำงานทันที**
- **บังคับวินัย**: ไม่มีทางลัด AI ต้องผ่านด่านตรวจก่อนเสมอ

## การติดตั้ง

### 1. วาง `lazyguard.py` ใน workspace ของ agent

### 2. วาง `lazyguard_gate.py` ใน directory เดียวกัน

### 3. เพิ่มที่ด้านบนของทุก skill script:

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/scripts"))
from lazyguard_gate import require_lazyguard

require_lazyguard("your-skill-name", session_id=os.environ.get("OPENCLAW_SESSION_ID"))
```

## ฟีเจอร์เด่น

- **SHA256 Fingerprinting**: ตรวจพบทุกความเปลี่ยนแปลงในไฟล์กฎของคุณ
- **Garbage Collection (GC)**: ลบไฟล์แคชเก่า (เกิน 7 วัน) ให้อัตโนมัติ
- **ปลอดภัย**: ป้องกัน Path Traversal และไฟล์พังด้วย Atomic Writes
- **Session-aware**: แยก cache ตาม session ป้องกัน hallucination หลัง clear chat

## ความต้องการ

- **Python 3.10+**
- **ไม่ต้องติดตั้งอะไรเพิ่ม** — ใช้แค่ standard library

## License

MIT

---

_Created by [Chunny](https://github.com/chunnytechmate) | Built for AI Agents & [OpenClaw](https://github.com/nicepkg/openclaw)_
