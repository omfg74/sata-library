import unittest

from sata_library.disks import disks_from_lsblk
from sata_library.errors import LibraryError

PAYLOAD = """
{
  "blockdevices": [
    {
      "name": "sda",
      "serial": "WD-1",
      "wwn": "0x5000",
      "size": "4T",
      "type": "disk",
      "tran": "usb",
      "path": "/dev/sda",
      "children": [
        {"name": "sda1", "serial": null, "type": "part", "path": "/dev/sda1"}
      ]
    },
    {
      "name": "nvme0n1",
      "serial": null,
      "wwn": null,
      "size": "1T",
      "type": "disk",
      "tran": "nvme",
      "path": "/dev/nvme0n1"
    }
  ]
}
"""


class LsblkTests(unittest.TestCase):
    def test_keeps_disks_and_drops_partitions(self) -> None:
        found = disks_from_lsblk(PAYLOAD)
        self.assertEqual([item.name for item in found], ["sda", "nvme0n1"])
        self.assertEqual(found[0].serial, "WD-1")
        self.assertEqual(found[1].serial, "")
        self.assertEqual(found[0].tran, "usb")

    def test_rejects_garbage(self) -> None:
        with self.assertRaises(LibraryError) as caught:
            disks_from_lsblk("{")
        self.assertEqual(caught.exception.code, "bad_lsblk")
