# RISC-V Hardware Support Matrix

R² OS is built around RISC-V as a primary architecture. This page tracks the
hardware we currently support and the boards we plan to evaluate or enable.

## Current Support

| Board | SoC | Core | Memory | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Canaan CanMV-K230 | Canaan K230 | T-HEAD C908 (RISC-V64) | 2 GiB | **Active** | Current Yocto machine: `k230-canmv`; verified under QEMU, real-board bring-up pending |

The active BSP targets the `k230-canmv` machine. It includes:

- Linux kernel recipe: `linux-k230_6.18.28`
- Device tree: `recipes-kernel/linux/files/k230-canmv.dts`
- Kernel config fragment: `recipes-kernel/linux/files/k230-canmv.cfg`
- QEMU machine: `k230-canmv` from `processmission/qemu` branch `devel`
- WIC/SDK SD image layouts under `wic/` and `scripts/k230-sdk-image`

## Planned / Evaluation Candidates

These boards are natural next targets because they use mature, publicly
documented RISC-V SoCs and have upstream Linux support that can be folded into
this layer.

| Board | SoC | Core | Memory | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| StarFive VisionFive 2 | StarFive JH7110 | SiFive U74 (RISC-V64) | 2/4/8 GiB | Planned | Widely available; good upstream Linux support |
| StarFive VisionFive 1 | StarFive JH7100 | SiFive U74 (RISC-V64) | 8 GiB | Evaluation | Older board; useful for comparison |
| Pine64 Star64 | StarFive JH7110 | SiFive U74 (RISC-V64) | 4/8 GiB | Evaluation | JH7110 sibling of VisionFive 2 |
| Milk-V Mars | StarFive JH7110 | SiFive U74 (RISC-V64) | 2/4/8 GiB | Evaluation | JH7110 in a small form factor |
| SiFive HiFive Unmatched | SiFive FU740 | SiFive U74 (RISC-V64) | 16 GiB | Evaluation | Good developer board, higher price |
| Allwinner D1 / D1s (Nezha) | Allwinner D1 | T-HEAD C906 (RISC-V64) | 512 MiB / 1 GiB | Evaluation | Popular low-cost RISC-V SBC |
| Milk-V Duo | Sophgo SG2002 | T-HEAD C906 (RISC-V64) + ARM | 64 MiB | Evaluation | Very small; may suit a separate minimal image |
| LicheePi 4A | T-HEAD TH1520 | T-HEAD C910/C906 (RISC-V64) | 8/16 GiB | Planned | High-performance Linux SBC |
| BeagleV-Ahead | T-HEAD TH1520 | T-HEAD C910/C906 (RISC-V64) | 4/8 GiB | Evaluation | TH1520-based SBC |
| Milk-V Pioneer | Sophgo SG2042 | T-HEAD C920 (RISC-V64) | 64/128 GiB | Planned | High-core-count workstation-class board |

## How to Add a Board

1. Add a machine configuration under `conf/machine/`, reusing the RISC-V tune
   from OE-core.
2. Add or extend a kernel recipe with the board device tree and config fragment.
3. Add a WIC layout under `wic/` if the board boots from SD/eMMC.
4. Add a QEMU smoke path in `scripts/` when a QEMU machine is available.
5. Update this matrix and the README.

All new board enablement should keep the Rust-first packaging policy in mind:
the default image should stay small, and Rust tools are preferred when adding
new user-space components.
