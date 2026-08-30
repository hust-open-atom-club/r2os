# K230 SDK U-Boot Binary

`u-boot` is the K230 SDK U-Boot binary used by `scripts/k230-qemu-run --sd --uboot`.

It is included so the QEMU boot path is reproducible from this repository
without depending on `~/k230-project/images/riscv-nomtee/u-boot`. The binary is
not covered by this layer's `COPYING.MIT`; keep its provenance tied to the K230
SDK source and license terms.

The SDK-compatible Yocto SD image still requires a K230-tuned OpenSBI payload.
When available, `scripts/k230-sdk-image` builds that payload from:

```text
~/k230-project/sdk/k230_sdk/src/common/opensbi
```

## K230 SDK RTT System Binary (Big-Core Firmware)

`rtt_system.bin` is the K230 big-core (C908V) firmware. It contains
OpenSBI + RT-Thread Smart kernel + romfs with KPU AI models and user
applications, loaded by U-Boot from the `rtt` GPT partition (10 MiB
offset, 20 MiB region) into the RTT memory region at 0x00200000.

### Source

Built from the K230 SDK via:

```bash
cd ~/k230-project/sdk/k230_sdk
make CONF=k230_canmv_defconfig rt-smart-kernel rt-smart-apps big-core-opensbi uboot
```

The SDK's `gen_rtt_bin()` packages the final binary:
gzip -> U-Boot mkimage header -> K230 firmware header.

### Integration

When `rtt_system.bin` is present in this directory, `scripts/k230-sdk-image`
writes it into the `rtt` GPT partition at 10 MiB. U-Boot loads it from there
and releases the big core from reset.

If absent, the SD image is still bootable for non-KPU / non-big-core use
cases. The rtt partition is simply left empty.

### Fetch

Use the remote fetch script to build on the remote K230 SDK build host
and download:

```bash
./scripts/k230-rtt-system-fetch
```

The binary is not covered by this layer's `COPYING.MIT`; keep its
provenance tied to the K230 SDK source and license terms.
