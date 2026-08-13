"""Safe comment removal script (dry-run by default).

Usage: python scripts/remove_comments_clean.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
from pathlib import Path
from typing import Iterable
import tokenize

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = REPO_ROOT / ".comment_backups"
WHITELIST_TOKENS = ("ruff", "prompt")  # case-insensitive
EXCLUDE_DIRS = {"node_modules", ".git", ".comment_backups"}
TARGET_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".sh", ".env", ".yaml", ".yml"}
BLOCK_COMMENT_EXTS = {".js", ".ts", ".jsx", ".tsx"}


def contains_whitelist(s: str) -> bool:
    s_low = s.lower()
    return any(tok in s_low for tok in WHITELIST_TOKENS)


def backup_file(path: Path, dry_run: bool) -> None:
    dest = BACKUP_DIR / path.relative_to(REPO_ROOT)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        return
    shutil.copy2(path, dest.with_suffix(dest.suffix + ".orig"))


def process_python_file(path: Path, dry_run: bool) -> int:
    changed = 0
    with path.open("rb") as f:
        src_bytes = f.read()
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(src_bytes).readline)
    except Exception:
        encoding = "utf-8"
    src = src_bytes.decode(encoding)

    out_tokens = []
    g = tokenize.generate_tokens(io.StringIO(src).readline)
    for toknum, tokval, start, end, line in g:
        if toknum == tokenize.COMMENT:
            if tokval.startswith("#!"):
                out_tokens.append((toknum, tokval))
            elif contains_whitelist(tokval):
                out_tokens.append((toknum, tokval))
            else:
                changed += 1
                continue
        else:
            out_tokens.append((toknum, tokval))

    new_src = tokenize.untokenize(out_tokens)
    if new_src != src:
        backup_file(path, dry_run=dry_run)
        if not dry_run:
            path.write_text(new_src, encoding=encoding)
    return changed


def process_line_comment_file(path: Path, comment_marker: str = "#", dry_run: bool = True) -> int:
    changed = 0
    with path.open("r", encoding="utf-8", errors="surrogateescape") as f:
        lines = f.readlines()

    new_lines: list[str] = []
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("#!") and i == 0:
            new_lines.append(line)
            continue
        if comment_marker in line:
            if stripped.startswith(comment_marker):
                if contains_whitelist(line):
                    new_lines.append(line)
                else:
                    changed += 1
                    continue
            else:
                parts = line.split(comment_marker, 1)
                before, after = parts[0], parts[1]
                if contains_whitelist(after):
                    new_lines.append(line)
                else:
                    new_lines.append(before.rstrip() + "\n")
                    changed += 1
        else:
            new_lines.append(line)

    new_src = "".join(new_lines)
    src = "".join(lines)
    if new_src != src:
        backup_file(path, dry_run=dry_run)
        if not dry_run:
            path.write_text(new_src, encoding="utf-8")
    return changed


def process_js_like_file(path: Path, dry_run: bool = True) -> int:
    changed = 0
    text = path.read_text(encoding="utf-8")

    def block_replacer(m: re.Match) -> str:
        body = m.group(0)
        if contains_whitelist(body):
            return body
        nonlocal changed
        changed += 1
        return ""

    text2 = re.sub(r"/\*.*?\*/", block_replacer, text, flags=re.S)

    lines = text2.splitlines(keepends=True)
    new_lines = []
    for line in lines:
        if "//" in line:
            idx = line.find("//")
            comment = line[idx:]
            if contains_whitelist(comment):
                new_lines.append(line)
            else:
                new_lines.append(line[:idx].rstrip() + ("\n" if line.endswith("\n") else ""))
                changed += 1
        else:
            new_lines.append(line)
    new_text = "".join(new_lines)

    if new_text != text:
        backup_file(path, dry_run=dry_run)
        if not dry_run:
            path.write_text(new_text, encoding="utf-8")
    return changed


def find_target_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        if p.name.startswith("."):
            continue
        if p.suffix.lower() in TARGET_EXTENSIONS:
            yield p


def main(dry_run: bool = True) -> None:
    BACKUP_DIR.mkdir(exist_ok=True)
    total_removed = 0
    modified_files = 0
    files = list(find_target_files(REPO_ROOT))
    print(f"Found {len(files)} target files to scan.")
    for path in files:
        try:
            if path.suffix == ".py":
                removed = process_python_file(path, dry_run=dry_run)
            elif path.suffix in BLOCK_COMMENT_EXTS:
                removed = process_js_like_file(path, dry_run=dry_run)
            elif path.suffix in {".sh"}:
                removed = process_line_comment_file(path, comment_marker="#", dry_run=dry_run)
            elif path.suffix in {".env", ".yaml", ".yml"}:
                removed = process_line_comment_file(path, comment_marker="#", dry_run=dry_run)
            else:
                removed = process_line_comment_file(path, comment_marker="#", dry_run=dry_run)

            if removed > 0:
                modified_files += 1
                total_removed += removed
                print(f"Modified {path} (removed {removed} comments)")
        except Exception as err:
            print(f"[ERROR] Failed to process {path}: {err}")

    print("Done.")
    print(f"Modified files: {modified_files}")
    print(f"Total comments removed: {total_removed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Strip non-whitelisted comments (dry-run default)")
    parser.add_argument("--apply", action="store_true", help="Apply changes. Default is dry-run.")
    args = parser.parse_args()
    main(dry_run=not args.apply)
