from urllib.parse import (
    parse_qs,
    parse_qsl,
    quote,
    quote_plus,
    unquote,
    urlencode,
    urljoin,
    urlparse,
    urlunparse,
    ParseResult
)


__export__ = (parse_qs,
              parse_qsl,
              quote,
              quote_plus,
              unquote,
              urlencode,
              urljoin,
              urlparse,
              urlunparse,
              ParseResult)
