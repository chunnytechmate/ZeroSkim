# 🛡 zeroskim

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Node.js 18+](https://img.shields.io/badge/node-18%2B-brightgreen.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)
![Category: AI Agents](https://img.shields.io/badge/Category-AI_Agents-purple.svg)

**Stop AI agents from skimming skill files. zeroskim forces full reads, intelligently caches context, and hard-blocks execution if the agent attempts a shortcut — preventing costly mistakes in production AI systems.**

> *zeroskim = Zero Tolerance for Skimming.*

---

## 📑 Table of Contents
- [The Problem](#the-problem)
- [The Solution (3-Layer Protection)](#the-solution--3-layer-protection)
- [⚙️ Architecture & How It Works](#️-architecture--how-it-works)
- [📦 Installation](#-installation)
- [🚀 One-Prompt Install for AI Agents](#-one-prompt-install-for-ai-agents)
- [Quick Start & Usage](#quick-start--usage)
- [🛡 Safety & Auto-Maintenance](#-safety--auto-maintenance)
- [🇹🇭 zeroskim (ภาษาไทย)](#-zeroskim-ภาษาไทย)

---

## The Problem

AI agents utilizing skill-based architectures (OpenClaw, Claude, GPT, etc.) face a recurring dilemma every time they initialize a new session:

- **Skip reading entirely** → Miss critical directives, leading to invalid parameters, skipped steps, and broken workflows.
- **Read everything repeatedly** → Burn thousands of tokens re-reading files that haven't changed.
- **Partial reads (Skimming)** → The silent killer. Causes unpredictable failures due to incomplete context.
- **Fake memory (Hallucination)** → The agent confidently claims it remembers the rules, even though its memory was just wiped.

When scaling to dozens of skills with extensive manuals, token burn and error rates scale exponentially. **Skimming is the silent killer of AI agent reliability.**

## The Solution — 3-Layer Protection

### Layer 1: Soft Gate (Agent Discipline)
zeroskim acts as a smart, session-aware cache between your agent and its skill files:
1. **Initial read** → Outputs full file content and records a SHA256 fingerprint.
2. **File unchanged** → Outputs a 5-line metadata summary (**~97% fewer tokens**).
3. **Session isolation** → Separates cache per session ID, completely preventing hallucination after a chat reset.

### Layer 2: Hard Gate — File Read (Script Enforcement)
If the agent attempts to skim or skip zeroskim entirely, the script immediately blocks execution:
```text
❌ ZEROSKIM BLOCK: Skill not found in read-cache. Run zeroskim first.
 → Run: npx zeroskim send-recording-line
```

### Layer 3: Hard Gate — Step Completion (`require_step_done`)
Even after reading the SKILL.md, agents may skip required workflow steps (e.g., reading comments before posting). `require_step_done` verifies that a step was **actually performed** by checking if the step name appears in today's agent log:

```python
from zeroskim_gate import require_zeroskim, require_step_done

# Layer 1+2: File read gate
require_zeroskim("my-skill")

# Layer 3: Step completion gate
require_step_done("my-skill", "read-comments")
```

```text
✅ Step OK: 'read-comments' found in 2026-05-22.md
```

**How it works:**
1. Auto-discovers the skill's log file (no config needed)
2. Reads today's log
3. Searches for the step name (supports hyphen/underscore/space variants)
4. Found → pass. Not found → block with clear error message.

```text
🛑 STEP BLOCK: Step 'read-comments' not found in today's logs (2026-05-22).
   Skill: my-skill
   Required step: read-comments
   Fix: Complete 'read-comments' and log it, then try again.
```

## ⚙️ Architecture & How It Works

zeroskim works through a simple but highly effective **3-step hash-based read gate**:

```text
┌─────────────────────────────────────┐
│  zeroskim <skill_name>              │
└─────────────┬───────────────────────┘
              ▼
┌─────────────────────────┐
│ 1. Find SKILL.md        │ → Searches in workspace & app skills
└─────────────┬───────────┘   (Supports - and _ naming conventions)
              ▼
┌─────────────────────────┐
│ 2. Compute SHA256 Hash  │ → Chunked read (8192 bytes), zero memory bloat
└─────────────┬───────────┘
              ▼
┌─────────────────────────┐
│ 3. Compare State        │ → Loads session-specific state file
└─────────────┬───────────┘
              │
     ┌────────┴────────┐
  Unchanged         Fresh / Changed
     │                    │
     ▼                    ▼
┌──────────┐    ┌──────────────────┐
│ OUTPUT:  │    │ OUTPUT:          │
│ 5 Lines  │    │ Full Content     │
│ of Meta  │    │ + Update Hash    │
└──────────┘    └──────────────────┘
```

### 🔄 3 Reading States (Token Management)

zeroskim drastically reduces token burn by determining exactly what the agent needs to see:

| State | Condition | Output | Token Usage |
| :--- | :--- | :--- | :--- |
| **📖 FIRST READ** | Never read in this session | Full Content | **High** (Necessary) |
| **⚠️ CHANGED** | Read before, but file hash changed | Full Content | **High** (Necessary) |
| **✅ UNCHANGED** | Read before, hash matched perfectly | Metadata only (5 lines) | **Minimal** (Token Saver) |

### 📦 State Management

Read history is securely tracked in `.zeroskim-state.json`. Each session maintains its own state file to isolate context windows:

```json
{
  "send-lesson-line": {
    "hash": "a3f2b8c8d9e...",
    "last_read": "2026-05-11T13:30:00",
    "path": "/home/node/.openclaw/workspace/skills/send-lesson-line/SKILL.md",
    "lines": 245
  }
}
```

State files are session-specific (e.g. `.zeroskim-state-session-abc123.json`), ensuring that each conversation maintains its own read cache. When a new session starts, the cache is empty — forcing a fresh first read and preventing hallucinated context from bleeding across sessions.

## 📦 Installation

zeroskim can be installed as a modern package or used as a standalone script.

### Option A: Install as Package (Recommended)

**For Python (PyPI):**
```bash
pip install zeroskim
```
```python
from zeroskim import zeroskim, require_zeroskim

zs = zeroskim(workspace_dir="/path/to/workspace")
result = zs.read("my-skill", session_id="abc123")

# Enforce the 15-Minute Rule in your skill scripts
# (pass the same workspace_dir you used for read())
require_zeroskim("my-skill", workspace_dir="/path/to/workspace")
```

**For Node.js (npm):**
```bash
npm install zeroskim
```
```javascript
const { zeroskim, requirezeroskim } = require('zeroskim');

const zs = new zeroskim({ workspaceDir: '/path/to/workspace' });
const result = zs.read('my-skill', { sessionId: 'abc123' });

// Enforce the 15-Minute Rule in your skill scripts
// (pass the same workspaceDir you used for read())
requirezeroskim('my-skill', { workspaceDir: '/path/to/workspace' });
```

📖 Full API documentation: [`PACKAGE.md`](./PACKAGE.md)

### Option B: Standalone Script (Direct Download)

If you prefer not to use package managers, you can download the core scripts directly into your project's workspace using `curl`:

```bash
# Download the main script and the gate enforcement
curl -O https://raw.githubusercontent.com/chunnytechmate/zeroskim/main/zeroskim.py
curl -O https://raw.githubusercontent.com/chunnytechmate/zeroskim/main/zeroskim_gate.py
```

Then, import the gate directly into your skill scripts:

```python
import sys, os
sys.path.insert(0, os.environ.get("OPENCLAW_SCRIPTS_DIR", "/your/path"))
from zeroskim_gate import require_zeroskim

require_zeroskim("your-skill-name", session_id=os.environ.get("OPENCLAW_SESSION_ID"))
```

### Option C: Docker Environments

If your AI agent runs inside a Docker container, zeroskim is fully equipped to handle containerized environments via configuration variables.

**1. Set Environment Variables:**
Configure these variables in your `Dockerfile` or `docker-compose.yml` so zeroskim knows where to store its cache and locate scripts:

```yaml
environment:
  - OPENCLAW_STATE_DIR=/app/workspace   # Where .zeroskim-state.json lives
  - OPENCLAW_SCRIPTS_DIR=/app/scripts   # Where zeroskim_gate.py lives
  # Optional: widen the gate window per skill (minutes). Default is 15.
  # Skill "my-skill" -> ZEROSKIM_MAX_AGE_MY_SKILL=60
  - ZEROSKIM_MAX_AGE_MY_SKILL=60
```

**2. Ensure Volumes are Mounted:**
Since zeroskim needs to read your SKILL.md files and persist its cache across container restarts, ensure your workspace is mounted as a volume:

```yaml
volumes:
  - ./local_workspace:/app/workspace
  - ./local_scripts:/app/scripts
```

## 🚀 One-Prompt Install for AI Agents

Copy this snippet to your `AGENTS.md` or the agent's System Prompt to enforce strict discipline:

```markdown
## ⚠️ zeroskim — Anti-Skimming Skill Read System

You MUST follow these rules. No exceptions. Skimming kills reliability.

### Rule 1: Always use zeroskim before using any skill
Before executing ANY skill, you must always run:
  zeroskim <skill_name> [--session <id>]

- NEVER read SKILL.md directly using standard read tools — always route through zeroskim.
- If the output includes full content, read it carefully and completely before proceeding.
- If the output says UNCHANGED, you already have the required context in this session.

### Rule 2: The 15-Minute Enforcement
You must have called zeroskim within the last 15 minutes to run a skill. If you wait too long, the script will BLOCK you. Re-run zeroskim to refresh your context.

### Rule 3: No Shortcuts
Skill scripts will hard-block execution if Rule 1 and Rule 2 are not met. No shortcuts. Run zeroskim first. Always.

### Rule 4: Complete Every Step
If your skill has a workflow with required steps (e.g., read comments before posting), use `require_step_done` to verify each step was actually performed:
  require_step_done("skill-name", "step-name")

- This checks today's agent log for evidence that the step was completed.
- If the step is not found, execution is blocked until the step is done.
- No skipping steps. Complete them in order.
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

**Step Completion Gate (Layer 3):**
```python
# Python — in your skill script
from zeroskim_gate import require_step_done

# Verify a workflow step was actually performed
require_step_done("my-skill", "read-comments")
# ✅ Step OK: 'read-comments' found in 2026-05-22.md

require_step_done("my-skill", "fetch-data")
# 🛑 STEP BLOCK: Step 'fetch-data' not found in today's logs
```

```javascript
// Node.js — in your skill script
const { requireStepDone } = require('zeroskim');

requireStepDone('my-skill', 'read-comments');
// ✅ Step OK: 'read-comments' found in 2026-05-22.md
```

## 🛡 Safety & Auto-Maintenance

zeroskim is designed for robust, long-running agentic workflows that run for days or weeks unattended:

### Atomic Writes
State files are saved using the **atomic write pattern** (`tempfile.mkstemp()` → `os.replace()`). This two-step process guarantees that if the script crashes mid-write (OOM kill, signal, power loss), your state file will **never be corrupted** — you'll either have the old intact version or the new complete version, never a partial write.

### Session-Aware Isolation
Context is strictly bound to session IDs (`.zeroskim-state-session-xyz789.json`). When a chat session resets, the cache is fresh — completely preventing hallucinations where the agent falsely claims to remember rules from a previous conversation.

### Auto Garbage Collection (GC)
Every time zeroskim runs, it silently triggers `gc_stale_session_states(max_age_days=7)`, which prunes session state files older than 7 days. This keeps your workspace clean without manual maintenance, even with hundreds of concurrent sessions.

### Path Traversal Protection
Session IDs are strictly sanitized to `[a-zA-Z0-9_-]` only. Any characters outside this set are stripped, preventing arbitrary file writes or directory traversal attacks.

## License

MIT

---

# 🇹🇭 zeroskim (ภาษาไทย)

ระบบป้องกัน AI Agent อ่านแบบลวกๆ (Skimming) — บังคับให้อ่านกฎ (SKILL.md) ให้จบก่อนเริ่มงานเสมอ เพื่อป้องกันความเสียหายร้ายแรงในระดับ Production

## ปัญหา

AI agent มักจะเจอปัญหาเดิมๆ ทุกครั้งที่เริ่มต้น Session ใหม่:

- **ข้ามการอ่านไปเลย** → พลาดรายละเอียดสำคัญ, ใส่ parameter ผิด, ข้ามขั้นตอนการทำงาน
- **อ่านทุกอย่างซ้ำไปซ้ำมา** → สูญเสีย Token มหาศาลไปกับไฟล์ที่ไม่ได้ถูกแก้ไข
- **อ่านลวกๆ (Skim)** → ตัวการสำคัญที่ทำให้เกิด Error เงียบ เพราะได้ Context ไปไม่ครบ
- **แกล้งทำเป็นจำได้ (Hallucination)** → AI หลอนไปเองว่าจำกฎได้ ทั้งที่เพิ่งถูกล้างความจำไป

## วิธีแก้ — ระบบป้องกัน 3 ชั้น

### ชั้นที่ 1: Soft Gate (สร้างวินัย)
zeroskim ทำหน้าที่เป็นแคชอัจฉริยะ:
- **รันครั้งแรก**: พิมพ์เนื้อหาเต็ม + บันทึก SHA256 Hash
- **ไฟล์ไม่เปลี่ยน**: พิมพ์สรุป 5 บรรทัด (ช่วยประหยัด Token ได้ถึง ~97%)
- **แยกตาม Session**: ป้องกันการสับสนระหว่างแชทเก่าและแชทใหม่

### ชั้นที่ 2: Hard Gate — การอ่านไฟล์ (บล็อกในระดับโค้ด)
ใช้ `require_zeroskim` ติดตั้งไว้ในทุก Skill Script:
- **กฎ 15 นาที**: AI จะต้องรัน zeroskim มาไม่เกิน 15 นาทีก่อนรันงานจริง มิฉะนั้นสคริปต์จะ **บล็อกการทำงานทันที**
- **ไม่อนุญาตให้ใช้ทางลัด**: AI ต้องผ่านด่านตรวจก่อนเสมอ ไม่มีข้อยกเว้น

### ชั้นที่ 3: Hard Gate — การทำ Step (`require_step_done`)
แม้อ่าน SKILL.md แล้ว AI ก็อาจข้าม workflow step ที่บังคับ (เช่น ไม่อ่าน comments ก่อนโพส) `require_step_done` ตรวจสอบว่า step ถูก **ทำจริง** โดยค้นหาชื่อ step ใน agent log ของวันนี้

```python
from zeroskim_gate import require_zeroskim, require_step_done

require_zeroskim("my-skill")  # ชั้นที่ 1+2
require_step_done("my-skill", "read-comments")  # ชั้นที่ 3
```

**วิธีทำงาน:**
1. หาไฟล์ log ของ skill อัตโนมัติ
2. อ่าน log ของวันนี้
3. ค้นหาชื่อ step (รองรับ hyphen/underscore/space)
4. เจอ = ผ่าน, ไม่เจอ = บล็อก

## ⚙️ สถาปัตยกรรม (Architecture)

zeroskim ทำงานผ่านระบบ **Hash-based Read Gate 3 ขั้นตอน**:

```text
┌─────────────────────────────────────┐
│  zeroskim <skill_name>              │
└─────────────┬───────────────────────┘
              ▼
┌─────────────────────────┐
│ 1. หาไฟล์ SKILL.md     │ → ค้นหาใน workspace & app skills
└─────────────┬───────────┘   (รองรับทั้ง - และ _)
              ▼
┌─────────────────────────┐
│ 2. คำนวณ SHA256 Hash   │ → อ่านแบบ chunked (8192 bytes)
└─────────────┬───────────┘
              ▼
┌─────────────────────────┐
│ 3. เปรียบเทียบ State    │ → โหลดไฟล์ state ของ session นี้
└─────────────┬───────────┘
              │
     ┌────────┴────────┐
  ไม่เปลี่ยน          ใหม่ / เปลี่ยนแล้ว
     │                    │
     ▼                    ▼
┌──────────┐    ┌──────────────────┐
│ OUTPUT:  │    │ OUTPUT:          │
│ 5 บรท.   │    │ เนื้อหาเต็ม       │
│ Meta     │    │ + อัพเดต Hash    │
└──────────┘    └──────────────────┘
```

### 🔄 3 สถานะการอ่าน (Token Management)

| สถานะ | เงื่อนไข | Output | Token ที่ใช้ |
| :--- | :--- | :--- | :--- |
| **📖 FIRST READ** | ยังไม่เคยอ่านใน session นี้ | เนื้อหาเต็ม | **สูง** (จำเป็น) |
| **⚠️ CHANGED** | เคยอ่าน แต่ hash เปลี่ยน | เนื้อหาเต็ม | **สูง** (จำเป็น) |
| **✅ UNCHANGED** | เคยอ่าน และ hash ตรง | Metadata 5 บรรทัดเท่านั้น | **ต่ำมาก** (ประหยัด) |

### 📦 State Management

ประวัติการอ่านถูกเก็บไว้ใน `.zeroskim-state.json` แยกตาม session:

```json
{
  "send-lesson-line": {
    "hash": "a3f2b8c8d9e...",
    "last_read": "2026-05-11T13:30:00",
    "path": "/workspace/skills/send-lesson-line/SKILL.md",
    "lines": 245
  }
}
```

## 🛡 ความปลอดภัยและการบำรุงรักษาอัตโนมัติ

### Atomic Writes
บันทึกไฟล์ State ด้วยรูปแบบ **Atomic Write** (`mkstemp` → `os.replace`) — รับประกันว่าหากสคริปต์ดับกะทันหัน (OOM kill, signal, ไฟฟ้าดับ) ไฟล์ State จะ **ไม่พังเด็ดขาด** จะได้ไฟล์เก่าที่สมบูรณ์ หรือไฟล์ใหม่ที่สมบูรณ์เสมอ

### แยก State ตาม Session
Context ถูกแยกอย่างเข้มงวดตาม Session ID (`.zeroskim-state-session-xyz789.json`) เมื่อ session ใหม่เริ่มขึ้น cache จะว่างเปล่า — ป้องกัน AI ดึงความจำจาก session อื่นมาหลอนผสมกันอย่างเด็ดขาด

### Garbage Collection (GC)
ทุกครั้งที่ zeroskim รัน จะลบไฟล์ State ที่เก่าเกิน 7 วันทิ้งอัตโนมัติ ไม่เปลืองพื้นที่ Workspace แม้จะมี session เป็นร้อยๆ

### Path Traversal Protection
Session ID ถูกกรองเหลือเฉพาะ `[a-zA-Z0-9_-]` เท่านั้น ป้องกันการเขียนไฟล์นอกเส้นทางที่กำหนด

## 📦 การติดตั้ง

zeroskim รองรับการติดตั้งแบบ Package มาตรฐานเพื่อความสะดวกสูงสุด

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
const { requirezeroskim } = require('zeroskim');
requirezeroskim('my-skill'); // บล็อกทันทีถ้ายังไม่ได้อ่าน
```

💡 หากไม่ต้องการติดตั้งผ่าน Package คุณสามารถใช้ `curl` ดึงสคริปต์ไปวางในโปรเจกต์ได้เลย:

```bash
curl -O https://raw.githubusercontent.com/chunnytechmate/zeroskim/main/zeroskim.py
curl -O https://raw.githubusercontent.com/chunnytechmate/zeroskim/main/zeroskim_gate.py
```

### Docker

หาก AI Agent ของคุณรันอยู่ใน Docker Container สามารถตั้งค่า Environment Variables เพื่อให้ zeroskim ทำงานได้ทันที:

```yaml
environment:
  - OPENCLAW_STATE_DIR=/app/workspace   # ตำแหน่งเก็บ .zeroskim-state.json
  - OPENCLAW_SCRIPTS_DIR=/app/scripts   # ตำแหน่ง zeroskim_gate.py
  # ไม่บังคับ: ขยายหน้าต่าง gate ราย skill (นาที) — default คือ 15
  # Skill "my-skill" -> ZEROSKIM_MAX_AGE_MY_SKILL=60
  - ZEROSKIM_MAX_AGE_MY_SKILL=60

volumes:
  - ./local_workspace:/app/workspace    # Mount เพื่อให้อ่าน SKILL.md ได้
  - ./local_scripts:/app/scripts        # Mount เพื่อให้ cache คงอยู่ข้าม restart
```

## 🚀 Prompt สำหรับตั้งค่า AI Agent (One-Prompt Install)

คัดลอก Prompt ด้านล่างนี้ไปใส่ใน `AGENTS.md` หรือ System Prompt ของ AI เพื่อสร้างวินัยการอ่านที่เข้มงวด:

```markdown
## ⚠️ zeroskim — ระบบ Anti-Skimming (คำสั่งบังคับ)

คุณต้องทำตามกฎเหล่านี้ทุกครั้ง ไม่มีข้อยกเว้น การอ่านแบบลวกๆ จะทำให้ระบบพัง

### กฎข้อที่ 1: ต้องใช้ zeroskim ก่อนใช้ Skill เสมอ
ก่อนที่จะใช้งาน Skill ใดๆ คุณต้องรันคำสั่งนี้ก่อนเสมอ:
  zeroskim <skill_name> [--session <id>]

- ห้ามอ่านไฟล์ SKILL.md โดยตรงเด็ดขาด — ต้องอ่านผ่าน zeroskim เท่านั้น
- ถ้าผลลัพธ์แสดงเนื้อหาแบบเต็ม ให้คุณอ่านให้ละเอียดก่อนทำงาน
- ถ้าผลลัพธ์แสดงคำว่า UNCHANGED แปลว่าคุณมีข้อมูลนี้ในความจำของ session นี้แล้ว ทำงานต่อได้เลย

### กฎข้อที่ 2: กฎ 15 นาที (The 15-Minute Enforcement)
คุณต้องรัน zeroskim มาไม่เกิน 15 นาทีก่อนที่จะเรียกใช้ Skill หากคุณทิ้งช่วงนานเกินไป สคริปต์จะ BLOCK คุณทันที ให้คุณรัน zeroskim ใหม่อีกครั้งเพื่อรีเฟรชความจำ

### กฎข้อที่ 3: ห้ามแอบข้ามขั้นตอน
Skill Scripts ถูกเขียนไว้ให้บล็อกการทำงานทันทีหากคุณไม่ทำตามกฎข้อ 1 และ 2 ไม่มีทางลัด คุณต้องรัน zeroskim ก่อนเสมอ!

### กฎข้อที่ 4: ทำทุก Step ให้ครบ
หาก Skill ของคุณมี workflow ที่บังคับ step (เช่น ต้องอ่าน comments ก่อนโพสต์) ให้ใช้ `require_step_done` ตรวจสอบว่าแต่ละ step ถูกทำจริง:
  require_step_done("skill-name", "step-name")

- ระบบจะตรวจว่า step ปรากฏใน agent log ของวันนี้หรือไม่
- ถ้าไม่เจอ การทำงานจะถูกบล็อกจนกว่าจะทำ step นั้นเสร็จ
- ห้ามข้าม step — ทำตามลำดับให้ครบทุกขั้น
```

## License

MIT

---

_Created by [Chunny](https://github.com/chunnytechmate) | Built for AI Agents & [OpenClaw](https://openclaw.ai/)_
