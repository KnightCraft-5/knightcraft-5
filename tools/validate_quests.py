#!/usr/bin/env python3
"""Structural validation of the FTB Quests book.

Catches the failure modes this pack has actually hit:
  - a chapter that parses as text but that FTB Quests silently refuses to load
    (a regex-based checker once passed a file the server dropped on the floor)
  - duplicate quest/task/reward IDs
  - dependencies pointing at quests that do not exist
  - dependency cycles
  - a quest orphaned in its own chapter because its only parent is in another
    one, which FTB Quests draws no line to
  - item IDs that no installed mod provides (only when mods/ is present)

Exit code is non-zero if anything is wrong, so CI fails loudly.
"""
import collections
import glob
import json
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import snbt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTERS = os.path.join(ROOT, 'config', 'ftbquests', 'quests', 'chapters')
MODS = os.path.join(ROOT, 'mods')

# Ars Nouveau registers its glyph items at runtime, so they never appear in a
# lang file. Anything matching this is exempt from the item-exists check.
RUNTIME_ITEMS = (re.compile(r'^ars_nouveau:glyph_'),)


def mod_item_ids():
    """Every item/block id declared by an installed mod's en_us lang file."""
    ids = set()
    for jar in glob.glob(os.path.join(MODS, '*.jar')):
        try:
            z = zipfile.ZipFile(jar)
        except Exception:
            continue
        for n in z.namelist():
            if not n.endswith('lang/en_us.json'):
                continue
            try:
                d = json.loads(z.read(n).decode('utf-8-sig'))
            except Exception:
                continue
            for k in d:
                m = re.match(r'^(?:item|block)\.([a-z0-9_]+)\.([a-z0-9_./]+)$', k)
                if m:
                    ids.add(f'{m.group(1)}:{m.group(2).replace(".", "/")}')
        z.close()
    return ids


def item_of(v):
    """A task/reward item is either a plain id or an expanded ItemStack."""
    if isinstance(v, dict) and 'id' in v:
        return v['id'][1]
    if isinstance(v, tuple):
        return v[1]
    return None


def main():
    files = sorted(glob.glob(os.path.join(CHAPTERS, '*.snbt')))
    if not files:
        print(f'no chapters found under {CHAPTERS}', file=sys.stderr)
        return 1

    quests, deps, seen_ids, problems = {}, {}, collections.Counter(), []
    items_used = []

    for f in files:
        chapter = os.path.basename(f)[:-5]
        try:
            data = snbt.parse(f)
        except Exception as e:
            problems.append(f'{chapter}: does not parse as SNBT - {e}')
            continue
        for q in data.get('quests', []):
            qid = q['id'][1]
            title = q.get('title', ('s', '?'))[1]
            if qid in quests:
                problems.append(f'duplicate quest id {qid}')
            quests[qid] = (chapter, title)
            seen_ids[qid] += 1
            deps[qid] = [x[1] for x in q.get('dependencies', [])]
            for coll in ('tasks', 'rewards'):
                for entry in q.get(coll, []):
                    seen_ids[entry['id'][1]] += 1
                    if 'item' in entry:
                        it = item_of(entry['item'])
                        if it:
                            items_used.append((chapter, title, it))

    for i, c in seen_ids.items():
        if c > 1:
            problems.append(f'duplicate id {i} used {c} times')

    for qid, ds in deps.items():
        for d in ds:
            if d not in quests:
                problems.append(
                    f'{quests[qid][0]}/{quests[qid][1]}: dependency {d} does not exist')

    # cycles
    state = {}

    def walk(n, stack):
        if n in stack:
            cyc = ' -> '.join(quests[x][1] for x in stack[stack.index(n):] + [n])
            problems.append(f'dependency cycle: {cyc}')
            return
        if state.get(n):
            return
        state[n] = 1
        for p in deps.get(n, []):
            if p in quests:
                walk(p, stack + [n])

    for n in quests:
        walk(n, [])

    # a quest whose parents all live in another chapter renders with no incoming
    # line. Exactly one per chapter is correct - that is the act entry point.
    entries = collections.Counter()
    for qid, ds in deps.items():
        if ds and all(quests[d][0] != quests[qid][0] for d in ds if d in quests):
            entries[quests[qid][0]] += 1
    for chapter, n in entries.items():
        if n > 1:
            offenders = [quests[q][1] for q, ds in deps.items()
                         if quests[q][0] == chapter and ds
                         and all(quests[d][0] != chapter for d in ds if d in quests)]
            problems.append(
                f'{chapter}: {n} quests have no parent inside their own chapter '
                f'(expected 1 act entry point): {", ".join(offenders)}')

    if os.path.isdir(MODS) and glob.glob(os.path.join(MODS, '*.jar')):
        known = mod_item_ids()
        for chapter, title, it in items_used:
            if it.startswith('minecraft:') or any(r.match(it) for r in RUNTIME_ITEMS):
                continue
            if it not in known:
                problems.append(f'{chapter}/{title}: no installed mod provides {it}')
    else:
        print('note: mods/ absent, skipping item-id existence check')

    per_chapter = collections.Counter(v[0] for v in quests.values())
    for c in sorted(per_chapter):
        print(f'  {c:16} {per_chapter[c]:>3} quests')
    print(f'  {"TOTAL":16} {len(quests):>3} quests in {len(files)} chapters')

    if problems:
        print(f'\n{len(problems)} problem(s):', file=sys.stderr)
        for p in problems:
            print(f'  {p}', file=sys.stderr)
        return 1
    print('\nquest book OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
