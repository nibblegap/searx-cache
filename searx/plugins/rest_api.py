import hmac
import hashlib

from flask_babel import gettext

from searx import settings
from searx.url_utils import urlencode


name = gettext('Rest API')
description = gettext('Update REST API')
default_on = True
preference_section = 'general'


def proxify(url):
    """ helper copied from webapp module
    """
    if url.startswith('//'):
        url = 'https:' + url

    if not settings.get('result_proxy'):
        return url

    if url.startswith('data:image/'):
        # 50 is an arbitrary number to get only the beginning of the image.
        partial_base64 = url[len('data:image/'):50].split(';')
        if len(partial_base64) == 2 \
           and partial_base64[0] in ['gif', 'png', 'jpeg', 'pjpeg', 'webp', 'tiff', 'bmp']\
           and partial_base64[1].startswith('base64,'):
            return url
        else:
            return None

    url_params = dict(mortyurl=url.encode('utf-8'))

    if settings['result_proxy'].get('key'):
        url_params['mortyhash'] = hmac.new(settings['result_proxy']['key'],
                                           url.encode('utf-8'),
                                           hashlib.sha256).hexdigest()

    return '{0}?{1}'.format(settings['result_proxy']['url'],
                            urlencode(url_params))


def on_result(request, search, result):
    if request.form.get("format") != "json":
        return True

    for attr in ["thumbnail", "thumbnail_src"]:
        if attr in result:
            result[attr] = proxify(result[attr])

    return True
