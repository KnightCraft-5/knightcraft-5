#!/usr/bin/env python3
"""Sanity-check built artifacts before they are published.

Guards against the specific ways these bundles have gone wrong:
  - a server pack carrying world state or player data
  - a pack whose hqm config has hardcore lives off (the test server runs with
    them disabled; shipping that config silently deletes the death stakes)
  - an mrpack that bundles jars instead of linking them, or lists none at all
  - the CurseForge pack missing PackMenu's resources while shipping the mod,
    which leaves the custom main menu broken

Usage:  tools/verify_artifacts.py dist/ 2026-07-26
"""
import json
import os
import sys
import zipfile

HQM_OK = b'"AUTO_HARDCORE": true'


def fail(msg, errors):
    errors.append(msg)


def main():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    dist, date = sys.argv[1], sys.argv[2]
    errors = []

    paths = {
        'client': os.path.join(dist, f'knightcraft5-client-{date}.zip'),
        'server': os.path.join(dist, f'knightcraft5-server-{date}.zip'),
        'curseforge': os.path.join(dist, f'knightcraft5-curseforge-{date}.zip'),
        'mrpack': os.path.join(dist, f'knightcraft5-{date}.mrpack'),
    }
    for kind, p in paths.items():
        if not os.path.exists(p):
            fail(f'{kind}: missing {p}', errors)
    if errors:
        for e in errors:
            print(f'  {e}', file=sys.stderr)
        return 1

    # --- mrpack ------------------------------------------------------------
    mr = zipfile.ZipFile(paths['mrpack'])
    names = mr.namelist()
    idx = json.loads(mr.read('modrinth.index.json'))
    if idx.get('dependencies', {}).get('minecraft') != '1.20.1':
        fail(f'mrpack: wrong minecraft version {idx.get("dependencies")}', errors)
    if not idx.get('files'):
        fail('mrpack: lists no mods', errors)
    if any(n.endswith('.jar') for n in names):
        fail('mrpack: bundles jars - it is meant to link them', errors)
    for f in idx.get('files', []):
        if not f.get('downloads') or not f['hashes'].get('sha512'):
            fail(f'mrpack: {f.get("path")} lacks a download url or sha512', errors)
            break
    server_side = sum(1 for f in idx.get('files', [])
                      if f['env']['server'] == 'required')
    print(f'  mrpack      {len(idx.get("files", []))} mods '
          f'({server_side} server-side), no jars bundled')

    # --- server pack -------------------------------------------------------
    srv = zipfile.ZipFile(paths['server'])
    names = srv.namelist()
    for required in ('temizle.sh', 'mods.manifest.txt', 'SUNUCU-KURULUM.txt',
                     'server.properties.example'):
        if required not in names:
            fail(f'server: missing {required}', errors)
    leaked = [n for n in names
              if n.startswith(('world/', 'logs/', 'backups/', 'crash-reports/'))
              or os.path.basename(n) in ('server.properties', 'ops.json',
                                         'whitelist.json', 'usercache.json',
                                         '.sl_password',
                                         'simpleauth_users.json')]
    if leaked:
        fail(f'server: carries server state or credentials: {leaked[:3]}', errors)
    if HQM_OK not in srv.read('config/hqm/config.json5'):
        fail('server: AUTO_HARDCORE is not true', errors)
    manifest = set(srv.read('mods.manifest.txt').decode().splitlines())
    jars = {n.split('/', 1)[1] for n in names if n.startswith('mods/')}
    if manifest != jars:
        fail(f'server: mods.manifest.txt disagrees with mods/ '
             f'({len(manifest)} vs {len(jars)})', errors)
    print(f'  server      {len(jars)} jars, manifest matches')

    # --- client + curseforge ----------------------------------------------
    cli = zipfile.ZipFile(paths['client'])
    cf = zipfile.ZipFile(paths['curseforge'])
    cf_names = cf.namelist()
    cf_manifest = json.loads(cf.read('manifest.json'))
    if cf_manifest.get('manifestType') != 'minecraftModpack':
        fail('curseforge: manifest.json is not a minecraftModpack', errors)
    loaders = cf_manifest.get('minecraft', {}).get('modLoaders', [])
    if not any(l.get('id', '').startswith('forge-') for l in loaders):
        fail(f'curseforge: no forge loader declared: {loaders}', errors)

    # PackMenu the mod without packmenu/ resources = broken main menu
    for label, z, prefix in (('client', cli, ''), ('curseforge', cf, 'overrides/')):
        n = z.namelist()
        has_mod = any(os.path.basename(x).startswith('PackMenu')
                      for x in n if f'{prefix}mods/' in x)
        has_res = any(x.startswith(f'{prefix}packmenu/') for x in n)
        if has_mod and not has_res:
            fail(f'{label}: ships PackMenu but not its packmenu/ resources '
                 f'- the custom main menu will render broken', errors)
    for label, z, prefix in (('client', cli, ''), ('curseforge', cf, 'overrides/')):
        if HQM_OK not in z.read(f'{prefix}config/hqm/config.json5'):
            fail(f'{label}: AUTO_HARDCORE is not true', errors)
    print(f'  client      {sum(1 for n in cli.namelist() if n.startswith("mods/"))} jars')
    print(f'  curseforge  {sum(1 for n in cf_names if n.startswith("overrides/mods/"))} jars, '
          f'files[] empty by design: {not cf_manifest.get("files")}')

    if errors:
        print(f'\n{len(errors)} problem(s):', file=sys.stderr)
        for e in errors:
            print(f'  {e}', file=sys.stderr)
        return 1
    print('\nartifacts OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
