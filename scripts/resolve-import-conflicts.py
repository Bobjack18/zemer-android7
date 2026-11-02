#!/usr/bin/env python3
"""Auto-resolve 3-way conflicts that are purely inside a source file's import block.

`git apply -3` stops with conflict markers whenever upstream edits the same import
list the Android 7.1 port adds an import to (a one-line change, but git cannot know
the two edits are independent). The correct merge for an import-only hunk is simply
the union of both sides, so do that and leave every other conflict untouched.

Exits 0 when nothing is left unmerged, 1 otherwise (the workflow then fails with
the file list below).
"""
import subprocess
import sys


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def split_conflicts(lines):
    """Return (out_lines, all_import_only) for the given file's lines."""
    out, emitted, i, import_only = [], set(), 0, True

    def emit(line):
        # An import must appear once; everything else is copied verbatim.
        if line.startswith("import "):
            if line in emitted:
                return
            emitted.add(line)
        out.append(line)

    while i < len(lines):
        if lines[i].startswith("<<<<<<<"):
            try:
                mid = next(j for j in range(i + 1, len(lines)) if lines[j].startswith("======="))
                end = next(j for j in range(mid + 1, len(lines)) if lines[j].startswith(">>>>>>>"))
            except StopIteration:
                return lines, False  # malformed markers: leave the file alone
            ours = lines[i + 1:mid]
            theirs = lines[mid + 1:end]
            if not all(l.startswith("import ") or not l.strip() for l in ours + theirs):
                import_only = False
            else:
                for l in ours + theirs:
                    emit(l)
            i = end + 1
            continue
        emit(lines[i])
        i += 1
    return out, import_only


def main():
    unmerged = git("diff", "--name-only", "--diff-filter=U").stdout.split()
    if not unmerged:
        print("no unmerged files")
        return 0

    still_broken = []
    for path in unmerged:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines(keepends=True)
        fixed, was_import_only = split_conflicts(lines)
        if not was_import_only:
            still_broken.append(path)
            continue
        text = "".join(fixed)
        if any(m in text for m in ("<<<<<<<", "=======", ">>>>>>>")):
            still_broken.append(path)
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        git("add", path)
        print(f"resolved import-only conflict: {path}")

    leftovers = git("diff", "--name-only", "--diff-filter=U").stdout.split()
    if still_broken or leftovers:
        print("::error::The port patch does not apply cleanly to this upstream commit.")
        for p in sorted(set(still_broken + leftovers)):
            print(f"  conflicted: {p}")
        print("Rebase patches/android-7.1.patch onto the upstream commit and push again.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
