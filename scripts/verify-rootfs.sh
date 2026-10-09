#!/bin/bash
# Feed to ARM bash via scripts/chroot.sh /bin/bash -se < this-file.
set -euo pipefail
test "$(dpkg --print-architecture)" = armhf
dpkg --audit
apt-get check
systemctl is-enabled NetworkManager systemd-timesyncd ssh serial-getty@ttyS0
systemd-analyze verify --man=no /etc/systemd/system/de1soc-ssh-hostkeys.service /lib/systemd/system/ssh.service
passwd -S de1soc
passwd -S root
# Host keys are deliberately generated per board at boot. Use a throwaway key
# only in the builder's tmpfs to test sshd's effective config and syntax.
mkdir -p /run/sshd
keydir=$(mktemp -d /run/ssh-check.XXXXXX)
trap 'rm -rf "$keydir"' EXIT
ssh-keygen -q -t ed25519 -N '' -f "$keydir/key"
/usr/sbin/sshd -t -h "$keydir/key"
/usr/sbin/sshd -T -h "$keydir/key" | grep -E 'permitrootlogin|permitemptypasswords|passwordauthentication'
modinfo -k 6.1.187 -F firmware mt76x2u
modinfo -k 6.1.187 -F vermagic mt76x2u
modprobe -S 6.1.187 --show-depends mt76x2u
tar -xOzf /usr/share/usb_modeswitch/configPack.tar.gz 0e8d:2870
test "$(find /lib/modules/6.1.187 -name '*.ko' | wc -l)" -eq 28
ls -l /lib/firmware/mt7662.bin /lib/firmware/mt7662_rom_patch.bin
test -x /sbin/init
test ! -s /etc/machine-id
test ! -e /etc/ssh/ssh_host_ed25519_key
echo 'Offline rootfs checks passed; hardware services have not been started.'
