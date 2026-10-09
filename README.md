# DE1-SoC Debian 12 ARMHF

Build scripts and board configuration for Debian 12 on the Terasic DE1-SoC, using Linux 6.1.187 and a validated 4 GiB SD image layout. [中文说明](README.zh-CN.md).

**Current publication: source and documentation. No downloadable public SD image is available yet.** The local system has booted on a real DE1-SoC from a 32 GB microSD card and accepted SSH public-key login over Ethernet. A generic first-login process and FPGA artifact redistribution review are still required before an image release.

## Hardware and validation

| Component | Status |
| --- | --- |
| Board | Terasic DE1-SoC, Cyclone V 5CSEMA5F31C6, ARM Cortex-A9, 1 GiB RAM |
| Debian | ARMHF, Bookworm; tested board reports 12.15 |
| Kernel | 6.1.187; exact configuration included |
| Boot and Ethernet SSH | Verified on one physical board using a 32 GB card |
| USB MT7612U Wi-Fi | mt76x2u modules and firmware provisioned; board test pending |
| NTP | systemd-timesyncd configured; synchronization test pending |
| HPS–FPGA communication | Not validated |
| Automatic SD expansion | Not implemented |

The image builder produces 4,294,967,296 bytes. Use a nominal **8 GB or larger** card; a nominal 4 GB card is normally too small. Only 32 GB media has been tested in this project. Both the partition table and ext4 filesystem are checked against the actual image size, including regression tests for a partition extending beyond the end of the file. Compression reduces download size, not the required target capacity.

## Repository contents

| Path | Purpose |
| --- | --- |
| `scripts/` | QEMU/chroot, provisioning, boot preparation, regular-image building and verification |
| `board/` | DE1-SoC device tree, U-Boot script and extlinux configuration |
| `docker/` | Debian build and image tooling |
| `kernel-config/` | Tested Linux configuration |
| `manifests/` | Package versions from the local build |
| `artifacts/original-build.sha256` | Reference checksums for the locally tested boot artifacts |
| `tests/` | Image-layout regression checks |

Start with [the build workflow](docs/build.md), [validation notes](docs/validation.md), and [licensing and provenance](docs/licensing.md). The build workflow requires separately prepared kernel, U-Boot and FPGA artifacts; this repository is not yet a complete clean-checkout image factory.

## Local tests

```bash
python3 -m unittest discover -s tests -v
```

These tests run without Docker or a board. Image creation uses Docker on Linux; the tested development environment is Arch Linux under WSL2 with its own Docker daemon. No physical disk is written by the image builder.

## Login and public image status

The provisioning scripts create a locked `de1soc` account and prohibit direct root SSH login. A developer must explicitly configure their own login before imaging; see [the build workflow](docs/build.md). No default password, user authorization key, private key, or populated root filesystem is supplied in this repository. Automatic public-key import from the FAT boot partition is planned but not implemented.

## License and references

Project-authored scripts and documentation are distributed under **GPL-2.0-or-later**, with the license text in [LICENSE](LICENSE). Existing file-level notices remain applicable. External dependencies retain their own licenses; this license does not grant rights to excluded upstream FPGA designs or generated bitstreams.

The hardware/build reference is [fredowski/dtsoc](https://github.com/fredowski/dtsoc). [David-OC17/de1soc-linux](https://github.com/David-OC17/de1soc-linux) was also consulted as a Debian image reference. This repository publishes the current project's build helpers and configuration; it does not redistribute either project's SD image.
