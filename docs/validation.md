# Validation record

The local personal deployment booted on a Terasic DE1-SoC using a 32 GB microSD card. Ethernet SSH public-key authentication succeeded; the board returned hostname `de1soc`, UID/GID 1000, kernel `6.1.187` and Debian `12.15`. This does not establish Wi-Fi connectivity, NTP synchronization, FPGA register access, Ethernet throughput or long-term stability.

Earlier SSH failures were caused by connecting to another device's IP address. That endpoint remained reachable after the board was disconnected and advertised a different Debian/OpenSSH version. Check the router's current DHCP lease and the target's identity before changing image passwords or SSH policy. This repository does not prescribe a fixed LAN address.

## Image geometry and offline checks

The tested builder uses a 4 GiB regular image, reserves 1 MiB at the tail and keeps every partition within the image. The root ext4 filesystem also fits its partition. FAT/ext4 consistency checks, four identical SPL copies, the U-Boot header location, boot content comparisons and SHA-256 validation passed during local construction.

The five unit tests cover a valid layout, truncation, an oversized root partition, overlap and shifted MBR slots. They deliberately test a roughly 115 GiB partition claim inside a much smaller file. Compression cannot fix an invalid partition table or shrink the filesystem required by a card.

## Public release readiness

The original local base image was inspected directly: its root and de1soc standard SSH authorization files were absent/empty; `/etc/shadow` and `/etc/shadow-` contained only locked account markers without password hashes. Machine-id was empty and the SSH configuration directory contained no host key files. Partition and ext4 bounds, `e2fsck -fn` and the saved SHA-256 passed. This was a targeted configuration audit, not a complete forensic scan of all files or free space.

That base image cannot provide an immediate login because its accounts are locked. The personally configured images are excluded from public distribution. A generic first-login mechanism and its hardware test remain pending. No downloadable image is attached to this source publication.
