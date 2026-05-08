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

When you have dozens of skills with 200+ line manuals each, the token cost adds up fast.

## The Solution

LazyGuard provides **two layers of protection**:

### Layer 1: Soft Gate (Agent Discipline)

`lazyguard.py` acts as a smart cache between your agent and its skill files:

1. **First read** → Outputs the full file content and records a SHA256 fingerprint.
2. **File unchanged** → Outputs only a 5-line metadata summary — **~97% fewer tokens**.
3. **File changed** → Outputs the full content again and updates the fingerprint.
4. **Session-aware** (`--session <id>`) → Separate cache per session, prevents hallucination after chat clear.
5. **Force flag** (`--force`) → Always outputs full content, ignoring the cache.

### Layer 2: Hard Gate (Script Enforcement)

If the agent skips lazyguard and tries to run a skill script directly, the script **blocks execution**:

```python
# At the top of every skill script:
from lazyguard_gate import require_lazyguard
require_lazyguard("send-recording-line")
```

```
❌ SKILL GUARD NOT RUN: lazyguard.py has never been called for 'send-recording-line'
   → Run: python3 ~/.openclaw/workspace/scripts/lazyguard.py send-recording-line
```

**Why both layers?**
- Layer 1 depends on the agent reading `AGENTS.md` — if the agent is lazy and skips it, Layer 1 is bypassed.
- Layer 2 is a hard block inside the script itself — even if the agent skips everything, it **cannot run the skill** without lazyguard.

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

## 🚀 One-Prompt Install for AI Agents

Copy this prompt and paste it into your AI agent's system prompt, `AGENTS.md`, or equivalent:

```markdown
## ⚠️ LazyGuard — Mandatory Skill Read System

You MUST follow these rules. No exceptions.

### Rule 1: Always use lazyguard.py before using any skill
Before using ANY skill, always run:
  python3 ~/.openclaw/workspace/scripts/lazyguard.py <skill_name>

- NEVER read SKILL.md directly with the `read` tool — always go through lazyguard.py
- If the output includes full content, read it carefully before proceeding
- If the output says UNCHANGED, you already have the context in this session

### Rule 2: What lazyguard.py does
- First time: prints full SKILL.md content + saves hash
- Unchanged: prints 5-line summary only (saves tokens)
- Changed: prints full content again + updates hash
- Use --force to force re-read, --session <id> for session isolation

### Rule 3: If you skip lazyguard, scripts will block you
Every skill script has a hard check at the top:
  from lazyguard_gate import require_lazyguard
  require_lazyguard("<skill_name>")

If you try to run a skill without lazyguard, the script will exit with an error.
There is NO way around this. Run lazyguard first. Always.
```

### Adding Hard Gate to Your Skill Scripts

Add this to the top of every skill script:

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/scripts"))
from lazyguard_gate import require_lazyguard
require_lazyguard("your-skill-name")
```

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

### Safety Features

- **Session-aware cache** — prevents hallucination when agent starts a new session with empty memory
- **Atomic writes** — state file uses `os.replace()` to prevent corruption on crash
- **Corrupt recovery** — invalid JSON in the state file is handled gracefully (resets to empty)
- **Path traversal protection** — session ID is sanitized to `[a-zA-Z0-9_-]` only
- **Garbage collection** — auto-removes session state files older than 7 days
- **Robust error handling** — permission errors, encoding issues, and missing files all produce clear error messages
- **Flexible path resolution** — searches multiple skill directories and supports both `-` and `_` naming conventions

### File Structure

```
LazyGuard/
├── lazyguard.py               # Main script
├── .lazyguard-state.json      # Global hash cache (gitignored)
├── .lazyguard-state-session-<id>.json  # Per-session cache (gitignored, auto-GC)
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
  │       lazyguard.py               │
  │  - Check hash cache              │
  │  - Print content if FRESH/CHANGED│
  │  - Print summary if UNCHANGED    │
  └──────────────┬───────────────────┘
                 │
                 ▼
  ┌──────────────────────────────────┐
  │   skill script (Layer 2: Hard)   │
  │   require_lazyguard() ← BLOCKS  │
  │   if lazyguard not run           │
  └──────────────────────────────────┘
```

## License

MIT

---

# LazyGuard (ภาษาไทย)

**ผู้เฝ้าประตูเข้มงวดที่บังคับให้ AI agent อ่านและแคช SKILL.md ให้ครบก่อนทำงาน — ป้องกันข้อผิดพลาดที่แพงในระบบ production**

## ปัญหา

AI agent ที่ใช้ระบบ skill (เช่น OpenClaw, Claude, GPT) จะเจอปัญหาเดิมทุกครั้งที่เริ่ม session ใหม่:

- **ไม่อ่านเลย** → พลาดรายละเอียดสำคัญ — ใช้ parameter ผิด, ข้าม step, ผลลัพธ์พัง
- **อ่านหมดทุกอย่าง** → เสีย token เป็นพันๆ กับไฟล์ที่ไม่ได้เปลี่ยน
- **อ่านไม่ครบ** → แย่กว่าเดิม — error เงียบจาก context ไม่ครบ

## วิธีแก้ — 2 ชั้นป้องกัน

### ชั้นที่ 1: Soft Gate (วินัย Agent)

`lazyguard.py` ทำหน้าที่เป็น smart cache ระหว่าง agent กับไฟล์ skill:

1. **อ่านครั้งแรก** → พิมพ์เนื้อหาเต็ม + บันทึก SHA256 fingerprint
2. **ไฟล์ไม่เปลี่ยน** → พิมพ์แค่ metadata 5 บรรทัด — **ประหยัด token ~97%**
3. **ไฟล์เปลี่ยน** → พิมพ์เนื้อหาเต็มอีกครั้ง + อัปเดต fingerprint
4. **Session-aware** (`--session <id>`) → แยก cache ตาม session ป้องกัน hallucination หลัง clear chat
5. **Force flag** (`--force`) → พิมพ์เนื้อหาเต็มเสมอ ไม่สน cache

### ชั้นที่ 2: Hard Gate (บล็อกใน Script)

ถ้า agent ขี้เกียจอ่าน AGENTS.md แล้วข้าม lazyguard ไปเลย → script **บล็อกการทำงาน**:

```python
# อยู่ข้างบนทุก skill script:
from lazyguard_gate import require_lazyguard
require_lazyguard("send-recording-line")
```

```
❌ SKILL GUARD NOT RUN: lazyguard.py has never been called for 'send-recording-line'
   → Run: python3 ~/.openclaw/workspace/scripts/lazyguard.py send-recording-line
```

**ทำไมต้อง 2 ชั้น?**
- ชั้น 1 พึ่ง agent อ่าน AGENTS.md — ถ้าขี้เกียจอ่าน ก็ข้ามได้
- ชั้น 2 บล็อกใน script — **ไม่มีทางข้ามได้** ถ้าไม่รัน lazyguard ก่อน

## 🚀 One-Prompt Install (ภาษาไทย)

คัดลอก prompt นี้ไปใส่ใน system prompt หรือ `AGENTS.md` ของ agent:

```markdown
## ⚠️ LazyGuard — ระบบบังคับอ่าน Skill

ต้องทำตามกฎนี้ทุกครั้ง ไม่มีข้อยกเว้น

### กฎ 1: ก่อนใช้ skill ใดๆ ต้องรัน lazyguard.py ก่อนเสมอ
  python3 ~/.openclaw/workspace/scripts/lazyguard.py <ชื่อ_skill>

- ห้ามอ่าน SKILL.md โดยตรง — ต้องผ่าน lazyguard.py เท่านั้น
- ถ้า output มีเนื้อหา → อ่านให้ครบก่อนดำเนินการ
- ถ้า output บอก UNCHANGED → ใช้ context จาก session นี้ได้เลย

### กฎ 2: lazyguard.py ทำอะไร
- ครั้งแรก: พิมพ์ SKILL.md เต็ม + บันทึก hash
- ไม่เปลี่ยน: พิมพ์แค่ 5 บรรทัด (ประหยัด token)
- เปลี่ยน: พิมพ์เต็มใหม่ + อัปเดต hash
- ใช้ --force เพื่อบังคับอ่านใหม่, --session <id> แยก session

### กฎ 3: ถ้าข้าม lazyguard จะถูกบล็อก
ทุก skill script มี hard check ข้างบน:
  from lazyguard_gate import require_lazyguard
  require_lazyguard("<skill_name>")

ถ้ารันโดยไม่ผ่าน lazyguard → script จะ error และไม่ทำงาน
**ไม่มีทางข้ามได้** — ต้องรัน lazyguard ก่อนทุกครั้ง
```

### เพิ่ม Hard Gate ใน Skill Script ของคุณ

เพิ่มนี้ไว้ข้างบนสุดของทุก skill script:

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/scripts"))
from lazyguard_gate import require_lazyguard
require_lazyguard("your-skill-name")
```

## การใช้งาน

```bash
# อ่าน skill (ตรวจอัตโนมัติว่าเนื้อหาเปลี่ยนหรือไม่)
python3 lazyguard.py <ชื่อ_skill>

# บังคับอ่านเต็ม ไม่สน cache
python3 lazyguard.py <ชื่อ_skill> --force

# แยก cache ตาม session (ป้องกัน hallucination)
python3 lazyguard.py <ชื่อ_skill> --session <session_id>

# แสดง skill ทั้งหมด + สถานะการอ่าน
python3 lazyguard.py --list
```

## ความปลอดภัย

- **Session-aware** — แยก cache ตาม session ป้องกัน hallucination หลัง clear chat
- **Atomic writes** — ใช้ `os.replace()` ป้องกัน state file เสียหายเมื่อระบบ crash
- **Path traversal protection** — sanitize session ID เฉพาะ `[a-zA-Z0-9_-]`
- **Garbage collection** — ลบ session state files เก่าเกิน 7 วันอัตโนมัติ
- **กู้คืนจาก state เสีย** — JSON ไม่ valid จะ reset เป็นค่าว่างโดยอัตโนมัติ

## ความต้องการ

- **Python 3.10+**
- **ไม่ต้องติดตั้งอะไรเพิ่ม** — ใช้แค่ standard library

## License

MIT

---

_สร้างสำหรับ [OpenClaw](https://github.com/nicepkg/openclaw) แต่ใช้ได้กับทุกระบบ AI agent ที่ใช้ไฟล์ skill manifest_
