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
# Items whose display name is built at runtime, so no mod ships a lang entry for
# them and the en_us scan cannot see them. apotheosis:gem is named from its rarity
# plus its gem type; verified real - socketing one moved a dragonsteel axe 18.0 -> 29.75.
RUNTIME_ITEMS = (re.compile(r'^ars_nouveau:glyph_'),
                 re.compile(r'^apotheosis:gem$'),
                 # items registered by KubeJS at startup exist in no jar's lang file
                 re.compile(r'^kubejs:'))


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


ACT_ORDER = ['act1_cirak', 'act2_gezgin', 'act3_madenci', 'act4_avci', 'act5_arena',
             'act6_cehennem', 'act7_ejderha', 'act8_kadim', 'act9_son', 'act10_yakinda']


def boss_drop_map():
    """item id -> {entities that drop it}, from every installed mod's entity loot tables.

    Items that also have a vanilla source are dropped from the map: iron, diamond and
    emerald all appear in modded mob loot tables, and treating those as boss-gated
    produced a page of false positives.
    """
    import zipfile
    out = {}
    for jar in glob.glob(os.path.join(MODS, '*.jar')):
        try:
            z = zipfile.ZipFile(jar)
        except Exception:
            continue
        for n in z.namelist():
            if '/loot_tables/entities/' not in n or not n.endswith('.json'):
                continue
            try:
                body = z.read(n).decode('utf-8')
            except Exception:
                continue
            ns = n.split('/')[1]
            ent = ns + ':' + n.split('/loot_tables/entities/')[1][:-5]
            for it in set(re.findall(r'"name": "([\w]+:[\w/]+)"', body)):
                if it.startswith('minecraft:'):
                    continue
                out.setdefault(it, set()).add(ent)
    return out


def structural_problems():
    """Rules the book has actually violated, each one a bug that shipped.

    R1 one hexagon per act, and it must be a kill - 15 non-boss quests wore the capstone
       shape, so act 5 looked like it had six bosses.
    R2 a quest requiring a boss drop must sit AFTER that boss's kill - 24 of 25 did not,
       and act 8 asked for the Ender Guardian's gauntlet to unlock the fight against it.
    R3 no quest may need an item whose only source boss is in a later act.
    R4 an optional quest may not gate a non-optional one.
    R5 no duplicate titles inside a chapter.
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from questfile import Chapter

    probs = []
    chapters, where, blocks = {}, {}, {}
    for f in sorted(glob.glob(os.path.join(CHAPTERS, '*.snbt'))):
        name = os.path.basename(f)[:-5]
        chapters[name] = Chapter(f)
        for b in chapters[name].blocks:
            where[Chapter.qid(b)] = name
            blocks[Chapter.qid(b)] = b

    for name, ch in chapters.items():
        # R1
        hexes = [b for b in ch.blocks if 'hexagon' in b]
        if len(hexes) > 1:
            probs.append(f'{name}: {len(hexes)} hexagon quests - the capstone shape must be '
                         f'unique: {", ".join(Chapter.title(b) for b in hexes)}')
        for b in hexes:
            if 'type: "kill"' not in b:
                probs.append(f'{name}/{Chapter.title(b)}: hexagon but not a kill quest')
        # R5
        titles = [Chapter.title(b) for b in ch.blocks]
        for t in sorted(set(titles)):
            if titles.count(t) > 1:
                probs.append(f'{name}: {titles.count(t)} quests share the title "{t}"')

    # R4
    kids = {}
    for i, b in blocks.items():
        for d in Chapter.deps(b):
            kids.setdefault(d, []).append(i)
    for i, b in blocks.items():
        if 'optional: true' not in b:
            continue
        for k in kids.get(i, []):
            if 'optional: true' not in blocks[k]:
                probs.append(f'{where[i]}/{Chapter.title(b)} is optional but gates '
                             f'{Chapter.title(blocks[k])}')

    if not (os.path.isdir(MODS) and glob.glob(os.path.join(MODS, '*.jar'))):
        return probs

    drops = boss_drop_map()
    killed = {}          # entity -> quest that kills it
    for i, b in blocks.items():
        for e in re.findall(r'entity: "([\w:]+)"', b):
            killed[e] = i

    def reaches(start, target, seen=None):
        seen = seen or set()
        for d in Chapter.deps(blocks[start]):
            if d in seen or d not in blocks:
                continue
            if d == target:
                return True
            seen.add(d)
            if reaches(d, target, seen):
                return True
        return False

    for i, b in blocks.items():
        act = ACT_ORDER.index(where[i]) if where[i] in ACT_ORDER else None
        for it in set(re.findall(r'item: "([\w]+:[\w_]+)"', b)):
            srcs = drops.get(it)
            if not srcs:
                continue
            # R2 - same-act boss must be killed first
            same = [s for s in srcs if s in killed and where.get(killed[s]) == where[i]]
            if same and not any(reaches(i, killed[s]) for s in same):
                probs.append(f'{where[i]}/{Chapter.title(b)}: needs {it} from '
                             f'{same[0]}, but does not come after that kill')
            # R3 - source boss only exists in a later act
            if act is not None:
                later = [s for s in srcs if s in killed
                         and where.get(killed[s]) in ACT_ORDER
                         and ACT_ORDER.index(where[killed[s]]) > act]
                if later and not same:
                    probs.append(f'{where[i]}/{Chapter.title(b)}: needs {it}, only dropped '
                                 f'by {later[0]} which is act {ACT_ORDER.index(where[killed[later[0]]])+1}')
    return probs


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

    problems += structural_problems()

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
