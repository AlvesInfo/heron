import platform

from .base import *
from .staging import *
from heron.settings.production import *
# if platform.uname().node in {"DESKP082", "PauloMSI", "MSI"}:
#     # print("LOCAL_SETTINGS")
#     from heron.settings.local import *
#
# else:
#     # print("PRODUCTION_SETTINGS")
#     from heron.settings.production import *
