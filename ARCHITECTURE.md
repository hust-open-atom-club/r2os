# R² OS / meta-k230 Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐    术语说明（Yocto 相关）
│                          Yocto / Poky (Wrynose)                              │    Yocto：嵌入式 Linux 构建体系，不是单一发行版
│  ┌───────────────────────────────────────────────────────────────────────┐   │    Poky：Yocto 官方参考发行版和默认构建基础
│  │             meta-k230  BSP Layer  (priority: 6)                       │   │    BSP：板级支持层，描述特定 SoC/板卡的构建支持
│  │             LAYERSERIES_COMPAT = scarthgap / wrynose                  │   │    Layer：元数据层，包含 recipe、配置和 class
│  └───────────────────────────────────────────────────────────────────────┘   │    meta-k230：本项目的 K230 BSP layer
└──────────────────────────────────────────────────────────────────────────────┘    LAYERSERIES_COMPAT：声明兼容的 Yocto 发布系列
                                      │    BitBake：Yocto 的任务执行和依赖调度引擎
                                      v    Recipe/.bb：描述源码、依赖、编译和安装步骤
┌──────────────────────────────────────────────────────────────────────────────┐    配置相关
│                           Configuration Layer                                │    bblayers.conf：列出参与解析的 layer
│                                                                              │    local.conf：本地构建参数，例如 MACHINE/DISTRO/缓存路径
│  conf/templates/default/                conf/fragments/                      │    template：初始化 build 目录时使用的配置模板
│  ┌──────────────────────────┐           ┌──────────────────────┐             │    fragment：可复用的小段配置，用于组合构建参数
│  │ bblayers.conf.sample     │           │ distro/r2os    │             │    DISTRO：发行版策略，决定 init、包格式和功能集合
│  │   - meta (oe-core)       │           │   -> DISTRO_NAME     │             │    MACHINE：目标硬件/板卡，选择内核、设备树和启动参数
│  │   - meta-yocto-bsp       │           │      = "R² OS"       │             │    DISTRO_NAME：发行版显示名称，用于 /etc/os-release
│  │                          │           │                      │             │    DL_DIR：源码下载缓存，复用后可减少重复下载
│  │   - meta-poky            │           │ machine/k230-canmv   │             │    SSTATE：共享状态缓存，复用后可减少重复编译
│  │   - meta-k230            │           │  -> MACHINE = "canmv"│             │    oe-core/meta：OpenEmbedded Core，提供基础 recipe
│  │                          │           └──────────────────────┘             │    meta-poky：Poky 发行版相关 metadata
│  │ local.conf.sample        │                                                │    meta-yocto-bsp：Yocto 示例 BSP layer
│  │   - MACHINE = k230-canmv │                                                │
│  │   - DISTRO  = r2os │                                                │    发行版/机器相关
│  │   - DL_DIR / SSTATE path │                                                │    conf/machine：定义板卡、CPU 架构、镜像类型和启动方式
│  └──────────────────────────┘                                                │    conf/distro：定义发行版策略、包格式和功能开关
│                                                                              │    IMAGE_FEATURES：镜像级功能，例如 SSH、空密码、包管理
│  conf/machine/k230-canmv.conf            conf/distro/r2os.conf         │    DISTRO_FEATURES：发行版能力集合，例如 ipv4、nfs、pam
│  ┌────────────────────────────────┐      ┌────────────────────────────┐      │    PACKAGE_CLASSES/ipk：选择生成 .ipk 软件包
│  │ SoC: Canaan K230               │      │ Name:   R² OS              │      │    RootFS：镜像中的根文件系统内容
│  │                                │      │ Base:   poky.conf          │      │    DISTRO_NAME：发行版显示名称
│  │ Arch: RISC-V 64 (rv64imafdc)   │      │ Package: ipk (.ipk)        │      │    IMAGE_FSTYPES：决定输出 cpio.gz、ext4、wic.gz 等格式
│  │ CPU:  T-HEAD C908 x 1 core     │      │ Init:   BusyBox (no sysd)  │      │    BusyBox init：轻量 init；这里没有启用 systemd
│  │ RAM:  2GB (QEMU)               │      │                            │      │    Dropbear：轻量 SSH server，作为普通包安装
│  │                                │      │ Image Features:            │      │    empty-root-password：root 密码为空，便于 QEMU 验证
│  │ Kernel:   linux-k230 6.18.28   │      │  - allow-empty-password    │      │    allow-empty-password：开发镜像常用，允许空密码登录
│  │ Firmware: OpenSBI (generic)    │      │  - empty-root-password     │      │    serial autologin：由 K230 image 后处理 inittab
│  │ Bootloader: U-Boot (ext SDK)   │      │  - allow-root-login        │      │    usrmerge：使用 /usr 合并目录布局
│  │                                │      │                            │      │
│  │ Image Types:                   │      │                            │      │    输出/缓存相关
│  │  cpio.gz / ext4 / wic.gz / tar │      │ Distro Features:           │      │    tmp/deploy/images：最终镜像、内核和设备树输出目录
│  │                                │      │  ipv4 / ipv6 / nfs / pam   │      │    deploy-rpm/ipk/deb：软件包输出目录，取决于包格式
│  │ QEMU: -machine k230-canmv      │      │  usrmerge                  │      │    sstate-cache：任务结果缓存，可跨 build 复用
│  │  -smp 1  -m 2G  -nographic     │      └────────────────────────────┘      │    downloads：源码包和 git mirror 缓存
│  │  -nic user,model=usb-rtl8152   │                                          │
│  │  hostfwd=tcp::10022-:22        │                                          │
│  │  -drive if=sd,format=raw       │                                          │
│  └────────────────────────────────┘                                          │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      v
┌──────────────────────────────────────────────────────────────────────────────┐
│                            Recipes Layer                                     │
│                                                                              │
│  recipes-kernel/linux/linux-k230_6.18.bb                                     │    recipes-kernel：内核相关 recipe 的常见目录
│  ┌───────────────────────────────────────────────────────────────────────┐   │    linux-k230_6.18.bb：内核 recipe，版本写在文件名中
│  │ Source: kernel.org  linux-6.18.28.tar.xz                              │   │    SRC_URI：recipe 中声明源码下载位置和补丁
│  │ Config: defconfig  +  k230-canmv.cfg  (merge_config.sh)               │   │    merge_config.sh：把 defconfig 和配置片段合并成最终配置
│  │ DTS:    k230-canmv.dts  -> arch/riscv/boot/dts/canaan/                │   │    DTS/DTB：设备树源码/编译产物，由内核构建流程生成
│  │ Output: Image  +  canaan/k230-canmv.dtb                               │   │    do_deploy：把内核、设备树等产物复制到 deploy 目录
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  recipes-core/images/k230-core-image.bb                                      │    recipes-core/images：镜像 recipe 的常见目录
│  ┌───────────────────────────────────────────────────────────────────────┐   │    image recipe：定义最终 rootfs 要安装什么
│  │ Inherits: core-image                                                  │   │    inherit：复用 .bbclass 中定义的通用构建逻辑
│  │ RootFS:   256MB + 64MB extra                                          │   │    IMAGE_ROOTFS_*：控制根文件系统大小和额外空间
│  │ Installs: packagegroup-k230-common                                    │   │    IMAGE_INSTALL：镜像预装包列表通常在这里汇总
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  recipes-core/packagegroups/packagegroup-k230-common.bb                      │    packagegroup：用一个 recipe 聚合多组运行时软件包
│  ┌───────────────────────────────────────────────────────────────────────┐   │    RDEPENDS：packagegroup 常用它声明运行时依赖
│  │ ┌─────────────────────────────┐  ┌────────────────────────────────┐   │   │
│  │ │ OE Core CLI Tools           │  │ Networking                     │   │   │
│  │ ├─────────────────────────────┤  ├────────────────────────────────┤   │   │
│  │ │ busybox    bash             │  │ dhcpcd     dropbear            │   │   │
│  │ │ coreutils findutils         │  │ curl       wget                │   │   │
│  │ │ grep sed gawk diffutils     │  │ iproute2   iputils             │   │   │
│  │ │ file which tar xz less vim  │  │ net-tools  ethtool             │   │   │
│  │ │ procps psmisc kmod strace   │  │ rsync      socat               │   │   │
│  │ │ lsof sudo opkg              │  │                                │   │   │
│  │ └─────────────────────────────┘  └────────────────────────────────┘   │   │
│  │ ┌─────────────────────────────┐  ┌────────────────────────────────┐   │   │
│  │ │ Peripherals / Storage       │  │ Kernel Artifacts               │   │   │
│  │ ├─────────────────────────────┤  ├────────────────────────────────┤   │   │
│  │ │ usbutils   pciutils         │  │ Image                          │   │   │
│  │ │ dosfstools e2fsprogs        │  │ k230-canmv.dtb                 │   │   │
│  │ │ parted     mtd-utils        │  │ fw_payload.bin                 │   │   │
│  │ └─────────────────────────────┘  └────────────────────────────────┘   │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      v
┌──────────────────────────────────────────────────────────────────────────────┐
│                         WIC Image Partition Layout                           │
│                                                                              │
│  wic/k230-canmv-sdimage.wks                                                  │    .wks：WIC 的磁盘分区布局描述文件
│  ┌───────────────────────────────────────────────────────────────────────┐   │    WIC：Yocto 用来生成 SD/磁盘镜像的工具
│  │  MBR (msdos partition table)                                          │   │    MBR/msdos：传统分区表格式
│  │  ┌──────────────────────┬────────────────────────────────────────┐    │   │    part：.wks 中定义分区的语句
│  │  │ /boot (FAT32, 64MB)  │  / (ext4, 1980MB)                      │    │   │    /boot：通常放内核、设备树和启动文件
│  │  │ active, align=4096   │  align=4096                            │    │   │    align：控制分区对齐，便于启动器和存储介质
│  │  │                      │                                        │    │   │
│  │  │  - Image (kernel)    │  - BusyBox init                        │    │   │
│  │  │  - k230-canmv.dtb    │  - CLI tools                           │    │   │
│  │  │  - U-Boot (ext SDK)  │  - Dropbear SSH                        │    │   │
│  │  │                      │  - dhcpcd networking                   │    │   │
│  │  └──────────────────────┴────────────────────────────────────────┘    │   │    wic.gz：压缩后的整盘镜像，适合写入 SD 卡
│  └───────────────────────────────────────────────────────────────────────┘   │    bootimg/rootfs source：WIC 常用的分区内容来源
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                              Boot Flow                                       │
│                                                                              │
│   QEMU                 U-Boot                    OpenSBI                     │
│  ┌──────────┐    ┌─────────────────┐    ┌──────────────────────┐             │
│  │ -machine │    │ External K230   │    │ PLAT = generic       │             │
│  │   k230   │--->│ SDK U-Boot      │--->│ FW_TEXT_START =      │             │
│  │ -m 2G    │    │ binary from     │    │   0x0800_0000        │             │
│  │ -smp 1   │    │ prebuilt/k230-  │    │ FW_JUMP_ADDR  =      │             │
│  │ -nic ... │    │ sdk/riscv-      │    │   0x0820_0000        │             │
│  └──────────┘    │ nomtee/u-boot   │    │ FW_FDT_ADDR   =      │             │
│                  └────────┬────────┘    │   0x0A00_0000        │             │
│                           │             └──────────┬───────────┘             │
│                           │                        │                         │
│                           v                        v                         │
│                     Loads OpenSBI          Jumps to Linux Kernel             │
│                     from SD image          at 0x0820_0000                    │
│                                                      │                       │
│                          ┌───────────────────────────┘                       │
│                          v                                                   │
│                    ┌──────────────────────────┐                              │
│                    │      Linux Kernel        │                              │
│                    │  Image @ 0x0820_0000     │                              │
│                    │  DTB   @ 0x0A00_0000     │                              │
│                    │  cmdline:                │                              │
│                    │   console=ttyS0,115200   │                              │
│                    │   root=/dev/mmcblk0p2    │                              │
│                    │   rootwait rw            │                              │
│                    └────────────┬─────────────┘                              │
│                                 │                                            │
│                                 v                                            │
│                    ┌──────────────────────────┐                              │
│                    │     BusyBox init         │                              │
│                    └────────────┬─────────────┘                              │
│                                 │                                            │
│              ┌──────────────────┼──────────────────┐                         │
│              v                  v                  v                         │
│      ┌────────────┐    ┌────────────┐    ┌────────────────┐                  │
│      │  dhcpcd    │    │  dropbear  │    │  serial ttyS0  │                  │
│      │  DHCP      │    │  SSH:10022 │    │  autologin     │                  │
│      └────────────┘    └────────────┘    └────────────────┘                  │
│                                                                              │
│  -- Direct Boot (--initrd) --                                                │
│   QEMU -> OpenSBI -> Linux Kernel (initrd cpio.gz) -> BusyBox init           │
│                                                                              │
│  -- SD + U-Boot Boot (--sd --uboot) --                                       │
│   QEMU -> U-Boot (ext SDK) -> OpenSBI -> Linux Kernel -> BusyBox init        │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                   Device Tree Hardware Topology (k230-canmv.dts)             │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐   │
│  │                       Canaan K230 SoC                                 │   │
│  │                                                                       │   │
│  │  ┌───────────────┐  ┌────────────────────┐  ┌────────────────────┐    │   │
│  │  │ CPU0          │  │ Interrupt Ctrl     │  │ UART0              │    │   │
│  │  │ T-HEAD C908   │  │ CLINT @f0400_0000  │  │ snps,dw-apb-uart   │    │   │
│  │  │ rv64imafdc    │  │ PLIC  @f0000_0000  │  │ @0x9140_0000       │    │   │
│  │  │ sv39 MMU      │  │ ndev=208           │  │ IRQ=16, 115200bps  │    │   │
│  │  └───────────────┘  └────────────────────┘  └────────────────────┘    │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────┐  ┌─────────────────────────┐     │   │
│  │  │ MMC / SD                        │  │ USB Host                │     │   │
│  │  │ SD0 @0x9158_0000 (disabled)     │  │ USB0 @0x9150_0000       │     │   │
│  │  │ SD1 @0x9158_1000 -> mmcblk1     │  │   (disabled)            │     │   │
│  │  │   dwcmshc-sdhci, 4-bit, 50MHz   │  │ USB1 @0x9154_0000       │     │   │
│  │  │   cap-sd-highspeed, no-mmc      │  │   DWC2 host mode        │     │   │
│  │  │   no-sdio                       │  │                         │     │   │
│  │  └─────────────────────────────────┘  └─────────────────────────┘     │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────┐  ┌─────────────────────────┐     │   │
│  │  │ Disabled base peripherals       │  │ K230 control blocks     │     │   │
│  │  │ UART1-4: snps,dw-apb-uart       │  │ reset @0x9110_1000      │     │   │
│  │  │ I2C0-4: snps,designware-i2c     │  │ pinctrl @0x9110_5000    │     │   │
│  │  │ SPI0-2: snps,dwc-ssi-1.01a      │  │ watchdog @0x9110_6000   │     │   │
│  │  └─────────────────────────────────┘  └─────────────────────────┘     │   │
│  │                                                                       │   │
│  │  Memory @0x0000_0000, 2GB (0x8000_0000)                               │   │
│  │  Finisher: sifive,test1 @0x0010_0000                                  │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                    Kernel Config Highlights (k230-canmv.cfg)                 │
│                                                                              │
│  ┌────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐    │
│  │ SoC                │  │ Storage & FS        │  │ Networking          │    │
│  ├────────────────────┤  ├─────────────────────┤  ├─────────────────────┤    │
│  │ ARCH_CANAAN        │  │ EXT4_FS             │  │ NET, INET, PACKET   │    │
│  │ NONPORTABLE        │  │ FAT_FS / VFAT       │  │ UNIX                │    │
│  │                    │  │ MSDOS_FS            │  │ IP_PNP              │    │
│  ├────────────────────┤  │ MMC / MMC_BLOCK     │  │ IP_PNP_DHCP         │    │
│  │ Serial             │  │ MMC_SDHCI           │  │                     │    │
│  ├────────────────────┤  │ MMC_SDHCI_OF_       │  ├─────────────────────┤    │
│  │ SERIAL_8250        │  │   DWCMSHC           │  │ USB Net             │    │
│  │ SERIAL_8250_DW     │  │ VIRTIO_MMIO         │  ├─────────────────────┤    │
│  │ SERIAL_OF_PLATFORM │  │ DEVTMPFS / TMPFS    │  │ USB_RTL8152         │    │
│  │                    │  │ BLK_DEV_INITRD      │  │ USB_USBNET          │    │
│  │                    │  │                     │  │ USB_DWC2            │    │
│  │                    │  │                     │  │ USB_DWC2_HOST       │    │
│  ├────────────────────┤  ├─────────────────────┤  ├─────────────────────┤    │
│  │ Base Peripherals   │  │ I2C_DESIGNWARE      │  │ SPI_DESIGNWARE      │    │
│  ├────────────────────┤  │ I2C_CHARDEV         │  │ SPI_DW_MMIO         │    │
│  │ PINCTRL_K230       │  │ DW_WATCHDOG         │  │ RESET_K230          │    │
│  └────────────────────┘  └─────────────────────┘  └─────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│                           Build Artifacts                                    │
│                                                                              │
│  $ MACHINE=k230-canmv DISTRO=r2os bitbake k230-core-image              │    bitbake：执行 recipe/task 的命令入口
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌────────────┐  │    tmp/deploy/images/${MACHINE}：镜像和启动文件输出目录
│  │ tmp/deploy/    │  │ tmp/deploy/    │  │ tmp/deploy/    │  │ tmp/deploy │  │
│  │ images/k230-   │  │ images/k230-   │  │ images/k230-   │  │ images/    │  │
│  │ canmv/         │  │ canmv/         │  │ canmv/         │  │ k230-canmv │  │
│  │                │  │                │  │                │  │            │  │
│  │ .cpio.gz       │  │ .ext4          │  │ .wic.gz        │  │ .tar.zst   │  │    同一 rootfs 可以输出为 initrd、ext4、整盘镜像或归档
│  │ (initrd boot)  │  │ (raw rootfs)   │  │ (SD image)     │  │ (archive)  │  │
│  └────────────────┘  └────────────────┘  └────────────────┘  └────────────┘  │
│                                                                              │
│  Boot commands:                                                              │
│    $ scripts/k230-qemu-run --initrd          # direct initrd boot            │    --initrd：直接用 cpio.gz 作为临时根文件系统启动
│    $ scripts/k230-qemu-run --sd --uboot      # SDK SD image + U-Boot boot    │    --sd --uboot：使用 SDK 兼容 SD 镜像和 U-Boot 启动链路
└──────────────────────────────────────────────────────────────────────────────┘
```
