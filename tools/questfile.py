#!/usr/bin/env python3
"""Read/write FTB Quests chapter files without corrupting them.

WHY THIS EXISTS
The obvious approach - `text.split('\\n\\t\\t}\\n\\t\\t{\\n')` - silently corrupts the
file. The LAST element it produces carries the array terminator and the closing brace
of the root object (`\\n\\t\\t}\\n\\t]\\n}`), so appending a quest to that list writes
the new quest AFTER the file has already closed. The result still looks plausible and
still parses far enough to load, but chapters quietly lose quests. That mistake cost
three chapters here.

This module brace-matches each top-level entry in `quests: [ ... ]` instead, and keeps
the header and trailer verbatim so a read-modify-write with no changes is byte-identical.
"""
import re


class Chapter:
    def __init__(self, path):
        self.path = path
        with open(path, encoding='utf-8') as fh:
            self.text = fh.read()
        key = 'quests: ['
        i = self.text.index(key) + len(key)
        self.head = self.text[:i]
        depth, start, self.blocks = 0, None, []
        j = i
        while j < len(self.text):
            c = self.text[j]
            if c == '{':
                if depth == 0:
                    start = j
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    self.blocks.append(self.text[start:j + 1])
                    start = None
            elif c == ']' and depth == 0:
                self.tail = self.text[j:]
                break
            j += 1
        else:
            raise ValueError(f'{path}: quests array never closed')

    def render(self):
        if not self.blocks:
            return self.head + self.tail
        body = '\n\t\t' + '\n\t\t'.join(self.blocks) + '\n\t'
        return self.head + body + self.tail

    def save(self):
        with open(self.path, 'w', encoding='utf-8') as fh:
            fh.write(self.render())

    # -- helpers ----------------------------------------------------------
    @staticmethod
    def qid(block):
        m = re.search(r'\bid: "([0-9A-F]{16})"', block)
        return m.group(1) if m else None

    @staticmethod
    def title(block):
        m = re.search(r'\btitle: "([^"]*)"', block)
        return m.group(1) if m else ''

    @staticmethod
    def deps(block):
        m = re.search(r'dependencies: \[([^\]]*)\]', block, re.S)
        return re.findall(r'"([0-9A-F]{16})"', m.group(1)) if m else []

    def find(self, quest_id):
        for b in self.blocks:
            if self.qid(b) == quest_id:
                return b
        return None

    def remove(self, quest_id):
        before = len(self.blocks)
        self.blocks = [b for b in self.blocks if self.qid(b) != quest_id]
        return before != len(self.blocks)

    def repoint(self, old_id, new_id):
        """Rewrite dependency references only - never the quest's own id."""
        out = []
        for b in self.blocks:
            m = re.search(r'dependencies: \[([^\]]*)\]', b, re.S)
            if m and old_id in m.group(1):
                b = b[:m.start(1)] + m.group(1).replace(old_id, new_id) + b[m.end(1):]
            out.append(b)
        self.blocks = out

    @staticmethod
    def set_deps(block, deps):
        dep_str = ', '.join(f'"{d}"' for d in deps)
        if re.search(r'dependencies: \[[^\]]*\]', block, re.S):
            return re.sub(r'dependencies: \[[^\]]*\]', f'dependencies: [{dep_str}]',
                          block, count=1, flags=re.S)
        return block.replace('{\n', f'{{\n\t\t\tdependencies: [{dep_str}]\n', 1)

    @staticmethod
    def set_pos(block, x, y):
        block = re.sub(r'\bx: -?[\d.]+d', f'x: {x}d', block, count=1)
        return re.sub(r'\by: -?[\d.]+d', f'y: {y}d', block, count=1)


def count(path):
    return len(Chapter(path).blocks)
