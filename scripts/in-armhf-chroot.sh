#!/bin/bash
# Run inside the existing amd64 rootfs-builder container with CAP_SYS_ADMIN.
set -euo pipefail
root=/work/rootfs/bookworm-armhf
binfmt=/run/de1soc-binfmt
handler="de1soc-arm-${HOSTNAME}"
registered=0
binfmt_mounted=0
mounts=()
cleanup() {
    local result=$?
    trap - EXIT
    for ((i=${#mounts[@]}-1; i>=0; i--)); do
        if mountpoint -q "${mounts[i]}"; then
            umount "${mounts[i]}" || result=1
        fi
    done
    if ((registered)); then
        echo -1 > "$binfmt/$handler" || result=1
    fi
    if ((binfmt_mounted)); then
        umount "$binfmt" || result=1
    fi
    exit "$result"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
test -x "$root/usr/bin/dash"
mkdir -p "$binfmt"
mount -t binfmt_misc binfmt_misc "$binfmt"
binfmt_mounted=1
# Match ARM little-endian ELF32 ET_EXEC and ET_DYN, as in Debian qemu-arm.
# F pins the static interpreter so chroot and every subsequent execve work.
printf ':%s:%s\n' "$handler" 'M::\x7fELF\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00:\xff\xff\xff\xff\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff\xff:/usr/bin/qemu-arm-static:F' > "$binfmt/register"
registered=1
cat "$binfmt/$handler"
for name in dev proc sys; do
    mkdir -p "$root/$name"
    mount --bind "/$name" "$root/$name"
    mounts+=("$root/$name")
done
mount --bind /dev/pts "$root/dev/pts"
mounts+=("$root/dev/pts")
mount -o remount,bind,ro "$root/sys"
mkdir -p "$root/run"
mount -t tmpfs -o mode=755,nosuid,nodev tmpfs "$root/run"
mounts+=("$root/run")
export container=docker LC_ALL=C DEBIAN_FRONTEND=noninteractive
chroot "$root" "$@"
