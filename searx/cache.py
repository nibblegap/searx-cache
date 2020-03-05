import functools

import redis
import ring

from ring.func import base as fbase
from ring.func.sync import CacheUserInterface

from searx import settings

redis_cache = None


class RequestCacheUserInterface(CacheUserInterface):
    @fbase.interface_attrs(
        transform_args=fbase.transform_kwargs_only, return_annotation=str)
    def key(self, wire, **kwargs):
        kwargs["kwargs"] = {}
        return wire._rope.compose_key(*wire._bound_objects, **kwargs)

    @fbase.interface_attrs(transform_args=fbase.transform_kwargs_only)
    def get_or_update(self, wire, **kwargs):
        key = self.key(wire, **kwargs)
        try:
            result = wire.storage.get(key)
        except fbase.NotFound:
            result = self.execute(wire, **kwargs)
            if result.status_code >= 300:
                return result
            wire.storage.set(key, result)
        return result


if "redis_host" in settings["server"]:
    client = redis.StrictRedis(host=settings["server"]["redis_host"])

    redis_cache = functools.partial(
        ring.redis,
        client,
        coder="pickle",
        user_interface=RequestCacheUserInterface,
        expire=86400
    )
