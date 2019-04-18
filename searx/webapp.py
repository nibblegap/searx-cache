#!/usr/bin/env python

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

import hashlib
import hmac
import os
import copy
import asyncio
from pathlib import Path

from html import escape
from datetime import datetime, timedelta

import requests
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from pygments.formatters import HtmlFormatter

from aiohttp import web, ClientSession
import jinja2
import aiohttp_jinja2
from aiohttp_jinja2.helpers import url_for, static_url

from gettext import gettext
from babel.dates import format_date
from babel.numbers import format_decimal
from aiohttp_babel.locale import load_gettext_translations, set_locale_detector
from aiohttp_babel.middlewares import babel_middleware, _

from searx import logger
from searx import settings, searx_dir, searx_debug
from searx.exceptions import SearxParameterException
from searx.engines import (
    categories, engines, engine_shortcuts, get_engines_stats, initialize_engines
)
from searx.utils import (
    highlight_content, get_resources_directory,
    get_static_files, get_result_templates, get_themes, gen_useragent,
    dict_subset, prettify_url, match_language
)
from searx.version import VERSION_STRING
from searx.languages import language_codes as languages
from searx.search import Search
from searx.search_database import RedisCache
from searx.query import RawTextQuery
from searx.autocomplete import searx_bang, backends as autocomplete_backends
from searx.plugins import plugins
from searx.plugins.oa_doi_rewrite import get_doi_resolver
from searx.preferences import Preferences, ValidationException, LANGUAGE_CODES
from searx.answerers import answerers
from searx.url_utils import urlencode, urlparse, urljoin
from searx.utils import new_hmac

logger = logger.getChild('webapp')


# about static
static_path = get_resources_directory(searx_dir, 'static', settings['ui']['static_path'])
logger.debug('static directory is %s', static_path)
static_files = get_static_files(static_path)

# about templates
default_theme = settings['ui']['default_theme']
templates_path = get_resources_directory(searx_dir, 'templates', settings['ui']['templates_path'])
logger.debug('templates directory is %s', templates_path)
themes = get_themes(templates_path)
result_templates = get_result_templates(templates_path)
global_favicons = []
for indice, theme in enumerate(themes):
    global_favicons.append([])
    theme_img_path = os.path.join(static_path, 'themes', theme, 'img', 'icons')
    for (dirpath, dirnames, filenames) in os.walk(theme_img_path):
        global_favicons[indice].extend(filenames)

routes = web.RouteTableDef()


if not searx_debug:
    initialize_engines(settings['engines'])


rtl_locales = ['ar', 'arc', 'bcc', 'bqi', 'ckb', 'dv', 'fa', 'glk', 'he',
               'ku', 'mzn', 'pnb', 'ps', 'sd', 'ug', 'ur', 'yi']

# used when translating category names
_category_names = (gettext('files'),
                   gettext('general'),
                   gettext('music'),
                   gettext('social media'),
                   gettext('images'),
                   gettext('videos'),
                   gettext('it'),
                   gettext('news'),
                   gettext('map'),
                   gettext('science'))

outgoing_proxies = settings['outgoing'].get('proxies') or None


def get_locale(request):
    locale = "en-US"

    for lang in request.headers.get("Accept-Language", locale).split(","):
        locale = match_language(lang, settings['locales'].keys(), fallback=None)
        if locale is not None:
            break

    logger.debug("default locale from browser info is `%s`", locale)

    if request.preferences.get_value('locale') != '':
        locale = request.preferences.get_value('locale')

    if 'locale' in request.form and request.form['locale'] in settings['locales']:
        locale = request.form['locale']

    if locale == 'zh_TW':
        locale = 'zh_Hant_TW'

    logger.debug("selected locale is `%s`", locale)

    return locale

# {{{ jinja2 custom function


# code-highlighter
def code_highlighter(codelines, language=None):
    if not language:
        language = 'text'

    try:
        # find lexer by programing language
        lexer = get_lexer_by_name(language, stripall=True)
    except ClassNotFound:
        # if lexer is not found, using default one
        logger.debug('highlighter cannot find lexer for {0}'.format(language))
        lexer = get_lexer_by_name('text', stripall=True)

    html_code = ''
    tmp_code = ''
    last_line = None

    # parse lines
    for line, code in codelines:
        if not last_line:
            line_code_start = line

        # new codeblock is detected
        if last_line is not None and \
                last_line + 1 != line:
            # highlight last codepart
            formatter = HtmlFormatter(linenos='inline',
                                      linenostart=line_code_start)
            html_code = html_code + highlight(tmp_code, lexer, formatter)

            # reset conditions for next codepart
            tmp_code = ''
            line_code_start = line

        # add codepart
        tmp_code += code + '\n'

        # update line
        last_line = line

    # highlight last codepart
    formatter = HtmlFormatter(linenos='inline', linenostart=line_code_start)
    html_code = html_code + highlight(tmp_code, lexer, formatter)

    return html_code


# Extract domain from url
def extract_domain(url):
    return urlparse(url)[1]


def get_result_template(theme, template_name):
    themed_path = theme + '/result_templates/' + template_name
    if themed_path in result_templates:
        return themed_path
    return 'result_templates/' + template_name


def proxify(url):
    if url.startswith('//'):
        url = 'https:' + url

    if not settings.get('result_proxy'):
        return url

    url_params = dict(mortyurl=url)

    if settings['result_proxy'].get('key'):
        url_params['mortyhash'] = hmac.new(settings['result_proxy']['key'],
                                           url,
                                           hashlib.sha256).hexdigest()

    return '{0}?{1}'.format(settings['result_proxy']['url'],
                            urlencode(url_params))


@jinja2.contextfunction
def image_proxify(context, url):
    preferences = context["preferences"]

    if url.startswith('//'):
        url = 'https:' + url

    if not preferences.get_value('image_proxy'):
        return url

    if url.startswith('data:image/jpeg;base64,'):
        return url

    if settings.get('result_proxy'):
        return proxify(url)

    h = new_hmac(settings['server']['secret_key'], url)

    return '{0}?{1}'.format(context["app"].router['/image_proxy'].url_for(),
                            urlencode(dict(url=url, h=h)))

# }}} end jinja filter
# {{{ helpers


def get_current_theme_name(request, override=None):
    """Returns theme name.

    Checks in this order:
    1. override
    2. cookies
    3. settings"""

    if override and (override in themes or override == '__common__'):
        return override
    theme_name = request.query.get('theme', request.preferences.get_value('theme'))
    if theme_name not in themes:
        theme_name = default_theme
    return theme_name


@jinja2.contextfunction
def url_for_theme(context, endpoint, **values):
    filename = values.get('filename', None)
    if endpoint == 'static' and filename:
        if "theme" in context:
            filename_with_theme = "themes/{}/{}".format(context["theme"], filename)
            if filename_with_theme in static_files:
                filename = filename_with_theme
        return static_url(context, filename)
    if "_external" in values:
        values.pop("_external")
        return url_for(context, endpoint, **values).join(context["base_url"])
    return url_for(context, endpoint, **values)


def render(request, template_name, override_theme=None, status=200, **kwargs):
    disabled_engines = request.preferences.engines.get_disabled()

    enabled_categories = set(category for engine_name in engines
                             for category in engines[engine_name].categories
                             if (engine_name, category) not in disabled_engines)

    if 'categories' not in kwargs:
        kwargs['categories'] = ['general']
        kwargs["categories"].extend(
            x
            for x in sorted(categories.keys())
            if x != "general" and x in enabled_categories
        )

    if 'all_categories' not in kwargs:
        kwargs['all_categories'] = ['general']
        kwargs['all_categories'].extend(x for x in
                                        sorted(categories.keys())
                                        if x != 'general')

    if 'selected_categories' not in kwargs:
        kwargs['selected_categories'] = []
        for arg in request.query:
            if arg.startswith('category_'):
                c = arg.split('_', 1)[1]
                if c in categories:
                    kwargs['selected_categories'].append(c)

    if not kwargs['selected_categories']:
        cookie_categories = request.preferences.get_value('categories')
        for ccateg in cookie_categories:
            kwargs['selected_categories'].append(ccateg)

    if not kwargs['selected_categories']:
        kwargs['selected_categories'] = ['general']

    if 'autocomplete' not in kwargs:
        kwargs['autocomplete'] = request.preferences.get_value('autocomplete')

    locale = request.preferences.get_value('locale')

    if locale in rtl_locales and 'rtl' not in kwargs:
        kwargs['rtl'] = True

    kwargs['searx_version'] = VERSION_STRING

    kwargs['method'] = request.preferences.get_value('method')

    kwargs['safesearch'] = str(request.preferences.get_value('safesearch'))

    kwargs['language_codes'] = languages
    if 'current_language' not in kwargs:
        kwargs['current_language'] = match_language(request.preferences.get_value('language'),
                                                    LANGUAGE_CODES,
                                                    fallback=locale)

    # override url_for function in templates
    kwargs['proxify'] = proxify if settings.get('result_proxy', {}).get('url') else None

    kwargs['theme'] = get_current_theme_name(request, override=override_theme)

    kwargs['template_name'] = template_name

    kwargs['cookies'] = request.cookies

    kwargs['errors'] = request.errors

    kwargs['base_url'] = request.url.origin()

    kwargs['instance_name'] = settings['general']['instance_name']

    kwargs['results_on_new_tab'] = request.preferences.get_value('results_on_new_tab')

    kwargs['unicode'] = str

    kwargs['preferences'] = request.preferences

    kwargs['scripts'] = set()
    for plugin in request.user_plugins:
        for script in plugin.js_dependencies:
            kwargs['scripts'].add(script)

    kwargs['styles'] = set()
    for plugin in request.user_plugins:
        for css in plugin.css_dependencies:
            kwargs['styles'].add(css)

    return aiohttp_jinja2.render_template(
        '{}/{}'.format(kwargs['theme'], template_name), request, status=status, context=kwargs)

# }}}
# {{{ endpoints


@web.middleware
async def pre_request_middleware(request, handler):
    request.errors = []

    preferences = Preferences(themes, list(categories.keys()), engines, plugins)
    request.preferences = preferences
    try:
        preferences.parse_dict(request.cookies)
    except:
        request.errors.append(gettext('Invalid settings, please edit your preferences'))

    # merge GET, POST vars
    # request.form
    if request.method == "GET":
        request.form = dict(request.query)
    elif request.method == "POST":
        request.form = dict(await request.post())
    else:
        logger.warning("unsupportted method to fetch data")

    for k, v in request.query.items():
        if k not in request.form:
            request.form[k] = v

    if request.form.get('preferences'):
        preferences.parse_encoded_data(request.form['preferences'])
    else:
        try:
            preferences.parse_dict(request.form)
        except Exception:
            logger.exception('invalid settings')
            request.errors.append(gettext('Invalid settings'))

    # init search language and locale
    locale = get_locale(request)
    if not preferences.get_value("language"):
        preferences.parse_dict({"language": locale})
    if not preferences.get_value("locale"):
        preferences.parse_dict({"locale": locale})

    # request.user_plugins
    request.user_plugins = []
    allowed_plugins = preferences.plugins.get_enabled()
    disabled_plugins = preferences.plugins.get_disabled()
    for plugin in plugins:
        if (
            plugin.default_on and plugin.id not in disabled_plugins
        ) or plugin.id in allowed_plugins:
            request.user_plugins.append(plugin)

    return await handler(request)


def config_results(results, query):
    for result in results:
        if 'content' in result and result['content']:
            result['content'] = highlight_content(escape(result['content'][:1024]), query)
        result['title'] = highlight_content(escape(result['title'] or ''), query)
        result['pretty_url'] = prettify_url(result['url'])

        if 'pubdate' in result:
            publishedDate = datetime.strptime(result['pubdate'], '%Y-%m-%d %H:%M:%S')
            if publishedDate >= datetime.now() - timedelta(days=1):
                timedifference = datetime.now() - publishedDate
                minutes = int((timedifference.seconds / 60) % 60)
                hours = int(timedifference.seconds / 60 / 60)
                if hours == 0:
                    result['publishedDate'] = gettext('{minutes} minute(s) ago').format(minutes=minutes)
                else:
                    result['publishedDate'] = gettext('{hours} hour(s), {minutes} minute(s) ago').format(
                        hours=hours, minutes=minutes)  # noqa
            else:
                result['publishedDate'] = format_date(publishedDate)


def index_error(request, exn, output, status):
    user_error = gettext("search error")
    if output == "json":
        return web.json_response({"error": f"{user_error}: {exn}"})

    request.errors.append(user_error)
    return render(request, 'index.html', error_details=exn, status=status)


@routes.get('/', name="index")
@routes.post('/')
@routes.get('/search')
@routes.post('/search')
async def index(request):
    # check the response format
    output = request.form.get("output", "html")

    # check if there is query
    if not request.form.get('q'):
        if output == 'json':
            return web.json_response({}, status=204)
        return render(request, 'index.html')

    if request.form.get('category') is None:
        category = None
        for name, value in request.form.items():
            if name.startswith('category_'):
                category = name[9:]
                if category in categories and value == "on":
                    break
        if category is not None:
            request.form["category"] = category

    selected_category = request.form.get('category') or 'general'
    first_page = request.form.get('pageno')
    is_general_first_page = selected_category == 'general' and (first_page is None or first_page == u'1')

    images = []
    videos = []
    # search
    search_data = None
    try:
        if is_general_first_page:
            request.form['categories'] = ['general', 'videos', 'images']
        else:
            request.form['categories'] = [selected_category]
        search_data = await request.app["search"](request)

    except Exception as e:
        # log exception
        logger.exception('search error')

        # is it an invalid input parameter or something else ?
        if issubclass(e.__class__, SearxParameterException):
            return index_error(request, e, output, status=400)
        else:
            return index_error(request, e, output, status=500)

    results_copy = copy.deepcopy(search_data.results)
    if is_general_first_page:
        for res in results_copy:
            if res.get('category') == 'images':
                if len(images) < 5:
                    images.append(res)
                results_copy.remove(res)
            elif res.get('category') == 'videos':
                if len(videos) < 2:
                    videos.append(res)
                results_copy.remove(res)
            elif res.get('category') is None:
                results_copy.remove(res)

    # output
    config_results(results_copy, search_data.query)
    config_results(images, search_data.query)
    config_results(videos, search_data.query)

    response = dict(
        results=results_copy,
        q=search_data.query,
        selected_category=selected_category,
        selected_categories=[selected_category],
        pageno=search_data.pageno,
        time_range=search_data.time_range,
        number_of_results=format_decimal(search_data.results_number),
        advanced_search=request.form.get('advanced_search', None),
        suggestions=list(search_data.suggestions),
        answers=list(search_data.answers),
        corrections=list(search_data.corrections),
        infoboxes=search_data.infoboxes,
        paging=search_data.paging,
        unresponsive_engines=list(search_data.unresponsive_engines),
        current_language=match_language(search_data.language,
                                        LANGUAGE_CODES,
                                        fallback=request.preferences.get_value("language")),
        image_results=images,
        videos_results=videos,
        favicons=global_favicons[themes.index(get_current_theme_name(request))]
    )
    if output == 'json':
        return web.json_response(response)
    return render(request, 'results.html', **response)


@routes.get('/about', name="about")
async def about(request):
    """Render about page"""
    return render(request, 'about.html')


@routes.get('/privacy', name="privacy")
async def privacy(request):
    """Render privacy page"""
    return render(request, 'privacy.html')


@routes.get('/autocompleter')
@routes.post('/autocompleter')
async def autocompleter(request):
    """Return autocompleter results"""
    # set blocked engines
    disabled_engines = request.preferences.engines.get_disabled()

    # parse query
    raw_text_query = RawTextQuery(request.form.get('q', ''), disabled_engines)
    raw_text_query.parse_query()

    # check if search query is set
    if not raw_text_query.getSearchQuery():
        return '', 400

    # run autocompleter
    completer = autocomplete_backends.get(request.preferences.get_value('autocomplete'))

    # parse searx specific autocompleter results like !bang
    raw_results = searx_bang(raw_text_query)

    # normal autocompletion results only appear if max 3 inner results returned
    if len(raw_results) <= 3 and completer:
        # get language from cookie
        language = request.preferences.get_value('language')
        if not language or language == 'all':
            language = 'en'
        else:
            language = language.split('-')[0]
        # run autocompletion
        raw_results.extend(completer(raw_text_query.getSearchQuery(), language))

    # parse results (write :language and !engine back to result string)
    results = []
    for result in raw_results:
        raw_text_query.changeSearchQuery(result)

        # add parsed result
        results.append(raw_text_query.getFullQuery())

    # return autocompleter results
    if request.form.get('format') == 'x-suggestions':
        return web.json_response([raw_text_query.query, results])

    return web.json_response(results)


@routes.get('/preferences', name="preferences")
@routes.post('/preferences')
async def preferences(request):
    """Render preferences page && save user preferences"""

    # save preferences
    if request.method == 'POST':
        location = request.app.router['index'].url_for()
        resp = web.HTTPFound(location=location)

        try:
            request.preferences.parse_form(request.form)
        except ValidationException:
            request.errors.append(gettext('Invalid settings, please edit your preferences'))
            raise resp
        raise request.preferences.save(resp)

    # render preferences
    image_proxy = request.preferences.get_value('image_proxy')
    disabled_engines = request.preferences.engines.get_disabled()
    allowed_plugins = request.preferences.plugins.get_enabled()

    # stats for preferences page
    stats = {}

    for c in categories:
        for e in categories[c]:
            stats[e.name] = {'time': None,
                             'warn_timeout': False,
                             'warn_time': False}
            if e.timeout > settings['outgoing']['request_timeout']:
                stats[e.name]['warn_timeout'] = True
            stats[e.name]['supports_selected_language'] = _is_selected_language_supported(e, request.preferences)

    # get first element [0], the engine time,
    # and then the second element [1] : the time (the first one is the label)
    for engine_stat in get_engines_stats()[0][1]:
        stats[engine_stat.get('name')]['time'] = round(engine_stat.get('avg'), 3)
        if engine_stat.get('avg') > settings['outgoing']['request_timeout']:
            stats[engine_stat.get('name')]['warn_time'] = True
    # end of stats

    return render(request, 'preferences.html',
                  locales=settings['locales'],
                  current_locale=request.preferences.get_value("locale"),
                  image_proxy=image_proxy,
                  engines_by_category=categories,
                  stats=stats,
                  answerers=[{'info': a.self_info(), 'keywords': a.keywords} for a in answerers],
                  disabled_engines=disabled_engines,
                  autocomplete_backends=autocomplete_backends,
                  shortcuts={y: x for x, y in engine_shortcuts.items()},
                  themes=themes,
                  plugins=plugins,
                  doi_resolvers=settings['doi_resolvers'],
                  current_doi_resolver=get_doi_resolver(request.query, request.preferences.get_value('doi_resolver')),
                  allowed_plugins=allowed_plugins,
                  preferences_url_params=request.preferences.get_as_url_params(),
                  preferences=True)


def _is_selected_language_supported(engine, preferences):
    language = preferences.get_value("language")
    return language == "all" or match_language(
        language,
        getattr(engine, "supported_languages", []),
        getattr(engine, "language_aliases", {}),
        None,
    )


@routes.get('/image_proxy', name="image_proxy")
async def image_proxy(request):
    url = request.query.get('url')

    if not url:
        return '', 400

    h = new_hmac(settings['server']['secret_key'], url)

    if h != request.query.get('h'):
        return '', 400

    headers = dict_subset(request.headers, {'If-Modified-Since', 'If-None-Match'})
    headers['User-Agent'] = gen_useragent()

    resp = requests.get(url,
                        stream=True,
                        timeout=settings['outgoing']['request_timeout'],
                        headers=headers,
                        proxies=outgoing_proxies)

    if resp.status_code == 304:
        return '', resp.status_code

    if resp.status_code != 200:
        logger.debug('image-proxy: wrong response code: {0}'.format(resp.status_code))
        if resp.status_code >= 400:
            return '', resp.status_code
        return '', 400

    if not resp.headers.get('content-type', '').startswith('image/'):
        logger.debug('image-proxy: wrong content-type: {0}'.format(resp.headers.get('content-type')))
        return '', 400

    img = b''
    chunk_counter = 0

    for chunk in resp.iter_content(1024 * 1024):
        chunk_counter += 1
        if chunk_counter > 5:
            return '', 502  # Bad gateway - file is too big (>5M)
        img += chunk

    headers = dict_subset(resp.headers, {'Content-Length', 'Length', 'Date', 'Last-Modified', 'Expires', 'Etag'})

    return web.Response(img, content_type=resp.headers['content-type'], headers=headers)


@routes.get('/robots.txt')
async def robots(request):
    return web.Response(text="""User-agent: *
Allow: /
Allow: /about
Disallow: /preferences
Disallow: /*?*q=*
""")


@routes.get('/opensearch.xml', name="opensearch")
async def opensearch(request):
    method = 'post'

    if request.preferences.get_value('method') == 'GET':
        method = 'get'

    # chrome/chromium only supports HTTP GET....
    if request.headers.get('User-Agent', '').lower().find('webkit') >= 0:
        method = 'get'

    ret = render(request, 'opensearch.xml',
                 opensearch_method=method,
                 urljoin=urljoin,
                 override_theme='__common__')

    return web.Response(body=ret.text, content_type="text/xml")


@routes.get('/favicon.ico')
async def favicon(request):
    raise web.HTTPNotFound()
#    return send_from_directory(os.path.join(app.root_path,
#                                            static_path,
#                                            'themes',
#                                            get_current_theme_name(),
#                                            'img'),
#                               'favicon.png',
#                               mimetype='image/vnd.microsoft.icon')


@routes.get('/clear_cookies', name="clear_cookies")
async def clear_cookies(request):
    location = request.app.router['index'].url_for()
    resp = web.HTTPFound(location=location)
    for name in request.cookies:
        resp.del_cookie(name)
    raise resp


@routes.get('/config')
async def config(request):
    return web.json_response(
        {
            "categories": categories.keys(),
            "engines": [
                {
                    "name": engine_name,
                    "categories": engine.categories,
                    "shortcut": engine.shortcut,
                    "enabled": not engine.disabled,
                    "paging": engine.paging,
                    "language_support": engine.language_support,
                    "supported_languages": engine.supported_languages.keys()
                    if isinstance(engine.supported_languages, dict)
                    else engine.supported_languages,
                    "safesearch": engine.safesearch,
                    "time_range_support": engine.time_range_support,
                    "timeout": engine.timeout,
                }
                for engine_name, engine in engines.items()
            ],
            "plugins": [
                {"name": plugin.name, "enabled": plugin.default_on}
                for plugin in plugins
            ],
            "instance_name": settings["general"]["instance_name"],
            "locales": settings["locales"],
            "default_locale": settings["ui"]["default_locale"],
            "autocomplete": settings["search"]["autocomplete"],
            "safe_search": settings["search"]["safe_search"],
            "default_theme": settings["ui"]["default_theme"],
            "version": VERSION_STRING,
            "doi_resolvers": [r for r in settings["doi_resolvers"]],
            "default_doi_resolver": settings["default_doi_resolver"],
        }
    )


@web.middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if response.status != 404:
            return response
    except web.HTTPException as ex:
        if ex.status != 404:
            raise
    return aiohttp_jinja2.render_template('404.html', request, {})


# }}} end endpoint
# {{{ aiohttp hooks

async def on_startup(app):
    session = ClientSession()
    search = Search(session, RedisCache) if settings["redis"]["enable"] else Search(session)
    app["session"] = session
    app["search"] = search
    app["update_results"] = asyncio.create_task(search.cache.update_results(search))


async def on_cleanup(app):
    app['update_results'].cancel()
    await app['session'].close()
    await app['update_results']


# }}} end aiohttp hooks
# {{{ init

def create_app():
    app = web.Application()

    SEARX_HELPERS = {
        "code_highlighter": code_highlighter,
        "extract_domain": extract_domain,
        "get_result_template": get_result_template,
        "proxify": proxify,
        "image_proxify": image_proxify,
        "url_for": url_for_theme,
        "_": _
    }
    env = aiohttp_jinja2.setup(
        app,
        loader=jinja2.FileSystemLoader(templates_path),
        trim_blocks=True, lstrip_blocks=True
    )
    env.globals.update(SEARX_HELPERS)

    # only for dev env
    routes.static('/static', static_path)

    app['static_root_url'] = "/static"
    app.add_routes(routes)
    app.middlewares.append(pre_request_middleware)
    app.middlewares.append(error_middleware)
    app.middlewares.append(babel_middleware)

    # init locale
    set_locale_detector(get_locale)
    load_gettext_translations(Path(__file__).parent / "translations", "messages")

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    return app


def run():
    host = settings['server']['bind_address']
    port = settings['server']['port']

    logger.info('starting webserver on %s:%s', host, port)
    web.run_app(create_app(), host=host, port=port)
    logger.info("wait for shutdown...")


if __name__ == "__main__":
    run()

# }}}
