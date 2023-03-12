import platform

from heron.settings.base import *

if platform.uname().node in {"DESKP082", "PauloMSI", "MSI", "FR07123475L"}:
    # print("LOCAL_SETTINGS")
    from heron.settings.local import *

else:
    # print("PRODUCTION_SETTINGS")
    from heron.settings.production import *

from heron.settings.clients import *
from heron.settings.directories import *
from heron.settings.suppliers import *
