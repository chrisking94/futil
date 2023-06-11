# -*- coding: utf-8 -*-
# @Time         : 9:06 2023/6/11
# @Author       : Chris
from unittest import TestCase
from lxml import etree

from t2r import TreeExtractor

test_config = etree.parse("./test_t2r.xml")

test_data = [
    {"name": "Mary"},
    {"name": "Tom"}
]


# @Description  :
class TestTreeExtractor(TestCase):
    def test_extract_items(self):
        extractor = TreeExtractor(test_config)
        res = extractor.extract_items(test_data)
        return res
