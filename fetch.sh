#!/bin/bash
# Fetch all inline PR review comments since 2026-05-01. Requires `gh auth login`.
set -e
D=$(dirname "$0")/data; mkdir -p "$D"
R=open-telemetry/opentelemetry-go-compile-instrumentation
for p in $(seq 1 100); do
  gh api "repos/$R/pulls/comments?since=2026-05-01T00:00:00Z&sort=created&direction=asc&per_page=100&page=$p" > "$D/rc_$p.json"
  n=$(python3 -c "import json;print(len(json.load(open('$D/rc_$p.json'))))")
  [ "$n" -lt 100 ] && break
done
echo "fetched $p pages"

# Reviews (for ordering and low-confidence comments) on PRs where both Copilot and maintainers left inline comments.
mkdir -p "$D/reviews"
for n in $(python3 "$(dirname "$0")/analyze.py" --shared-prs | tail -1); do
  gh api "repos/$R/pulls/$n/reviews?per_page=100" > "$D/reviews/$n.json"; sleep 1
done
