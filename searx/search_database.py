import threading
import redis
import pickle

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
        self.pool = redis.ConnectionPool(host=settings['redis']['host'])
        self.running = threading.Event()

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

    def _get_connection(self):
        return redis.Redis(connection_pool=self.pool)

    def read(self, q):
        conn = self._get_connection()
        key = self.make_key(q)
        response = conn.get(key)
        if not response:
            return None
        return pickle.loads(response)

    def _save(self, d):
        conn = self._get_connection()
        key = self.make_key(d)
        history = conn.incr("SEARCH_HISTORY_INDEX")
        conn.zadd("SEARCH_HISTORY_KEYS", {key: history})
        conn.set(key, pickle.dumps(d, protocol=4))

    def save(self, d):
        threading.Thread(
            target=self._save,
            args=(d,),
            name='save_search_' + str(d)
        ).start()

    def get_twenty_queries(self, x):
        result = []

        conn = self._get_connection()
        keys = conn.zrange('SEARCH_HISTORY_KEYS', int(x), int(x) + 20)
        if not keys:
            return result

        pipe = conn.pipeline()
        for key in keys:
            pipe.get(key)
        output = pipe.execute()
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

    def update(self, d):
        conn = self._get_connection()
        key = self.make_key(d)
        current = self.read(d)
        current.results = d.results
        current.paging = d.paging
        current.results_number = d.results_number
        current.answers = d.answers
        current.corrections = d.corrections
        current.infoboxes = d.infoboxes
        current.suggestions = d.suggestions
        current.unresponsive_engines = d.unresponsive_engines
        conn.set(key, pickle.dumps(current, protocol=4))
