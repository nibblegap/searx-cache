import json
import threading
import urllib.parse

import redis

from searx import settings
from searx.plugins import plugins
from searx.query import SearchQuery
from searx.url_utils import urlparse
from searx.results import SearchData


def _get_connection(host):
    host = host if host else settings['redis']['host']
    return redis.StrictRedis(host=host, decode_responses=True)


def read(q, host):
    time_range = q.time_range
    if q.time_range is None:
        q.time_range = ""

    conn = _get_connection(host)
    key = "SEARCH_HISTORY:{}:{}:{}:{}:{}:{}:{}".format(
        e(q.query), je(q.engines), q.categories[0], q.lang, q.safesearch, q.pageno, time_range)
    response = conn.hgetall(key)
    if not response:
        return None
    results = jd(response['results'])
    for result in results:
        result['parsed_url'] = urlparse(result['url'])
    return SearchData(q, results, response['paging'], int(response['results_number']),
                      jds(response['answers']), jds(response['corrections']), jd(response['infoboxes']),
                      jds(response['suggestions']), jds(response['unresponsive_engines']))


def save(d, host):
    conn = _get_connection(host)
    key = "SEARCH_HISTORY:{}:{}:{}:{}:{}:{}:{}".format(
        e(d.query), je(d.engines), d.categories[0], d.language, d.safe_search, d.pageno, d.time_range)
    mapping = {
        'query': e(d.query), 'category': d.categories[0], 'pageno': d.pageno, 'safe_search': d.safe_search,
        'language': d.language, 'time_range': d.time_range, 'engines': je(d.engines), 'results': je(d.results),
        'paging': d.paging, 'results_number': d.results_number, 'answers': jes(d.answers),
        'corrections': jes(d.corrections), 'infoboxes': je(d.infoboxes), 'suggestions': jes(d.suggestions),
        'unresponsive_engines': jes(d.unresponsive_engines)
    }
    conn.zadd('SEARCH_HISTORY_KEYS', conn.incr('SEARCH_HISTORY_INDEX'), key)
    conn.hmset(key, mapping)


def get_twenty_queries(x, host):
    result = []

    conn = _get_connection(host)
    keys = conn.zrange('SEARCH_HISTORY_KEYS', int(x), int(x) + 20)
    if not keys:
        return result

    pipe = conn.pipeline()
    for key in keys:
        pipe.hgetall(key)
    output = pipe.execute()
    for row in output:
        result.append(SearchQuery(d(row['query']), jd(row['engines']), [row['category']], row['language'],
                                  int(row['safe_search']), int(row['pageno']), row['time_range']))

    return result


def e(obj):
    return urllib.parse.quote_plus(obj)


def d(coded):
    return urllib.parse.unquote_plus(coded)


def je(obj):
    return e(json.dumps(obj))


def jd(coded):
    return json.loads(d(coded))


def jes(set):
    return je(list(set))


def jds(coded):
    return jd(coded)


def update(d, host):
    conn = redis.StrictRedis(host)
    key = "SEARCH_HISTORY:{}:{}:{}:{}:{}:{}:{}".format(
        e(d.query), je(d.engines), d.categories[0], d.language, d.safe_search, d.pageno, d.time_range)
    current = conn.hgetall(key)
    current.update({
        'results': je(d.results), 'paging': d.paging, 'results_number': d.results_number,
        'answers': jes(d.answers), 'corrections': jes(d.corrections), 'infoboxes': je(d.infoboxes),
        'suggestions': jes(d.suggestions), 'unresponsive_engines': jes(d.unresponsive_engines)
    })
    conn.hmset(key, current)
