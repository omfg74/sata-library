#!/usr/bin/env python3
"""Проверка скобок и кавычек в файлах KiCad. Не заменяет DRC."""

import sys
from pathlib import Path


def check(text, path):
    depth = 0
    i = 0
    n = len(text)
    line = 1
    while i < n:
        c = text[i]
        if c == "\n":
            line += 1
            i += 1
            continue
        if c == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    break
                if text[i] == "\n":
                    line += 1
                i += 1
            else:
                raise SystemExit(f"{path}:{line}: незакрытая кавычка")
            i += 1
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth < 0:
                raise SystemExit(f"{path}:{line}: лишняя )")
        i += 1
    if depth != 0:
        raise SystemExit(f"{path}: скобки не сошлись, глубина {depth}")


def main():
    root = Path(__file__).resolve().parent
    suffixes = {".kicad_sch", ".kicad_pcb", ".kicad_sym", ".kicad_mod"}
    files = [p for p in root.rglob("*") if p.suffix in suffixes]
    if not files:
        raise SystemExit("нет файлов KiCad")
    for path in sorted(files):
        check(path.read_text(encoding="utf-8"), path)
    print(f"ok {len(files)} files")


if __name__ == "__main__":
    main()
