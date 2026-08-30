# syntax=docker/dockerfile:1

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bc \
        build-essential \
        bzip2 \
        ca-certificates \
        chrpath \
        cpio \
        curl \
        debianutils \
        diffstat \
        file \
        findutils \
        gawk \
        gcc \
        git \
        gosu \
        gzip \
        iproute2 \
        iputils-ping \
        less \
        libacl1 \
        libcrypt-dev \
        locales \
        nano \
        openssh-client \
        patch \
        perl \
        python3 \
        python3-git \
        python3-jinja2 \
        python3-pexpect \
        python3-pip \
        python3-subunit \
        python3-websockets \
        rsync \
        socat \
        sudo \
        tar \
        texinfo \
        unzip \
        vim \
        wget \
        xz-utils \
        zstd \
    && sed -i 's/^# *en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY docker/yocto-entrypoint.sh /usr/local/bin/yocto-entrypoint

RUN chmod 0755 /usr/local/bin/yocto-entrypoint \
    && mkdir -p /work/src /work/build /work/downloads /work/sstate /work/home \
    && chmod 0775 /work/src /work/build /work/downloads /work/sstate /work/home

WORKDIR /work/src

ENTRYPOINT ["/usr/local/bin/yocto-entrypoint"]
CMD ["bash"]
