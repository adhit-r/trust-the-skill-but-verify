import sys
import unittest

sys.path.insert(0, "src")

from utils.text import slugify, truncate


class TextTests(unittest.TestCase):
    def test_slugify(self) -> None:
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_truncate(self) -> None:
        self.assertEqual(truncate("abcdef", 4), "abc…")


if __name__ == "__main__":
    unittest.main()
