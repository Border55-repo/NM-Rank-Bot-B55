import unittest

from nmtool.cooldown import parse_cooldown


class CooldownTests(unittest.TestCase):
    def test_clock_formats(self):
        self.assertEqual(parse_cooldown("01:20"), 80)
        self.assertEqual(parse_cooldown("1:02:03"), 3723)

    def test_word_formats(self):
        self.assertEqual(parse_cooldown("2 min 8 sek"), 128)
        self.assertEqual(parse_cooldown("45s"), 45)

    def test_no_timer(self):
        self.assertIsNone(parse_cooldown("klar"))


if __name__ == "__main__":
    unittest.main()
