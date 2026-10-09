# DE1-SoC Debian 12 ARMHF

本仓库提供 Terasic DE1-SoC 的 Debian 12 构建脚本、Linux 6.1.187 配置、设备树和镜像布局验证工具。[English](README.md)。

**当前发布源码和文档，尚无公开 SD 镜像下载。** 本地版本已在 32 GB microSD 上启动，实机报告 Debian 12.15、内核 6.1.187，并通过有线网络完成 SSH 公钥登录。Wi-Fi、NTP 同步和 HPS–FPGA 通信仍待验证。

## 镜像容量

镜像大小为 4 GiB（4,294,967,296 字节），要求标称至少 8 GB 的卡；不能宣称兼容标称 4 GB 卡。本项目仅实测过 32 GB 卡。构建时同时校验镜像文件、分区和 ext4 容量，避免分区超出文件末尾。首次启动自动扩容尚未实现。

## 开发使用

[构建说明](docs/build.md) 介绍 Docker、ARMHF chroot、系统配置及普通镜像构建流程。该流程需要自行准备匹配的内核、U-Boot 和 FPGA 构建产物，目前不是从干净 checkout 一键生成镜像的完整流程。

```bash
python3 -m unittest discover -s tests -v
```

`de1soc` 账户初始锁定，没有固定默认密码。开发者需在本地交互配置自己的凭据后再制作个人镜像。公开镜像计划提供独立的首次登录初始化方式；启动分区自动导入公钥尚未实现。仓库不包含维护者的授权公钥、密码配置、私钥或 rootfs。

## 授权和测试范围

本项目自编脚本及文档采用 GPL-2.0-or-later；已有文件级许可保留，外部依赖分别遵循自己的许可证。实际使用的 `fredowski/dtsoc` FPGA 参考文件及生成位流仍需确认再分发授权，所以没有纳入本次公开内容。详细说明见 [来源和许可证](docs/licensing.md) 与 [验证记录](docs/validation.md)。
