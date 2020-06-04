"""Miscellaneous helper functions ported from Compass.

See: http://compass-style.org/reference/compass/helpers/

This collection is not necessarily complete or up-to-date.
"""
from __future__ import absolute_import
from __future__ import unicode_literals

import logging
import math
import os.path

import six

from . import CompassExtension
from scss import config
from scss.types import Boolean, Function, List, Null, Number, String, Url
from scss.util import to_str, getmtime, make_data_url
import re

log = logging.getLogger(__name__)
ns = CompassExtension.namespace

FONT_TYPES = {
    'woff': 'woff',
    'otf': 'opentype',
    'opentype': 'opentype',
    'ttf': 'truetype',
    'truetype': 'truetype',
    'svg': 'svg',
    'eot': 'embedded-opentype'
}


def add_cache_buster(url, mtime):
    fragment = url.split('#')
    query = fragment[0].split('?')
    if len(query) > 1 and query[1] != '':
        cb = '&_=%s' % (mtime)
        url = '?'.join(query) + cb
    else:
        cb = '?_=%s' % (mtime)
        url = query[0] + cb
    if len(fragment) > 1:
        url += '#' + fragment[1]
    return url


# ------------------------------------------------------------------------------
# Data manipulation

@ns.declare
def blank(*objs):
    """Returns true when the object is false, an empty string, or an empty list"""
    for o in objs:
        if isinstance(o, Boolean):
            is_blank = not o
        elif isinstance(o, String):
            is_blank = not len(o.value.strip())
        elif isinstance(o, List):
            is_blank = all(blank(el) for el in o)
        else:
            is_blank = False

        if not is_blank:
            return Boolean(False)

    return Boolean(True)


@ns.declare
def compact(*args):
    """Returns a new list after removing any non-true values"""
    use_comma = True
    if len(args) == 1 and isinstance(args[0], List):
        use_comma = args[0].use_comma
        args = args[0]

    return List(
        [arg for arg in args if arg],
        use_comma=use_comma,
    )


@ns.declare
def reject(lst, *values):
    """Removes the given values from the list"""
    lst = List.from_maybe(lst)
    values = frozenset(List.from_maybe_starargs(values))

    ret = []
    for item in lst:
        if item not in values:
            ret.append(item)
    return List(ret, use_comma=lst.use_comma)


@ns.declare
def first_value_of(*args):
    if len(args) == 1 and isinstance(args[0], String):
        first = args[0].value.split()[0]
        return type(args[0])(first)

    args = List.from_maybe_starargs(args)
    if len(args):
        return args[0]
    else:
        return Null()


@ns.declare_alias('-compass-list')
def dash_compass_list(*args):
    return List.from_maybe_starargs(args)


@ns.declare_alias('-compass-space-list')
def dash_compass_space_list(*lst):
    """
    If the argument is a list, it will return a new list that is space delimited
    Otherwise it returns a new, single element, space-delimited list.
    """
    ret = dash_compass_list(*lst)
    ret.value.pop('_', None)
    return ret


@ns.declare_alias('-compass-slice')
def dash_compass_slice(lst, start_index, end_index=None):
    start_index = Number(start_index).value
    end_index = Number(end_index).value if end_index is not None else None
    ret = {}
    lst = List(lst)
    if end_index:
        # This function has an inclusive end, but Python slicing is exclusive
        end_index += 1
    ret = lst.value[start_index:end_index]
    return List(ret, use_comma=lst.use_comma)


# ------------------------------------------------------------------------------
# Property prefixing

@ns.declare
def prefixed(prefix, *args):
    to_fnct_str = 'to_' + to_str(prefix).replace('-', '_')
    for arg in List.from_maybe_starargs(args):
        if hasattr(arg, to_fnct_str):
            return Boolean(True)
    return Boolean(False)


@ns.declare
def prefix(prefix, *args):
    to_fnct_str = 'to_' + to_str(prefix).replace('-', '_')
    args = list(args)
    for i, arg in enumerate(args):
        if isinstance(arg, List):
            _value = []
            for iarg in arg:
                to_fnct = getattr(iarg, to_fnct_str, None)
                if to_fnct:
                    _value.append(to_fnct())
                else:
                    _value.append(iarg)
            args[i] = List(_value)
        else:
            to_fnct = getattr(arg, to_fnct_str, None)
            if to_fnct:
                args[i] = to_fnct()

    return List.maybe_new(args, use_comma=True)


@ns.declare_alias('-moz')
def dash_moz(*args):
    return prefix('_moz', *args)


@ns.declare_alias('-svg')
def dash_svg(*args):
    return prefix('_svg', *args)


@ns.declare_alias('-css2')
def dash_css2(*args):
    return prefix('_css2', *args)


@ns.declare_alias('-pie')
def dash_pie(*args):
    return prefix('_pie', *args)


@ns.declare_alias('-webkit')
def dash_webkit(*args):
    return prefix('_webkit', *args)


@ns.declare_alias('-owg')
def dash_owg(*args):
    return prefix('_owg', *args)


@ns.declare_alias('-khtml')
def dash_khtml(*args):
    return prefix('_khtml', *args)


@ns.declare_alias('-ms')
def dash_ms(*args):
    return prefix('_ms', *args)


@ns.declare_alias('-o')
def dash_o(*args):
    return prefix('_o', *args)


# ------------------------------------------------------------------------------
# Selector generation

@ns.declare
def append_selector(selector, to_append):
    if isinstance(selector, List):
        lst = selector.value
    else:
        lst = String.unquoted(selector).value.split(',')
    to_append = String.unquoted(to_append).value.strip()
    ret = sorted(set(s.strip() + to_append for s in lst if s.strip()))
    ret = dict(enumerate(ret))
    ret['_'] = ','
    return ret


_elements_of_type_block = 'address, article, aside, blockquote, center, dd, details, dir, div, dl, dt, fieldset, figcaption, figure, footer, form, frameset, h1, h2, h3, h4, h5, h6, header, hgroup, hr, isindex, menu, nav, noframes, noscript, ol, p, pre, section, summary, ul'
_elements_of_type_inline = 'a, abbr, acronym, audio, b, basefont, bdo, big, br, canvas, cite, code, command, datalist, dfn, em, embed, font, i, img, input, kbd, keygen, label, mark, meter, output, progress, q, rp, rt, ruby, s, samp, select, small, span, strike, strong, sub, sup, textarea, time, tt, u, var, video, wbr'
_elements_of_type_table = 'table'
_elements_of_type_list_item = 'li'
_elements_of_type_table_row_group = 'tbody'
_elements_of_type_table_header_group = 'thead'
_elements_of_type_table_footer_group = 'tfoot'
_elements_of_type_table_row = 'tr'
_elements_of_type_table_cel = 'td, th'
_elements_of_type_html5_block = 'article, aside, details, figcaption, figure, footer, header, hgroup, menu, nav, section, summary'
_elements_of_type_html5_inline = 'audio, canvas, command, datalist, embed, keygen, mark, meter, output, progress, rp, rt, ruby, time, video, wbr'
_elements_of_type_html5 = 'article, aside, audio, canvas, command, datalist, details, embed, figcaption, figure, footer, header, hgroup, keygen, mark, menu, meter, nav, output, progress, rp, rt, ruby, section, summary, time, video, wbr'
_elements_of_type = {
    'block': sorted(_elements_of_type_block.replace(' ', '').split(',')),
    'inline': sorted(_elements_of_type_inline.replace(' ', '').split(',')),
    'table': sorted(_elements_of_type_table.replace(' ', '').split(',')),
    'list-item': sorted(_elements_of_type_list_item.replace(' ', '').split(',')),
    'table-row-group': sorted(_elements_of_type_table_row_group.replace(' ', '').split(',')),
    'table-header-group': sorted(_elements_of_type_table_header_group.replace(' ', '').split(',')),
    'table-footer-group': sorted(_elements_of_type_table_footer_group.replace(' ', '').split(',')),
    'table-row': sorted(_elements_of_type_table_footer_group.replace(' ', '').split(',')),
    'table-cell': sorted(_elements_of_type_table_footer_group.replace(' ', '').split(',')),
    'html5-block': sorted(_elements_of_type_html5_block.replace(' ', '').split(',')),
    'html5-inline': sorted(_elements_of_type_html5_inline.replace(' ', '').split(',')),
    'html5': sorted(_elements_of_type_html5.replace(' ', '').split(',')),
}


@ns.declare
def elements_of_type(display):
    d = String.unquoted(display)
    ret = _elements_of_type.get(d.value, None)
    if ret is None:
        raise Exception("Elements of type '%s' not found!" % d.value)
    return List(map(String, ret), use_comma=True)


@ns.declare
def enumerate_(prefix, frm, through, separator='-'):
    separator = String.unquoted(separator).value
    try:
        frm = int(getattr(frm, 'value', frm))
    except ValueError:
        frm = 1
    try:
        through = int(getattr(through, 'value', through))
    except ValueError:
        through = frm
    if frm > through:
        # DEVIATION: allow reversed enumerations (and ranges as range() uses enumerate, like '@for .. from .. through')
        frm, through = through, frm
        rev = reversed
    else:
        rev = lambda x: x

    ret = []
    for i in rev(range(frm, through + 1)):
        if prefix and prefix.value:
            ret.append(String.unquoted(prefix.value + separator + six.text_type(i)))
        else:
            ret.append(Number(i))

    return List(ret, use_comma=True)


@ns.declare_alias('headings')
@ns.declare
def headers(frm=None, to=None):
    if frm and to is None:
        if isinstance(frm, String) and frm.value.lower() == 'all':
            frm = 1
            to = 6
        else:
            try:
                to = int(getattr(frm, 'value', frm))
            except ValueError:
                to = 6
            frm = 1
    else:
        try:
            frm = 1 if frm is None else int(getattr(frm, 'value', frm))
        except ValueError:
            frm = 1
        try:
            to = 6 if to is None else int(getattr(to, 'value', to))
        except ValueError:
            to = 6
    ret = [String.unquoted('h' + six.text_type(i)) for i in range(frm, to + 1)]
    return List(ret, use_comma=True)


@ns.declare
def nest(*arguments):
    if isinstance(arguments[0], List):
        lst = arguments[0]
    elif isinstance(arguments[0], String):
        lst = arguments[0].value.split(',')
    else:
        raise TypeError("Expected list or string, got %r" % (arguments[0],))

    ret = []
    for s in lst:
        if isinstance(s, String):
            s = s.value
        elif isinstance(s, six.string_types):
            s = s
        else:
            raise TypeError("Expected string, got %r" % (s,))

        s = s.strip()
        if not s:
            continue

        ret.append(s)

    for arg in arguments[1:]:
        if isinstance(arg, List):
            lst = arg
        elif isinstance(arg, String):
            lst = arg.value.split(',')
        else:
            raise TypeError("Expected list or string, got %r" % (arg,))

        new_ret = []
        for s in lst:
            if isinstance(s, String):
                s = s.value
            elif isinstance(s, six.string_types):
                s = s
            else:
                raise TypeError("Expected string, got %r" % (s,))

            s = s.strip()
            if not s:
                continue

            for r in ret:
                if '&' in s:
                    new_ret.append(s.replace('&', r))
                else:
                    if not r or r[-1] in ('.', ':', '#'):
                        new_ret.append(r + s)
                    else:
                        new_ret.append(r + ' ' + s)
        ret = new_ret

    ret = [String.unquoted(s) for s in sorted(set(ret))]
    return List(ret, use_comma=True)


# This isn't actually from Compass, but it's just a shortcut for enumerate().
# DEVIATION: allow reversed ranges (range() uses enumerate() which allows reversed values, like '@for .. from .. through')
@ns.declare
def range_(frm, through=None):
    if through is None:
        through = frm
        frm = 1
    return enumerate_(None, frm, through)

# ------------------------------------------------------------------------------
# Working with CSS constants

OPPOSITE_POSITIONS = {
    'top': String.unquoted('bottom'),
    'bottom': String.unquoted('top'),
    'left': String.unquoted('right'),
    'right': String.unquoted('left'),
    'center': String.unquoted('center'),
}
DEFAULT_POSITION = [String.unquoted('center'), String.unquoted('top')]


def _position(opposite, positions):
    if positions is None:
        positions = DEFAULT_POSITION
    else:
        positions = List.from_maybe(positions)

    ret = []
    for pos in positions:
        if isinstance(pos, (String, six.string_types)):
            pos_value = getattr(pos, 'value', pos)
            if pos_value in OPPOSITE_POSITIONS:
                if opposite:
                    ret.append(OPPOSITE_POSITIONS[pos_value])
                else:
                    ret.append(pos)
                continue
            elif pos_value == 'to':
                # Gradient syntax keyword; leave alone
                ret.append(pos)
                continue

        elif isinstance(pos, Number):
            if pos.is_simple_unit('%'):
                if opposite:
                    ret.append(Number(100 - pos.value, '%'))
                else:
                    ret.append(pos)
                continue
            elif pos.is_simple_unit('deg'):
                # TODO support other angle types?
                if opposite:
                    ret.append(Number((pos.value + 180) % 360, 'deg'))
                else:
                    ret.append(pos)
                continue

        if opposite:
            log.warn("Can't find opposite for position %r" % (pos,))
        ret.append(pos)

    return List(ret, use_comma=False).maybe()


@ns.declare
def position(p):
    return _position(False, p)


@ns.declare
def opposite_position(p):
    return _position(True, p)


# ------------------------------------------------------------------------------
# Math

@ns.declare
def pi():
    return Number(math.pi)


@ns.declare
def e():
    return Number(math.e)


@ns.declare
def log_(number, base=None):
    if not isinstance(number, Number):
        raise TypeError("Expected number, got %r" % (number,))
    elif not number.is_unitless:
        raise ValueError("Expected unitless number, got %r" % (number,))

    if base is None:
        pass
    elif not isinstance(base, Number):
        raise TypeError("Expected number, got %r" % (base,))
    elif not base.is_unitless:
        raise ValueError("Expected unitless number, got %r" % (base,))

    if base is None:
        ret = math.log(number.value)
    else:
        ret = math.log(number.value, base.value)

    return Number(ret)


@ns.declare
def pow(number, exponent):
    return number ** exponent


ns.set_function('sqrt', 1, Number.wrap_python_function(math.sqrt))
ns.set_function('sin', 1, Number.wrap_python_function(math.sin))
ns.set_function('cos', 1, Number.wrap_python_function(math.cos))
ns.set_function('tan', 1, Number.wrap_python_function(math.tan))


# ------------------------------------------------------------------------------
# Fonts

def _fonts_root():
    return config.STATIC_ROOT if config.FONTS_ROOT is None else config.FONTS_ROOT


def _font_url(path, only_path=False, cache_buster=True, inline=False):
    filepath = String.unquoted(path).value
    file = None
    FONTS_ROOT = _fonts_root()
    if callable(FONTS_ROOT):
        try:
            _file, _storage = list(FONTS_ROOT(filepath))[0]
        except IndexError:
            filetime = None
        else:
            filetime = getmtime(_file, _storage)
        if filetime is None:
            filetime = 'NA'
        elif inline:
            file = _storage.open(_file)
    else:
        _path = os.path.join(FONTS_ROOT, filepath.strip('/'))
        filetime = getmtime(_path)
        if filetime is None:
            filetime = 'NA'
        elif inline:
            file = open(_path, 'rb')

    BASE_URL = config.FONTS_URL or config.STATIC_URL
    if file and inline:
        font_type = None
        if re.match(r'^([^?]+)[.](.*)([?].*)?$', path.value):
            font_type = String.unquoted(re.match(r'^([^?]+)[.](.*)([?].*)?$', path.value).groups()[1]).value

        try:
            mime = FONT_TYPES[font_type]
        except KeyError:
            raise Exception('Could not determine font type for "%s"' % path.value)

        mime = FONT_TYPES.get(font_type)
        if font_type == 'woff':
            mime = 'application/font-woff'
        elif font_type == 'eot':
            mime = 'application/vnd.ms-fontobject'
        url = make_data_url(
            (mime if '/' in mime else 'font/%s' % mime),
            file.read())
        file.close()
    else:
        url = '%s/%s' % (BASE_URL.rstrip('/'), filepath.lstrip('/'))
        if cache_buster and filetime != 'NA':
            url = add_cache_buster(url, filetime)

    if only_path:
        return String.unquoted(url)
    else:
        return Url.unquoted(url)


def _font_files(args, inline):
    if args == ():
        return String.unquoted("")

    fonts = []
    args_len = len(args)
    skip_next = False
    for index, arg in enumerate(args):
        if not skip_next:
            font_type = args[index + 1] if args_len > (index + 1) else None
            if font_type and font_type.value in FONT_TYPES:
                skip_next = True
            else:
                if re.match(r'^([^?]+)[.](.*)([?].*)?$', arg.value):
                    font_type = String.unquoted(re.match(r'^([^?]+)[.](.*)([?].*)?$', arg.value).groups()[1])

            if font_type.value in FONT_TYPES:
                fonts.append(List([
                    _font_url(arg, inline=inline),
                    Function(FONT_TYPES[font_type.value], 'format'),
                ], use_comma=False))
            else:
                raise Exception('Could not determine font type for "%s"' % arg.value)
        else:
            skip_next = False

    return List(fonts, separator=',')


@ns.declare
def font_url(path, only_path=False, cache_buster=True):
    """
    Generates a path to an asset found relative to the project's font directory.
    Passing a true value as the second argument will cause the only the path to
    be returned instead of a `url()` function
    """
    return _font_url(path, only_path, cache_buster, False)


@ns.declare
def font_files(*args):
    return _font_files(args, inline=False)


@ns.declare
def inline_font_files(*args):
    return _font_files(args, inline=True)


# ------------------------------------------------------------------------------
# External stylesheets

@ns.declare
def stylesheet_url(path, only_path=False, cache_buster=True):
    """
    Generates a path to an asset found relative to the project's css directory.
    Passing a true value as the second argument will cause the only the path to
    be returned instead of a `url()` function
    """
    filepath = String.unquoted(path).value
    if callable(config.STATIC_ROOT):
        try:
            _file, _storage = list(config.STATIC_ROOT(filepath))[0]
        except IndexError:
            filetime = None
        else:
            filetime = getmtime(_file, _storage)
        if filetime is None:
            filetime = 'NA'
    else:
        _path = os.path.join(config.STATIC_ROOT, filepath.strip('/'))
        filetime = getmtime(_path)
        if filetime is None:
            filetime = 'NA'
    BASE_URL = config.STATIC_URL

    url = '%s%s' % (BASE_URL, filepath)
    if cache_buster:
        url = add_cache_buster(url, filetime)
    if only_path:
        return String.unquoted(url)
    else:
        return Url.unquoted(url)
