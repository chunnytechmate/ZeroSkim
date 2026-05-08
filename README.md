# skill-read-guard

**Ensure AI agents always read the full skill manual before use — without burning tokens on re-reads.**

## 🎯 Problem

AI assistants (like OpenClaw) have **dozens of skills**, each with a `SKILL.md` manual (some 200+ lines). Every session, the agent wakes up fresh and needs to read these files to use skills correctly.

- **Read nothing?** → Miss critical details → wrong parameters, skipped steps, bad outputs
- **Read everything every time?** → Massive token waste across 80+ skills
- **Partial reads?** → Silent failures, inconsistent behavior

## 💡 Solution

A **hash-based read gate** that:

1. Tracks SHA256 fingerprints of every `SKILL.md`
2. **First read / file changed** → Prints full content (agent must consume it)
3. **Unchanged** → Prints only metadata (5 lines vs 200+ lines) — saves ~97% tokens
4. **Force flag** → Bypass cache when you want a manual refresh

```
$ python skill_read_guard.py music-class-summarizer
📖 FIRST READ (219 lines)
📌 Path: /skills/music-class-summarizer/SKILL.md

--- SKILL.md CONTENT ---
(full content here...)
--- END (219 lines) ---

$ python skill_read_guard.py music-class-summarizer
✅ UNCHANGED — already read (219 lines)
📌 Path: /skills/music-class-summarizer/SKILL.md
📖 Last read: 2026-05-08T12:45:11
🔑 Hash: f74e5050ca0cbc8a...
📌 Action: ใช้ความจำ session นี้ได้เลย
```

## 🚀 Usage

```bash
# Read a skill (auto-detects change)
python skill_read_guard.py <skill_name>

# Force full re-read regardless of cache
python skill_read_guard.py <skill_name> --force

# List all skills with read status
python skill_read_guard.py --list
```

### Integration with AI Agent

In your agent's `AGENTS.md` or system prompt:

```markdown
## ⚠️ Rule: Always use skill_read_guard.py before using any skill

```bash
python3 ~/.openclaw/workspace/scripts/skill_read_guard.py <skill_name>
```

- NEVER use `read` tool to read SKILL.md directly
- Script will output full content on first read / change, metadata only if unchanged
- Follow the output — if content is shown, read it; if UNCHANGED, skip
```

## 📁 File Structure

```
skill-read-guard/
├── skill_read_guard.py          # Main script
├── .skill-state.json       # Auto-generated hash cache (gitignored)
└── README.md               # This file
```

## 🔧 How It Works

| Scenario | Behavior |
|----------|----------|
| First read ever | Print full content + save hash |
| File unchanged | Print 5-line summary only |
| File modified | Print full content + update hash |
| `--force` flag | Always print full content |
| Corrupt state file | Auto-recover, start fresh |
| File not found | Error with exit code 1 |

### Safety Features

- **Atomic writes** — state file uses `os.replace()` to prevent corruption
- **Corrupt recovery** — invalid JSON gracefully resets to empty state
- **Error handling** — permission errors, encoding errors, missing files all handled
- **Multiple search paths** — supports both workspace skills and system skills

## 📋 Requirements

- Python 3.10+
- No external dependencies (stdlib only)

## 📜 License

MIT

---

_Built for [OpenClaw](https://github.com/openclaw/openclaw) but works with any AI agent system that uses skill manifest files._
