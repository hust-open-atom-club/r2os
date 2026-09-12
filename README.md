<div align="center">

# R² OS

**A small, Rust-first Linux distribution for the Canaan CanMV-K230.**

[Quick start](#quick-start) · [Architecture](#architecture) · [Details](#details)

</div>

<table align="center">
  <tr>
    <th>Target</th>
    <th>Build</th>
    <th>Firmware</th>
    <th>Userspace</th>
  </tr>
  <tr>
    <td>RISC-V 64</td>
    <td>Yocto/OpenEmbedded</td>
    <td>RustSBI</td>
    <td>BusyBox + Dropbear</td>
  </tr>
</table>

<p align="center">
  Current focus: reproducible Linux bring-up on the K230 QEMU model.<br />
  KPU, camera, AI2D, and full multimedia support still require hardware or
  SDK-side integration.
</p>

<h2 align="center">Boot snapshot</h2>

<p align="center">
  After booting, the image identifies itself roughly like this.<br />
  The left column comes from
  <a href="meta-r2os-apps/recipes-support/fastfetch/files/r2os-logo.txt"><code>r2os-logo.txt</code></a>;
  Fastfetch color placeholders are removed here for plain Markdown.
</p>

```text
root@k230-canmv:~# fastfetch
    ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░              ░▓██████▒      root@k230-canmv
     ░▒███████▒  ░▒████████       ████    █████░   ---------------
        ██████▒      ███████▒    ░████▒    █████   OS: R² OS 1.0 (wrynose) riscv64
        ██████▒      ░███████      ▓▓     ▒█████   Host: Canaan CanMV-K230
        ██████▒      ░███████            ▒█████    Kernel: Linux 6.18.28
        ██████▒      ███████           ▒████▒      Uptime: 11 mins
        ██████▒    ▒██████           ███░          Shell: sh
        ███████████████           ▓██████████████  Terminal: vt102
        ██████▒ ░███████░                          CPU: k230
        ██████▒   ████████                         Memory: 41.96 MiB / 1.80 GiB (2%)
        ██████▒    ░███████▓                       Swap: Unused
        ██████▒      ████████                      Disk (/): 63.91 MiB / 1.84 GiB (3%) - ext4
       ░███████       ▒████████                    Local IP (eth0): 10.0.2.15/24
    ██████████████      ██████████░                Locale: C
```

Uptime, memory, disk usage, and the IP address are runtime values.

## Quick start

From the repository root:

```bash
make qemu              # Build and boot with initramfs
make k230-qemu-sd      # Boot the direct WIC/SD image
make k230-sdk-image    # Build the optional SDK-compatible SD image
./scripts/k230-qemu-run --deploy build-artifacts/k230-canmv --sd --uboot
make check             # Run static checks and unit tests
```

The exported artifacts live under `build-artifacts/k230-canmv/`.

## Architecture

R² OS is split into three layers:

| Layer | Responsibility |
| --- | --- |
| `meta-k230-bsp` | K230 machine, Linux recipe, DTS, WIC, RustSBI layout |
| `meta-r2os-distro` | Distro policy, image recipe, packagegroups, userspace |
| `meta-r2os-apps` | Application recipes such as Fastfetch and PicoClaw |

The boot paths share the same Linux kernel and userspace:

```text
Direct initrd  -> RustSBI dynamic -> Linux -> initramfs
Direct WIC     -> RustSBI dynamic -> Linux -> /dev/mmcblk1p2
SDK U-Boot     -> RustSBI payload -> Linux -> /dev/mmcblk1p3
```

`scripts/rustsbi-build` turns the exported kernel and device tree into the
dynamic and payload firmware used by these paths.

## Current scope

- QEMU initramfs, direct WIC/SD, and SDK U-Boot paths reach a root shell.
- Direct WIC uses `/dev/mmcblk1p2`; the SDK GPT image uses `/dev/mmcblk1p3`.
- KPU, camera, AI2D, and full multimedia validation still require hardware or
  SDK-side integration.

## Details

<details>
<summary>Build environment</summary>

The default `YOCTO_BACKEND=auto` uses Docker when available and falls back to
a local Poky checkout. RustSBI is built on the host after deploy export and
requires `rustup`, the `nightly-2026-05-11` toolchain with `rust-src` and the
RISC-V target, plus `rust-objcopy` from `cargo-binutils`.

</details>

For the full memory map, layer wiring, and boot diagrams, see
[`ARCHITECTURE.md`](ARCHITECTURE.md). Individual scripts expose their options
through `--help`.

## More

- [RISC-V hardware matrix](docs/riscv-hardware.md)
- [K230 architecture and boot diagrams](ARCHITECTURE.md)
- [`scripts/rustsbi-build --help`](scripts/rustsbi-build)
- [`scripts/k230-qemu-run --help`](scripts/k230-qemu-run)

## License

R² OS is released under the MIT License. See [COPYING.MIT](COPYING.MIT).
