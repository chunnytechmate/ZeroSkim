# 📦 ZeroSkim Packages

ZeroSkim is available as both a **Python (pip)** and **Node.js (npm)** package.

## Python (pip)

```bash
pip install zeroskim
```

### Usage as a library

```python
from zeroskim import ZeroSkim, require_zeroskim

# Read a skill with anti-skimming cache
zs = ZeroSkim(workspace_dir="/path/to/workspace")
result = zs.read("my-skill", session_id="abc123")

if result["content"]:
    print(result["content"])  # Full SKILL.md content
else:
    print("Already cached, proceed!")  # Unchanged

# Hard gate enforcement in skill scripts
require_zeroskim("my-skill")  # Exits if not read recently
```

### CLI

```bash
zeroskim <skill_name> [--session <id>] [--force] [--list]
```

## Node.js (npm)

```bash
npm install zeroskim
```

### Usage as a library

```javascript
const { ZeroSkim, requireZeroskim } = require('zeroskim');

// Read a skill with anti-skimming cache
const zs = new ZeroSkim({ workspaceDir: '/path/to/workspace' });
const result = zs.read('my-skill', { sessionId: 'abc123' });

if (result.content) {
    console.log(result.content);  // Full SKILL.md content
} else {
    console.log('Already cached, proceed!');  // Unchanged
}

// Hard gate enforcement in skill scripts
requireZeroskim('my-skill');  // Exits if not read recently
```

### CLI

```bash
npx zeroskim <skill_name> [--session <id>] [--force] [--list]
```
