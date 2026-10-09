#!/usr/bin/env python3
"""Build only a new regular 4 GiB image; never accept a block-device path."""
import hashlib
import fcntl
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile

WORK = Path('/work')
OUTPUT = WORK / 'artifacts/images'
SECTOR = 512
IMAGE_BYTES = 4 * 1024**3
PARTITIONS = [
    {'number': 1, 'start': 4096, 'size': 262144, 'type': 0x0c},
    # Keep 1 MiB at EOF; also avoids sfdisk's first-partition alignment
    # accounting warning with the deliberately non-monotonic p1/p2/p3 order.
    {'number': 2, 'start': 266240, 'size': 8120320, 'type': 0x83},
    {'number': 3, 'start': 2048, 'size': 2048, 'type': 0xa2},
]


def run(*args, **kwargs):
    print('+', *map(str, args), flush=True)
    return subprocess.run(list(map(str, args)), check=True, **kwargs)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def copy_sparse(source, dest, offset):
    with source.open('rb') as src:
        dest.seek(offset)
        while chunk := src.read(1024 * 1024):
            if chunk.strip(b'\0'):
                dest.write(chunk)
            else:
                dest.seek(len(chunk), os.SEEK_CUR)


def main():
    os.umask(0o077)
    name = sys.argv[1] if len(sys.argv) == 2 else 'de1soc-bookworm-armhf.img'
    if len(sys.argv) > 2 or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]*\.img', name):
        raise SystemExit('Pass a filename ending in .img, never a path or device.')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    final = OUTPUT / name
    partial = OUTPUT / (name + '.partial')
    if final.exists() or final.is_symlink():
        raise SystemExit(f'Refusing to overwrite {final}')
    root = WORK / 'rootfs/bookworm-armhf'
    boot = WORK / 'artifacts/boot'
    spl = WORK / 'artifacts/u-boot-with-spl.sfp'
    if not (root / 'var/lib/de1soc-provisioned').is_file():
        raise SystemExit('Provision the rootfs first.')
    if (root / 'usr/sbin/policy-rc.d').exists():
        raise SystemExit('Rootfs provisioning is still active.')
    login_status = subprocess.run(
        ['passwd', '--root', str(root), '--status', 'de1soc'],
        check=True, capture_output=True, text=True).stdout.split()[1]
    authorized_keys = root / 'home/de1soc/.ssh/authorized_keys'
    authorized_keys_sha256 = digest(authorized_keys) if authorized_keys.is_file() else None
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        if line.split()[4].startswith(str(root) + '/'):
            raise SystemExit('Unmount build-time rootfs mounts before imaging.')
    if spl.stat().st_size > PARTITIONS[2]['size'] * SECTOR:
        raise SystemExit('SPL/U-Boot exceeds the A2 partition.')

    # Exclusive creation rejects existing files, symlinks and devices.
    with partial.open('xb') as image, tempfile.TemporaryDirectory(dir=OUTPUT) as tmp:
        image.truncate(IMAGE_BYTES)
        mbr = bytearray(SECTOR)
        struct.pack_into('<I', mbr, 440, 0xde1a2026)
        for p in PARTITIONS:
            struct.pack_into('<B3sB3sII', mbr, 446 + (p['number'] - 1) * 16,
                             0x80 if p['number'] == 1 else 0,
                             b'\xfe\xff\xff', p['type'], b'\xfe\xff\xff',
                             p['start'], p['size'])
        mbr[510:512] = b'\x55\xaa'
        image.write(mbr)
        fat = Path(tmp) / 'boot.fat'
        ext = Path(tmp) / 'root.ext4'
        for path, part in ((fat, PARTITIONS[0]), (ext, PARTITIONS[1])):
            with path.open('xb') as stream:
                stream.truncate(part['size'] * SECTOR)
        run('mkfs.vfat', '-F', '32', '-n', 'DE1SOCBOOT', '-i', 'DE1A2026', fat)
        run('mcopy', '-i', fat, '-s', *sorted(boot.iterdir()), '::/')
        run('mkfs.ext4', '-F', '-L', 'DE1SOCROOT', '-U',
            'de1a2026-1000-4000-8000-000000000002', '-m', '1',
            '-E', 'lazy_itable_init=0,lazy_journal_init=0', '-d', root, ext)
        run('fsck.vfat', '-n', fat)
        run('e2fsck', '-fn', ext)
        for path, part in ((fat, PARTITIONS[0]), (ext, PARTITIONS[1]), (spl, PARTITIONS[2])):
            copy_sparse(path, image, part['start'] * SECTOR)
        image.flush()
        os.fsync(image.fileno())

    # Validate the assembled image, not only its component filesystems.
    run(sys.executable, WORK / 'scripts/verify-image.py', partial)
    os.link(partial, final)  # Atomically publish without replacing an existing file.
    partial.unlink()
    manifest = {'image': name, 'bytes': final.stat().st_size,
                'sha256': digest(final), 'partitions': PARTITIONS,
                'boot_files': {str(p.relative_to(boot)): digest(p)
                               for p in sorted(boot.rglob('*')) if p.is_file()},
                'spl_sha256': digest(spl), 'hardware_tested': False,
                'login': {'user': 'de1soc', 'password_status': login_status,
                          'authorized_keys_sha256': authorized_keys_sha256,
                          'note': 'P=password set, L=locked, NP=no password; authentication not hardware-tested.'}}
    final.with_suffix('.manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    final.with_suffix('.img.sha256').write_text(f'{manifest["sha256"]}  {name}\n')
    print(f'Validated image: {final} ({IMAGE_BYTES} bytes)', flush=True)


if __name__ == '__main__':
    with (WORK / '.rootfs.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('Another rootfs operation is running.')
        main()
