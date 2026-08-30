#!/usr/bin/env python3
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "gen-rtt-system"
K230_HEADER_SIZE = 528
VERSION_SIZE = 4
UBOOT_HEADER_SIZE = 64
UBOOT_MAGIC = 0x27051956


class GenRttSystemTest(unittest.TestCase):
    def run_script(self, *args: str) -> Path:
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            fw_payload = tmpdir / "fw_payload.bin"
            output = tmpdir / "rtt_system.bin"
            fw_payload.write_bytes(b"test payload")

            subprocess.run(
                [sys.executable, str(SCRIPT), *args, str(fw_payload), str(output)],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            kept_output = Path(self.enterContext(tempfile.TemporaryDirectory())) / output.name
            kept_output.write_bytes(output.read_bytes())
            return kept_output

    def assert_load_addr(self, output: Path, expected: int):
        data = output.read_bytes()
        uboot_header_start = K230_HEADER_SIZE + VERSION_SIZE
        uboot_header = data[uboot_header_start : uboot_header_start + UBOOT_HEADER_SIZE]

        magic, load, entry = struct.unpack_from(">I12xII", uboot_header)
        self.assertEqual(magic, UBOOT_MAGIC)
        self.assertEqual(load, expected)
        self.assertEqual(entry, expected)

    def test_load_addr_accepts_separate_argument(self):
        output = self.run_script("--load-addr", "0x00200000")
        self.assert_load_addr(output, 0x00200000)

    def test_load_addr_accepts_equals_argument(self):
        output = self.run_script("--load-addr=0x00240000")
        self.assert_load_addr(output, 0x00240000)


if __name__ == "__main__":
    unittest.main()
