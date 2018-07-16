import json
import threading
import urllib

import redis

from searx import settings
from searx.plugins import plugins
from searx.query import SearchQuery
from searx.search import Search, get_search_query_from_webapp
from searx.url_utils import urlparse


class SearchData(object):
    def __init__(self, search_query, results, paging,
                 results_number, answers, corrections, infoboxes, suggestions, unresponsive_engines):
        self.categories = search_query.categories
        self.query = search_query.query
        self.pageno = search_query.pageno
        self.safe_search = search_query.safesearch
        self.language = search_query.lang
        self.time_range = search_query.time_range
        self.engines = search_query.engines
        self.results = results
        self.paging = paging
        self.results_number = results_number
        self.answers = answers
        self.corrections = corrections
        self.infoboxes = infoboxes
        self.suggestions = suggestions
        self.unresponsive_engines = unresponsive_engines


def _get_connection(host):
    return redis.StrictRedis(host if host else settings['redis']['host'], decode_responses=True)


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
    return urllib.quote_plus(obj)


def d(coded):
    return urllib.unquote_plus(coded)


def je(obj):
    return e(json.dumps(obj))


def jd(coded):
    return json.loads(d(coded))


def jes(set):
    return je(list(set))


def jds(coded):
    return set(jd(coded))


def get_search_data(q, r):
    results_number = r.results_number()
    if results_number < r.results_length():
        results_number = 0
    results = r.get_ordered_results()
    for result in results:
        result['engines'] = list(result['engines'])
        if not type(result['engines']) is list:
            print(result['engines'])
        if 'publishedDate' in result:
            try:
                result['pubdate'] = result['publishedDate'].strftime('%Y-%m-%d %H:%M:%S')
            finally:
                result['publishedDate'] = None
    if q.time_range is None:
        q.time_range = ""

    return SearchData(q, results, r.paging, results_number, r.answers, r.corrections,
                      r.infoboxes, r.suggestions, r.unresponsive_engines)


def search(request, host):
    search_query = get_search_query_from_webapp(request.preferences, request.form)
    searchData = read(search_query, host)
    if searchData is None:
        result_container = Search(search_query).search()
        searchData = get_search_data(search_query, result_container)
        threading.Thread(target=save, args=(searchData, host), name='save_search_' + str(searchData)).start()

    ordered_plugin = request.user_plugins
    plugins.call(ordered_plugin, 'post_search', request, searchData)

    for result in searchData.results:
        plugins.call(ordered_plugin, 'on_result', request, searchData, result)
    return searchData


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
