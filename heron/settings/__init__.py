import platform

from .base import *
from .staging import *

if platform.uname().node in {"DESKP082", "PauloMSI"}:
    from heron.settings.local import *

else:
    from heron.settings.production import *
