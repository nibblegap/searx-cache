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

import certifi
import logging
from os import environ
from os.path import realpath, dirname, join, abspath, isfile
from io import open
from ssl import OPENSSL_VERSION_INFO, OPENSSL_VERSION
try:
    from yaml import load
except ImportError:
    from sys import exit, stderr
    stderr.write('[E] install pyyaml\n')
    exit(2)

searx_dir = abspath(dirname(__file__))
engine_dir = dirname(realpath(__file__))


def check_settings_yml(file_name):
    if isfile(file_name):
        return file_name
    else:
        return None


# find location of settings.yml
if 'SEARX_SETTINGS_PATH' in environ:
    # if possible set path to settings using the
    # enviroment variable SEARX_SETTINGS_PATH
    settings_path = check_settings_yml(environ['SEARX_SETTINGS_PATH'])
else:
    # if not, get it from searx code base or last solution from /etc/searx
    settings_path = check_settings_yml(join(searx_dir, 'settings.yml')) or check_settings_yml('/etc/searx/settings.yml')

if not settings_path:
    raise Exception('settings.yml not found')

# load settings
with open(settings_path, 'r', encoding='utf-8') as settings_yaml:
    settings = load(settings_yaml)

'''
enable debug if
the environnement variable SEARX_DEBUG is 1 or true
(whatever the value in settings.yml)
or general.debug=True in settings.yml

disable debug if
the environnement variable SEARX_DEBUG is 0 or false
(whatever the value in settings.yml)
or general.debug=False in settings.yml
'''
searx_debug = True if settings.get('general', {}).get('debug') else False
searx_loglevel = 'DEBUG' if searx_debug else 'WARNING'
searx_loglevel = environ.get('SEARX_LOGGER', searx_loglevel).upper()
logging.basicConfig(level=getattr(logging, searx_loglevel))

logger = logging.getLogger('searx')
logger.debug('read configuration from %s', settings_path)
# Workaround for openssl versions <1.0.2
# https://github.com/certifi/python-certifi/issues/26
if OPENSSL_VERSION_INFO[0:3] < (1, 0, 2):
    if hasattr(certifi, 'old_where'):
        environ['REQUESTS_CA_BUNDLE'] = certifi.old_where()
    logger.warning('You are using an old openssl version({0}), please upgrade above 1.0.2!'.format(OPENSSL_VERSION))

logger.info('Initialisation done')

if 'SEARX_SECRET' in environ:
    settings['server']['secret_key'] = environ['SEARX_SECRET']
if 'BASE_URL' in environ:
    settings['server']['base_url'] = environ['BASE_URL']
if 'IMAGE_PROXY' in environ:
    settings['server']['image_proxy'] = environ['IMAGE_PROXY']
if 'SEARX_REDIS_HOST' in environ:
    settings['redis']['enable'] = True
    settings['redis']['host'] = environ['SEARX_REDIS_HOST']
if 'HTTP_PROXY_URL' in environ:
    settings['proxies']['http'] = environ['HTTP_PROXY_URL']
if 'HTTPS_PROXY_URL' in environ:
    settings['proxies']['https'] = environ['HTTPS_PROXY_URL']
