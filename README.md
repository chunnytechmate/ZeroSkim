# 🛡 ZeroSkim

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Node.js 18+](https://img.shields.io/badge/node-18%2B-brightgreen.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)
![Category: AI Agents](https://img.shields.io/badge/Category-AI_Agents-purple.svg)

**Stop AI agents from skimming skill files. ZeroSkim forces full reads, intelligently caches context, and hard-blocks execution if the agent attempts a shortcut — preventing costly mistakes in production AI systems.**

> *ZeroSkim = Zero Tolerance for Skimming.*

---

## 📑 Table of Contents
- [The Problem](#the-problem)
- [The Solution (2-Layer Gate)](#the-solution--2-layer-protection)
- [Installation (Package & Standalone)](#-installation)
- [One-Prompt Install for AI Agents](#-one-prompt-install-for-ai-agents)
- [Quick Start & Usage](#quick-start--usage)
- [How It Works](#how-it-works)
- [🇹🇭 ZeroSkim (ภาษาไทย)](#-zeroskim-ภาษาไทย)

---

## The Problem

AI agents utilizing skill-based architectures (OpenClaw, Claude, GPT, etc.) face a recurring dilemma every time they initialize a new session:

- **Skip reading entirely** → Miss critical directives, leading to invalid parameters, skipped steps, and broken workflows.
- **Read everything repeatedly** → Burn thousands of tokens re-reading files that haven't changed.
- **Partial reads (Skimming)** → The silent killer. Causes unpredictable failures due to incomplete context.
- **Fake memory (Hallucination)** → The agent confidently claims it remembers the rules, even though its memory was just wiped.

When scaling to dozens of skills with extensive manuals, token burn and error rates scale exponentially. **Skimming is the silent killer of AI agent reliability.**

## The Solution — 2-Layer Protection

### Layer 1: Soft Gate (Agent Discipline)
ZeroSkim acts as a smart, session-aware cache between your agent and its skill files:
1. **Initial read** → Outputs full file content and records a SHA256 fingerprint.
2. **File unchanged** → Outputs a 5-line metadata summary (**~97% fewer tokens**).
3. **Session isolation** → Separates cache per session ID, completely preventing hallucination after a chat reset.

### Layer 2: Hard Gate (Script Enforcement)
If the agent attempts to skim or skip ZeroSkim entirely, the script immediately blocks execution:
```text
❌ ZEROSKIM BLOCK: Skill not found in read-cache. Run zeroskim first.
 → Run: npx zeroskim send-recording-line
```

## 📦 Installation

ZeroSkim can be installed as a modern package or used as a standalone script.

### Option A: Install as Package (Recommended)

**For Python (PyPI):**
```bash
pip install zeroskim
```
```python
from zeroskim import ZeroSkim, require_zeroskim

zs = ZeroSkim(workspace_dir="/path/to/workspace")
result = zs.read("my-skill", session_id="abc123")

# Enforce the 5-Minute Rule in your skill scripts
require_zeroskim("my-skill")
```

**For Node.js (npm):**
```bash
npm install zeroskim
```
```javascript
const { ZeroSkim, requireZeroskim } = require('zeroskim');

const zs = new ZeroSkim({ workspaceDir: '/path/to/workspace' });
const result = zs.read('my-skill', { sessionId: 'abc123' });

// Enforce the 5-Minute Rule in your skill scripts
requireZeroskim('my-skill');
```

📖 Full API documentation: [`PACKAGE.md`](./PACKAGE.md)

### Option B: Standalone Script Installation

If you prefer not to use package managers, you can drop the scripts directly into your project:

1. Place `zeroskim.py` and `zeroskim_gate.py` into your agent's workspace directory.
2. Import the gate directly into your skill scripts:

```python
import sys, os
sys.path.insert(0, os.environ.get("OPENCLAW_SCRIPTS_DIR", "/your/path"))
from zeroskim_gate import require_zeroskim

require_zeroskim("your-skill-name", session_id=os.environ.get("OPENCLAW_SESSION_ID"))
```

## 🚀 One-Prompt Install for AI Agents

Copy this snippet to your `AGENTS.md` or the agent's System Prompt to enforce strict discipline:

```markdown
## ⚠️ ZeroSkim — Anti-Skimming Skill Read System

You MUST follow these rules. No exceptions. Skimming kills reliability.

### Rule 1: Always use ZeroSkim before using any skill
Before executing ANY skill, you must always run:
  zeroskim <skill_name> [--session <id>]

- NEVER read SKILL.md directly using standard read tools — always route through ZeroSkim.
- If the output includes full content, read it carefully and completely before proceeding.
- If the output says UNCHANGED, you already have the required context in this session.

### Rule 2: The 5-Minute Enforcement
You must have called ZeroSkim within the last 5 minutes to run a skill. If you wait too long, the script will BLOCK you. Re-run ZeroSkim to refresh your context.

### Rule 3: No Shortcuts
Skill scripts will hard-block execution if Rule 1 and Rule 2 are not met. No shortcuts. Run zeroskim first. Always.
```

## Quick Start & Usage

**Command Line Usage (Python / Node CLI):**
```bash
# Read a skill (auto-detects if content has changed)
zeroskim <skill_name>

# Force a full re-read regardless of cache
zeroskim <skill_name> --force

# Session-aware cache (prevents hallucination after chat clear)
zeroskim <skill_name> --session <session_id>

# List all discovered skills and their read status
zeroskim --list
```

**Example Output:**
```text
$ zeroskim music-class-summarizer
✅ UNCHANGED — already read (219 lines)
📌 Path: /skills/music-class-summarizer/SKILL.md
📖 Last read: 2026-05-08T12:45:11
🔑 Hash: f74e5050ca0cbc8a...
📌 Action: ALREADY IN CONTEXT — Proceed with task.
```

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
- **SHA256 Fingerprinting**: Automatically detects even a single-character change in your SKILL.md.
- **Auto Garbage Collection (GC)**: Seamlessly removes session state files older than 7 days.
- **Atomic Writes**: Prevents state file corruption during unexpected crashes using `os.replace()`.
- **Path Traversal Protection**: Strictly sanitizes session IDs to `[a-zA-Z0-9_-]` only.

## License

MIT

---

# 🇹🇭 ZeroSkim (ภาษาไทย)

ระบบป้องกัน AI Agent อ่านแบบลวกๆ (Skimming) — บังคับให้อ่านกฎ (SKILL.md) ให้จบก่อนเริ่มงานเสมอ เพื่อป้องกันความเสียหายร้ายแรงในระดับ Production

## ปัญหา

AI agent มักจะเจอปัญหาเดิมๆ ทุกครั้งที่เริ่มต้น Session ใหม่:

- **ข้ามการอ่านไปเลย** → พลาดรายละเอียดสำคัญ, ใส่ parameter ผิด, ข้ามขั้นตอนการทำงาน
- **อ่านทุกอย่างซ้ำไปซ้ำมา** → สูญเสีย Token มหาศาลไปกับไฟล์ที่ไม่ได้ถูกแก้ไข
- **อ่านลวกๆ (Skim)** → ตัวการสำคัญที่ทำให้เกิด Error เงียบ เพราะได้ Context ไปไม่ครบ
- **แกล้งทำเป็นจำได้ (Hallucination)** → AI หลอนไปเองว่าจำกฎได้ ทั้งที่เพิ่งถูกล้างความจำไป

## วิธีแก้ — ระบบป้องกัน 2 ชั้น

### ชั้นที่ 1: Soft Gate (สร้างวินัย)
ZeroSkim ทำหน้าที่เป็นแคชอัจฉริยะ:
- **รันครั้งแรก**: พิมพ์เนื้อหาเต็ม + บันทึก SHA256 Hash
- **ไฟล์ไม่เปลี่ยน**: พิมพ์สรุป 5 บรรทัด (ช่วยประหยัด Token ได้ถึง ~97%)
- **แยกตาม Session**: ป้องกันการสับสนระหว่างแชทเก่าและแชทใหม่

### ชั้นที่ 2: Hard Gate (บล็อกในระดับโค้ด)
ใช้ `require_zeroskim` ติดตั้งไว้ในทุก Skill Script:
- **กฎ 5 นาที**: AI จะต้องรัน ZeroSkim มาไม่เกิน 5 นาทีก่อนรันงานจริง มิฉะนั้นสคริปต์จะ **บล็อกการทำงานทันที**
- **ไม่อนุญาตให้ใช้ทางลัด**: AI ต้องผ่านด่านตรวจก่อนเสมอ ไม่มีข้อยกเว้น

## 📦 การติดตั้ง

ZeroSkim รองรับการติดตั้งแบบ Package มาตรฐานเพื่อความสะดวกสูงสุด

### Python (ผ่าน pip)
```bash
pip install zeroskim
```
```python
from zeroskim import require_zeroskim
require_zeroskim("my-skill")  # บล็อกทันทีถ้ายังไม่ได้อ่าน
```

### Node.js (ผ่าน npm)
```bash
npm install zeroskim
```
```javascript
const { requireZeroskim } = require('zeroskim');
requireZeroskim('my-skill'); // บล็อกทันทีถ้ายังไม่ได้อ่าน
```

💡 หากไม่ต้องการติดตั้งผ่าน Package คุณสามารถนำสคริปต์ `zeroskim.py` ไปวางในโปรเจกต์โดยตรงได้เช่นกัน

## 🚀 Prompt สำหรับตั้งค่า AI Agent (One-Prompt Install)

คัดลอก Prompt ด้านล่างนี้ไปใส่ใน `AGENTS.md` หรือ System Prompt ของ AI เพื่อสร้างวินัยการอ่านที่เข้มงวด:

```markdown
## ⚠️ ZeroSkim — ระบบ Anti-Skimming (คำสั่งบังคับ)

คุณต้องทำตามกฎเหล่านี้ทุกครั้ง ไม่มีข้อยกเว้น การอ่านแบบลวกๆ จะทำให้ระบบพัง

### กฎข้อที่ 1: ต้องใช้ ZeroSkim ก่อนใช้ Skill เสมอ
ก่อนที่จะใช้งาน Skill ใดๆ คุณต้องรันคำสั่งนี้ก่อนเสมอ:
  zeroskim <skill_name> [--session <id>]

- ห้ามอ่านไฟล์ SKILL.md โดยตรงเด็ดขาด — ต้องอ่านผ่าน ZeroSkim เท่านั้น
- ถ้าผลลัพธ์แสดงเนื้อหาแบบเต็ม ให้คุณอ่านให้ละเอียดก่อนทำงาน
- ถ้าผลลัพธ์แสดงคำว่า UNCHANGED แปลว่าคุณมีข้อมูลนี้ในความจำของ session นี้แล้ว ทำงานต่อได้เลย

### กฎข้อที่ 2: กฎ 5 นาที (The 5-Minute Enforcement)
คุณต้องรัน ZeroSkim มาไม่เกิน 5 นาทีก่อนที่จะเรียกใช้ Skill หากคุณทิ้งช่วงนานเกินไป สคริปต์จะ BLOCK คุณทันที ให้คุณรัน ZeroSkim ใหม่อีกครั้งเพื่อรีเฟรชความจำ

### กฎข้อที่ 3: ห้ามแอบข้ามขั้นตอน
Skill Scripts ถูกเขียนไว้ให้บล็อกการทำงานทันทีหากคุณไม่ทำตามกฎข้อ 1 และ 2 ไม่มีทางลัด คุณต้องรัน zeroskim ก่อนเสมอ!
```

## License

MIT

---

_Created by [Chunny](https://github.com/chunnytechmate) | Built for AI Agents & [OpenClaw](https://github.com/nicepkg/openclaw)_
