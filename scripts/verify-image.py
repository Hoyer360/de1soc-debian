#!/usr/bin/env python3
"""Independently verify MBR bounds, SPL placement and extracted filesystems."""
import os
from pathlib import Path
import stat
import re
import struct
import subprocess
import sys
import tempfile


def run(*args, **kwargs):
    return subprocess.run(list(map(str, args)), check=True, **kwargs)


def check(condition, message):
    if not condition:
        raise ValueError(message)


def validate_mbr(mbr, length):
    check(len(mbr) == 512 and mbr[510:] == b'\x55\xaa', 'Invalid MBR signature')
    check(struct.unpack_from('<I', mbr, 440)[0] == 0xde1a2026, 'Unexpected disk ID')
    parts = []
    for i in range(4):
        active, _, kind, _, start, size = struct.unpack_from('<B3sB3sII', mbr, 446 + i * 16)
        if kind:
            check(active in (0, 0x80), 'Invalid active flag')
            check(start >= 2048 and size > 0, 'Invalid partition geometry')
            check((start + size) * 512 <= length, 'Partition extends beyond image EOF')
            parts.append((i + 1, kind, start * 512, size * 512))
    check([(p[0], p[1]) for p in parts] == [(1, 0x0c), (2, 0x83), (3, 0xa2)],
          'Unexpected partition slots/types')
    ordered = sorted(parts, key=lambda p: p[2])
    for first, second in zip(ordered, ordered[1:]):
        check(first[2] + first[3] <= second[2], 'Overlapping partitions')
    check(parts[0][2] == 2 * 1024**2 and parts[2][2] == 1024**2,
          'Unexpected Cyclone V boot partition offsets')
    return parts


def main():
    image = Path(sys.argv[1])
    check(not image.is_symlink() and stat.S_ISREG(image.stat().st_mode), 'Regular image required')
    with image.open('rb') as stream:
        parts = validate_mbr(stream.read(512), image.stat().st_size)
        for p in parts:
            print(f'p{p[0]} type={p[1]:02x} offset={p[2]} bytes={p[3]}', flush=True)
        spl = Path('/work/artifacts/u-boot-with-spl.sfp').read_bytes()
        check(len(spl) <= parts[2][3], 'SPL/U-Boot too large')
        stream.seek(parts[2][2])
        check(stream.read(len(spl)) == spl, 'SPL/U-Boot differs from original artifact')
        check(spl[:65536] == spl[65536:131072] == spl[131072:196608] == spl[196608:262144],
              'Four SPL copies differ')
        check(spl[262144:262148] == b'\x27\x05\x19\x56', 'U-Boot header missing at A2 + 256 KiB')
        with tempfile.TemporaryDirectory(dir='/work/artifacts/images') as tmp:
            fat, root = Path(tmp) / 'boot.fat', Path(tmp) / 'root.ext4'
            for path, part in ((fat, parts[0]), (root, parts[1])):
                stream.seek(part[2])
                remaining = part[3]
                with path.open('xb') as target:
                    target.truncate(remaining)
                    while remaining:
                        chunk = stream.read(min(1024 * 1024, remaining))
                        check(bool(chunk), 'Unexpected EOF extracting partition')
                        if chunk.strip(b'\0'):
                            target.write(chunk)
                        else:
                            target.seek(len(chunk), os.SEEK_CUR)
                        remaining -= len(chunk)
            with root.open('rb') as fs:
                fs.seek(1024)
                sb = fs.read(1024)
            check(struct.unpack_from('<H', sb, 56)[0] == 0xef53, 'Invalid ext4 magic')
            blocks = struct.unpack_from('<I', sb, 4)[0] | (struct.unpack_from('<I', sb, 336)[0] << 32)
            block_size = 1024 << struct.unpack_from('<I', sb, 24)[0]
            check(blocks * block_size <= parts[1][3], 'ext4 exceeds its partition')
            run('fsck.vfat', '-n', fat)
            run('e2fsck', '-fn', root)
            for source in sorted(Path('/work/artifacts/boot').rglob('*')):
                if source.is_file():
                    copied = Path(tmp) / 'boot-file'
                    run('mcopy', '-o', '-i', fat, '::/' + str(source.relative_to('/work/artifacts/boot')), copied)
                    check(copied.read_bytes() == source.read_bytes(), f'Boot file mismatch: {source.name}')
            for filename in ('/etc/fstab', '/etc/hostname', '/etc/passwd', '/lib/firmware/mt7662.bin',
                             '/lib/firmware/mt7662_rom_patch.bin', '/lib/modules/6.1.187/modules.dep'):
                # debugfs does not traverse the merged-/usr /lib symlink.
                disk_name = filename.replace('/lib/', '/usr/lib/', 1) if filename.startswith('/lib/') else filename
                copied = Path(tmp) / 'root-file'
                if copied.exists():
                    copied.unlink()
                run('debugfs', '-R', f'dump {disk_name} {copied}', root, stdout=subprocess.DEVNULL)
                check(copied.is_file(), f'Rootfs file missing: {filename}')
                check(copied.read_bytes() == (Path('/work/rootfs/bookworm-armhf') / disk_name[1:]).read_bytes(),
                      f'Rootfs file mismatch: {filename}')
            # Compare credentials only in memory; never print or persist hashes.
            shadow = run('debugfs', '-R', 'cat /etc/shadow', root, capture_output=True).stdout
            check(shadow == Path('/work/rootfs/bookworm-armhf/etc/shadow').read_bytes(),
                  'Image account credentials differ from the source rootfs')
            print('Image account database matches the source rootfs (credentials not displayed).')
            authorized_keys = Path('/work/rootfs/bookworm-armhf/home/de1soc/.ssh/authorized_keys')
            if authorized_keys.is_file():
                key_content = run('debugfs', '-R', 'cat /home/de1soc/.ssh/authorized_keys',
                                  root, capture_output=True).stdout
                check(key_content == authorized_keys.read_bytes(), 'Authorized SSH keys differ')
                for path, mode in (('/home/de1soc', 0o755), ('/home/de1soc/.ssh', 0o700),
                                   ('/home/de1soc/.ssh/authorized_keys', 0o600)):
                    info = run('debugfs', '-R', f'stat {path}', root,
                               capture_output=True, text=True).stdout
                    actual_mode = re.search(r'Mode:\s+([0-7]+)', info)
                    owner = re.search(r'User:\s+(\d+)\s+Group:\s+(\d+)', info)
                    check(actual_mode is not None and int(actual_mode[1], 8) == mode,
                          f'Incorrect SSH path permissions: {path}')
                    check(owner is not None and (int(owner[1]), int(owner[2])) == (1000, 1000),
                          f'Incorrect SSH path ownership: {path}')
                print('Authorized SSH keys and image ownership/permissions verified.')
            print(f'ext4: {blocks} blocks x {block_size} bytes; partition bounds and content verified.')


if __name__ == '__main__':
    main()
