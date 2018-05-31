import base64
import json

import pymysql


class Search(object):
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


def read(q, settings):
    time_range = q.time_range
    if time_range == "":
        time_range = "None"
    connection = pymysql.connect(host=settings['host'], user=settings['user'], password=settings['password'],
                                 database=settings['database'])
    try:
        with connection.cursor() as cursor:
            sql = "SELECT RESULTS, PAGING, RESULTS_NUMBER, ANSWERS, CORRECTIONS, INFOBOXES, SUGGESTIONS, " \
                  "UNRESPONSIVE_ENGINES FROM SEARCH_HISTORY WHERE QUERY='%s' AND CATEGORIES='%s' AND PAGENO=%s AND " \
                  "SAFE_SEARCH=%s AND LANGUAGE='%s' AND TIME_RANGE='%s' AND ENGINES='%s'"
            cursor.execute(
                sql % (e(q.query), je(q.categories), q.pageno, q.safesearch, e(q.lang), time_range, je(q.engines)))
            for result in cursor:
                return Search(q, jd(result[0]), result[1] != 0, result[2], jd(result[3]),
                              jd(result[4]), jd(result[5]), jd(result[6]), jd(result[7]))
    finally:
        connection.close()
    return None


def save(q, r, settings):
    results_number = r.results_number()
    if results_number < r.results_length():
        results_number = 0
    results = r.get_ordered_results()
    for result in results:
        result['engines'] = list(result['engines'])
    time_range = q.time_range
    if time_range == "":
        time_range = "None"

    connection = pymysql.connect(host=settings['host'], user=settings['user'], password=settings['password'],
                                 database=settings['database'])
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO SEARCH_HISTORY(QUERY, CATEGORIES, PAGENO, SAFE_SEARCH, LANGUAGE, TIME_RANGE, ENGINES, " \
                  "RESULTS, PAGING, RESULTS_NUMBER, ANSWERS, CORRECTIONS, INFOBOXES, SUGGESTIONS, " \
                  "UNRESPONSIVE_ENGINES) VALUES('%s', '%s', %s, %s, '%s', '%s', '%s', '%s', %s, %s, '%s', '%s', '%s'," \
                  " '%s', '%s')"
            cursor.execute(sql % (e(q.query), je(q.categories), q.pageno, q.safesearch, e(q.lang), time_range,
                                  je(q.engines), jle(results), r.paging, results_number, jle(r.answers),
                                  jle(r.corrections), je(r.infoboxes), jle(r.suggestions), jle(r.unresponsive_engines)))
            connection.commit()
    finally:
        connection.close()
    return Search(q, results, r.paging, results_number, r.answers, r.corrections,
                  r.infoboxes, r.suggestions, r.unresponsive_engines)


def e(uncoded):
    return base64.b64encode(uncoded)


def d(coded):
    return base64.b64decode(coded)


def je(uncoded):
    return base64.b64encode(json.dumps(uncoded))


def jle(uncoded):
    return base64.b64encode(json.dumps(list(uncoded)))


def jd(coded):
    return json.loads(base64.b64decode(coded))
