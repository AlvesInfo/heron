#! /home/paulo/.envs/heron/bin/python3
# from pathlib import Path
#
# with Path("test.txt").open("w") as file:
#     file.write("test passé")

import sys
import subprocess


def get_status_output(*args, **kwargs):
    p = subprocess.Popen(*args, **kwargs)
    stdout, stderr = p.communicate()
    return p.returncode, stdout


status, output = get_status_output("monit status")

print("%s" % output)
if status != 0:
    sys.exit(status)
