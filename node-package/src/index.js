/**
 * ZeroSkim — Stop AI agents from skimming skill files.
 *
 * Core module providing the ZeroSkim cache system and gate enforcement.
 *
 * @module zeroskim
 * @author Chunny
 * @license MIT
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// ---------------------------------------------------------------------------
// ZeroSkim: Smart SKILL.md cache (anti-skimming)
// ---------------------------------------------------------------------------

class ZeroSkim {
  /**
   * @param {object} [options]
   * @param {string} [options.workspaceDir] - Workspace directory path
   */
  constructor(options = {}) {
    this.workspaceDir = options.workspaceDir ||
      process.env.OPENCLAW_WORKSPACE_DIR ||
      path.join(require('os').homedir(), '.openclaw', 'workspace');
    this.skillsDir = path.join(this.workspaceDir, 'skills');
    this.maxCacheAgeDays = 7;
  }

  // --- State management ---

  _statePath(sessionId = null) {
    if (sessionId) {
      const safeId = sessionId.replace(/[^a-zA-Z0-9_-]/g, '');
      return path.join(this.workspaceDir, `.zeroskim-state-${safeId}.json`);
    }
    return path.join(this.workspaceDir, '.zeroskim-state.json');
  }

  _loadState(sessionId = null) {
    const fp = this._statePath(sessionId);
    try {
      if (fs.existsSync(fp)) {
        return JSON.parse(fs.readFileSync(fp, 'utf-8'));
      }
    } catch { /* corrupt state, start fresh */ }
    return {};
  }

  _saveState(state, sessionId = null) {
    const fp = this._statePath(sessionId);
    const tmp = fp + '.tmp';
    try {
      fs.writeFileSync(tmp, JSON.stringify(state, null, 2), 'utf-8');
      fs.renameSync(tmp, fp);
    } catch (e) {
      console.error(`[⚠️] Could not save state: ${e.message}`);
    }
  }

  // --- Skill discovery ---

  _findSkillMd(skillName) {
    const candidates = [
      path.join(this.skillsDir, skillName, 'SKILL.md'),
      path.join(this.skillsDir, skillName.replace(/-/g, '_'), 'SKILL.md'),
      path.join(this.skillsDir, skillName.replace(/_/g, '-'), 'SKILL.md'),
    ];
    for (const p of candidates) {
      if (fs.existsSync(p)) return p;
    }
    // Fuzzy match
    try {
      const entries = fs.readdirSync(this.skillsDir);
      for (const entry of entries) {
        const mdPath = path.join(this.skillsDir, entry, 'SKILL.md');
        if (entry.toLowerCase().includes(skillName.toLowerCase()) && fs.existsSync(mdPath)) {
          return mdPath;
        }
      }
    } catch { /* ignore */ }
    return null;
  }

  /**
   * List all discovered skills.
   * @returns {Array<{name: string, path: string}>}
   */
  listSkills() {
    const skills = [];
    try {
      const entries = fs.readdirSync(this.skillsDir).sort();
      for (const entry of entries) {
        const mdPath = path.join(this.skillsDir, entry, 'SKILL.md');
        const entryPath = path.join(this.skillsDir, entry);
        if (fs.statSync(entryPath).isDirectory() && fs.existsSync(mdPath)) {
          skills.push({ name: entry, path: mdPath });
        }
      }
    } catch { /* ignore */ }
    return skills;
  }

  /**
   * Read a skill with anti-skimming cache.
   * @param {string} skillName
   * @param {object} [options]
   * @param {string} [options.sessionId]
   * @param {boolean} [options.force]
   * @returns {{status: string, content?: string, path: string, hash: string, lines: number, lastRead: string}}
   */
  read(skillName, options = {}) {
    const { sessionId = null, force = false } = options;
    const skillPath = this._findSkillMd(skillName);

    if (!skillPath) {
      return { status: 'NOT_FOUND', skillName };
    }

    const content = fs.readFileSync(skillPath, 'utf-8');
    const currentHash = crypto.createHash('sha256').update(content).digest('hex');
    const lines = content.split('\n').length;
    const state = this._loadState(sessionId);
    const entry = state[skillName] || {};
    const cachedHash = entry.hash || '';

    const now = new Date().toISOString().replace(/\.\d{3}Z$/, '');

    if (force || cachedHash !== currentHash) {
      state[skillName] = { hash: currentHash, path: skillPath, lastRead: now, lines };
      this._saveState(state, sessionId);
      return {
        status: cachedHash ? 'CHANGED' : 'FIRST_READ',
        content,
        path: skillPath,
        hash: currentHash,
        lines,
        lastRead: now,
      };
    }

    return {
      status: 'UNCHANGED',
      content: null,
      path: skillPath,
      hash: currentHash,
      lines,
      lastRead: entry.lastRead || now,
    };
  }

  /**
   * Garbage collect old state files.
   * @returns {number} Number of files removed.
   */
  gc() {
    let removed = 0;
    const cutoff = Date.now() - (this.maxCacheAgeDays * 86400000);
    try {
      const entries = fs.readdirSync(this.workspaceDir);
      for (const entry of entries) {
        if (entry.startsWith('.zeroskim-state') && entry.endsWith('.json')) {
          const fp = path.join(this.workspaceDir, entry);
          const stat = fs.statSync(fp);
          if (stat.mtimeMs < cutoff) {
            fs.unlinkSync(fp);
            removed++;
          }
        }
      }
    } catch { /* ignore */ }
    return removed;
  }
}

// ---------------------------------------------------------------------------
// Gate enforcement
// ---------------------------------------------------------------------------

/**
 * Hard gate: blocks execution if ZeroSkim hasn't been run recently.
 * @param {string} skillName
 * @param {object} [options]
 * @param {string} [options.sessionId]
 * @param {number} [options.maxAgeMinutes=5]
 */
function requireZeroskim(skillName, options = {}) {
  const { sessionId = null, maxAgeMinutes = 5 } = options;
  const zs = new ZeroSkim();
  const state = zs._loadState(sessionId);
  const entry = state[skillName];

  if (!entry) {
    console.error(`❌ ZEROSKIM BLOCK: Skill '${skillName}' not found in read-cache.`);
    console.error(`   → Run: npx zeroskim ${skillName}`);
    process.exit(1);
  }

  const lastRead = entry.lastRead || '';
  if (lastRead) {
    const lastMs = new Date(lastRead).getTime();
    const ageMinutes = (Date.now() - lastMs) / 60000;
    if (ageMinutes > maxAgeMinutes) {
      console.error(`❌ ZEROSKIM BLOCK: Read-cache EXPIRED (${Math.round(ageMinutes)} mins ago).`);
      console.error(`   → Run: npx zeroskim ${skillName}`);
      process.exit(1);
    }
  }

  console.log(`✅ ZeroSkim OK: '${skillName}' active (${entry.lastRead || '?'}, ${entry.lines || '?'} lines).`);
}

module.exports = { ZeroSkim, requireZeroskim };
