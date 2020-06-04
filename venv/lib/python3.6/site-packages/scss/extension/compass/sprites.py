"""Functions used for generating CSS sprites.

These are ported from the Compass sprite library:
http://compass-style.org/reference/compass/utilities/sprites/
"""
from __future__ import absolute_import
from __future__ import unicode_literals

import six

import glob
import logging
import os.path
import tempfile
import time
import sys

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    from PIL import Image
except ImportError:
    try:
        import Image
    except:
        Image = None

from six.moves import xrange

from . import CompassExtension
from .layouts import PackedSpritesLayout, HorizontalSpritesLayout, VerticalSpritesLayout, DiagonalSpritesLayout
from scss import config
from scss.errors import SassMissingDependency
from scss.types import Color, List, Number, String, Boolean
from scss.util import escape, getmtime, make_data_url, make_filename_hash
from scss.extension import Cache

log = logging.getLogger(__name__)
ns = CompassExtension.namespace

MAX_SPRITE_MAPS = 4096
KEEP_SPRITE_MAPS = int(MAX_SPRITE_MAPS * 0.8)


def _assets_root():
    return config.ASSETS_ROOT or os.path.join(config.STATIC_ROOT, 'assets')


def _get_cache(prefix):
    return Cache((config.CACHE_ROOT or _assets_root(), prefix))


# ------------------------------------------------------------------------------
# Compass-like functionality for sprites and images

def alpha_composite(im1, im2, offset=None, box=None, opacity=1):
    im1size = im1.size
    im2size = im2.size
    if offset is None:
        offset = (0, 0)
    if box is None:
        box = (0, 0) + im2size
    o1x, o1y = offset
    o2x, o2y, o2w, o2h = box
    width = o2w - o2x
    height = o2h - o2y
    im1_data = im1.load()
    im2_data = im2.load()
    for y in xrange(height):
        for x in xrange(width):
            pos1 = o1x + x, o1y + y
            if pos1[0] >= im1size[0] or pos1[1] >= im1size[1]:
                continue
            pos2 = o2x + x, o2y + y
            if pos2[0] >= im2size[0] or pos2[1] >= im2size[1]:
                continue
            dr, dg, db, da = im1_data[pos1]
            sr, sg, sb, sa = im2_data[pos2]
            da /= 255.0
            sa /= 255.0
            sa *= opacity
            ida = da * (1 - sa)
            oa = (sa + ida)
            if oa:
                pixel = (
                    int(round((sr * sa + dr * ida)) / oa),
                    int(round((sg * sa + dg * ida)) / oa),
                    int(round((sb * sa + db * ida)) / oa),
                    int(round(255 * oa))
                )
            else:
                pixel = (0, 0, 0, 0)
            im1_data[pos1] = pixel
    return im1


@ns.declare
def sprite_map(g, **kwargs):
    """
    Generates a sprite map from the files matching the glob pattern.
    Uses the keyword-style arguments passed in to control the placement.

    $direction - Sprite map layout. Can be `vertical` (default), `horizontal`, `diagonal` or `smart`.

    $position - For `horizontal` and `vertical` directions, the position of the sprite. (defaults to `0`)
    $<sprite>-position - Position of a given sprite.

    $padding, $spacing - Adds paddings to sprites (top, right, bottom, left). (defaults to `0, 0, 0, 0`)
    $<sprite>-padding, $<sprite>-spacing - Padding for a given sprite.

    $dst-color - Together with `$src-color`, forms a map of source colors to be converted to destiny colors (same index of `$src-color` changed to `$dst-color`).
    $<sprite>-dst-color - Destiny colors for a given sprite. (defaults to `$dst-color`)

    $src-color - Selects source colors to be converted to the corresponding destiny colors. (defaults to `black`)
    $<sprite>-dst-color - Source colors for a given sprite. (defaults to `$src-color`)

    $collapse - Collapses every image in the sprite map to a fixed size (`x` and `y`).
    $collapse-x  - Collapses a size for `x`.
    $collapse-y  - Collapses a size for `y`.
    """
    if not Image:
        raise SassMissingDependency('PIL', 'image manipulation')

    sprite_maps = _get_cache('sprite_maps')

    now_time = time.time()

    globs = String(g, quotes=None).value
    globs = sorted(g.strip() for g in globs.split(','))

    _k_ = ','.join(globs)

    files = None
    rfiles = None
    tfiles = None
    map_name = None

    if _k_ in sprite_maps:
        sprite_maps[_k_]['*'] = now_time
    else:
        files = []
        rfiles = []
        tfiles = []
        for _glob in globs:
            if '..' not in _glob:  # Protect against going to prohibited places...
                if callable(config.STATIC_ROOT):
                    _glob_path = _glob
                    _rfiles = _files = sorted(config.STATIC_ROOT(_glob))
                else:
                    _glob_path = os.path.join(config.STATIC_ROOT, _glob)
                    _files = glob.glob(_glob_path)
                    _files = sorted((f, None) for f in _files)
                    _rfiles = [(rf[len(config.STATIC_ROOT):], s) for rf, s in _files]
                if _files:
                    files.extend(_files)
                    rfiles.extend(_rfiles)
                    base_name = os.path.normpath(os.path.dirname(_glob)).replace('\\', '_').replace('/', '_')
                    _map_name, _, _map_type = base_name.partition('.')
                    if _map_type:
                        _map_type += '-'
                    if not map_name:
                        map_name = _map_name
                    tfiles.extend([_map_type] * len(_files))
                else:
                    glob_path = _glob_path

    if files is not None:
        if not files:
            log.error("Nothing found at '%s'", glob_path)
            return String.unquoted('')

        key = [f for (f, s) in files] + [repr(kwargs), config.ASSETS_URL]
        key = map_name + '-' + make_filename_hash(key)
        asset_file = key + '.png'
        ASSETS_ROOT = _assets_root()
        asset_path = os.path.join(ASSETS_ROOT, asset_file)
        cache_path = os.path.join(config.CACHE_ROOT or ASSETS_ROOT, asset_file + '.cache')

        inline = Boolean(kwargs.get('inline', False))

        sprite_map = None
        asset = None
        file_asset = None
        inline_asset = None
        if os.path.exists(asset_path) or inline:
            try:
                save_time, file_asset, inline_asset, sprite_map, sizes = pickle.load(open(cache_path))
                if file_asset:
                    sprite_maps[file_asset.render()] = sprite_map
                if inline_asset:
                    sprite_maps[inline_asset.render()] = sprite_map
                if inline:
                    asset = inline_asset
                else:
                    asset = file_asset
            except:
                pass

            if sprite_map:
                for file_, storage in files:
                    _time = getmtime(file_, storage)
                    if save_time < _time:
                        if _time > now_time:
                            log.warning("File '%s' has a date in the future (cache ignored)" % file_)
                        sprite_map = None  # Invalidate cached sprite map
                        break

        if sprite_map is None or asset is None:
            cache_buster = Boolean(kwargs.get('cache_buster', True))
            direction = String.unquoted(kwargs.get('direction', config.SPRTE_MAP_DIRECTION)).value
            repeat = String.unquoted(kwargs.get('repeat', 'no-repeat')).value
            collapse = kwargs.get('collapse', Number(0))
            if isinstance(collapse, List):
                collapse_x = int(Number(collapse[0]).value)
                collapse_y = int(Number(collapse[-1]).value)
            else:
                collapse_x = collapse_y = int(Number(collapse).value)
            if 'collapse_x' in kwargs:
                collapse_x = int(Number(kwargs['collapse_x']).value)
            if 'collapse_y' in kwargs:
                collapse_y = int(Number(kwargs['collapse_y']).value)

            position = Number(kwargs.get('position', 0))
            if not position.is_simple_unit('%') and position.value > 1:
                position = position.value / 100.0
            else:
                position = position.value
            if position < 0:
                position = 0.0
            elif position > 1:
                position = 1.0

            padding = kwargs.get('padding', kwargs.get('spacing', Number(0)))
            padding = [int(Number(v).value) for v in List.from_maybe(padding)]
            padding = (padding * 4)[:4]

            dst_colors = kwargs.get('dst_color')
            dst_colors = [list(Color(v).value[:3]) for v in List.from_maybe(dst_colors) if v]
            src_colors = kwargs.get('src_color', Color.from_name('black'))
            src_colors = [tuple(Color(v).value[:3]) for v in List.from_maybe(src_colors)]
            len_colors = max(len(dst_colors), len(src_colors))
            dst_colors = (dst_colors * len_colors)[:len_colors]
            src_colors = (src_colors * len_colors)[:len_colors]

            def images(f=lambda x: x):
                for file_, storage in f(files):
                    if storage is not None:
                        _file = storage.open(file_)
                    else:
                        _file = file_
                    _image = Image.open(_file)
                    yield _image

            names = tuple(os.path.splitext(os.path.basename(file_))[0] for file_, storage in files)
            tnames = tuple(tfiles[i] + n for i, n in enumerate(names))

            has_dst_colors = False
            all_dst_colors = []
            all_src_colors = []
            all_positions = []
            all_paddings = []

            for name in names:
                name = name.replace('-', '_')

                _position = kwargs.get(name + '_position')
                if _position is None:
                    _position = position
                else:
                    _position = Number(_position)
                    if not _position.is_simple_unit('%') and _position.value > 1:
                        _position = _position.value / 100.0
                    else:
                        _position = _position.value
                    if _position < 0:
                        _position = 0.0
                    elif _position > 1:
                        _position = 1.0
                all_positions.append(_position)

                _padding = kwargs.get(name + '_padding', kwargs.get(name + '_spacing'))
                if _padding is None:
                    _padding = padding
                else:
                    _padding = [int(Number(v).value) for v in List.from_maybe(_padding)]
                    _padding = (_padding * 4)[:4]
                all_paddings.append(_padding)

                _dst_colors = kwargs.get(name + '_dst_color')
                if _dst_colors is None:
                    _dst_colors = dst_colors
                    if dst_colors:
                        has_dst_colors = True
                else:
                    has_dst_colors = True
                    _dst_colors = [list(Color(v).value[:3]) for v in List.from_maybe(_dst_colors) if v]
                _src_colors = kwargs.get(name + '_src_color', Color.from_name('black'))
                if _src_colors is None:
                    _src_colors = src_colors
                else:
                    _src_colors = [tuple(Color(v).value[:3]) for v in List.from_maybe(_src_colors)]
                _len_colors = max(len(_dst_colors), len(_src_colors))
                _dst_colors = (_dst_colors * _len_colors)[:_len_colors]
                _src_colors = (_src_colors * _len_colors)[:_len_colors]
                all_dst_colors.append(_dst_colors)
                all_src_colors.append(_src_colors)

            sizes = tuple((collapse_x or i.size[0], collapse_y or i.size[1]) for i in images())

            if direction == 'horizontal':
                layout = HorizontalSpritesLayout(sizes, all_paddings, position=all_positions)
            elif direction == 'vertical':
                layout = VerticalSpritesLayout(sizes, all_paddings, position=all_positions)
            elif direction == 'diagonal':
                layout = DiagonalSpritesLayout(sizes, all_paddings)
            elif direction == 'smart':
                layout = PackedSpritesLayout(sizes, all_paddings)
            else:
                raise Exception("Invalid direction %r" % (direction,))
            layout_positions = list(layout)

            new_image = Image.new(
                mode='RGBA',
                size=(layout.width, layout.height),
                color=(0, 0, 0, 0)
            )

            useless_dst_color = has_dst_colors

            offsets_x = []
            offsets_y = []
            for i, image in enumerate(images()):
                x, y, width, height, cssx, cssy, cssw, cssh = layout_positions[i]
                iwidth, iheight = image.size

                if has_dst_colors:
                    pixdata = image.load()
                    for _y in xrange(iheight):
                        for _x in xrange(iwidth):
                            pixel = pixdata[_x, _y]
                            a = pixel[3] if len(pixel) == 4 else 255
                            if a:
                                rgb = pixel[:3]
                                for j, dst_color in enumerate(all_dst_colors[i]):
                                    if rgb == all_src_colors[i][j]:
                                        new_color = tuple([int(c) for c in dst_color] + [a])
                                        if pixel != new_color:
                                            pixdata[_x, _y] = new_color
                                            useless_dst_color = False
                                        break

                if iwidth != width or iheight != height:
                    cy = 0
                    while cy < iheight:
                        cx = 0
                        while cx < iwidth:
                            new_image = alpha_composite(new_image, image, (x, y), (cx, cy, cx + width, cy + height))
                            cx += width
                        cy += height
                else:
                    new_image.paste(image, (x, y))
                offsets_x.append(cssx)
                offsets_y.append(cssy)

            if useless_dst_color:
                log.warning("Useless use of $dst-color in sprite map for files at '%s' (never used for)" % glob_path)

            filetime = int(now_time)

            if not inline:
                try:
                    new_image.save(asset_path)
                    url = '%s%s' % (config.ASSETS_URL, asset_file)
                    if cache_buster:
                        url += '?_=%s' % filetime
                except IOError:
                    log.exception("Error while saving image")
                    inline = True
            if inline:
                output = six.BytesIO()
                new_image.save(output, format='PNG')
                contents = output.getvalue()
                output.close()
                mime_type = 'image/png'
                url = make_data_url(mime_type, contents)

            url = 'url(%s)' % escape(url)
            if inline:
                asset = inline_asset = List([String.unquoted(url), String.unquoted(repeat)])
            else:
                asset = file_asset = List([String.unquoted(url), String.unquoted(repeat)])

            # Add the new object:
            sprite_map = dict(zip(tnames, zip(sizes, rfiles, offsets_x, offsets_y)))
            sprite_map['*'] = now_time
            sprite_map['*f*'] = asset_file
            sprite_map['*k*'] = key
            sprite_map['*n*'] = map_name
            sprite_map['*t*'] = filetime

            sizes = zip(files, sizes)
            cache_tmp = tempfile.NamedTemporaryFile(delete=False, dir=ASSETS_ROOT)
            pickle.dump((now_time, file_asset, inline_asset, sprite_map, sizes), cache_tmp)
            cache_tmp.close()
            if sys.platform == 'win32' and os.path.isfile(cache_path):
                # on windows, cannot rename a file to a path that matches
                # an existing file, we have to remove it first
                os.remove(cache_path)
            os.rename(cache_tmp.name, cache_path)

            # Use the sorted list to remove older elements (keep only 500 objects):
            if len(sprite_maps) > MAX_SPRITE_MAPS:
                for a in sorted(sprite_maps, key=lambda a: sprite_maps[a]['*'], reverse=True)[KEEP_SPRITE_MAPS:]:
                    del sprite_maps[a]
                log.warning("Exceeded maximum number of sprite maps (%s)" % MAX_SPRITE_MAPS)
            sprite_maps[asset.render()] = sprite_map
        image_size_cache = _get_cache('image_size_cache')
        for file_, size in sizes:
            image_size_cache[file_] = size
    # TODO this sometimes returns an empty list, or is never assigned to
    return asset


@ns.declare
def sprite_map_name(map):
    """
    Returns the name of a sprite map The name is derived from the folder than
    contains the sprites.
    """
    map = map.render()
    sprite_maps = _get_cache('sprite_maps')
    sprite_map = sprite_maps.get(map)
    if not sprite_map:
        log.error("No sprite map found: %s", map, extra={'stack': True})
    if sprite_map:
        return String.unquoted(sprite_map['*n*'])
    return String.unquoted('')


@ns.declare
def sprite_file(map, sprite):
    """
    Returns the relative path (from the images directory) to the original file
    used when construction the sprite. This is suitable for passing to the
    image_width and image_height helpers.
    """
    map = map.render()
    sprite_maps = _get_cache('sprite_maps')
    sprite_map = sprite_maps.get(map)
    sprite_name = String.unquoted(sprite).value
    sprite = sprite_map and sprite_map.get(sprite_name)
    if not sprite_map:
        log.error("No sprite map found: %s", map, extra={'stack': True})
    elif not sprite:
        log.error("No sprite found: %s in %s", sprite_name, sprite_map['*n*'], extra={'stack': True})
    if sprite:
        return String(sprite[1][0])
    return String.unquoted('')


@ns.declare_alias('sprite-names')
@ns.declare
def sprites(map, remove_suffix=False):
    map = map.render()
    sprite_maps = _get_cache('sprite_maps')
    sprite_map = sprite_maps.get(map, {})
    return List([String.unquoted(s) for s in sorted(set(s.rsplit('-', 1)[0] if remove_suffix else s for s in sprite_map if not s.startswith('*')))])


@ns.declare
def sprite_classes(map):
    return sprites(map, True)


@ns.declare
def sprite(map, sprite, offset_x=None, offset_y=None, cache_buster=True):
    """
    Returns the image and background position for use in a single shorthand
    property
    """
    map = map.render()
    sprite_maps = _get_cache('sprite_maps')
    sprite_map = sprite_maps.get(map)
    sprite_name = String.unquoted(sprite).value
    sprite = sprite_map and sprite_map.get(sprite_name)
    if not sprite_map:
        log.error("No sprite map found: %s", map, extra={'stack': True})
    elif not sprite:
        log.error("No sprite found: %s in %s", sprite_name, sprite_map['*n*'], extra={'stack': True})
    if sprite:
        url = '%s%s' % (config.ASSETS_URL, sprite_map['*f*'])
        if cache_buster:
            url += '?_=%s' % sprite_map['*t*']
        x = Number(offset_x or 0, 'px')
        y = Number(offset_y or 0, 'px')
        if not x.value or (x.value <= -1 or x.value >= 1) and not x.is_simple_unit('%'):
            x -= Number(sprite[2], 'px')
        if not y.value or (y.value <= -1 or y.value >= 1) and not y.is_simple_unit('%'):
            y -= Number(sprite[3], 'px')
        url = "url(%s)" % escape(url)
        return List([String.unquoted(url), x, y])
    return List([Number(0), Number(0)])


@ns.declare
def sprite_url(map, cache_buster=True):
    """
    Returns a url to the sprite image.
    """
    map = map.render()
    sprite_maps = _get_cache('sprite_maps')
    sprite_map = sprite_maps.get(map)
    if not sprite_map:
        log.error("No sprite map found: %s", map, extra={'stack': True})
    if sprite_map:
        url = '%s%s' % (config.ASSETS_URL, sprite_map['*f*'])
        if cache_buster:
            url += '?_=%s' % sprite_map['*t*']
        url = "url(%s)" % escape(url)
        return String.unquoted(url)
    return String.unquoted('')


@ns.declare
def has_sprite(map, sprite):
    map = map.render()
    sprite_maps = _get_cache('sprite_maps')
    sprite_map = sprite_maps.get(map)
    sprite_name = String.unquoted(sprite).value
    sprite = sprite_map and sprite_map.get(sprite_name)
    if not sprite_map:
        log.error("No sprite map found: %s", map, extra={'stack': True})
    return Boolean(bool(sprite))


@ns.declare
def sprite_position(map, sprite, offset_x=None, offset_y=None):
    """
    Returns the position for the original image in the sprite.
    This is suitable for use as a value to background-position.
    """
    map = map.render()
    sprite_maps = _get_cache('sprite_maps')
    sprite_map = sprite_maps.get(map)
    sprite_name = String.unquoted(sprite).value
    sprite = sprite_map and sprite_map.get(sprite_name)
    if not sprite_map:
        log.error("No sprite map found: %s", map, extra={'stack': True})
    elif not sprite:
        log.error("No sprite found: %s in %s", sprite_name, sprite_map['*n*'], extra={'stack': True})
    if sprite:
        x = None
        if offset_x is not None and not isinstance(offset_x, Number):
            x = offset_x
        if not x or x.value not in ('left', 'right', 'center'):
            if x:
                offset_x = None
            x = Number(offset_x or 0, 'px')
            if not x.value or (x.value <= -1 or x.value >= 1) and not x.is_simple_unit('%'):
                x -= Number(sprite[2], 'px')
        y = None
        if offset_y is not None and not isinstance(offset_y, Number):
            y = offset_y
        if not y or y.value not in ('top', 'bottom', 'center'):
            if y:
                offset_y = None
            y = Number(offset_y or 0, 'px')
            if not y.value or (y.value <= -1 or y.value >= 1) and not y.is_simple_unit('%'):
                y -= Number(sprite[3], 'px')
        return List([x, y])
    return List([Number(0), Number(0)])
