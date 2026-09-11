# SPDX-License-Identifier: MIT

SUMMARY = "R² OS image with common command-line tools"
LICENSE = "MIT"

inherit core-image

IMAGE_FEATURES += "allow-empty-password empty-root-password allow-root-login package-management"

IMAGE_INSTALL = " \
    packagegroup-k230-common \
"

IMAGE_ROOTFS_SIZE ?= "262144"
IMAGE_ROOTFS_EXTRA_SPACE ?= "65536"
EXTRA_IMAGECMD:ext4 = "-i 4096 -L root"

ROOTFS_POSTPROCESS_COMMAND += "k230_serial_autologin_root; k230_network_interfaces_cleanup; k230_tmpfs_mountpoints; k230_sysctl_embedded; "

k230_serial_autologin_root() {
    inittab="${IMAGE_ROOTFS}${sysconfdir}/inittab"
    if [ -e "$inittab" ] && ! grep -q "ttyS0::respawn:.*--autologin root" "$inittab"; then
        sed -i '\#^ttyS0::respawn:.*/usr/sbin/getty #s#/usr/sbin/getty #/usr/sbin/getty --autologin root #' "$inittab"
    fi
}

k230_network_interfaces_cleanup() {
    interfaces="${IMAGE_ROOTFS}${sysconfdir}/network/interfaces"
    if [ -e "$interfaces" ]; then
        sed -i "/^# Busybox ifupdown won't process \\/en\\* correctly$/,/^iface eth inet dhcp$/d" "$interfaces"
        sed -i "s/^auto eth0$/# eth0 DHCP is started asynchronously by k230-network./" "$interfaces"
    fi
}

k230_tmpfs_mountpoints() {
    for d in tmp var/log var/tmp; do
        mkdir -p "${IMAGE_ROOTFS}/$d"
    done
}

k230_sysctl_embedded() {
    conf="${IMAGE_ROOTFS}${sysconfdir}/sysctl.conf"
    cat >> "$conf" <<'SYSCONF'

# R² OS embedded sysctl optimizations for 2 GB RISC-V64
vm.swappiness = 1
vm.dirty_ratio = 10
vm.dirty_background_ratio = 5
vm.vfs_cache_pressure = 50
vm.min_free_kbytes = 8192
vm.page-cluster = 0
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 3
net.ipv4.tcp_fin_timeout = 15
fs.file-max = 65536
fs.inotify.max_user_watches = 8192
kernel.panic = 10
kernel.sysrq = 1
SYSCONF
}
