# vilya.libs.doubandb

from vilya.libs.store import mc
from vilya.config import DOUBANDB
from douban.beansdb import ReadFailedError

db = beansdb_from_config(DOUBANDB, mc=mc)
