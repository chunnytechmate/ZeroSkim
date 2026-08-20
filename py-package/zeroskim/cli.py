#!/usr/bin/env python3
"""zeroskim CLI — command-line interface for anti-skimming enforcement."""

import sys
import argparse
from .core import zeroskim


def main():
    parser = argparse.ArgumentParser(
        prog="zeroskim",
        description="zeroskim — Stop AI agents from skimming skill files."
    )
    parser.add_argument("skill_name", nargs="?", help="Skill name to read")
    parser.add_argument("--session", "-s", help="Session ID for per-session cache")
    parser.add_argument("--force", "-f", action="store_true", help="Force full re-read")
    parser.add_argument("--list", "-l", action="store_true", help="List all skills and read status")

    args = parser.parse_args()

    zs = zeroskim()

    if args.list:
        skills = zs.list_skills()
        if not skills:
            print("No skills found.")
            return 0
        for s in skills:
            print(f"  📂 {s['name']}")
        return 0

    if not args.skill_name:
        parser.error("Skill name required (or use --list)")

    result = zs.read(args.skill_name, session_id=args.session, force=args.force)

    if result["status"] == "NOT_FOUND":
        print(f"❌ Skill '{args.skill_name}' not found.")
        return 1

    if result["content"]:
        # Full read
        print(f"📖 FIRST READ ({result['lines']} lines)")
        print(f"📌 Path: {result['path']}")
        print()
        print("--- SKILL.md CONTENT ---")
        print()
        print(result["content"])
        print()
        print("--- END ({} lines) ---".format(result['lines']))
        print("⚠️ SYSTEM DIRECTIVE: You MUST read and strictly follow ALL rules and formats specified above before proceeding.")
    else:
        # Unanged
        print(f"✅ UNCHANGED — already read ({result['lines']} lines)")
        print(f"📌 Path: {result['path']}")
        print(f"📖 Last read: {result['last_read']}")
        print(f"🔑 Hash: {result['hash'][:20]}...")
        print(f"📌 Action: ALREADY IN CONTEXT — Proceed with task.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
