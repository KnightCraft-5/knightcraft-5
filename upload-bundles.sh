#!/usr/bin/env bash
# Uploads built bundles to the Cloudflare R2 bucket over the S3 API.
#
# Credentials come from the environment ONLY - nothing is stored in this repo.
# Either export them, or keep them in an untracked r2.env and source it:
#
#     set -a; . ./r2.env; set +a
#     ./upload-bundles.sh
#
# Required:
#   R2_ACCESS_KEY_ID       (or AWS_ACCESS_KEY_ID)
#   R2_SECRET_ACCESS_KEY   (or AWS_SECRET_ACCESS_KEY)
#   R2_ENDPOINT            https://<account-id>.r2.cloudflarestorage.com
# Optional:
#   R2_BUCKET              defaults to "knightcraft"
#
# Usage:
#   ./upload-bundles.sh                  upload today's client+server bundles
#   ./upload-bundles.sh a.zip b.zip      upload the named files
#   ./upload-bundles.sh --check          verify credentials and bucket, upload nothing
#   ./upload-bundles.sh --list           list what is already in the bucket
#   ./upload-bundles.sh --presign KEY    print a 7-day download link (R2 maximum)
set -euo pipefail

BUCKET="${R2_BUCKET:-knightcraft}"
KEY_ID="${R2_ACCESS_KEY_ID:-${AWS_ACCESS_KEY_ID:-}}"
SECRET="${R2_SECRET_ACCESS_KEY:-${AWS_SECRET_ACCESS_KEY:-}}"
ENDPOINT="${R2_ENDPOINT:-}"

die() { echo "error: $*" >&2; exit 1; }

missing=()
[ -n "$KEY_ID"   ] || missing+=("R2_ACCESS_KEY_ID")
[ -n "$SECRET"   ] || missing+=("R2_SECRET_ACCESS_KEY")
[ -n "$ENDPOINT" ] || missing+=("R2_ENDPOINT")
if [ ${#missing[@]} -gt 0 ]; then
    echo "error: missing environment variable(s): ${missing[*]}" >&2
    echo >&2
    echo "  set -a; . ./r2.env; set +a     # see r2.env.example" >&2
    exit 1
fi
command -v aws >/dev/null || die "aws CLI not found"

# Credentials are passed through the environment, never on the command line
# (argv is world-readable via ps) and never written to ~/.aws.
export AWS_ACCESS_KEY_ID="$KEY_ID"
export AWS_SECRET_ACCESS_KEY="$SECRET"
export AWS_DEFAULT_REGION=auto
# AWS CLI >=2.23 sends CRC32 checksum headers that R2 rejects mid-multipart.
export AWS_REQUEST_CHECKSUM_CALCULATION=when_required
export AWS_RESPONSE_CHECKSUM_VALIDATION=when_required

s3() { aws --endpoint-url "$ENDPOINT" "$@"; }

case "${1:-}" in
    --check)
        # A bucket-scoped R2 token cannot ListBuckets; head-bucket is the real test.
        s3 s3api head-bucket --bucket "$BUCKET" >/dev/null \
            && echo "OK: credentials valid, bucket '$BUCKET' reachable at $ENDPOINT"
        exit 0 ;;
    --list)
        s3 s3 ls "s3://$BUCKET/" --human-readable; exit 0 ;;
    --presign)
        [ -n "${2:-}" ] || die "--presign needs an object key"
        s3 s3 presign "s3://$BUCKET/$2" --expires-in 604800; exit 0 ;;
esac

# --- pick files ------------------------------------------------------------
if [ $# -gt 0 ]; then
    FILES=("$@")
else
    FILES=()
    for kind in client server; do
        f="$HOME/knightcraft5-$kind-$(date +%Y-%m-%d).zip"
        [ -f "$f" ] && FILES+=("$f")
    done
    [ ${#FILES[@]} -gt 0 ] || die "no bundles dated $(date +%Y-%m-%d) in \$HOME; pass paths explicitly"
fi

s3 s3api head-bucket --bucket "$BUCKET" >/dev/null || die "cannot reach bucket '$BUCKET'"

fail=0
for f in "${FILES[@]}"; do
    [ -f "$f" ] || { echo "skip (not found): $f" >&2; fail=1; continue; }
    key="$(basename "$f")"
    local_size="$(stat -c %s "$f")"
    echo
    echo "uploading $key  ($(du -h "$f" | cut -f1))"
    s3 s3 cp "$f" "s3://$BUCKET/$key" --content-type application/zip --no-progress

    remote_size="$(s3 s3api head-object --bucket "$BUCKET" --key "$key" \
                      --query ContentLength --output text)"
    if [ "$remote_size" = "$local_size" ]; then
        echo "  verified: $remote_size bytes"
    else
        echo "  SIZE MISMATCH: local=$local_size remote=$remote_size" >&2
        fail=1
    fi
done

echo
[ $fail -eq 0 ] && echo "all uploads verified" || { echo "one or more uploads failed" >&2; exit 1; }
echo "download links:  $0 --presign <key>"
