"""Extension for built-in Sass functionality."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from itertools import product
import math
import os.path
from pathlib import PurePosixPath

from six.moves import xrange

from scss.extension import Extension
from scss.namespace import Namespace
from scss.source import SourceFile
from scss.types import (
    Arglist, Boolean, Color, List, Null, Number, String, Map, expect_type)


class CoreExtension(Extension):
    name = 'core'
    namespace = Namespace()

    def handle_import(self, name, compilation, rule):
        """Implementation of the core Sass import mechanism, which just looks
        for files on disk.
        """
        # TODO this is all not terribly well-specified by Sass.  at worst,
        # it's unclear how far "upwards" we should be allowed to go.  but i'm
        # also a little fuzzy on e.g. how relative imports work from within a
        # file that's not actually in the search path.
        # TODO i think with the new origin semantics, i've made it possible to
        # import relative to the current file even if the current file isn't
        # anywhere in the search path.  is that right?
        path = PurePosixPath(name)

        search_exts = list(compilation.compiler.dynamic_extensions)
        if path.suffix and path.suffix in search_exts:
            basename = path.stem
        else:
            basename = path.name
        relative_to = path.parent
        search_path = []  # tuple of (origin, start_from)
        if relative_to.is_absolute():
            relative_to = PurePosixPath(*relative_to.parts[1:])
        elif rule.source_file.origin:
            # Search relative to the current file first, only if not doing an
            # absolute import
            search_path.append((
                rule.source_file.origin,
                rule.source_file.relpath.parent / relative_to,
            ))
        search_path.extend(
            (origin, relative_to)
            for origin in compilation.compiler.search_path
        )

        for prefix, suffix in product(('_', ''), search_exts):
            filename = prefix + basename + suffix
            for origin, relative_to in search_path:
                relpath = relative_to / filename
                # Lexically (ignoring symlinks!) eliminate .. from the part
                # of the path that exists within Sass-space.  pathlib
                # deliberately doesn't do this, but os.path does.
                relpath = PurePosixPath(os.path.normpath(str(relpath)))

                if rule.source_file.key == (origin, relpath):
                    # Avoid self-import
                    # TODO is this what ruby does?
                    continue

                path = origin / relpath
                if not path.exists():
                    continue

                # All good!
                # TODO if this file has already been imported, we'll do the
                # source preparation twice.  make it lazy.
                return SourceFile.read(origin, relpath)


# Alias to make the below declarations less noisy
ns = CoreExtension.namespace


# ------------------------------------------------------------------------------
# Color creation

def _interpret_percentage(n, relto=1., clamp=True):
    expect_type(n, Number, unit='%')

    if n.is_unitless:
        ret = n.value / relto
    else:
        ret = n.value / 100

    if clamp:
        if ret < 0:
            return 0
        elif ret > 1:
            return 1

    return ret


@ns.declare
def rgba(r, g, b, a):
    r = _interpret_percentage(r, relto=255)
    g = _interpret_percentage(g, relto=255)
    b = _interpret_percentage(b, relto=255)
    a = _interpret_percentage(a, relto=1)

    return Color.from_rgb(r, g, b, a)


@ns.declare
def rgb(r, g, b, type='rgb'):
    return rgba(r, g, b, Number(1.0))


@ns.declare
def rgba_(color, a=None):
    if a is None:
        alpha = 1
    else:
        alpha = _interpret_percentage(a)

    return Color.from_rgb(*color.rgba[:3], alpha=alpha)


@ns.declare
def rgb_(color):
    return rgba_(color, a=Number(1))


@ns.declare
def hsla(h, s, l, a):
    return Color.from_hsl(
        h.value / 360 % 1,
        # Ruby sass treats plain numbers for saturation and lightness as though
        # they were percentages, just without the %
        _interpret_percentage(s, relto=100),
        _interpret_percentage(l, relto=100),
        alpha=a.value,
    )


@ns.declare
def hsl(h, s, l):
    return hsla(h, s, l, Number(1))


@ns.declare
def hsla_(color, a=None):
    return rgba_(color, a)


@ns.declare
def hsl_(color):
    return rgba_(color, a=Number(1))


@ns.declare
def mix(color1, color2, weight=Number(50, "%")):
    """
    Mixes together two colors. Specifically, takes the average of each of the
    RGB components, optionally weighted by the given percentage.
    The opacity of the colors is also considered when weighting the components.

    Specifically, takes the average of each of the RGB components,
    optionally weighted by the given percentage.
    The opacity of the colors is also considered when weighting the components.

    The weight specifies the amount of the first color that should be included
    in the returned color.
    50%, means that half the first color
        and half the second color should be used.
    25% means that a quarter of the first color
        and three quarters of the second color should be used.

    For example:

        mix(#f00, #00f) => #7f007f
        mix(#f00, #00f, 25%) => #3f00bf
        mix(rgba(255, 0, 0, 0.5), #00f) => rgba(63, 0, 191, 0.75)
    """
    # This algorithm factors in both the user-provided weight
    # and the difference between the alpha values of the two colors
    # to decide how to perform the weighted average of the two RGB values.
    #
    # It works by first normalizing both parameters to be within [-1, 1],
    # where 1 indicates "only use color1", -1 indicates "only use color 0",
    # and all values in between indicated a proportionately weighted average.
    #
    # Once we have the normalized variables w and a,
    # we apply the formula (w + a)/(1 + w*a)
    # to get the combined weight (in [-1, 1]) of color1.
    # This formula has two especially nice properties:
    #
    #   * When either w or a are -1 or 1, the combined weight is also that
    #     number (cases where w * a == -1 are undefined, and handled as a
    #     special case).
    #
    #   * When a is 0, the combined weight is w, and vice versa
    #
    # Finally, the weight of color1 is renormalized to be within [0, 1]
    # and the weight of color2 is given by 1 minus the weight of color1.
    #
    # Algorithm from the Sass project: http://sass-lang.com/

    p = _interpret_percentage(weight)

    # Scale weight to [-1, 1]
    w = p * 2 - 1
    # Compute difference in alpha channels
    a = color1.alpha - color2.alpha

    # Weight of first color
    if w * a == -1:
        # Avoid zero-div case
        scaled_weight1 = w
    else:
        scaled_weight1 = (w + a) / (1 + w * a)

    # Unscale back to [0, 1] and get the weight of the other color
    w1 = (scaled_weight1 + 1) / 2
    w2 = 1 - w1

    # Do the scaling.  Note that alpha isn't scaled by alpha, as that wouldn't
    # make much sense; it uses the original untwiddled weight, p.
    channels = [
        ch1 * w1 + ch2 * w2
        for (ch1, ch2) in zip(color1.rgba[:3], color2.rgba[:3])]
    alpha = color1.alpha * p + color2.alpha * (1 - p)
    return Color.from_rgb(*channels, alpha=alpha)


# ------------------------------------------------------------------------------
# Color inspection

@ns.declare
def red(color):
    r, g, b, a = color.rgba
    return Number(r * 255)


@ns.declare
def green(color):
    r, g, b, a = color.rgba
    return Number(g * 255)


@ns.declare
def blue(color):
    r, g, b, a = color.rgba
    return Number(b * 255)


@ns.declare_alias('opacity')
@ns.declare
def alpha(color):
    return Number(color.alpha)


@ns.declare
def hue(color):
    h, s, l = color.hsl
    return Number(h * 360, "deg")


@ns.declare
def saturation(color):
    h, s, l = color.hsl
    return Number(s * 100, "%")


@ns.declare
def lightness(color):
    h, s, l = color.hsl
    return Number(l * 100, "%")


@ns.declare
def ie_hex_str(color):
    c = Color(color).value
    return String("#{3:02X}{0:02X}{1:02X}{2:02X}".format(
        int(round(c[0])),
        int(round(c[1])),
        int(round(c[2])),
        int(round(c[3] * 255)),
    ))


# ------------------------------------------------------------------------------
# Color modification

@ns.declare_alias('fade-in')
@ns.declare_alias('fadein')
@ns.declare
def opacify(color, amount):
    r, g, b, a = color.rgba
    if amount.is_simple_unit('%'):
        amt = amount.value / 100
    else:
        amt = amount.value
    return Color.from_rgb(
        r, g, b,
        alpha=a + amt)


@ns.declare_alias('fade-out')
@ns.declare_alias('fadeout')
@ns.declare
def transparentize(color, amount):
    r, g, b, a = color.rgba
    if amount.is_simple_unit('%'):
        amt = amount.value / 100
    else:
        amt = amount.value
    return Color.from_rgb(
        r, g, b,
        alpha=a - amt)


@ns.declare
def lighten(color, amount):
    return adjust_color(color, lightness=amount)


@ns.declare
def darken(color, amount):
    return adjust_color(color, lightness=-amount)


@ns.declare
def saturate(color, amount):
    return adjust_color(color, saturation=amount)


@ns.declare
def desaturate(color, amount):
    return adjust_color(color, saturation=-amount)


@ns.declare
def greyscale(color):
    h, s, l = color.hsl
    return Color.from_hsl(h, 0, l, alpha=color.alpha)


@ns.declare
def grayscale(color):
    if isinstance(color, Number):
        # grayscale(n) and grayscale(n%) are CSS3 filters and should be left
        # intact, but only when using the "a" spelling
        return String.unquoted("grayscale(%s)" % (color.render(),))
    else:
        return greyscale(color)


@ns.declare_alias('spin')
@ns.declare
def adjust_hue(color, degrees):
    h, s, l = color.hsl
    delta = degrees.value / 360
    return Color.from_hsl((h + delta) % 1, s, l, alpha=color.alpha)


@ns.declare
def complement(color):
    h, s, l = color.hsl
    return Color.from_hsl((h + 0.5) % 1, s, l, alpha=color.alpha)


@ns.declare
def invert(color):
    """Returns the inverse (negative) of a color.  The red, green, and blue
    values are inverted, while the opacity is left alone.
    """
    if isinstance(color, Number):
        # invert(n) and invert(n%) are CSS3 filters and should be left
        # intact
        return String.unquoted("invert(%s)" % (color.render(),))

    expect_type(color, Color)
    r, g, b, a = color.rgba
    return Color.from_rgb(1 - r, 1 - g, 1 - b, alpha=a)


@ns.declare
def adjust_lightness(color, amount):
    return adjust_color(color, lightness=amount)


@ns.declare
def adjust_saturation(color, amount):
    return adjust_color(color, saturation=amount)


@ns.declare
def scale_lightness(color, amount):
    return scale_color(color, lightness=amount)


@ns.declare
def scale_saturation(color, amount):
    return scale_color(color, saturation=amount)


@ns.declare
def adjust_color(
        color, red=None, green=None, blue=None,
        hue=None, saturation=None, lightness=None, alpha=None):
    do_rgb = red or green or blue
    do_hsl = hue or saturation or lightness
    if do_rgb and do_hsl:
        raise ValueError(
            "Can't adjust both RGB and HSL channels at the same time")

    zero = Number(0)
    a = color.alpha + (alpha or zero).value

    if do_rgb:
        r, g, b = color.rgba[:3]
        channels = [
            current + (adjustment or zero).value / 255
            for (current, adjustment) in zip(color.rgba, (red, green, blue))]
        return Color.from_rgb(*channels, alpha=a)

    else:
        h, s, l = color.hsl
        h = (h + (hue or zero).value / 360) % 1
        s += _interpret_percentage(saturation or zero, relto=100, clamp=False)
        l += _interpret_percentage(lightness or zero, relto=100, clamp=False)
        return Color.from_hsl(h, s, l, a)


def _scale_channel(channel, scaleby):
    if scaleby is None:
        return channel

    expect_type(scaleby, Number)
    if not scaleby.is_simple_unit('%'):
        raise ValueError("Expected percentage, got %r" % (scaleby,))

    factor = scaleby.value / 100
    if factor > 0:
        # Add x% of the remaining range, up to 1
        return channel + (1 - channel) * factor
    else:
        # Subtract x% of the existing channel.  We add here because the factor
        # is already negative
        return channel * (1 + factor)


@ns.declare
def scale_color(
        color, red=None, green=None, blue=None,
        saturation=None, lightness=None, alpha=None):
    do_rgb = red or green or blue
    do_hsl = saturation or lightness
    if do_rgb and do_hsl:
        raise ValueError(
            "Can't scale both RGB and HSL channels at the same time")

    scaled_alpha = _scale_channel(color.alpha, alpha)

    if do_rgb:
        channels = [
            _scale_channel(channel, scaleby)
            for channel, scaleby in zip(color.rgba, (red, green, blue))]
        return Color.from_rgb(*channels, alpha=scaled_alpha)

    else:
        channels = [
            _scale_channel(channel, scaleby)
            for channel, scaleby
            in zip(color.hsl, (None, saturation, lightness))]
        return Color.from_hsl(*channels, alpha=scaled_alpha)


@ns.declare
def change_color(
        color, red=None, green=None, blue=None,
        hue=None, saturation=None, lightness=None, alpha=None):
    do_rgb = red or green or blue
    do_hsl = hue or saturation or lightness
    if do_rgb and do_hsl:
        raise ValueError(
            "Can't change both RGB and HSL channels at the same time")

    if alpha is None:
        alpha = color.alpha
    else:
        alpha = alpha.value

    if do_rgb:
        channels = list(color.rgba[:3])
        if red:
            channels[0] = _interpret_percentage(red, relto=255)
        if green:
            channels[1] = _interpret_percentage(green, relto=255)
        if blue:
            channels[2] = _interpret_percentage(blue, relto=255)

        return Color.from_rgb(*channels, alpha=alpha)

    else:
        channels = list(color.hsl)
        if hue:
            expect_type(hue, Number, unit=None)
            channels[0] = (hue.value / 360) % 1
        # Ruby sass treats plain numbers for saturation and lightness as though
        # they were percentages, just without the %
        if saturation:
            channels[1] = _interpret_percentage(saturation, relto=100)
        if lightness:
            channels[2] = _interpret_percentage(lightness, relto=100)

        return Color.from_hsl(*channels, alpha=alpha)


# ------------------------------------------------------------------------------
# String functions

@ns.declare_alias('e')
@ns.declare_alias('escape')
@ns.declare
def unquote(*args):
    arg = List.from_maybe_starargs(args).maybe()

    if isinstance(arg, String):
        return String(arg.value, quotes=None)
    else:
        return String(arg.render(), quotes=None)


@ns.declare
def quote(*args):
    arg = List.from_maybe_starargs(args).maybe()

    if isinstance(arg, String):
        return String(arg.value, quotes='"')
    else:
        return String(arg.render(), quotes='"')


@ns.declare
def str_length(string):
    expect_type(string, String)

    # nb: can't use `len(string)`, because that gives the Sass list length,
    # which is 1
    return Number(len(string.value))


# TODO this and several others should probably also require integers
# TODO and assert that the indexes are valid
@ns.declare
def str_insert(string, insert, index):
    expect_type(string, String)
    expect_type(insert, String)
    expect_type(index, Number, unit=None)

    py_index = index.to_python_index(len(string.value), check_bounds=False)
    return String(
        string.value[:py_index] + insert.value + string.value[py_index:],
        quotes=string.quotes)


@ns.declare
def str_index(string, substring):
    expect_type(string, String)
    expect_type(substring, String)

    # 1-based indexing, with 0 for failure
    return Number(string.value.find(substring.value) + 1)


@ns.declare
def str_slice(string, start_at, end_at=None):
    expect_type(string, String)
    expect_type(start_at, Number, unit=None)

    if int(start_at) == 0:
        py_start_at = 0
    else:
        py_start_at = start_at.to_python_index(len(string.value))

    if end_at is None or int(end_at) > len(string.value):
        py_end_at = None
    else:
        expect_type(end_at, Number, unit=None)
        # Endpoint is inclusive, unlike Python
        py_end_at = end_at.to_python_index(len(string.value)) + 1

    return String(
        string.value[py_start_at:py_end_at],
        quotes=string.quotes)


@ns.declare
def to_upper_case(string):
    expect_type(string, String)

    return String(string.value.upper(), quotes=string.quotes)


@ns.declare
def to_lower_case(string):
    expect_type(string, String)

    return String(string.value.lower(), quotes=string.quotes)


# ------------------------------------------------------------------------------
# Number functions

@ns.declare
def percentage(value):
    expect_type(value, Number, unit=None)
    return value * Number(100, unit='%')


ns.set_function('abs', 1, Number.wrap_python_function(abs))
ns.set_function('round', 1, Number.wrap_python_function(round))
ns.set_function('ceil', 1, Number.wrap_python_function(math.ceil))
ns.set_function('floor', 1, Number.wrap_python_function(math.floor))


# ------------------------------------------------------------------------------
# List functions

# TODO get the compass bit outta here
@ns.declare_alias('-compass-list-size')
@ns.declare
def length(*lst):
    if len(lst) == 1 and isinstance(lst[0], (list, tuple, List)):
        lst = lst[0]
    return Number(len(lst))


@ns.declare
def set_nth(list, n, value):
    expect_type(n, Number, unit=None)

    py_n = n.to_python_index(len(list))
    return List(
        tuple(list[:py_n]) + (value,) + tuple(list[py_n + 1:]),
        use_comma=list.use_comma)


# TODO get the compass bit outta here
@ns.declare_alias('-compass-nth')
@ns.declare
def nth(lst, n):
    """Return the nth item in the list."""
    expect_type(n, (String, Number), unit=None)

    if isinstance(n, String):
        if n.value.lower() == 'first':
            i = 0
        elif n.value.lower() == 'last':
            i = -1
        else:
            raise ValueError("Invalid index %r" % (n,))
    else:
        # DEVIATION: nth treats lists as circular lists
        i = n.to_python_index(len(lst), circular=True)

    return lst[i]


@ns.declare
def join(lst1, lst2, separator=String.unquoted('auto')):
    expect_type(separator, String)

    ret = []
    ret.extend(List.from_maybe(lst1))
    ret.extend(List.from_maybe(lst2))

    if separator.value == 'comma':
        use_comma = True
    elif separator.value == 'space':
        use_comma = False
    elif separator.value == 'auto':
        # The Sass docs are slightly misleading here, but the algorithm is: use
        # the delimiter from the first list that has at least 2 items, or
        # default to spaces.
        if len(lst1) > 1:
            use_comma = lst1.use_comma
        elif len(lst2) > 1:
            use_comma = lst2.use_comma
        else:
            use_comma = False
    else:
        raise ValueError("separator for join() must be comma, space, or auto")

    return List(ret, use_comma=use_comma)


@ns.declare
def min_(*lst):
    if len(lst) == 1 and isinstance(lst[0], (list, tuple, List)):
        lst = lst[0]
    return min(lst)


@ns.declare
def max_(*lst):
    if len(lst) == 1 and isinstance(lst[0], (list, tuple, List)):
        lst = lst[0]
    return max(lst)


@ns.declare
def append(lst, val, separator=String.unquoted('auto')):
    expect_type(separator, String)

    ret = []
    ret.extend(List.from_maybe(lst))
    ret.append(val)

    separator = separator.value
    if separator == 'comma':
        use_comma = True
    elif separator == 'space':
        use_comma = False
    elif separator == 'auto':
        if len(lst) < 2:
            use_comma = False
        else:
            use_comma = lst.use_comma
    else:
        raise ValueError('Separator must be auto, comma, or space')

    return List(ret, use_comma=use_comma)


@ns.declare
def index(lst, val):
    for i in xrange(len(lst)):
        if lst.value[i] == val:
            return Number(i + 1)
    return Boolean(False)


@ns.declare
def zip_(*lists):
    return List(
        [List(zipped) for zipped in zip(*lists)],
        use_comma=True)


# TODO need a way to use "list" as the arg name without shadowing the builtin
@ns.declare
def list_separator(list):
    if list.use_comma:
        return String.unquoted('comma')
    else:
        return String.unquoted('space')


# ------------------------------------------------------------------------------
# Map functions

@ns.declare
def map_get(map, key):
    return map.to_dict().get(key, Null())


@ns.declare
def map_merge(*maps):
    key_order = []
    index = {}
    for map in maps:
        for key, value in map.to_pairs():
            if key not in index:
                key_order.append(key)

            index[key] = value

    pairs = [(key, index[key]) for key in key_order]
    return Map(pairs, index=index)


@ns.declare
def map_keys(map):
    return List(
        [k for (k, v) in map.to_pairs()],
        use_comma=True)


@ns.declare
def map_values(map):
    return List(
        [v for (k, v) in map.to_pairs()],
        use_comma=True)


@ns.declare
def map_has_key(map, key):
    return Boolean(key in map.to_dict())


# DEVIATIONS: these do not exist in ruby sass

@ns.declare
def map_get3(map, key, default):
    return map.to_dict().get(key, default)


@ns.declare
def map_get_nested3(map, keys, default=Null()):
    for key in keys:
        map = map.to_dict().get(key, None)
        if map is None:
            return default

    return map


@ns.declare
def map_merge_deep(*maps):
    pairs = []
    keys = set()
    for map in maps:
        for key, value in map.to_pairs():
            keys.add(key)

    for key in keys:
        values = [map.to_dict().get(key, None) for map in maps]
        values = [v for v in values if v is not None]
        if all(isinstance(v, Map) for v in values):
            pairs.append((key, map_merge_deep(*values)))
        else:
            pairs.append((key, values[-1]))

    return Map(pairs)


@ns.declare
def keywords(value):
    """Extract named arguments, as a map, from an argument list."""
    expect_type(value, Arglist)
    return value.extract_keywords()


# ------------------------------------------------------------------------------
# Introspection functions

# TODO feature-exists

@ns.declare_internal
def variable_exists(namespace, name):
    expect_type(name, String)
    try:
        namespace.variable('$' + name.value)
    except KeyError:
        return Boolean(False)
    else:
        return Boolean(True)


@ns.declare_internal
def global_variable_exists(namespace, name):
    expect_type(name, String)

    # TODO this is...  imperfect and invasive, but should be a good
    # approximation
    scope = namespace._variables
    while len(scope.maps) > 1:
        scope = scope.maps[-1]

    try:
        scope['$' + name.value]
    except KeyError:
        return Boolean(False)
    else:
        return Boolean(True)


@ns.declare_internal
def function_exists(namespace, name):
    expect_type(name, String)
    # TODO invasive, but there's no other way to ask for this at the moment
    for fname, arity in namespace._functions.keys():
        if name.value == fname:
            return Boolean(True)
    return Boolean(False)


@ns.declare_internal
def mixin_exists(namespace, name):
    expect_type(name, String)
    # TODO invasive, but there's no other way to ask for this at the moment
    for fname, arity in namespace._mixins.keys():
        if name.value == fname:
            return Boolean(True)
    return Boolean(False)


@ns.declare
def inspect(value):
    return String.unquoted(value.render())


@ns.declare
def type_of(obj):  # -> bool, number, string, color, list
    return String(obj.sass_type_name)


@ns.declare
def unit(number):  # -> px, em, cm, etc.
    numer = '*'.join(sorted(number.unit_numer))
    denom = '*'.join(sorted(number.unit_denom))

    if denom:
        ret = numer + '/' + denom
    else:
        ret = numer
    return String.unquoted(ret)


@ns.declare
def unitless(value):
    if not isinstance(value, Number):
        raise TypeError("Expected number, got %r" % (value,))

    return Boolean(value.is_unitless)


@ns.declare
def comparable(number1, number2):
    left = number1.to_base_units()
    right = number2.to_base_units()
    return Boolean(
        left.unit_numer == right.unit_numer
        and left.unit_denom == right.unit_denom)


# TODO call
