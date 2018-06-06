import json
import threading
import urllib

import pymysql

from searx.plugins import plugins
from searx.query import SearchQuery
from searx.search import Search, get_search_query_from_webapp
from searx.url_utils import urlparse

settings = None


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


def read(q):
    time_range = q.time_range
    if q.time_range is None:
        q.time_range = ""
    connection = pymysql.connect(host=settings['host'], user=settings['user'], password=settings['password'],
                                 database=settings['database'])
    try:
        with connection.cursor() as cursor:
            sql = "SELECT RESULTS, PAGING, RESULTS_NUMBER, ANSWERS, CORRECTIONS, INFOBOXES, SUGGESTIONS, " \
                  "UNRESPONSIVE_ENGINES FROM SEARCH_HISTORY WHERE QUERY='%s' AND CATEGORY='%s' AND PAGENO=%s AND " \
                  "SAFE_SEARCH=%s AND LANGUAGE='%s' AND TIME_RANGE='%s' AND ENGINES='%s'"
            cursor.execute(
                sql % (e(q.query), q.categories[0], q.pageno, q.safesearch, q.lang, time_range, je(q.engines)))
            for response in cursor:
                results = jd(response[0])
                for result in results:
                    result['parsed_url'] = urlparse(result['url'])
                return SearchData(q, results, response[1] != 0, response[2], jds(response[3]),
                                  jds(response[4]), jd(response[5]), jds(response[6]), jds(response[7]))
    finally:
        connection.close()
    return None


def save(d):
    connection = pymysql.connect(host=settings['host'], user=settings['user'], password=settings['password'],
                                 database=settings['database'])
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO SEARCH_HISTORY(QUERY, CATEGORY, PAGENO, SAFE_SEARCH, LANGUAGE, TIME_RANGE, ENGINES, " \
                  "RESULTS, PAGING, RESULTS_NUMBER, ANSWERS, CORRECTIONS, INFOBOXES, SUGGESTIONS, " \
                  "UNRESPONSIVE_ENGINES) VALUES('%s', '%s', %s, %s, '%s', '%s', '%s', '%s', %s, %s, '%s', '%s', '%s'," \
                  " '%s', '%s')"
            cursor.execute(sql % (e(d.query), d.categories[0], d.pageno, d.safe_search, d.language, d.time_range,
                                  je(d.engines), je(d.results), d.paging, d.results_number, jes(d.answers),
                                  jes(d.corrections), je(d.infoboxes), jes(d.suggestions), jes(d.unresponsive_engines)))
            connection.commit()
    finally:
        connection.close()


def get_twenty_queries(x):
    result = []
    connection = pymysql.connect(host=settings['host'], user=settings['user'], password=settings['password'],
                                 database=settings['database'])
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT QUERY, ENGINES, CATEGORY, LANGUAGE , SAFE_SEARCH, PAGENO, TIME_RANGE FROM "
                           "SEARCH_HISTORY LIMIT %s,20" % x)
            for row in cursor:
                result.append(SearchQuery(d(row[0]), jd(row[1]), [row[2]], row[3], row[4], row[5], row[6]))
    finally:
        connection.close()
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


def search(request):
    search_query = get_search_query_from_webapp(request.preferences, request.form)
    searchData = read(search_query)
    if searchData is None:
        result_container = Search(search_query).search()
        searchData = get_search_data(search_query, result_container)
        threading.Thread(target=save, args=(searchData,), name='save_search_' + str(searchData)).start()

    ordered_plugin = request.user_plugins
    plugins.call(ordered_plugin, 'post_search', request, searchData)

    for result in searchData.results:
        plugins.call(ordered_plugin, 'on_result', request, searchData, result)
    return searchData


def update(d):
    connection = pymysql.connect(host=settings['host'], user=settings['user'], password=settings['password'],
                                 database=settings['database'])
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE SEARCH_HISTORY SET RESULTS='%s', PAGING=%s, RESULTS_NUMBER=%s, ANSWERS='%s', CORRECTIONS='%s', INFOBOXES='%s', SUGGESTIONS='%s', " \
                  "UNRESPONSIVE_ENGINES='%s' WHERE QUERY='%s' AND CATEGORY='%s' AND PAGENO=%s AND " \
                  "SAFE_SEARCH=%s AND LANGUAGE='%s' AND TIME_RANGE='%s' AND ENGINES='%s'"
            cursor.execute(sql % (je(d.results), d.paging, d.results_number, jes(d.answers), jes(d.corrections),
                                  je(d.infoboxes), jes(d.suggestions), jes(d.unresponsive_engines),
                                  e(d.query), d.categories[0], d.pageno, d.safe_search, d.language, d.time_range,
                                  je(d.engines)))
            connection.commit()
    finally:
        connection.close()
