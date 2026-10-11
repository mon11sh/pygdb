#!/usr/bin/env python3
"""
Check whether a requirements.txt is fully installed in the CURRENT Python
(i.e. run this with the venv's python, or after activating the venv).

Exit 0  -> every requirement is installed (and '==' pins match).
Exit 1  -> something is missing/mismatched (prints the offending lines).

Usage:  python check_requirements.py requirements.txt
"""

import sys
import re

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:  # very old Python fallback
    from importlib_metadata import version, PackageNotFoundError


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python check_requirements.py <requirements.txt>")
        return 2

    missing = []
    for raw in open(sys.argv[1], encoding="utf-8"):
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        m = re.match(
            r"^([A-Za-z0-9_.\-]+)(\[[^\]]*\])?\s*(==|>=|<=|~=|!=|>|<)?\s*([A-Za-z0-9_.\-*]+)?",
            line,
        )
        if not m:
            continue
        name, op, want = m.group(1), m.group(3), m.group(4)
        try:
            have = version(name)
        except PackageNotFoundError:
            missing.append(line)
            continue
        if op == "==" and want and have != want:
            missing.append(f"{line} (installed: {have})")

    if missing:
        print("Missing / mismatched:")
        for x in missing:
            print("   - " + x)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
