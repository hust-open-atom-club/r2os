SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c

.DEFAULT_GOAL := help

ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
IMAGE_TARGET ?= k230-core-image
DEPLOY_DIR ?= build-artifacts/k230-canmv
DEPLOY_PATH := $(abspath $(DEPLOY_DIR))

QEMU_REPO ?= https://github.com/processmission/qemu.git
QEMU_BRANCH ?= devel
QEMU_DIR ?= $(HOME)/processmission-qemu
QEMU_BIN ?= $(QEMU_DIR)/build/qemu-system-riscv64
QEMU_TARGET_LIST ?= riscv64-softmmu
QEMU_MODE ?= initrd
QEMU_SNAPSHOT ?= 0
QEMU_NO_NET ?= 0
QEMU_APPEND ?=

YOCTO_BB_THREADS ?= 12
YOCTO_PARALLEL_MAKE_JOBS ?= 12

export YOCTO_BB_THREADS
export YOCTO_PARALLEL_MAKE_JOBS

.PHONY: help all build yocto-init k230-setup k230-build
.PHONY: qemu-build k230-qemu k230-qemu-initrd k230-qemu-sd qemu
.PHONY: k230-sdk-image check

help:
	@printf '%s\n' \
		'R² OS build targets:' \
		'  make k230-build       Build the Yocto image and export deploy artifacts.' \
		'  make k230-qemu        Build everything and boot QEMU with initramfs.' \
		'  make qemu              Alias for make k230-qemu.' \
		'  make k230-qemu-sd     Build everything and boot the direct WIC image.' \
		'  make qemu-build        Build processmission/qemu from the devel branch.' \
		'  make k230-sdk-image    Build the optional SDK-compatible SD image.' \
		'  make check             Run the repository static checks.' \
		'' \
		'Useful overrides:' \
		'  QEMU_MODE=initrd|sd   Select the direct Linux boot mode.' \
		'  QEMU_DIR=/path         QEMU source and build directory.' \
		'  DEPLOY_DIR=path       Relative deploy directory in this checkout.' \
		'  QEMU_SNAPSHOT=1       Discard writes made to the SD image.' \
		'  QEMU_NO_NET=1         Disable QEMU user networking.'

all: k230-build

build: k230-build

yocto-init:
	@cd "$(ROOT_DIR)" && ./scripts/yocto-init

k230-setup: yocto-init
	@cd "$(ROOT_DIR)" && ./scripts/yocto-k230-setup

# This is deliberately the SDK-free path.  The SDK-compatible GPT image is a
# separate opt-in target because direct initrd/WIC boots do not need it.
k230-build: k230-setup
	@cd "$(ROOT_DIR)" && ./scripts/yocto-bitbake "$(IMAGE_TARGET)"
	@cd "$(ROOT_DIR)" && ./scripts/yocto-export-deploy --clean "$(DEPLOY_DIR)"

qemu-build:
	@set -eu; \
	if [ ! -d "$(QEMU_DIR)/.git" ]; then \
		printf 'Cloning QEMU %s (%s) into %s\n' "$(QEMU_REPO)" "$(QEMU_BRANCH)" "$(QEMU_DIR)"; \
		git clone --single-branch --branch "$(QEMU_BRANCH)" "$(QEMU_REPO)" "$(QEMU_DIR)"; \
	else \
		if ! git -C "$(QEMU_DIR)" show-ref --verify --quiet "refs/heads/$(QEMU_BRANCH)"; then \
			git -C "$(QEMU_DIR)" fetch origin "$(QEMU_BRANCH)"; \
			git -C "$(QEMU_DIR)" switch --track -c "$(QEMU_BRANCH)" "origin/$(QEMU_BRANCH)"; \
		else \
			git -C "$(QEMU_DIR)" switch "$(QEMU_BRANCH)"; \
		fi; \
	fi; \
	if [ ! -x "$(QEMU_BIN)" ] || ! "$(QEMU_BIN)" -machine help 2>/dev/null | grep -q '^k230-canmv'; then \
		cd "$(QEMU_DIR)"; \
		./configure --target-list="$(QEMU_TARGET_LIST)"; \
	fi; \
	ninja -C "$(QEMU_DIR)/build"; \
	"$(QEMU_BIN)" -machine help | grep -q '^k230-canmv'; \
	printf 'QEMU ready: %s (%s)\n' "$(QEMU_BIN)" "$(QEMU_BRANCH)"

k230-qemu: k230-build qemu-build
	@set -eu; \
	case "$(QEMU_MODE)" in \
		initrd|sd) ;; \
		*) printf 'QEMU_MODE must be initrd or sd: %s\n' "$(QEMU_MODE)" >&2; exit 2 ;; \
	esac; \
	args=("--$(QEMU_MODE)" --deploy "$(DEPLOY_PATH)" --qemu "$(QEMU_BIN)"); \
	case "$(QEMU_SNAPSHOT)" in \
		1|yes|true|on) args+=(--snapshot) ;; \
		0|no|false|off|'') ;; \
		*) printf 'QEMU_SNAPSHOT must be a boolean: %s\n' "$(QEMU_SNAPSHOT)" >&2; exit 2 ;; \
	esac; \
	case "$(QEMU_NO_NET)" in \
		1|yes|true|on) args+=(--no-net) ;; \
		0|no|false|off|'') ;; \
		*) printf 'QEMU_NO_NET must be a boolean: %s\n' "$(QEMU_NO_NET)" >&2; exit 2 ;; \
	esac; \
	if [ -n "$(QEMU_APPEND)" ]; then args+=(--append "$(QEMU_APPEND)"); fi; \
	cd "$(ROOT_DIR)"; \
	./scripts/k230-qemu-run "$${args[@]}"

k230-qemu-initrd: QEMU_MODE := initrd
k230-qemu-initrd: k230-qemu

k230-qemu-sd: QEMU_MODE := sd
k230-qemu-sd: k230-qemu

qemu: k230-qemu

k230-sdk-image: k230-build
	@cd "$(ROOT_DIR)" && ./scripts/k230-sdk-image --deploy "$(DEPLOY_DIR)"

check:
	@cd "$(ROOT_DIR)" && ./scripts/k230-check
