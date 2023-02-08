import platform

from .base import *

if platform.uname().node in {"DESKP082", "PauloMSI", "MSI", "FR07123475L"}:
    # print("LOCAL_SETTINGS")
    from .local import *

else:
    # print("PRODUCTION_SETTINGS")
    from .production import *

from .clients import *
from .directories import *
from .suppliers import *
