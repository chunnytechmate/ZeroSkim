#!/usr/bin/env node

/**
 * ZeroSkim CLI — command-line interface for anti-skimming enforcement.
 */

const { ZeroSkim } = require('./index');

const args = process.argv.slice(2);
let skillName = null;
let sessionId = null;
let force = false;
let listMode = false;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--session' || args[i] === '-s') {
    sessionId = args[++i];
  } else if (args[i] === '--force' || args[i] === '-f') {
    force = true;
  } else if (args[i] === '--list' || args[i] === '-l') {
    listMode = true;
  } else if (!args[i].startsWith('-')) {
    skillName = args[i];
  }
}

const zs = new ZeroSkim();

if (listMode) {
  const skills = zs.listSkills();
  if (skills.length === 0) {
    console.log('No skills found.');
    process.exit(0);
  }
  for (const s of skills) {
    console.log(`  📂 ${s.name}`);
  }
  process.exit(0);
}

if (!skillName) {
  console.error('Usage: zeroskim <skill_name> [--session <id>] [--force] [--list]');
  process.exit(1);
}

const result = zs.read(skillName, { sessionId, force });

if (result.status === 'NOT_FOUND') {
  console.error(`❌ Skill '${skillName}' not found.`);
  process.exit(1);
}

if (result.content) {
  console.log(`📖 FIRST READ (${result.lines} lines)`);
  console.log(`📌 Path: ${result.path}`);
  console.log();
  console.log('--- SKILL.md CONTENT ---');
  console.log();
  console.log(result.content);
  console.log();
  console.log(`--- END (${result.lines} lines) ---`);
  console.log('⚠️ SYSTEM DIRECTIVE: You MUST read and strictly follow ALL rules and formats specified above before proceeding.');
} else {
  console.log(`✅ UNCHANGED — already read (${result.lines} lines)`);
  console.log(`📌 Path: ${result.path}`);
  console.log(`📖 Last read: ${result.lastRead}`);
  console.log(`🔑 Hash: ${result.hash.slice(0, 20)}...`);
  console.log(`📌 Action: ALREADY IN CONTEXT — Proceed with task.`);
}
