# 🛡 ZeroSkim

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)
![Category: AI Agents](https://img.shields.io/badge/Category-AI_Agents-purple.svg)
![Anti Skimming](https://img.shields.io/badge/Anti_Skimming-Enforced-red.svg)

**Stop AI agents from skimming skill files. ZeroSkim forces full reads, caches intelligently, and blocks execution if the agent tries to skip reading — preventing costly mistakes in production AI systems.**

> *ZeroSkim = Zero Tolerance for Skimming.*

---

## 📑 Table of Contents
- [The Problem](#the-problem)
- [The Solution (2-Layer Gate)](#the-solution--2-layer-protection)
- [Installation & Setup](#installation--setup)
- [One-Prompt Install for AI Agents](#-one-prompt-install-for-ai-agents)
- [Quick Start & Usage](#quick-start--usage)
- [How It Works](#how-it-works)
- [🇹🇭 ZeroSkim (ภาษาไทย)](#-zeroskim-ภาษาไทย)

---

## The Problem

AI agents that use skill-based architectures (OpenClaw, Claude, GPT, etc.) face a dilemma every time they wake up in a new session:

- **Skim nothing** → Miss critical details — wrong parameters, skipped steps, broken workflows.
- **Read everything** → Burn thousands of tokens re-reading files that haven't changed.
- **Partial reads (skimming)** → Even worse — silent failures from incomplete context.
- **Fake memory** → Agent claims it remembers the rules, but its memory was just wiped (hallucination).

When you have dozens of skills with 200+ line manuals each, the token cost adds up fast. **Skimming is the silent killer of AI agent reliability.**

## The Solution — 2-Layer Protection

### Layer 1: Soft Gate (Agent Discipline)

`zeroskim.py` acts as a smart cache between your agent and its skill files:

1. **First read** → Outputs full file content + records SHA256 fingerprint.
2. **File unchanged** → Outputs a 5-line metadata summary (**~97% fewer tokens**).
3. **Session-aware** → Separate cache per session, prevents hallucination after chat clear.

### Layer 2: Hard Gate (Script Enforcement)

If the agent skims or skips ZeroSkim, the script blocks execution:

```text
❌ ZEROSKIM BLOCK: Skill not found in read-cache. Run zeroskim first.
   → Run: python3 zeroskim.py send-recording-line
```

---

## Installation & Setup

**Requirements:** Python 3.10+ (Standard library only).

### 1. The Main Script

Place `zeroskim.py` in your agent's workspace (e.g., `~/.openclaw/workspace/scripts/`).

### 2. The Hard Gate Enforcement

Place `zeroskim_gate.py` (included in this repo) in the same directory. This enforces a **5-minute rule**: the agent must have called ZeroSkim within the last 5 minutes to run a skill.

### 3. Protecting Your Skills

Add this snippet to the top of every skill script you want to protect:

```python
import sys, os
scripts_dir = os.environ.get("OPENCLAW_SCRIPTS_DIR", os.path.expanduser("~/.openclaw/workspace/scripts"))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)
from zeroskim_gate import require_zeroskim

# Blocks execution if ZeroSkim hasn't been run recently
require_zeroskim("your-skill-name", session_id=os.environ.get("OPENCLAW_SESSION_ID"))
```

---

## 🚀 One-Prompt Install for AI Agents

Copy this to your `AGENTS.md` or System Prompt to discipline your agent:

```markdown
## ⚠️ ZeroSkim — Anti-Skimming Skill Read System

You MUST follow these rules. No exceptions. Skimming kills reliability.

### Rule 1: Always use zeroskim.py before using any skill
Before using ANY skill, always run:
  python3 zeroskim.py <skill_name> [--session <id>]

- NEVER read SKILL.md directly with the `read` tool — always go through zeroskim.py.
- If the output includes full content, read it carefully before proceeding.
- If the output says UNCHANGED, you already have the context in this session.

### Rule 2: The 5-Minute Enforcement
You must have called ZeroSkim within the last 5 minutes to run a skill. If you wait too long, the script will BLOCK you. Re-run ZeroSkim to refresh your context.

### Rule 3: No Bypassing
Skill scripts will hard-block execution if Rule 1 and Rule 2 are not met. No shortcuts. Run zeroskim first. Always.
```

---

## Quick Start & Usage

**Command Line Usage:**

```bash
# Read a skill (auto-detects if content has changed)
python3 zeroskim.py <skill_name>

# Force a full re-read regardless of cache
python3 zeroskim.py <skill_name> --force

# Session-aware cache (prevents hallucination after chat clear)
python3 zeroskim.py <skill_name> --session <session_id>

# List all discovered skills and their read status
python3 zeroskim.py --list
```

**Example Output:**

```
$ python3 zeroskim.py music-class-summarizer
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

## Why "ZeroSkim"?

**Skim** = to read something quickly and superficially, missing important details.  
**Zero Skim** = zero tolerance for superficial reading. Every skill must be fully read before use.

AI agents love to skim. ZeroSkim makes sure they don't.

---

## 📦 ติดตั้งเป็น Package

### Python (pip)

```bash
pip install zeroskim
```

```python
from zeroskim import ZeroSkim, require_zeroskim

zs = ZeroSkim(workspace_dir="/path/to/workspace")
result = zs.read("my-skill", session_id="abc123")
require_zeroskim("my-skill")  # บล็อกถ้ายังไม่ได้อ่าน
```

### Node.js (npm)

```bash
npm install zeroskim
```

```javascript
const { ZeroSkim, requireZeroskim } = require('zeroskim');

const zs = new ZeroSkim({ workspaceDir: '/path/to/workspace' });
const result = zs.read('my-skill', { sessionId: 'abc123' });
requireZeroskim('my-skill');  // บล็อกถ้ายังไม่ได้อ่าน
```

> 📖 รายละเอียดเพิ่มเติม: [`PACKAGE.md`](./PACKAGE.md)

---

## License

MIT

---

# 🇹🇭 ZeroSkim (ภาษาไทย)

ระบบป้องกัน AI Agent อ่านแบบเลื่อนไหล (Skimming) — บังคับให้อ่านกฎ (SKILL.md) ให้จบก่อนเริ่มงานเสมอ เพื่อป้องกันความเสียหายร้ายแรงในระบบ Production

## ปัญหา

AI agent มักจะเจอปัญหาเดิมๆ ทุกครั้งที่เริ่ม session ใหม่:

- **ไม่อ่านกฎเลย (Skim)** → พลาดรายละเอียดสำคัญ, ใส่ parameter ผิด, ข้ามขั้นตอน
- **อ่านหมดทุกอย่างซ้ำๆ** → เสีย Token มหาศาลไปกับไฟล์ที่ไม่ได้เปลี่ยน
- **แกล้งจำได้** → เกิดอาการ AI "หลอน" (Hallucination) ว่าจำกฎได้ทั้งที่เพิ่งล้างความจำ

## วิธีแก้ — ระบบป้องกัน 2 ชั้น

### ชั้นที่ 1: Soft Gate (สร้างวินัย)

`zeroskim.py` ทำหน้าที่เป็นแคชอัจฉริยะ:

- **รันครั้งแรก**: พิมพ์เนื้อหาเต็ม + บันทึก SHA256 Hash
- **ไฟล์ไม่เปลี่ยน**: พิมพ์สรุป 5 บรรทัด (ประหยัด Token ~97%)
- **แยกตาม Session**: ป้องกันการสับสนระหว่างแชทเก่าและแชทใหม่

### ชั้นที่ 2: Hard Gate (บล็อกในโค้ด)

ใช้ `zeroskim_gate.py` ใส่ไว้ในทุก Skill Script:

- **กฎ 5 นาที**: AI จะต้องรัน ZeroSkim มาไม่เกิน 5 นาทีก่อนรันงานจริง มิฉะนั้นสคริปต์จะ **บล็อกการทำงานทันที**
- **บังคับวินัย**: ไม่มีทางลัด AI ต้องผ่านด่านตรวจก่อนเสมอ

## 🚀 Prompt สำหรับตั้งค่า AI Agent (One-Prompt Install)

คัดลอก Prompt ด้านล่างนี้ไปใส่ใน `AGENTS.md` หรือ System Prompt ของ AI เพื่อสร้างวินัยให้ Agent ของคุณ:

```markdown
## ⚠️ ZeroSkim — ระบบ Anti-Skimming (คำสั่งบังคับ)

คุณต้องทำตามกฎเหล่านี้ทุกครั้ง ไม่มีข้อยกเว้น

### กฎข้อที่ 1: ต้องใช้ zeroskim.py ก่อนใช้ Skill เสมอ
ก่อนที่จะใช้งาน Skill ใดๆ คุณต้องรันคำสั่งนี้ก่อนเสมอ:
  python3 zeroskim.py <skill_name> [--session <id>]

- ห้ามอ่านไฟล์ SKILL.md โดยตรงผ่านเครื่องมือ read เด็ดขาด — ต้องอ่านผ่าน zeroskim.py เท่านั้น
- ถ้าผลลัพธ์แสดงเนื้อหาแบบเต็ม ให้คุณอ่านให้ละเอียดก่อนทำงาน
- ถ้าผลลัพธ์แสดงคำว่า UNCHANGED แปลว่าคุณมีข้อมูลนี้ในความจำของ session นี้แล้ว ทำงานต่อได้เลย

### กฎข้อที่ 2: กฎ 5 นาที (The 5-Minute Enforcement)
คุณต้องรัน ZeroSkim มาไม่เกิน 5 นาทีก่อนที่จะเรียกใช้ Skill หากคุณทิ้งช่วงนานเกินไป สคริปต์จะ BLOCK คุณทันที ให้คุณรัน ZeroSkim ใหม่อีกครั้งเพื่อรีเฟรชความจำ

### กฎข้อที่ 3: ห้ามแอบข้ามขั้นตอน
Skill Scripts ถูกเขียนไว้ให้บล็อกการทำงานทันทีหากคุณไม่ทำตามกฎข้อ 1 และ 2 ไม่มีทางลัด คุณต้องรัน zeroskim ก่อนเสมอ!
```

## การติดตั้ง

1. วาง `zeroskim.py` และ `zeroskim_gate.py` ใน workspace ของ agent
2. เพิ่มโค้ดที่ด้านบนของทุก skill script:

```python
import sys, os
scripts_dir = os.environ.get("OPENCLAW_SCRIPTS_DIR", os.path.expanduser("~/.openclaw/workspace/scripts"))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)
from zeroskim_gate import require_zeroskim

require_zeroskim("your-skill-name", session_id=os.environ.get("OPENCLAW_SESSION_ID"))
```

## 📦 Install as Package

### Python (pip)

```bash
pip install zeroskim
```

```python
from zeroskim import ZeroSkim, require_zeroskim

# Read a skill with anti-skimming cache
zs = ZeroSkim(workspace_dir="/path/to/workspace")
result = zs.read("my-skill", session_id="abc123")

# Hard gate enforcement in skill scripts
require_zeroskim("my-skill")  # Exits if not read recently
```

### Node.js (npm)

```bash
npm install zeroskim
```

```javascript
const { ZeroSkim, requireZeroskim } = require('zeroskim');

// Read a skill with anti-skimming cache
const zs = new ZeroSkim({ workspaceDir: '/path/to/workspace' });
const result = zs.read('my-skill', { sessionId: 'abc123' });

// Hard gate enforcement in skill scripts
requireZeroskim('my-skill');  // Exits if not read recently
```

> 📖 Full package docs: [`PACKAGE.md`](./PACKAGE.md)

---

## License

MIT

---

_Created by [Chunny](https://github.com/chunnytechmate) | Built for AI Agents & [OpenClaw](https://github.com/nicepkg/openclaw)_
