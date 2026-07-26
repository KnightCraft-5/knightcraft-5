#!/usr/bin/env python3
"""Validate the Turkish translation files.

Two checks, both from real bugs:

  1. Valid JSON. Shoulder Surfing shipped a tr_tr.json with a raw newline
     inside a string value. Minecraft's parser is lenient enough to load it,
     so the only symptom was Forge spamming 1473 "Illegal format found" errors.

  2. Format-placeholder parity with en_us. A translation that changes %s to %d,
     or drops a positional argument, crashes at the moment the string is
     formatted - which may be months later, in front of a player. Ice and Fire
     ships exactly this bug upstream (%d where a player name goes).
"""
import glob
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANG = os.path.join(ROOT, 'kubejs', 'assets')
MODS = os.path.join(ROOT, 'mods')

PLACEHOLDER = re.compile(r'%(?:\d+\$)?[sdfx]|\{\d+\}')


def arg_types(text):
    """Placeholder types, ignoring positional indices.

    Turkish word order frequently differs from English, so a translation may
    legitimately need `%2$s ... %1$s` where the original had `%s ... %s`. What
    must not change is the set of argument *types* - swapping %s for %d is what
    actually crashes at format time.
    """
    return sorted(re.sub(r'^%\d+\$', '%', p) for p in PLACEHOLDER.findall(text))


def english_for(namespace):
    """The mod's own en_us.json, to compare placeholders against."""
    for jar in glob.glob(os.path.join(MODS, '*.jar')):
        try:
            z = zipfile.ZipFile(jar)
        except Exception:
            continue
        name = f'assets/{namespace}/lang/en_us.json'
        if name in z.namelist():
            try:
                return json.loads(z.read(name).decode('utf-8-sig'))
            except Exception:
                return None
        z.close()
    return None


def main():
    files = sorted(glob.glob(os.path.join(LANG, '*', 'lang', 'tr_tr.json')))
    if not files:
        print(f'no tr_tr.json under {LANG}', file=sys.stderr)
        return 1

    problems, total = [], 0
    have_mods = bool(glob.glob(os.path.join(MODS, '*.jar')))

    for f in files:
        namespace = f.split(os.sep)[-3]
        raw = open(f, encoding='utf-8').read()
        try:
            tr = json.loads(raw)
        except json.JSONDecodeError as e:
            problems.append(f'{namespace}/tr_tr.json: invalid JSON - {e}')
            continue
        total += len(tr)
        print(f'  {namespace:24} {len(tr):>5} strings')

        if not have_mods:
            continue
        en = english_for(namespace)
        if not en:
            continue
        for key, val in tr.items():
            if key not in en or not isinstance(val, str) or not isinstance(en[key], str):
                continue
            want = arg_types(en[key])
            got = arg_types(val)
            if want != got:
                problems.append(
                    f'{namespace}: {key}\n      en: {want}\n      tr: {got}')

    print(f'  {"TOTAL":24} {total:>5} strings in {len(files)} files')
    if not have_mods:
        print('note: mods/ absent, skipping placeholder parity check')

    if problems:
        print(f'\n{len(problems)} problem(s):', file=sys.stderr)
        for p in problems:
            print(f'  {p}', file=sys.stderr)
        return 1
    print('\ntranslations OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
