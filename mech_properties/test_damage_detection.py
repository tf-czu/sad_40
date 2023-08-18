import unittest

from mech_properties.damage_detection import get_circle

class DamageDetectinTest(unittest.TestCase):
    def test_get_circle(self):
        p1 = (1, 0)
        p2 = (2, 1)
        p3 = (0, 1)
        cx, cy, r = get_circle(p1, p2, p3)
        print(cx, cy, r)
        self.assertEqual(cx, 1)
        self.assertEqual(cy, 1)
        self.assertEqual(r, 1)


if __name__ == '__main__':
    unittest.main()
