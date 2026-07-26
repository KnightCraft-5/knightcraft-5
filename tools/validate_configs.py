#!/usr/bin/env python3
"""Check every server-config key against what the mods actually define.

This exists because three keys in this repo were invented by hand and did
nothing:

    pmmo-server.toml          Party.share_xp
    pmmo-server.toml          Party.auto_join_party
    minecolonies-server.toml  debugging.netherworkertakesdamage

Forge silently discards keys outside a mod's spec, so a fabricated setting
produces no error and no log line - it just quietly fails to apply while
looking, to any reader, like the thing is configured. One of those keys even
carried a comment claiming it fixed a bug that was still live.

reference/serverconfig/ holds a mod-generated config set. Any key present in
ours but absent there does not exist. Value differences are fine and expected -
those are deliberate tuning - and are printed for review.
"""
import glob
import os
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCE = os.path.join(ROOT, 'reference', 'serverconfig')
SCOPES = ('defaultconfigs', 'serverconfig')


def flatten(d, prefix=''):
    out = {}
    for k, v in d.items():
        key = f'{prefix}{k}'
        if isinstance(v, dict):
            out.update(flatten(v, key + '.'))
        else:
            out[key] = v
    return out


def main():
    if not os.path.isdir(REFERENCE):
        print(f'missing {REFERENCE} - cannot tell a real key from an invented one',
              file=sys.stderr)
        return 1

    fabricated, tuned, checked, unref = [], [], 0, []

    for scope in SCOPES:
        for f in sorted(glob.glob(os.path.join(ROOT, scope, '*.toml'))):
            base = os.path.basename(f)
            ref = os.path.join(REFERENCE, base)
            if not os.path.exists(ref):
                unref.append(f'{scope}/{base}')
                continue
            try:
                mine = flatten(tomllib.load(open(f, 'rb')))
                theirs = flatten(tomllib.load(open(ref, 'rb')))
            except Exception as e:
                print(f'  {scope}/{base}: parse error - {e}', file=sys.stderr)
                return 1
            checked += 1
            for k in sorted(set(mine) - set(theirs)):
                fabricated.append(f'{scope}/{base}: {k} = {mine[k]!r}')
            for k in sorted(set(mine) & set(theirs)):
                if mine[k] != theirs[k]:
                    tuned.append(f'{scope}/{base}: {k}: {theirs[k]!r} -> {mine[k]!r}')

    print(f'checked {checked} config file(s) against the mod-generated reference')
    if unref:
        print(f'no reference for {len(unref)} file(s) (not checked): '
              + ', '.join(unref))
    if tuned:
        print(f'\n{len(tuned)} deliberate value change(s):')
        for t in tuned:
            print(f'  {t}')

    if fabricated:
        print(f'\n{len(fabricated)} FABRICATED KEY(S) - no mod defines these, '
              f'Forge will discard them:', file=sys.stderr)
        for k in fabricated:
            print(f'  {k}', file=sys.stderr)
        return 1

    print('\nno fabricated keys')
    return 0


if __name__ == '__main__':
    sys.exit(main())
