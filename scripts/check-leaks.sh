#!/usr/bin/env bash
# Fails if a tracked file contains an IPv4 literal, an sslip hostname or a backend-secret name.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
status=0
ip_re='(^|[^0-9.])([0-9]{1,3}\.){3}[0-9]{1,3}([^0-9.]|$)'
if git ls-files -z | xargs -0 grep -nIE "$ip_re" | grep -vE '(127\.0\.0\.1|0\.0\.0\.0)'; then
  echo "Leak check: IPv4 literal found (no addresses belong in this repo)." >&2; status=1
fi
if git ls-files -z | grep -zv '^scripts/check-leaks\.sh$' | xargs -0 grep -nIE 'sslip\.io|WEB2MD_RAPIDAPI_PROXY_SECRET|jwt_auth'; then
  echo "Leak check: backend hostname or secret name found." >&2; status=1
fi
[ "$status" -eq 0 ] && echo "Leak check passed."
exit "$status"
