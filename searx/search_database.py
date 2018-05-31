import json

import pymysql


class Search(object):
    def __init__(self, categories, query, pageno, paging, safe_search, language, time_range, engines, results,
                 results_number, results_length, answers, corrections, infoboxes, suggestions, unresponsive_engines):
        self.categories = categories
        self.query = query
        self.pageno = pageno
        self.paging = paging
        self.safe_search = safe_search
        self.language = language
        self.time_range = time_range
        self.engines = engines
        self.results = results
        self.results_number = results_number
        self.results_length = results_length
        self.answers = answers
        self.corrections = corrections
        self.infoboxes = infoboxes
        self.suggestions = suggestions
        self.unresponsive_engines = unresponsive_engines


def read(categories, query, pageno, safe_search, language, time_range, engines, mysql_settings):
    if len(categories) != 1:
        return None

    category = categories[0].upper().replace(" ", "_")

    with pymysql.connect(host=mysql_settings['host'],
                         user=mysql_settings['user'],
                         password=mysql_settings['password'],
                         database=mysql_settings['database'],
                         charset='utf8mb4',
                         cursorclass=pymysql.cursors.DictCursor) as connection:
        with connection.cursor() as cursor:
            sql = "SELECT RESULTS, PAGING, RESULTS_NUMBER, RESULTS_LENGTH, ANSWERS, CORRECTIONS, INFOBOXES, " \
                  "SUGGESTIONS, UNRESPONSIVE_ENGINES FROM %s WHERE QUERY=%s AND PAGENO=%s AND SAFE_SEARCH=%s" \
                  " AND LANGUAGE=%s AND TIME_RANGE=%s AND ENGINES=%s"
            cursor.execute(sql,
                           (category, query, pageno, safe_search, language, time_range, str(engines).replace("'", '"')))
            for result in cursor:
                return Search(categories, query, pageno, result[1] != 0, safe_search, language, time_range, engines,
                              json.loads(result[0]), result[2], result[3], json.loads(result[4]),
                              json.loads(result[5]), json.loads(result[6]), json.loads(result[7]),
                              json.loads(result[8]))
    return None

def save(search_query):
    path = find_path(search_query)
    writer = open(path, 'w')
