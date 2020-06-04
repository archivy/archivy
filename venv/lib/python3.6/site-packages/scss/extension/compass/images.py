"""Image utilities ported from Compass."""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import logging
import mimetypes
import os.path

import six
from six.moves import xrange

from . import CompassExtension
from .helpers import add_cache_buster
from scss import config
from scss.errors import SassMissingDependency
from scss.types import Color, List, Number, String, Url
from scss.util import getmtime, make_data_url, make_filename_hash
from scss.extension import Cache

try:
    from PIL import Image
except ImportError:
    try:
        import Image
    except:
        Image = None

log = logging.getLogger(__name__)
ns = CompassExtension.namespace


def _images_root():
    return config.STATIC_ROOT if config.IMAGES_ROOT is None else config.IMAGES_ROOT


def _assets_root():
    return config.ASSETS_ROOT or os.path.join(config.STATIC_ROOT, 'assets')


def _get_cache(prefix):
    return Cache((config.CACHE_ROOT or _assets_root(), prefix))


def _image_url(path, only_path=False, cache_buster=True, dst_color=None, src_color=None, inline=False, mime_type=None, spacing=None, collapse_x=None, collapse_y=None):
    """
    src_color - a list of or a single color to be replaced by each corresponding dst_color colors
    spacing - spaces to be added to the image
    collapse_x, collapse_y - collapsable (layered) image of the given size (x, y)
    """
    if inline or dst_color or spacing:
        if not Image:
            raise SassMissingDependency('PIL', 'image manipulation')

    filepath = String.unquoted(path).value
    fileext = os.path.splitext(filepath)[1].lstrip('.').lower()
    if mime_type:
        mime_type = String.unquoted(mime_type).value
    if not mime_type:
        mime_type = mimetypes.guess_type(filepath)[0]
    if not mime_type:
        mime_type = 'image/%s' % fileext
    path = None
    IMAGES_ROOT = _images_root()
    if callable(IMAGES_ROOT):
        try:
            _file, _storage = list(IMAGES_ROOT(filepath))[0]
        except IndexError:
            filetime = None
        else:
            filetime = getmtime(_file, _storage)
        if filetime is None:
            filetime = 'NA'
        elif inline or dst_color or spacing:
            path = _storage.open(_file)
    else:
        _path = os.path.join(IMAGES_ROOT.rstrip(os.sep), filepath.strip('\\/'))
        filetime = getmtime(_path)
        if filetime is None:
            filetime = 'NA'
        elif inline or dst_color or spacing:
            path = open(_path, 'rb')

    BASE_URL = config.IMAGES_URL or config.STATIC_URL
    if path:
        dst_colors = [list(Color(v).value[:3]) for v in List.from_maybe(dst_color) if v]

        src_color = Color.from_name('black') if src_color is None else src_color
        src_colors = [tuple(Color(v).value[:3]) for v in List.from_maybe(src_color)]

        len_colors = max(len(dst_colors), len(src_colors))
        dst_colors = (dst_colors * len_colors)[:len_colors]
        src_colors = (src_colors * len_colors)[:len_colors]

        spacing = Number(0) if spacing is None else spacing
        spacing = [int(Number(v).value) for v in List.from_maybe(spacing)]
        spacing = (spacing * 4)[:4]

        file_name, file_ext = os.path.splitext(os.path.normpath(filepath).replace(os.sep, '_'))
        key = (filetime, src_color, dst_color, spacing)
        asset_file = file_name + '-' + make_filename_hash(key) + file_ext
        ASSETS_ROOT = _assets_root()
        asset_path = os.path.join(ASSETS_ROOT, asset_file)

        if os.path.exists(asset_path):
            filepath = asset_file
            BASE_URL = config.ASSETS_URL
            if inline:
                path = open(asset_path, 'rb')
                url = make_data_url(mime_type, path.read())
            else:
                url = '%s%s' % (BASE_URL, filepath)
                if cache_buster:
                    filetime = getmtime(asset_path)
                    url = add_cache_buster(url, filetime)
        else:
            simply_process = False
            image = None

            if fileext in ('cur',):
                simply_process = True
            else:
                try:
                    image = Image.open(path)
                except IOError:
                    if not collapse_x and not collapse_y and not dst_colors:
                        simply_process = True

            if simply_process:
                if inline:
                    url = make_data_url(mime_type, path.read())
                else:
                    url = '%s%s' % (BASE_URL, filepath)
                    if cache_buster:
                        filetime = getmtime(asset_path)
                        url = add_cache_buster(url, filetime)
            else:
                width, height = collapse_x or image.size[0], collapse_y or image.size[1]
                new_image = Image.new(
                    mode='RGBA',
                    size=(width + spacing[1] + spacing[3], height + spacing[0] + spacing[2]),
                    color=(0, 0, 0, 0)
                )
                for i, dst_color in enumerate(dst_colors):
                    src_color = src_colors[i]
                    pixdata = image.load()
                    for _y in xrange(image.size[1]):
                        for _x in xrange(image.size[0]):
                            pixel = pixdata[_x, _y]
                            if pixel[:3] == src_color:
                                pixdata[_x, _y] = tuple([int(c) for c in dst_color] + [pixel[3] if len(pixel) == 4 else 255])
                iwidth, iheight = image.size
                if iwidth != width or iheight != height:
                    cy = 0
                    while cy < iheight:
                        cx = 0
                        while cx < iwidth:
                            cropped_image = image.crop((cx, cy, cx + width, cy + height))
                            new_image.paste(cropped_image, (int(spacing[3]), int(spacing[0])), cropped_image)
                            cx += width
                        cy += height
                else:
                    new_image.paste(image, (int(spacing[3]), int(spacing[0])))

                if not inline:
                    try:
                        new_image.save(asset_path)
                        filepath = asset_file
                        BASE_URL = config.ASSETS_URL
                        if cache_buster:
                            filetime = getmtime(asset_path)
                    except IOError:
                        log.exception("Error while saving image")
                        inline = True  # Retry inline version
                    url = os.path.join(config.ASSETS_URL.rstrip(os.sep), asset_file.lstrip(os.sep))
                    if cache_buster:
                        url = add_cache_buster(url, filetime)
                if inline:
                    output = six.BytesIO()
                    new_image.save(output, format='PNG')
                    contents = output.getvalue()
                    output.close()
                    url = make_data_url(mime_type, contents)
    else:
        url = os.path.join(BASE_URL.rstrip('/'), filepath.lstrip('\\/'))
        if cache_buster and filetime != 'NA':
            url = add_cache_buster(url, filetime)

    if not os.sep == '/':
        url = url.replace(os.sep, '/')

    if only_path:
        return String.unquoted(url)
    else:
        return Url.unquoted(url)


@ns.declare
def inline_image(image, mime_type=None, dst_color=None, src_color=None, spacing=None, collapse_x=None, collapse_y=None):
    """
    Embeds the contents of a file directly inside your stylesheet, eliminating
    the need for another HTTP request. For small files such images or fonts,
    this can be a performance benefit at the cost of a larger generated CSS
    file.
    """
    return _image_url(image, False, False, dst_color, src_color, True, mime_type, spacing, collapse_x, collapse_y)


@ns.declare
def image_url(path, only_path=False, cache_buster=True, dst_color=None, src_color=None, spacing=None, collapse_x=None, collapse_y=None):
    """
    Generates a path to an asset found relative to the project's images
    directory.
    Passing a true value as the second argument will cause the only the path to
    be returned instead of a `url()` function
    """
    return _image_url(path, only_path, cache_buster, dst_color, src_color, False, None, spacing, collapse_x, collapse_y)


@ns.declare
def image_width(image):
    """
    Returns the width of the image found at the path supplied by `image`
    relative to your project's images directory.
    """
    if not Image:
        raise SassMissingDependency('PIL', 'image manipulation')

    image_size_cache = _get_cache('image_size_cache')

    filepath = String.unquoted(image).value
    path = None
    try:
        width = image_size_cache[filepath][0]
    except KeyError:
        width = 0
        IMAGES_ROOT = _images_root()
        if callable(IMAGES_ROOT):
            try:
                _file, _storage = list(IMAGES_ROOT(filepath))[0]
            except IndexError:
                pass
            else:
                path = _storage.open(_file)
        else:
            _path = os.path.join(IMAGES_ROOT, filepath.strip(os.sep))
            if os.path.exists(_path):
                path = open(_path, 'rb')
        if path:
            image = Image.open(path)
            size = image.size
            width = size[0]
            image_size_cache[filepath] = size
    return Number(width, 'px')


@ns.declare
def image_height(image):
    """
    Returns the height of the image found at the path supplied by `image`
    relative to your project's images directory.
    """
    image_size_cache = _get_cache('image_size_cache')
    if not Image:
        raise SassMissingDependency('PIL', 'image manipulation')
    filepath = String.unquoted(image).value
    path = None
    try:
        height = image_size_cache[filepath][1]
    except KeyError:
        height = 0
        IMAGES_ROOT = _images_root()
        if callable(IMAGES_ROOT):
            try:
                _file, _storage = list(IMAGES_ROOT(filepath))[0]
            except IndexError:
                pass
            else:
                path = _storage.open(_file)
        else:
            _path = os.path.join(IMAGES_ROOT, filepath.strip(os.sep))
            if os.path.exists(_path):
                path = open(_path, 'rb')
        if path:
            image = Image.open(path)
            size = image.size
            height = size[1]
            image_size_cache[filepath] = size
    return Number(height, 'px')
