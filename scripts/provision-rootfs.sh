#!/bin/bash
# Container entry point; only /work is a writable project bind mount.
set -euo pipefail
exec 9> /work/.rootfs.lock
flock -n 9 || { echo 'Another rootfs operation is running.' >&2; exit 1; }
root=/work/rootfs/bookworm-armhf
test -s "$root/var/lib/dpkg/status"
test ! -e "$root/usr/sbin/policy-rc.d"
printf '#!/bin/sh\nexit 101\n' > "$root/usr/sbin/policy-rc.d"
chmod 755 "$root/usr/sbin/policy-rc.d"
trap 'rm -f "$root/usr/sbin/policy-rc.d"' EXIT
# Keep build-time DNS out of the final image.
if [[ -L "$root/etc/resolv.conf" ]]; then
    rm "$root/etc/resolv.conf"
fi
cp /etc/resolv.conf "$root/etc/resolv.conf"
/work/scripts/in-armhf-chroot.sh /bin/bash -se < /work/scripts/provision-target.sh
kernel=/work/reference/dtsoc/sw/linux/linux-source-6.1
release=$(cat "$kernel/include/config/kernel.release")
test "$release" = 6.1.187
mkdir -p "$root/lib/modules/$release" "$root/boot"
cp -a /work/reference/dtsoc/sw/linux/modules-staging/lib/modules/"$release"/. "$root/lib/modules/$release/"
# modules_install includes development symlinks to the build container.
for name in build source; do
    if [[ -L "$root/lib/modules/$release/$name" ]]; then
        rm "$root/lib/modules/$release/$name"
    fi
done
cp "$kernel/.config" "$root/boot/config-$release"
cp "$kernel/System.map" "$root/boot/System.map-$release"
depmod -b "$root" -e -F "$kernel/System.map" "$release" 2> /work/logs/depmod.log
test ! -s /work/logs/depmod.log
for firmware in $(modinfo -b "$root" -k "$release" -F firmware mt76x2u); do
    test -s "$root/lib/firmware/$firmware"
done
modinfo -b "$root" -k "$release" mt76x2u
modprobe -d "$root" -S "$release" --show-depends mt76x2u
ln -sfn /run/NetworkManager/resolv.conf "$root/etc/resolv.conf"
echo 'Rootfs provisioning completed.'
