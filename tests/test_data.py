# -*- coding: utf-8 -*-
# @Time         : 14:51 2022/12/18
# @Author       : Chris
# @Description  :
from unittest import TestCase
from ..data import zip_data2bytes, iter_files_from_zip_bytes
from ..data import zip_coco2bytes, unzip_bytes
from ..data import NestedListFlatter


class Test(TestCase):
    def test_zip_files2bytes(self):
        zip_bytes = zip_data2bytes(["Z:/Fishing/pms/img/goods/src/3636363713274707.jpg"])
        with open("F:/tmp/zip_files2bytes.zip", "wb") as f:
            f.write(zip_bytes)
        # for name, bts in iter_files_from_zip_bytes(zip_bytes):
        #     print(name, len(bts))
        return zip_bytes

    def test_zip_coco2bytes(self):
        zip_bytes = zip_coco2bytes("F:/git/FishingBrain/.tmp/result.json")
        with open("F:/tmp/zip_coco2bytes.zip", "wb") as f:
            f.write(zip_bytes)
        return zip_bytes

    def test_iter_files_from_zip_bytes(self):
        zip_bytes = self.test_zip_files2bytes()
        for name, bts in iter_files_from_zip_bytes(zip_bytes):
            print(name, bts)

    def test_unzip_bytes(self):
        zip_bytes = self.test_zip_coco2bytes()
        unzip_bytes(zip_bytes, "F:/tmp/zip_coco2bytes")


class NestedListFlatterTest(TestCase):
    def test_flat(self):
        nested, flatted = self._get_data()
        # res = NestedListFlatter(nested).flat()
        # assert res == flatted
        res = NestedListFlatter(nested, 2).flat()
        flatted = [[0, 1, 2, 3, 4], 5, [6, 7], [8, 9], 10, 11, [12, 13]]
        assert res == flatted

    def test_rehabilitate(self):
        nested, flatted = self._get_data()
        res = NestedListFlatter(nested).rehabilitate(flatted)
        assert res == nested
        flatted = [[0, 1, 2, 3, 4], 5, [6, 7], [8, 9], 10, 11, [12, 13]]
        res = NestedListFlatter(nested, 2).rehabilitate(flatted)
        assert res == nested

    def _get_data(self):
        nested = [
            [
                [0, 1, 2, 3, 4],
                5,
                [6, 7]
            ],
            [
                [8, 9],
                10,
                11,
                [12, 13]
            ]
        ]
        flatted = list(range(14))
        return nested, flatted
