#!/bin/bash
# Read-only local password check. Password stays in the interactive process.
set -euo pipefail
project=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if [[ ! -t 0 || ! -t 1 ]]; then
    echo 'Run this command in your own interactive Arch WSL2 terminal.' >&2
    exit 1
fi
exec docker run --rm -it --network none \
    --mount "type=bind,src=$project,dst=/work,readonly" \
    de1soc-image-builder:bookworm python3 -W ignore::DeprecationWarning -c '
import crypt
import getpass
import hmac

with open("/work/rootfs/bookworm-armhf/etc/shadow") as entries:
    stored = next(line.split(":")[1] for line in entries if line.startswith("de1soc:"))
if not stored or stored.startswith(("!", "*")):
    raise SystemExit("Account is locked or has no password.")
password = getpass.getpass("Enter the de1soc password (local check only): ")
actual = crypt.crypt(password, stored)
if not actual or actual.startswith("*"):
    raise SystemExit("Password hash algorithm is not supported by this checker.")
if hmac.compare_digest(actual, stored):
    print("MATCH: password matches the local rootfs. Check board identity and SSH logs next.")
else:
    raise SystemExit("NO MATCH: password differs from the local rootfs.")
'
