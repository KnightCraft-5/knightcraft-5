#!/usr/bin/env python3
"""Track what is actually deployed where, and diff it against this pack.

WHY THIS EXISTS
The pack drifted from every place it runs, silently and in both directions:

  * The published pack shipped Saros 3.5.6 while the live server ran 3.5.7. Both
    jars declare modId=saros__money_mod, so installing both aborts mod loading -
    and the filenames look like different mods, so nothing flags it.
  * ImprovedMobs and TenshiLib ran in production but were absent from the pack,
    and TenshiLib was briefly ADDED then REMOVED here because nothing in the
    pack referenced it - true of the pack, false of production.
  * A friend's server sat on an 8-chapter quest book while the pack had 14.

Every one of those was found by hand, by unpacking an archive someone mailed
over. This file makes that a command.

A deployment is one row in deployments.json: a name, where it runs, and the
mod-set hash it was last seen with. `check` re-hashes this pack and tells you
which deployments have diverged. `diff` names the exact jars.

Run:
  tools/deployments.py list
  tools/deployments.py hash                     # mod-set hash of this pack
  tools/deployments.py record <name> --from-dir <path>   # snapshot a deployment
  tools/deployments.py record <name> --from-rar <path>   # ... straight from a .rar
  tools/deployments.py check                    # which deployments have drifted
  tools/deployments.py diff <name>              # which jars differ, exactly
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, 'deployments.json')
MODS = os.path.join(ROOT, 'mods')


def pack_mods():
    """Mod filenames in this pack, sorted. Filename is the identity - the R2
    mirror and mods.sha256 are both keyed by it."""
    if not os.path.isdir(MODS):
        return []
    return sorted(f for f in os.listdir(MODS) if f.endswith('.jar'))


def mods_from_dir(path):
    d = path if os.path.basename(path) == 'mods' else os.path.join(path, 'mods')
    if not os.path.isdir(d):
        # tolerate a nested layout, e.g. "<pack>/Sunucu/<server>/mods"
        for base, dirs, _ in os.walk(path):
            if 'mods' in dirs:
                d = os.path.join(base, 'mods')
                break
    if not os.path.isdir(d):
        sys.exit(f'no mods/ directory under {path}')
    return sorted(f for f in os.listdir(d) if f.endswith('.jar'))


def mods_from_rar(path):
    """Read a .rar listing without extracting it - these archives are ~1.4 GB."""
    try:
        out = subprocess.run(['unrar', 'lb', path], capture_output=True,
                             text=True, timeout=300).stdout
    except FileNotFoundError:
        sys.exit('unrar not installed')
    jars = {line.split('/')[-1] for line in out.splitlines()
            if re.search(r'/mods/[^/]+\.jar$', line)}
    if not jars:
        sys.exit(f'no mods/*.jar entries inside {path}')
    return sorted(jars)


def modset_hash(names):
    """Order-independent hash of a mod set. Two installs with the same jars
    hash the same regardless of listing order or filesystem."""
    h = hashlib.sha256()
    for n in sorted(names):
        h.update(n.encode())
        h.update(b'\n')
    return h.hexdigest()[:16]


def load():
    if not os.path.exists(STATE):
        return {'deployments': {}}
    with open(STATE) as fh:
        return json.load(fh)


def save(state):
    with open(STATE, 'w') as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write('\n')


def cmd_hash(_):
    m = pack_mods()
    print(f'{modset_hash(m)}  {len(m)} jars  (this pack)')
    return 0


def cmd_list(_):
    st = load()
    if not st['deployments']:
        print('no deployments recorded')
        return 0
    cur = modset_hash(pack_mods())
    print(f'{"name":<16} {"where":<26} {"jars":>5}  {"hash":<16} status')
    print('-' * 78)
    for name, d in sorted(st['deployments'].items()):
        same = 'in sync' if d['modset'] == cur else 'DRIFTED'
        print(f'{name:<16} {d.get("where","?")[:26]:<26} {d["jars"]:>5}  '
              f'{d["modset"]:<16} {same}')
    print(f'\n{"pack":<16} {"(this repo)":<26} {len(pack_mods()):>5}  {cur}')
    return 0


def cmd_record(args):
    names = mods_from_rar(args.from_rar) if args.from_rar else mods_from_dir(args.from_dir)
    st = load()
    st['deployments'][args.name] = {
        'where': args.where or (args.from_rar or args.from_dir),
        'jars': len(names),
        'modset': modset_hash(names),
        'mods': names,
        'recorded_from': 'rar' if args.from_rar else 'dir',
    }
    save(st)
    cur = modset_hash(pack_mods())
    tag = 'in sync with pack' if st['deployments'][args.name]['modset'] == cur else 'DRIFTED from pack'
    print(f'recorded {args.name}: {len(names)} jars, {modset_hash(names)} - {tag}')
    return 0


def cmd_check(_):
    st = load()
    # mods/ is gitignored and restored from R2 mid-workflow, so on a fresh CI
    # checkout it does not exist yet. Hashing an empty directory would report
    # every deployment as drifted and fail the release for no reason.
    if not pack_mods():
        print('mods/ absent - skipping deployment parity check')
        return 0
    cur = modset_hash(pack_mods())
    drift = [n for n, d in st['deployments'].items() if d['modset'] != cur]
    for n in sorted(st['deployments']):
        d = st['deployments'][n]
        print(f'  {n:<16} {"DRIFTED" if n in drift else "in sync"}  '
              f'({d["jars"]} jars, {d["modset"]})')
    if drift:
        print(f'\n{len(drift)} deployment(s) drifted: {", ".join(sorted(drift))}')
        print('run  tools/deployments.py diff <name>  to see which jars')
        return 1
    print('\nall deployments in sync with the pack')
    return 0


def cmd_diff(args):
    st = load()
    d = st['deployments'].get(args.name)
    if not d:
        sys.exit(f'unknown deployment {args.name!r} - see `list`')
    theirs, ours = set(d['mods']), set(pack_mods())
    only_them, only_us = sorted(theirs - ours), sorted(ours - theirs)
    if not only_them and not only_us:
        print(f'{args.name}: identical to the pack ({len(ours)} jars)')
        return 0
    print(f'{args.name} vs pack:')
    for j in only_them:
        print(f'  only in {args.name:<12} {j}')
    for j in only_us:
        print(f'  only in pack        {j}')
    # same mod, different version - the failure mode that aborts mod loading
    def stem(j):
        return re.split(r'[-_]\d', j, maxsplit=1)[0].lower().replace('-', '').replace('_', '')
    a = {stem(j): j for j in only_them}
    b = {stem(j): j for j in only_us}
    both = sorted(set(a) & set(b))
    if both:
        print('\n  VERSION MISMATCH - installing both aborts mod loading:')
        for s in both:
            print(f'    {a[s]}   vs   {b[s]}')
    return 1


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('hash').set_defaults(fn=cmd_hash)
    sub.add_parser('list').set_defaults(fn=cmd_list)
    sub.add_parser('check').set_defaults(fn=cmd_check)
    d = sub.add_parser('diff'); d.add_argument('name'); d.set_defaults(fn=cmd_diff)
    r = sub.add_parser('record')
    r.add_argument('name')
    r.add_argument('--from-dir')
    r.add_argument('--from-rar')
    r.add_argument('--where')
    r.set_defaults(fn=cmd_record)
    a = p.parse_args()
    if a.cmd == 'record' and not (a.from_dir or a.from_rar):
        p.error('record needs --from-dir or --from-rar')
    return a.fn(a)


if __name__ == '__main__':
    sys.exit(main())
