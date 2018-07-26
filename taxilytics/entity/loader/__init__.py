from .taxi import Shenzhen
from .taxi import Hangzhou
from .taxi import NycTlc

from .ksu import Ksu
from .nasa import Nasa

from .common import commit_trip


from entity.loader.common import Loader


loader_classes = []
for k, v in globals().copy().items():
    if k.startswith('__'):
        continue
    if type(v) == type and issubclass(v, Loader) and not v == Loader:
        loader_classes.append(v)
