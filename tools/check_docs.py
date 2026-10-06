"""Check the docs for the things GitHub rendering and this repo's style care about.

    python tools/check_docs.py [folder]   # report problems, exit 1 if there are any
    python tools/check_docs.py --fix      # also rewrite plain $...$ inline math as $`...`$

Checks:
- math: inline math is written $`...`$ (in plain $...$ Markdown eats backslashes, * and _),
  display math goes in a ```math block, no macro GitHub refuses (\\operatorname and friends),
  no `<` that GitHub would read as an HTML tag inside a ```math block, no math inside
  italics or link text (it doesn't render there), and GitHub's brace limits
- relative links: the file exists, and the #anchor matches a heading
- em dashes and stray control characters
"""

import os
import re
import sys

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
ROOT = os.path.abspath(ARGS[0]) if ARGS else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = "--fix" in sys.argv
EM_DASH = chr(0x2014)
MARK = chr(0xE000)

# GitHub refuses a formula that contains any of these names, anywhere in it
REFUSED = ["DeclareMathOperator", "DeclarePairedDelimiters", "renewtagform", "newtagform", "colorbox",
           "fcolorbox", "hphantom", "vphantom", "phantom", "operatorname", "Newextarrow",
           "definecolor", "mathchoice", "unicode", "mmlToken"]
# macros from the MathJax packages GitHub leaves out (bbox, html, require, newcommand, action, colortbl)
MISSING = ["bbox", "href", "class", "cssId", "style", "require", "newcommand", "renewcommand",
           "newenvironment", "renewenvironment", "def", "let", "toggle", "mathtip", "texttip",
           "rowcolor", "columncolor", "cellcolor"]
BRACES_FORMULA, BRACES_PAGE = 1000, 2000


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


def code_spans(line):
    """Code spans as (start, end): a run of backticks up to the next run of the same length."""
    found, i = [], 0
    while i < len(line):
        if line[i] != "`":
            i += 1
            continue
        j = i
        while j < len(line) and line[j] == "`":
            j += 1
        run, k = line[i:j], j
        while True:
            k = line.find(run, k)
            if k == -1 or line[k + len(run):k + len(run) + 1] != "`":
                break
            while k < len(line) and line[k] == "`":
                k += 1
        if k == -1:
            i = j
            continue
        found.append((i, k + len(run)))
        i = k + len(run)
    return found


def math_and_code(line):
    """GitHub's $`...`$ math as (start, end, tex), and the other code spans as (start, end)."""
    math, code = [], []
    for a, b in code_spans(line):
        if line[a - 1:a] == "$" and line[b:b + 1] == "$" and line[a + 1] != "`":
            math.append((a - 1, b + 1, line[a + 1:b - 1]))
        else:
            code.append((a, b))
    return math, code


def plain_math(line, taken):
    """Spans GitHub reads as plain $...$ math: the closing $ isn't after a space or before a
    letter, digit, _ or backtick. Currency like "$5 and $10" doesn't pair up."""
    def free(i, j):
        return all(j <= a or i >= b for a, b in taken)

    spans, i = [], 0
    while i < len(line):
        if line[i] == "$" and free(i, i + 1) and line[i:i + 2] != "$$" and line[i - 1:i] != "$":
            j = line.find("$", i + 1)
            while j != -1 and (not free(j, j + 1) or line[j - 1].isspace()
                               or re.match(r"[A-Za-z0-9_`$]", line[j + 1:j + 2])):
                j = line.find("$", j + 1)
            if j == -1:
                break
            if not line[i + 1].isspace():
                spans.append((i, j + 1))
                taken.append((i, j + 1))
                i = j + 1
                continue
        i += 1
    return spans


def tex_problems(tex):
    found = [f"\\{name} isn't allowed on GitHub" for name in REFUSED if name in tex]
    found += [f"\\{name} isn't available on GitHub" for name in MISSING
              if re.search(r"\\" + name + r"(?![A-Za-z])", tex)]
    if tex.count("{") > BRACES_FORMULA:
        found.append(f"more than {BRACES_FORMULA} braces")
    return found


def check_math(path, text):
    problems, out, fence, block, start, braces = [], [], None, [], 0, 0
    for i, line in enumerate(text.split("\n"), 1):
        where = f"{rel(path)}:{i}"
        stripped = line.lstrip()
        if fence:
            if stripped.rstrip() == fence[0]:
                if fence[1] == "math":
                    tex = "\n".join(block)
                    braces += tex.count("{")
                    problems += [f"{rel(path)}:{start}: {p}" for p in tex_problems(tex)]
                    for m in re.finditer(r"<[A-Za-z/!?]", tex):
                        problems.append(f"{rel(path)}:{start}: GitHub reads '{m.group(0)}...' in a ```math "
                                        "block as an HTML tag; write \\lt or put a space after <")
                fence = None
            else:
                block.append(line)
            out.append(line)
            continue
        m = re.match(r"(```+|~~~+)\s*(\S*)", stripped)
        if m:
            fence, block, start = (m.group(1), m.group(2).lower()), [], i
            out.append(line)
            continue

        math, code = math_and_code(line)
        for a, b, tex in math:
            braces += tex.count("{")
            problems += [f"{where}: {p}: {line[a:b]}" for p in tex_problems(tex)]
            if "\\\\" in tex:
                problems.append(f"{where}: doubled backslash in $`...`$ (single ones work here): {line[a:b]}")
            if stripped.startswith("|") and re.search(r"(?<!\\)\|", tex):
                problems.append(f"{where}: | inside a table cell splits the cell; write \\| or \\vert: {line[a:b]}")
        math = [(a, b) for a, b, _ in math]
        taken = math + code
        for a, b in plain_math(line, taken):
            math.append((a, b))
            problems.append(f"{where}: plain $...$ inline math, write $`...`$ instead: {line[a:b]}")
        if "$$" in "".join(ch for k, ch in enumerate(line) if all(not a <= k < b for a, b in taken)):
            problems.append(f"{where}: $$ display math, use a ```math block")

        # math inside italics or link text never renders
        masked = list(line)
        for a, b in sorted(taken):
            masked[a:b] = [MARK if (a, b) in math else "c"] + [""] * (b - a - 1)
        masked = "".join(masked).replace("**", "")
        italics = r"(?<![\w*])\*(?!\s)([^*]+?)(?<!\s)\*(?![\w*])|(?<![\w_])_(?!\s)([^_]+?)(?<!\s)_(?![\w_])"
        for m in re.finditer(italics, masked):
            if MARK in m.group(0):
                problems.append(f"{where}: math inside italics doesn't render")
        for m in re.finditer(r"\[([^\]]*)\]\(", masked):
            if MARK in m.group(1):
                problems.append(f"{where}: math inside link text doesn't render")

        if FIX:
            bt, code = math_and_code(line)
            for a, b in sorted(plain_math(line, [(a, b) for a, b, _ in bt] + code), reverse=True):
                line = line[:a] + "$`" + line[a + 1:b - 1] + "`$" + line[b:]
        out.append(line)
    if braces > BRACES_PAGE:
        problems.append(f"{rel(path)}: {braces} braces in math on one page, GitHub stops at {BRACES_PAGE}")
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
        if EM_DASH in text:
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
