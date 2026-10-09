# Licensing and source provenance

The project-authored helpers and documentation in this repository are licensed under GPL-2.0-or-later. `board/socfpga_cyclone5_de1soc.dts` retains its existing GPL-2.0+ SPDX notice. The complete GPL version 2 text is provided in the root LICENSE file; the “or later” grant applies to project-authored material as stated here. External components and their individual notices are not relicensed by this repository.

## External sources

| Component | Source/revision used locally | Publication status |
| --- | --- | --- |
| Hardware/build reference | [fredowski/dtsoc](https://github.com/fredowski/dtsoc), `e483ffe7f1cde7e3fec78c1e13138ef1efde4938` | Source tree and generated FPGA bitstream excluded |
| U-Boot | [altera-opensource/u-boot-socfpga](https://github.com/altera-opensource/u-boot-socfpga), `0b3e82ca6e1e1859f7fc101987ac698f2743cc41` | Binaries and local hardware handoff headers excluded |
| Kernel | Debian Bookworm linux-source-6.1, kernel release 6.1.187 | Configuration included; source tree and binaries excluded |
| Root filesystem | Debian Bookworm ARMHF | Package version manifest included; populated rootfs excluded |
| MT7612U firmware | Debian firmware-misc-nonfree: mt7662.bin and mt7662_rom_patch.bin | Firmware binaries excluded |
| Additional image reference | [David-OC17/de1soc-linux](https://github.com/David-OC17/de1soc-linux) | Attribution only; its SD image is not redistributed |

At the time of inspection, the dtsoc reference checkout and current repository root had no LICENSE file, and the inspected FPGA file headers did not establish a redistribution license. The resulting FPGA bitstream is also omitted while those rights are clarified. Attribution alone does not grant redistribution rights. This is a statement of the unresolved provenance review, not a claim that all upstream files are unlicensed.

Linux's COPYING identifies GPL-2.0 WITH Linux-syscall-note, with additional file-level licenses. U-Boot contains GPL and other file-level licenses; the local build modifies four Cyclone V qts configuration headers to match the hardware handoff. A future binary release must provide the corresponding source, modifications, configuration and required notices under the applicable licenses. Upstream repository links alone do not replace those obligations.

The Debian firmware-misc-nonfree copyright file assigns `mt76*.bin` to binary-redist-MediaTek, allowing unmodified binary redistribution subject to its notice and other conditions. Other Debian packages retain their respective licenses. A full binary-release source and notice bundle has not yet been prepared.
