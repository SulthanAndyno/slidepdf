#!/usr/bin/env bash
# SlidePDF Studio - Gradual Commit Pusher
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

COMMITS=$(git log --reverse --format="%H" origin/main..HEAD)

if [ -z "$COMMITS" ]; then
    echo "✓ Semua commit sudah ter-push ke GitHub!"
    exit 0
fi

TOTAL=$(echo "$COMMITS" | wc -w)
CURRENT=0

echo "🚀 Memulai push bertahap untuk $TOTAL commit tersisa..."
echo "--------------------------------------------------------"

for c in $COMMITS; do
    CURRENT=$((CURRENT + 1))
    MSG=$(git log -1 --format="%s" "$c")
    SHORT_HASH=$(echo "$c" | cut -c1-7)
    echo "[$CURRENT/$TOTAL] Pushing ($SHORT_HASH): $MSG..."
    git push origin "$c:main"
    if [ "$CURRENT" -lt "$TOTAL" ]; then
        sleep 2
    fi
done

echo "--------------------------------------------------------"
echo "✓ Selesai! Semua commit berhasil di-push ke GitHub."
