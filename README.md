# 🛡 LazyGuard

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)
![Category: AI Agents](https://img.shields.io/badge/Category-AI_Agents-purple.svg)

**A strict gatekeeper that forces lazy AI agents to fully read and cache SKILL.md before execution — preventing costly mistakes in production AI systems.**

---

## 📑 Table of Contents
- [The Problem](#the-problem)
- [The Solution (2-Layer Gate)](#the-solution--2-layer-protection)
- [Installation & Setup](#installation--setup)
- [One-Prompt Install for AI Agents](#-one-prompt-install-for-ai-agents)
- [Quick Start & Usage](#quick-start--usage)
- [How It Works](#how-it-works)
- [🇹🇭 LazyGuard (ภาษาไทย)](#-lazyguard-ภาษาไทย)

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

1. **First read** → Outputs full file content + records SHA256 fingerprint.
2. **File unchanged** → Outputs a 5-line metadata summary (**~97% fewer tokens**).
3. **Session-aware** → Separate cache per session, prevents hallucination after chat clear.

### Layer 2: Hard Gate (Script Enforcement)

If the agent skips LazyGuard, the script blocks execution:

```text
❌ LAZYGUARD BLOCK: Skill not found in read-cache. Run lazyguard first.
   → Run: python3 lazyguard.py send-recording-line
```

---

## Installation & Setup

**Requirements:** Python 3.10+ (Standard library only).

### 1. The Main Script

Place `lazyguard.py` in your agent's workspace (e.g., `~/.openclaw/workspace/scripts/`).

### 2. The Hard Gate Enforcement

Place `lazyguard_gate.py` (included in this repo) in the same directory. This enforces a **5-minute rule**: the agent must have called LazyGuard within the last 5 minutes to run a skill.

### 3. Protecting Your Skills

Add this snippet to the top of every skill script you want to protect:

```python
import sys, os
scripts_dir = os.environ.get("OPENCLAW_SCRIPTS_DIR", os.path.expanduser("~/.openclaw/workspace/scripts"))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)
from lazyguard_gate import require_lazyguard

# Blocks execution if LazyGuard hasn't been run recently
require_lazyguard("your-skill-name", session_id=os.environ.get("OPENCLAW_SESSION_ID"))
```

---

## 🚀 One-Prompt Install for AI Agents

Copy this to your `AGENTS.md` or System Prompt to discipline your agent:

```markdown
## ⚠️ LazyGuard — Mandatory Skill Read System

You MUST follow these rules. No exceptions.

### Rule 1: Always use lazyguard.py before using any skill
Before using ANY skill, always run:
  python3 lazyguard.py <skill_name> [--session <id>]

- NEVER read SKILL.md directly with the `read` tool — always go through lazyguard.py.
- If the output includes full content, read it carefully before proceeding.
- If the output says UNCHANGED, you already have the context in this session.

### Rule 2: The 5-Minute Enforcement
You must have called LazyGuard within the last 5 minutes to run a skill. If you wait too long, the script will BLOCK you. Re-run LazyGuard to refresh your context.

### Rule 3: No Bypassing
Skill scripts will hard-block execution if Rule 1 and Rule 2 are not met. Run lazyguard first. Always.
```

---

## Quick Start & Usage

**Command Line Usage:**

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

**Example Output:**

```
$ python3 lazyguard.py music-class-summarizer
✅ UNCHANGED — already read (219 lines)
📌 Path: /skills/music-class-summarizer/SKILL.md
📖 Last read: 2026-05-08T12:45:11
🔑 Hash: f74e5050ca0cbc8a...
📌 Action: ALREADY IN CONTEXT — Proceed with task.
```

---

## How It Works

| Scenario | Behavior |
|----------|----------|
| Initial read | Print full content + save hash |
| File unchanged | Print 5-line summary only |
| File modified | Print full content + update hash |
| `--session <id>` | Separate state file per session |
| New session (empty cache) | Print full content (first read) |
| Corrupt state file | Auto-recover — starts fresh |

### Safety & Auto-Maintenance

- **SHA256 Fingerprinting**: Automatically detects any changes in your SKILL.md.
- **Auto Garbage Collection (GC)**: Removes session state files older than 7 days.
- **Atomic Writes**: Prevents state file corruption using `os.replace()`.
- **Path Traversal Protection**: Sanitizes session IDs to `[a-zA-Z0-9_-]` only.

---

## License

MIT

---

# 🇹🇭 LazyGuard (ภาษาไทย)

ผู้คุมกฎสุดเข้มงวดที่ดัดนิสัย AI agent ขี้เกียจ บังคับให้อ่านกฎ (SKILL.md) ให้จบก่อนเริ่มงาน — ป้องกันความเสียหายร้ายแรงในระบบ Production

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

## 🚀 Prompt สำหรับตั้งค่า AI Agent (One-Prompt Install)

คัดลอก Prompt ด้านล่างนี้ไปใส่ใน `AGENTS.md` หรือ System Prompt ของ AI เพื่อสร้างวินัยให้ Agent ของคุณ:

```markdown
## ⚠️ LazyGuard — ระบบบังคับอ่าน Skill (คำสั่งบังคับ)

คุณต้องทำตามกฎเหล่านี้ทุกครั้ง ไม่มีข้อยกเว้น

### กฎข้อที่ 1: ต้องใช้ lazyguard.py ก่อนใช้ Skill เสมอ
ก่อนที่จะใช้งาน Skill ใดๆ คุณต้องรันคำสั่งนี้ก่อนเสมอ:
  python3 lazyguard.py <skill_name> [--session <id>]

- ห้ามอ่านไฟล์ SKILL.md โดยตรงผ่านเครื่องมือ read เด็ดขาด — ต้องอ่านผ่าน lazyguard.py เท่านั้น
- ถ้าผลลัพธ์แสดงเนื้อหาแบบเต็ม ให้คุณอ่านให้ละเอียดก่อนทำงาน
- ถ้าผลลัพธ์แสดงคำว่า UNCHANGED แปลว่าคุณมีข้อมูลนี้ในความจำของ session นี้แล้ว ทำงานต่อได้เลย

### กฎข้อที่ 2: กฎ 5 นาที (The 5-Minute Enforcement)
คุณต้องรัน LazyGuard มาไม่เกิน 5 นาทีก่อนที่จะเรียกใช้ Skill หากคุณทิ้งช่วงนานเกินไป สคริปต์จะ BLOCK คุณทันที ให้คุณรัน LazyGuard ใหม่อีกครั้งเพื่อรีเฟรชความจำ

### กฎข้อที่ 3: ห้ามแอบข้ามขั้นตอน
Skill Scripts ถูกเขียนไว้ให้บล็อกการทำงานทันทีหากคุณไม่ทำตามกฎข้อ 1 และ 2 ไม่มีทางลัด คุณต้องรัน lazyguard ก่อนเสมอ!
```

## การติดตั้ง

1. วาง `lazyguard.py` และ `lazyguard_gate.py` ใน workspace ของ agent
2. เพิ่มโค้ดที่ด้านบนของทุก skill script:

```python
import sys, os
scripts_dir = os.environ.get("OPENCLAW_SCRIPTS_DIR", os.path.expanduser("~/.openclaw/workspace/scripts"))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)
from lazyguard_gate import require_lazyguard

require_lazyguard("your-skill-name", session_id=os.environ.get("OPENCLAW_SESSION_ID"))
```

## License

MIT

---

_Created by [Chunny](https://github.com/chunnytechmate) | Built for AI Agents & [OpenClaw](https://github.com/nicepkg/openclaw)_
