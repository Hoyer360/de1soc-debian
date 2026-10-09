"""Regression checks for corrupt SD images, including the prior EOF issue."""
import importlib.util
from pathlib import Path
import struct
import unittest

spec = importlib.util.spec_from_file_location(
    'verify_image', Path(__file__).resolve().parents[1] / 'scripts/verify-image.py')
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class ImageLayoutTests(unittest.TestCase):
    def setUp(self):
        self.mbr = bytearray(512)
        struct.pack_into('<I', self.mbr, 440, 0xde1a2026)
        self.mbr[510:] = b'\x55\xaa'
        for i, (kind, start, size) in enumerate([
                (0x0c, 4096, 262144), (0x83, 266240, 8120320), (0xa2, 2048, 2048)]):
            struct.pack_into('<B3sB3sII', self.mbr, 446 + i * 16,
                             0, bytes(3), kind, bytes(3), start, size)

    def test_valid_layout(self):
        self.assertEqual(len(verify.validate_mbr(self.mbr, 4 * 1024**3)), 3)

    def test_truncated_file(self):
        with self.assertRaisesRegex(ValueError, 'beyond image EOF'):
            verify.validate_mbr(self.mbr, 2 * 1024**3)

    def test_false_115_gib_partition(self):
        struct.pack_into('<I', self.mbr, 446 + 16 + 12, 242430771)
        with self.assertRaisesRegex(ValueError, 'beyond image EOF'):
            verify.validate_mbr(self.mbr, 6 * 1024**3)

    def test_overlap(self):
        struct.pack_into('<I', self.mbr, 446 + 12, 300000)
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            verify.validate_mbr(self.mbr, 4 * 1024**3)

    def test_shifted_partition_slots(self):
        self.mbr[462:510] = self.mbr[446:494]
        self.mbr[446:462] = bytes(16)
        with self.assertRaisesRegex(ValueError, 'slots/types'):
            verify.validate_mbr(self.mbr, 4 * 1024**3)


if __name__ == '__main__':
    unittest.main()
