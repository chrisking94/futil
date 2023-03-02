# -*- coding: utf-8 -*-
# @Time         : 20:05 2022/8/29
# @Author       : Chris
# @Description  :
import shlex
import subprocess


def shell(cmd: str, working_dir: str = None):
    """Synchronous invoke."""
    chips = shlex.split(cmd, posix=False)
    subprocess.check_call(chips, cwd=working_dir)
