# skill-read-guard

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

`skill_read_guard.py` acts as a **smart gate** between your agent and its skill files:

1. **First read** → Outputs the full file content and records a SHA256 fingerprint.
2. **File unchanged** → Outputs only a 5-line metadata summary — **~97% fewer tokens**.
3. **File changed** → Outputs the full content again and updates the fingerprint.
4. **Force flag** (`--force`) → Always outputs full content, ignoring the cache.

```
$ python skill_read_guard.py music-class-summarizer
📖 FIRST READ (219 lines)
📌 Path: /skills/music-class-summarizer/SKILL.md

--- SKILL.md CONTENT ---
(full content here...)
--- END (219 lines) ---
```

```
$ python skill_read_guard.py music-class-summarizer
✅ UNCHANGED — already read (219 lines)
📌 Path: /skills/music-class-summarizer/SKILL.md
📖 Last read: 2026-05-08T12:45:11
🔑 Hash: f74e5050ca0cbc8a...
📌 Action: No re-read needed — use session memory
```

## Usage

```bash
# Read a skill (auto-detects if content has changed)
python3 skill_read_guard.py <skill_name>

# Force a full re-read regardless of cache
python3 skill_read_guard.py <skill_name> --force

# List all discovered skills and their read status
python3 skill_read_guard.py --list
```

### Integrating with Your Agent

Add a rule to your agent's system prompt or `AGENTS.md`:

```markdown
Before using any skill, always run:
  python3 ~/.openclaw/workspace/scripts/skill_read_guard.py <skill_name>

- Never read SKILL.md directly — always go through this script.
- If the output includes content, read it carefully before proceeding.
- If the output says UNCHANGED, you already have the context in this session.
```

## How It Works

| Scenario | Behavior |
|----------|----------|
| First read ever | Print full content + save hash |
| File unchanged since last read | Print 5-line summary only |
| File modified since last read | Print full content + update hash |
| `--force` flag | Always print full content |
| Corrupt state file | Auto-recover — starts fresh |
| Skill file not found | Print error, exit with code 1 |

### Safety Features

- **Atomic writes** — state file uses `os.replace()` to prevent corruption on crash.
- **Corrupt recovery** — invalid JSON in the state file is handled gracefully (resets to empty).
- **Robust error handling** — permission errors, encoding issues, and missing files all produce clear error messages.
- **Flexible path resolution** — searches multiple skill directories and supports both `-` and `_` naming conventions.

### File Structure

```
skill-read-guard/
├── skill_read_guard.py     # Main script
├── .skill-state.json       # Auto-generated hash cache (gitignored)
└── README.md
```

## Requirements

- **Python 3.10+** (uses `str | None` union syntax)
- **No external dependencies** — standard library only

## License

MIT

---

_Built for [OpenClaw](https://github.com/nicepkg/openclaw) but works with any AI agent system that uses skill manifest files._

---

# skill-read-guard (ภาษาไทย)

**ผู้เฝ้าประตูเข้มงวดที่บังคับให้ AI agent อ่านและแคช SKILL.md ให้ครบก่อนทำงาน — ป้องกันข้อผิดพลาดที่แพงในระบบ production**

## ปัญหา

AI agent ที่ใช้ระบบ skill (เช่น OpenClaw, Claude, GPT) จะเจอปัญหาเดิมทุกครั้งที่เริ่ม session ใหม่:

- **ไม่อ่านเลย** → พลาดรายละเอียดสำคัญ — ใช้ parameter ผิด, ข้าม step, ผลลัพธ์พัง
- **อ่านหมดทุกอย่าง** → เสีย token เป็นพันๆ กับไฟล์ที่ไม่ได้เปลี่ยน
- **อ่านไม่ครบ** → แย่กว่าเดิม — error เงียบจาก context ไม่ครบ

## วิธีแก้

`skill_read_guard.py` ทำหน้าที่เป็น **gate อัจฉริยะ** ระหว่าง agent กับไฟล์ skill:

1. **อ่านครั้งแรก** → พิมพ์เนื้อหาเต็ม + บันทึก SHA256 fingerprint
2. **ไฟล์ไม่เปลี่ยน** → พิมพ์แค่ metadata 5 บรรทัด — **ประหยัด token ~97%**
3. **ไฟล์เปลี่ยน** → พิมพ์เนื้อหาเต็มอีกครั้ง + อัปเดต fingerprint
4. **Force flag** (`--force`) → พิมพ์เนื้อหาเต็มเสมอ ไม่สน cache

## การใช้งาน

```bash
# อ่าน skill (ตรวจอัตโนมัติว่าเนื้อหาเปลี่ยนหรือไม่)
python3 skill_read_guard.py <ชื่อ_skill>

# บังคับอ่านเต็ม ไม่สน cache
python3 skill_read_guard.py <ชื่อ_skill> --force

# แสดง skill ทั้งหมด + สถานะการอ่าน
python3 skill_read_guard.py --list
```

### ผูกเข้ากับ Agent ของคุณ

เพิ่มกฎใน system prompt หรือ `AGENTS.md` ของ agent:

```markdown
ก่อนใช้ skill ใดๆ ให้รันเสมอ:
  python3 ~/.openclaw/workspace/scripts/skill_read_guard.py <ชื่อ_skill>

- ห้ามอ่าน SKILL.md โดยตรง — ต้องผ่าน script นี้เท่านั้น
- ถ้า output มีเนื้อหา → อ่านให้ครบก่อนดำเนินการ
- ถ้า output บอก UNCHANGED → ใช้ context จาก session นี้ได้เลย
```

## วิธีทำงาน

| สถานการณ์ | พฤติกรรม |
|----------|----------|
| อ่านครั้งแรก | พิมพ์เนื้อหาเต็ม + บันทึก hash |
| ไฟล์ไม่เปลี่ยน | พิมพ์แค่ summary 5 บรรทัด |
| ไฟล์ถูกแก้ไข | พิมพ์เนื้อหาเต็ม + อัปเดต hash |
| ใช้ flag `--force` | พิมพ์เนื้อหาเต็มเสมอ |
| State file เสีย | กู้คืนอัตโนมัติ — เริ่มใหม่ |
| ไม่เจอไฟล์ | แจ้ง error, exit code 1 |

### ความปลอดภัย

- **Atomic writes** — ใช้ `os.replace()` ป้องกัน state file เสียหายเมื่อระบบ crash
- **กู้คืนจาก state เสีย** — JSON ไม่ valid จะ reset เป็นค่าว่างโดยอัตโนมัติ
- **จัดการ error ครบ** — permission, encoding, file not found ทั้งหมดมี error message ชัดเจน
- **ค้นหา path ยืดหยุ่น** — รองรับหลาย directory ทั้ง `-` และ `_` ในชื่อ

## ความต้องการ

- **Python 3.10+**
- **ไม่ต้องติดตั้งอะไรเพิ่ม** — ใช้แค่ standard library

## License

MIT

---

_สร้างสำหรับ [OpenClaw](https://github.com/nicepkg/openclaw) แต่ใช้ได้กับทุกระบบ AI agent ที่ใช้ไฟล์ skill manifest_
