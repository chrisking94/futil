# -*- coding: utf-8 -*-
# @Time         : 19:37 2023/7/3
# @Author       : Chris
# @Description  : Make data human-readable.


def sizeof_fmt(num, suffix="B"):
    for unit in ("", "K", "M", "G", "T", "P", "E", "Z"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Y{suffix}"
