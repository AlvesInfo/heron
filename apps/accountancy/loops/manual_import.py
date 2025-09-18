#! /home/paulo/.envs/heron/bin/python3
import os
import platform
import sys

import django

BASE_DIR = r"/"

if platform.uname().node not in ["PauloMSI", "MSI"]:
    BASE_DIR = "/home/paulo/heron"

sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "heron.settings")

django.setup()

from apps.accountancy.loops.import_sage_data import main

if __name__ == '__main__':
    main()
