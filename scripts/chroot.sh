#!/bin/bash
# Run from Arch WSL2. With a terminal, passwd can read credentials privately.
set -euo pipefail
project=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
exec 9> "$project/.rootfs.lock"
flock -n 9 || { echo 'Another rootfs operation is running.' >&2; exit 1; }
terminal=(-i)
if [[ -t 0 && -t 1 ]]; then terminal+=(-t); fi
if (($# == 0)); then set -- /bin/bash; fi
exec docker run --rm "${terminal[@]}" --cap-add SYS_ADMIN \
    --mount "type=bind,src=$project,dst=/work" \
    de1soc-image-builder:bookworm /work/scripts/in-armhf-chroot.sh "$@"
