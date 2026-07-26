#!/usr/bin/env bash
# Mirrors mods/ to R2 so CI can reconstruct the mod set byte-for-byte.
#
# mods/ is gitignored (651 MB, and redistributing jars through a public repo is
# dubious), and the jars have no launcher metadata to re-download them from.
# So the bucket is the source of truth for binaries and mods.sha256 - which IS
# tracked - is the source of truth for *which* binaries and what they hash to.
#
# Credentials come from the environment, same as upload-bundles.sh:
#   set -a; . ./r2.env; set +a
#
# Usage:
#   ./sync-mods.sh --manifest   regenerate mods.sha256 from local mods/
#   ./sync-mods.sh --verify     check local mods/ against mods.sha256 (offline)
#   ./sync-mods.sh --push       upload mods/ to the bucket, then regenerate+verify
#   ./sync-mods.sh --pull       download mods/ from the bucket, then verify
set -euo pipefail

cd "$(dirname "$0")"
BUCKET="${R2_BUCKET:-knightcraft}"
PREFIX="mods"
MANIFEST="mods.sha256"

die() { echo "error: $*" >&2; exit 1; }

need_creds() {
    local id="${R2_ACCESS_KEY_ID:-${AWS_ACCESS_KEY_ID:-}}"
    local sec="${R2_SECRET_ACCESS_KEY:-${AWS_SECRET_ACCESS_KEY:-}}"
    [ -n "$id" ] && [ -n "$sec" ] && [ -n "${R2_ENDPOINT:-}" ] \
        || die "need R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY / R2_ENDPOINT (see r2.env.example)"
    export AWS_ACCESS_KEY_ID="$id" AWS_SECRET_ACCESS_KEY="$sec"
    export AWS_DEFAULT_REGION=auto
    export AWS_REQUEST_CHECKSUM_CALCULATION=when_required
    export AWS_RESPONSE_CHECKSUM_VALIDATION=when_required
}
s3() { aws --endpoint-url "$R2_ENDPOINT" "$@"; }

gen_manifest() {
    [ -d mods ] || die "no mods/ directory"
    python3 - "$MANIFEST" <<'PY'
import hashlib, json, os, sys
out = sys.argv[1]
rows = []
for f in sorted(os.listdir('mods')):
    if not f.endswith('.jar'):
        continue
    p = os.path.join('mods', f)
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    rows.append({'sha256': h.hexdigest(), 'size': os.path.getsize(p), 'name': f})
with open(out, 'w') as fh:
    json.dump({'count': len(rows), 'mods': rows}, fh, indent=1)
    fh.write('\n')
print(f"{out}: {len(rows)} jars, {sum(r['size'] for r in rows)/2**20:.0f} MiB")
PY
}

verify() {
    [ -f "$MANIFEST" ] || die "$MANIFEST not found"
    python3 - "$MANIFEST" <<'PY'
import hashlib, json, os, sys
man = json.load(open(sys.argv[1]))
want = {m['name']: m for m in man['mods']}
have = {f for f in os.listdir('mods')} if os.path.isdir('mods') else set()
missing = sorted(set(want) - have)
extra   = sorted(f for f in have - set(want) if f.endswith('.jar'))
bad = []
for name, m in want.items():
    p = os.path.join('mods', name)
    if not os.path.exists(p):
        continue
    if os.path.getsize(p) != m['size']:
        bad.append((name, 'size')); continue
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    if h.hexdigest() != m['sha256']:
        bad.append((name, 'hash'))
for n in missing: print(f"  MISSING  {n}")
for n in extra:   print(f"  EXTRA    {n}   (not in manifest)")
for n, why in bad: print(f"  CORRUPT  {n}   ({why} mismatch)")
ok = len(want) - len(missing) - len(bad)
print(f"\n{ok}/{len(want)} jars verified against {sys.argv[1]}")
sys.exit(1 if (missing or bad or extra) else 0)
PY
}

case "${1:-}" in
    --manifest) gen_manifest ;;
    --verify)   verify ;;
    --push)
        need_creds
        [ -d mods ] || die "no mods/ directory"
        echo "uploading mods/ -> s3://$BUCKET/$PREFIX/"
        s3 s3 sync mods "s3://$BUCKET/$PREFIX/" --no-progress --exclude '.*'
        gen_manifest
        verify
        echo "remote objects: $(s3 s3 ls "s3://$BUCKET/$PREFIX/" | wc -l)"
        ;;
    --pull)
        need_creds
        [ -f "$MANIFEST" ] || die "$MANIFEST not found - cannot verify what we pull"
        mkdir -p mods
        echo "downloading s3://$BUCKET/$PREFIX/ -> mods/"
        s3 s3 sync "s3://$BUCKET/$PREFIX/" mods --no-progress
        verify
        ;;
    *)
        sed -n '2,20p' "$0" | sed 's/^# \?//'
        exit 1 ;;
esac
