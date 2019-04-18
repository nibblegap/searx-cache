import pickle
import time
import asyncio

import aioredis

from searx import settings
from searx.query import SearchQuery


class CacheInterface:
    """ Cache interface to store SearchData object
    """
    def read(self, q):
        pass

    def save(self, d):
        pass

    def update(self, d):
        pass

    def get_twenty_queries(self, x):
        return []


class RedisCache(CacheInterface):
    def __init__(self):
        self.pool = None

    def make_key(self, q):
        if q.time_range is None:
            q.time_range = ""

        return "SEARCH_HISTORY:{}:{}:{}:{}:{}:{}:{}".format(
            q.query,
            q.engines,
            q.categories[0],
            q.language,
            q.safesearch,
            q.pageno,
            q.time_range,
        )

    async def _get_connection(self):
        if not self.pool:
            host = settings["redis"]["host"]
            self.pool = await aioredis.create_redis_pool(
                f"redis://{host}", minsize=5, maxsize=10
            )
        return self.pool

    async def read(self, q):
        redis = await self._get_connection()
        key = self.make_key(q)
        response = await redis.get(key)
        if not response:
            return None
        return pickle.loads(response)

    async def save(self, d):
        redis = await self._get_connection()
        key = self.make_key(d)
        history = await redis.incr("SEARCH_HISTORY_INDEX")
        await redis.zadd("SEARCH_HISTORY_KEYS", history, key)
        await redis.set(key, pickle.dumps(d, protocol=4))

    async def get_twenty_queries(self, x):
        result = []

        redis = await self._get_connection()
        keys = await redis.zrange('SEARCH_HISTORY_KEYS', int(x), int(x) + 20)
        if not keys:
            return result

        pipe = redis.pipeline()
        for key in keys:
            pipe.get(key)
        output = await pipe.execute()
        for row in output:
            row = pickle.loads(row)
            result.append(
                SearchQuery(
                    row.query,
                    row.engines,
                    row.categories,
                    row.language,
                    row.safesearch,
                    row.pageno,
                    row.time_range,
                )
            )

        return result

    async def update(self, d):
        redis = await self._get_connection()
        key = self.make_key(d)
        current = await self.read(d)
        current.results = d.results
        current.paging = d.paging
        current.results_number = d.results_number
        current.answers = d.answers
        current.corrections = d.corrections
        current.infoboxes = d.infoboxes
        current.suggestions = d.suggestions
        current.unresponsive_engines = d.unresponsive_engines
        await redis.set(key, pickle.dumps(current, protocol=4))

    async def wait_updating(self, start_time):
        wait = settings["redis"]["upgrade_history"] - int(time.time() - start_time)
        if wait > 0:
            await asyncio.sleep(wait)

    async def update_results(self, search_instance):
        start_time = time.time()
        x = 0

        try:
            while True:
                queries = await self.get_twenty_queries(x)
                for query in queries:
                    result_container = await search_instance.search(query)
                    searchData = search_instance.create_search_data(query, result_container)
                    await self.update(searchData)
                x += 20
                if len(queries) < 20:
                    x = 0
                    await self.wait_updating(start_time)
                    start_time = time.time()
        except asyncio.CancelledError:
            pass
