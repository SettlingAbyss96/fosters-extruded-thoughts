"""Check the docs for the things GitHub rendering and this repo's style care about.

    python tools/check_docs.py          # report problems, exit 1 if there are any
    python tools/check_docs.py --fix    # also repair inline math escapes

Checks:
- inline math: `\\,` style escapes need a doubled backslash inside $...$, and `*` gets eaten
- relative links: the file exists, and the #anchor matches a heading
- em dashes and stray control characters
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = "--fix" in sys.argv


def md_files():
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in files:
            if fn.endswith(".md"):
                yield os.path.join(dirpath, fn)


def rel(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def slug(heading):
    heading = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading).strip().lower().replace("`", "")
    return "".join(ch for ch in heading if ch.isalnum() or ch in " -_").replace(" ", "-")


def anchors(path, cache={}):
    if path not in cache:
        found, fence = set(), False
        for line in open(path, encoding="utf-8"):
            if line.startswith("```"):
                fence = not fence
                continue
            m = None if fence else re.match(r"^#{1,6}\s+(.*)$", line)
            if m:
                found.add(slug(m.group(1)))
        cache[path] = found
    return cache[path]


def check_math(path, text):
    problems, out, fence = [], [], False
    for i, line in enumerate(text.split("\n"), 1):
        if line.startswith("```"):
            fence = not fence
            out.append(line)
            continue
        if fence:
            out.append(line)
            continue
        parts = re.split(r"(`[^`]*`)", line)
        for j, part in enumerate(parts):
            if part.startswith("`"):
                continue

            def repl(m):
                body = m.group(1)
                fixed = re.sub(r"(?<!\\)\\([,%;!])", r"\\\\\1", body)
                if fixed != body:
                    problems.append(f"{rel(path)}:{i}: single-backslash escape in inline math: {m.group(0)}")
                if "*" in body:
                    problems.append(f"{rel(path)}:{i}: '*' in inline math (use \\ast): {m.group(0)}")
                return "$" + fixed + "$"

            parts[j] = re.sub(r"\$(?![\s$])([^$]+?)\$", repl, part)
        out.append("".join(parts))
    return problems, "\n".join(out)


def check_links(path, text):
    problems = []
    for m in re.finditer(r"\]\(([^)\s]+)\)", text):
        target = m.group(1)
        if re.match(r"^[a-z]+:", target):
            continue
        file_part, _, anchor = target.partition("#")
        dest = os.path.normpath(os.path.join(os.path.dirname(path), file_part)) if file_part else path
        line = text[:m.start()].count("\n") + 1
        if file_part and not os.path.exists(dest):
            problems.append(f"{rel(path)}:{line}: missing file: {target}")
        elif anchor and dest.endswith(".md") and anchor not in anchors(dest):
            problems.append(f"{rel(path)}:{line}: missing anchor: {target}")
    return problems


def main():
    problems = []
    for path in md_files():
        text = open(path, encoding="utf-8", newline="").read()
        math_problems, fixed = check_math(path, text)
        problems += math_problems
        problems += check_links(path, text)
        if "—" in text:
            problems.append(f"{rel(path)}: em dash")
        bad = {hex(ord(c)) for c in text if ord(c) < 32 and c not in "\n\t"}
        if bad:
            problems.append(f"{rel(path)}: control characters {sorted(bad)}")
        if FIX and fixed != text:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(fixed)
    for p in problems:
        print(p)
    print(f"{len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
