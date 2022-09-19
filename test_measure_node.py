import unittest
from unittest.mock import MagicMock

from measure_node import MeasureNode
import os
import numpy as np
import cv2

class MeasureNodeTest(unittest.TestCase):
    def test_make_dir(self):
        c = MeasureNode(config={"storage_path": "."}, bus=MagicMock())
        c.wdn1 = "tmp_test"
        wd = c.make_dir("test_label")
        print(wd)
        os.path.isdir(wd)
        self.assertTrue(os.path.isdir(wd))
        os.rmdir(wd)
        os.rmdir(os.path.join(c.storage_path, c.wdn1))


    def test_process_image(self):
        c = MeasureNode(config={}, bus=MagicMock())
        test_color = np.ones((750, 1000, 3), dtype=np.uint8)
        res = c.process_image(test_color)
        self.assertTrue(cv2.imdecode(res, 1).shape == (450, 600, 3))


if __name__ == '__main__':
    unittest.main()
