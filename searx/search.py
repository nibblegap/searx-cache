'''
searx is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

searx is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with searx. If not, see < http://www.gnu.org/licenses/ >.

(C) 2013- by Adam Tauber, <asciimoo@gmail.com>
'''

import gc
import threading
from time import time
from uuid import uuid4

import requests.exceptions
from flask_babel import gettext

import searx.poolrequests as requests_lib
from searx import search_database
from searx import logger
from searx.answerers import ask
from searx.engines import (
    categories, engines, settings
)
from searx.exceptions import SearxParameterException
from searx.query import RawTextQuery, SearchQuery, VALID_LANGUAGE_CODE
from searx.results import ResultContainer, SearchData
from searx.utils import gen_useragent
from searx.plugins import plugins

from _thread import start_new_thread

logger = logger.getChild('search')

number_of_searches = 0


def send_http_request(engine, request_params):
    # create dictionary which contain all
    # informations about the request
    request_args = dict(
        headers=request_params['headers'],
        cookies=request_params['cookies'],
        verify=request_params['verify']
    )

    # specific type of request (GET or POST)
    if request_params['method'] == 'GET':
        req = requests_lib.get
    else:
        req = requests_lib.post
        request_args['data'] = request_params['data']

    # send the request
    return req(request_params['url'], **request_args)


def search_one_request(engine, query, request_params):
    # update request parameters dependent on
    # search-engine (contained in engines folder)
    engine.request(query, request_params)

    # ignoring empty urls
    if request_params['url'] is None:
        return []

    if not request_params['url']:
        return []

    # send request
    response = send_http_request(engine, request_params)

    # parse the response
    response.search_params = request_params
    return engine.response(response)


def search_one_request_safe(engine_name, query, request_params, result_container, start_time, timeout_limit):
    # set timeout for all HTTP requests
    requests_lib.set_timeout_for_thread(timeout_limit, start_time=start_time)
    # reset the HTTP total time
    requests_lib.reset_time_for_thread()

    #
    engine = engines[engine_name]

    # suppose everything will be alright
    requests_exception = False

    try:
        # send requests and parse the results
        search_results = search_one_request(engine, query, request_params)

        # add results
        result_container.extend(engine_name, search_results)

        # update engine time when there is no exception
        with threading.RLock():
            engine.stats['engine_time'] += time() - start_time
            engine.stats['engine_time_count'] += 1
            # update stats with the total HTTP time
            engine.stats['page_load_time'] += requests_lib.get_time_for_thread()
            engine.stats['page_load_count'] += 1

    except Exception as e:
        search_duration = time() - start_time

        with threading.RLock():
            engine.stats['errors'] += 1

        if (issubclass(e.__class__, requests.exceptions.Timeout)):
            result_container.add_unresponsive_engine((engine_name, gettext('timeout')))
            # requests timeout (connect or read)
            logger.error("engine {0} : HTTP requests timeout"
                         "(search duration : {1} s, timeout: {2} s) : {3}"
                         .format(engine_name, search_duration, timeout_limit, e.__class__.__name__))
            requests_exception = True
        elif (issubclass(e.__class__, requests.exceptions.RequestException)):
            result_container.add_unresponsive_engine((engine_name, gettext('request exception')))
            # other requests exception
            logger.exception("engine {0} : requests exception"
                             "(search duration : {1} s, timeout: {2} s) : {3}"
                             .format(engine_name, search_duration, timeout_limit, e))
            requests_exception = True
        else:
            result_container.add_unresponsive_engine((
                engine_name,
                '{0}: {1}'.format(gettext('unexpected crash'), e),
            ))
            # others errors
            logger.exception('engine {0} : exception : {1}'.format(engine_name, e))

    # suspend or not the engine if there are HTTP errors
    with threading.RLock():
        if requests_exception:
            # update continuous_errors / suspend_end_time
            engine.continuous_errors += 1
            engine.suspend_end_time = time() + min(settings['search']['max_ban_time_on_fail'],
                                                   engine.continuous_errors * settings['search']['ban_time_on_fail'])
        else:
            # no HTTP error (perhaps an engine error)
            # anyway, reset the suspend variables
            engine.continuous_errors = 0
            engine.suspend_end_time = 0


def search_multiple_requests(requests, result_container, start_time, timeout_limit):
    search_id = uuid4().__str__()

    for engine_name, query, request_params in requests:
        th = threading.Thread(
            target=search_one_request_safe,
            args=(engine_name, query, request_params, result_container, start_time, timeout_limit),
            name=search_id,
        )
        th._engine_name = engine_name
        th.start()

    for th in threading.enumerate():
        if th.name == search_id:
            remaining_time = max(0.0, timeout_limit - (time() - start_time))
            th.join(remaining_time)
            if th.isAlive():
                result_container.add_unresponsive_engine((th._engine_name, gettext('timeout')))
                logger.warning('engine timeout: {0}'.format(th._engine_name))


# get default reqest parameter
def default_request_params():
    return {
        'method': 'GET',
        'headers': {},
        'data': {},
        'url': '',
        'cookies': {},
        'verify': True
    }


class Search:
    """Search information manager"""

    def __init__(self, cachecls=search_database.CacheInterface):
        self.cache = cachecls()

    def __call__(self, request):
        """ Entry point to perform search request on engines
        """
        search_query = self.get_search_query_from_webapp(request.preferences, request.form)
        searchData = self.cache.read(search_query)

        if searchData is None:
            result_container = self.search(search_query)
            searchData = self.create_search_data(search_query, result_container)
            self.cache.save(searchData)

        self.search_with_plugins(request, searchData)
        return searchData

    def search(self, search_query):
        """ do search-request

        Return a ResultContainer object
        """
        global number_of_searches
        result_container = ResultContainer()

        # start time
        start_time = time()

        # answeres ?
        answerers_results = ask(search_query)

        if answerers_results:
            for results in answerers_results:
                result_container.extend('answer', results)
            return result_container

        # init vars
        requests = []

        # increase number of searches
        number_of_searches += 1

        # set default useragent
        # user_agent = request.headers.get('User-Agent', '')
        user_agent = gen_useragent()

        # max of all selected engine timeout
        timeout_limit = 0

        # start search-reqest for all selected engines
        for selected_engine in search_query.engines:
            if selected_engine['name'] not in engines:
                continue

            engine = engines[selected_engine['name']]

            # skip suspended engines
            if engine.suspend_end_time >= time():
                logger.debug('Engine currently suspended: %s', selected_engine['name'])
                continue

            # if paging is not supported, skip
            if search_query.pageno > 1 and not engine.paging:
                continue

            # if time_range is not supported, skip
            if search_query.time_range and not engine.time_range_support:
                continue

            # set default request parameters
            request_params = default_request_params()
            request_params['headers']['User-Agent'] = user_agent
            request_params['category'] = selected_engine['category']
            request_params['pageno'] = search_query.pageno

            if hasattr(engine, 'language') and engine.language:
                request_params['language'] = engine.language
            else:
                request_params['language'] = search_query.language

            # 0 = None, 1 = Moderate, 2 = Strict
            request_params['safesearch'] = search_query.safesearch
            request_params['time_range'] = search_query.time_range

            # append request to list
            requests.append((selected_engine['name'], search_query.query, request_params))

            # update timeout_limit
            timeout_limit = max(timeout_limit, engine.timeout)

        if requests:
            # send all search-request
            search_multiple_requests(requests, result_container, start_time, timeout_limit)
            start_new_thread(gc.collect, tuple())

        # return results, suggestions, answers and infoboxes
        return result_container

    def search_with_plugins(self, request, searchData):
        ordered_plugin = request.user_plugins
        plugins.call(ordered_plugin, 'post_search', request, searchData)

        for result in searchData.results:
            plugins.call(ordered_plugin, 'on_result', request, searchData, result)

    def get_search_query_from_webapp(self, preferences, form):
        # no text for the query ?
        if not form.get('q'):
            raise SearxParameterException('q', '')

        # set blocked engines
        disabled_engines = preferences.engines.get_disabled()

        # parse query, if tags are set, which change
        # the serch engine or search-language
        raw_text_query = RawTextQuery(form['q'], disabled_engines)
        raw_text_query.parse_query()

        # set query
        query = raw_text_query.getSearchQuery()

        # get and check page number
        pageno_param = form.get('pageno', '1')
        if not pageno_param.isdigit() or int(pageno_param) < 1:
            raise SearxParameterException('pageno', pageno_param)
        query_pageno = int(pageno_param)

        # get language
        # set specific language if set on request, query or preferences
        # TODO support search with multible languages
        if len(raw_text_query.languages):
            query_lang = raw_text_query.languages[-1]
        elif 'language' in form:
            query_lang = form.get('language')
        else:
            query_lang = preferences.get_value('language')

        # check language
        if not VALID_LANGUAGE_CODE.match(query_lang):
            raise SearxParameterException('language', query_lang)

        # get safesearch
        if 'safesearch' in form:
            query_safesearch = form.get('safesearch')
            # first check safesearch
            if not query_safesearch.isdigit():
                raise SearxParameterException('safesearch', query_safesearch)
            query_safesearch = int(query_safesearch)
        else:
            query_safesearch = preferences.get_value('safesearch')

        # safesearch : second check
        if query_safesearch < 0 or query_safesearch > 2:
            raise SearxParameterException('safesearch', query_safesearch)

        # get time_range
        query_time_range = form.get('time_range')

        # check time_range
        if query_time_range not in ('None', None, '', 'day', 'week', 'month', 'year'):
            raise SearxParameterException('time_range', query_time_range)

        # query_engines
        query_engines = raw_text_query.engines

        # we only need to check the categories parameter set by the caller (not by the user)
        # so we can assume it contains a list of categories
        query_categories = form.get('categories')

        def append_to_engines(cat):
            # protect agains custom category provided by the user
            engines = categories.get(cat)
            if engines is None:
                return
            for engine in engines:
                if (engine.name, cat) not in disabled_engines:
                    query_engines.append({'category': cat, 'name': engine.name})

        # on top of the category field we have query_categories, which will be the engines to
        # use to perform the search.
        for category in query_categories:
            append_to_engines(category)

        return SearchQuery(query, query_engines, query_categories, query_lang, query_safesearch, query_pageno,
                           query_time_range)

    def create_search_data(self, q, r):
        results_number = r.results_number()
        if results_number < r.results_length():
            results_number = 0
        results = r.get_ordered_results()
        for result in results:
            if 'publishedDate' in result:
                try:
                    result['pubdate'] = result['publishedDate'].strftime('%Y-%m-%d %H:%M:%S')
                finally:
                    result['publishedDate'] = None
        if q.time_range is None:
            q.time_range = ""

        return SearchData(q, results, r.paging, results_number, r.answers, r.corrections,
                          r.infoboxes, r.suggestions, r.unresponsive_engines)
