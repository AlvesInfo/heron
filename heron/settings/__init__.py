import platform

from .base import *

if platform.uname().node in {"DESKP082", "PauloMSI", "MSI"}:
    # print("LOCAL_SETTINGS")
    from .local import *

else:
    # print("PRODUCTION_SETTINGS")
    from .production import *

from .suppliers import *
from .clients import *
