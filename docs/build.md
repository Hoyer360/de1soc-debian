# Build workflow for a prepared workspace

These scripts assemble the system from an existing DE1-SoC hardware, bootloader and kernel build. They do not fetch or rebuild the external FPGA reference design automatically. Obtain the external sources under their applicable licenses and prepare the following inputs before running provisioning or boot preparation.

## Required inputs

Paths are relative to this checkout; `/work` is the Docker mount point.

| Required path | Contents |
| --- | --- |
| `reference/dtsoc/sw/linux/linux-source-6.1/` | Configured and built Linux 6.1.187 tree, including zImage, SoCDK DTB, System.map, .config and generated headers |
| `reference/dtsoc/sw/linux/modules-staging/lib/modules/6.1.187/` | Modules installed from that same kernel build |
| `reference/dtsoc/sw/u-boot/u-boot-socfpga/` | Matching built U-Boot, including SPL, u-boot.img and u-boot-with-spl.sfp |
| `reference/dtsoc/output_files/de1_soc_top.rbf` | FPGA bitstream matching that bootloader's HPS handoff |

The tested kernel configuration is `kernel-config/de1soc-6.1.187.config`. The [provenance document](licensing.md) records upstream revisions. Reproducing the external hardware build requires Quartus and its HPS handoff generation; those inputs are not shipped here. Preserve the pairing between the hardware handoff and U-Boot qts headers.

## Build containers

Use the Linux filesystem for the checkout. On WSL2, run these commands in the distribution that owns the Docker daemon.

```bash
docker build -f docker/Dockerfile -t de1soc-build:bookworm docker
docker build -f docker/Dockerfile.rootfs -t de1soc-image-builder:bookworm docker
mkdir -p logs artifacts/boot rootfs
```

## Initialize a new root filesystem

Run this only in a new workspace without an existing `rootfs/bookworm-armhf`. It downloads Debian packages, so network access is required.

```bash
docker run --rm --cap-add SYS_ADMIN \
  --mount "type=bind,src=$PWD,dst=/work" \
  de1soc-image-builder:bookworm bash -euc '
    test ! -e /work/rootfs/bookworm-armhf
    debootstrap --foreign --arch=armhf --variant=minbase    \
      bookworm /work/rootfs/bookworm-armhf http://deb.debian.org/debian
  '
./scripts/chroot.sh env DEBOOTSTRAP_DIR=/debootstrap \
  /bin/sh /debootstrap/debootstrap --second-stage
```

The chroot helper temporarily registers an ARM QEMU interpreter using binfmt_misc with the `F` flag, so child processes can execute after chroot. It requires `SYS_ADMIN` for mounts and cleans up its own registration on normal exit and handled signals. SIGKILL or a host crash can leave a registration requiring manual cleanup. It does not require Docker's full `--privileged` mode.

## Provision and configure personal login

Once the external module tree is available, provision packages, networking and firmware, then run offline checks.

```bash
docker run --rm --cap-add SYS_ADMIN \
  --mount "type=bind,src=$PWD,dst=/work" \
  de1soc-image-builder:bookworm /work/scripts/provision-rootfs.sh
./scripts/chroot.sh /bin/bash -se < scripts/verify-rootfs.sh
./scripts/chroot.sh passwd de1soc
```

The last command is interactive: use your own password, never a password from a README. It modifies the local build rootfs; it does not change an existing image. The account belongs to `sudo` and `dialout`; direct root SSH and empty passwords are disabled. Provisioning defaults to hostname `de1soc` and timezone `Australia/Sydney`, which can be changed locally before imaging. A password-bearing image is for personal deployment and must not be uploaded as a generic release.

Do not run image creation concurrently with rootfs mutations. The helper scripts use a shared workspace lock. Host SSH keys and machine-id are left uninitialized for per-board generation on first boot.

## Prepare boot files and build an image

`artifacts/original-build.sha256` contains checksums from the tested local build. The preparation script refuses mismatching inputs. If you build your own kernel, U-Boot or FPGA design, first validate the intended combination, then deliberately regenerate that checksum file for your own artifacts; do not bypass it just to suppress a mismatch.

```bash
docker run --rm --network none \
  --mount "type=bind,src=$PWD,dst=/work" \
  de1soc-image-builder:bookworm /work/scripts/prepare-boot.sh

docker run --rm --network none \
  --mount "type=bind,src=$PWD,dst=/work" \
  de1soc-image-builder:bookworm \
  python3 /work/scripts/build-image.py de1soc-bookworm-armhf-personal.img
```

The builder creates a new regular 4 GiB image and refuses an existing output filename or a device path. It checks MBR bounds, filesystem consistency, SPL placement, boot files, rootfs contents and account consistency before publishing the local file. It emits a checksum and manifest next to the image. The validation compares against the workspace's current rootfs and artifacts, so it is not a standalone verifier for an unrelated download.

| MBR slot | Type | Start sector | Sector count | Role |
| --- | --- | ---: | ---: | --- |
| p1 | FAT32 (0x0c) | 4096 | 262144 | Boot files |
| p2 | Linux (0x83) | 266240 | 8120320 | ext4 root filesystem |
| p3 | Altera A2 (0xa2) | 2048 | 2048 | SPL and U-Boot |

Sectors are 512 bytes. Partition numbering intentionally differs from physical order: the root partition is **p2**. Do not copy another project's command that expands p3 as root. No automatic expansion is provided. Physical SD writing and expansion must be done separately after positively identifying the target device.

A clean build using today's Debian mirrors may select newer package versions. This workflow is not bit-for-bit reproducible; the package manifest documents the tested build rather than pinning future APT resolution. The external build steps and clean-checkout workflow have not been re-executed for this source publication.
