#!/bin/bash
set -euo pipefail
cd /work
kernel=reference/dtsoc/sw/linux/linux-source-6.1
uboot=reference/dtsoc/sw/u-boot/u-boot-socfpga
mkdir -p artifacts/boot/extlinux
sha256sum -c artifacts/original-build.sha256
arm-linux-gnueabihf-gcc -E -nostdinc -undef -D__DTS__ -x assembler-with-cpp \
    -I "$kernel/arch/arm/boot/dts" -I "$kernel/include" \
    board/socfpga_cyclone5_de1soc.dts -o artifacts/de1soc.preprocessed.dts
dtc -I dts -O dtb -o artifacts/boot/socfpga_cyclone5_de1soc.dtb \
    artifacts/de1soc.preprocessed.dts 2> logs/de1soc-dtc.log
cp "$kernel/arch/arm/boot/zImage" artifacts/boot/
cp "$kernel/arch/arm/boot/dts/socfpga_cyclone5_socdk.dtb" artifacts/boot/
cp reference/dtsoc/output_files/de1_soc_top.rbf artifacts/boot/
cp board/extlinux.conf artifacts/boot/extlinux/
mkimage -A arm -O linux -T script -C none -n 'DE1-SoC Debian boot' \
    -d board/boot.script artifacts/boot/u-boot.scr
mkimage -l "$uboot/spl/u-boot-spl.sfp"
mkimage -l "$uboot/u-boot.img"
cp "$uboot/u-boot-with-spl.sfp" artifacts/
echo 'Boot artifacts prepared; no kernel, U-Boot or FPGA rebuild.'
