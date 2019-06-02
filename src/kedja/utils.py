
from datetime import datetime

import pytz


def utcnow():
    return pytz.utc.localize(datetime.utcnow())
