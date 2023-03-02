# -*- coding: utf-8 -*-
import os
import re
from urllib.parse import urlparse


FISHING_DATA = os.path.dirname(os.environ["FISHING_DATA"])
LS_ROOT = FISHING_DATA  # Label studio data root.


__RE_EXTRACT_PATH_FROM_QUERY = re.compile(r"d=(.+)")


def realpath(ls_url: str):
    """Get real file path from miscellaneous styled url."""
    url_obj = urlparse(ls_url)
    if url_obj.scheme == "file":
        if url_obj.netloc == "fishing.data":
            return f"{os.environ['FISHING_DATA']}/{url_obj.path}"
        return url_obj.path
    elif url_obj.path == "/data/local-files/":  # Local file.
        match = __RE_EXTRACT_PATH_FROM_QUERY.search(url_obj.query)
        if match is not None:
            return f"{LS_ROOT}/{match.group(1)}"  # Resize image and update path.
    return ls_url  # Unknown style, return the original url immediately.
