
from datetime import datetime

import pytz
from pyramid.threadlocal import get_current_registry
from redis import StrictRedis


def utcnow():
    return pytz.utc.localize(datetime.utcnow())


def get_redis_conn(registry=None):
    if registry is None:
        registry = get_current_registry()
    try:
        connection = registry.redis_conn
    except AttributeError:
        if registry.package_name == 'testing':
            # This is a unit test
            from fakeredis import FakeStrictRedis
            registry.redis_conn = connection = FakeStrictRedis()
        else:
            registry.redis_conn = connection = StrictRedis.from_url(registry.settings['kedja.redis_url'])
    return connection


def _redis_conn_rm(request):
    return get_redis_conn(request.registry)
