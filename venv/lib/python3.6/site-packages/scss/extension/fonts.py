"""Functions used for generating custom fonts from SVG files."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import errno
import glob
import logging
import os
import time
import tempfile
import subprocess
import warnings
import six

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    import fontforge
except:
    fontforge = None

from scss import config
from scss.errors import SassMissingDependency
from scss.extension import Extension
from scss.namespace import Namespace
from scss.types import Boolean, List, String, Url
from scss.util import getmtime, make_data_url, make_filename_hash
from scss.extension import Cache

log = logging.getLogger(__name__)

TTFAUTOHINT_EXECUTABLE = 'ttfautohint'
TTF2EOT_EXECUTABLE = 'ttf2eot'

MAX_FONT_SHEETS = 4096
KEEP_FONT_SHEETS = int(MAX_FONT_SHEETS * 0.8)

FONT_TYPES = ('eot', 'woff', 'ttf', 'svg')  # eot should be first for IE support

FONT_MIME_TYPES = {
    'ttf': 'application/x-font-ttf',
    'svg': 'image/svg+xml',
    'woff': 'application/x-font-woff',
    'eot': 'application/vnd.ms-fontobject',
}

FONT_FORMATS = {
    'ttf': "format('truetype')",
    'svg': "format('svg')",
    'woff': "format('woff')",
    'eot': "format('embedded-opentype')",
}

GLYPH_WIDTH_RE = re.compile(r'width="(\d+(\.\d+)?)')
GLYPH_HEIGHT_RE = re.compile(r'height="(\d+(\.\d+)?)')

GLYPH_HEIGHT = 512
GLYPH_ASCENT = 448
GLYPH_DESCENT = GLYPH_HEIGHT - GLYPH_ASCENT
GLYPH_WIDTH = GLYPH_HEIGHT

# Offset to work around Chrome Windows bug
GLYPH_START = 0xf100


class FontsExtension(Extension):
    """Functions for creating and manipulating fonts."""
    name = 'fonts'
    namespace = Namespace()


# Alias to make the below declarations less noisy
ns = FontsExtension.namespace


def _assets_root():
    return config.ASSETS_ROOT or os.path.join(config.STATIC_ROOT, 'assets')


def _get_cache(prefix):
    return Cache((config.CACHE_ROOT or _assets_root(), prefix))


def ttfautohint(ttf):
    try:
        proc = subprocess.Popen(
            [TTFAUTOHINT_EXECUTABLE, '--hinting-limit=200', '--hinting-range-max=50', '--symbol'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
    except OSError as e:
        if e.errno in (errno.EACCES, errno.ENOENT):
            warnings.warn('Could not autohint ttf font: The executable %s could not be run: %s' % (TTFAUTOHINT_EXECUTABLE, e))
            return None
        else:
            raise e
    output, output_err = proc.communicate(ttf)
    if proc.returncode != 0:
        warnings.warn("Could not autohint ttf font: Unknown error!")
        return None
    return output


def ttf2eot(ttf):
    try:
        proc = subprocess.Popen(
            [TTF2EOT_EXECUTABLE],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
    except OSError as e:
        if e.errno in (errno.EACCES, errno.ENOENT):
            warnings.warn('Could not generate eot font: The executable %s could not be run: %s' % (TTF2EOT_EXECUTABLE, e))
            return None
        else:
            raise e
    output, output_err = proc.communicate(ttf)
    if proc.returncode != 0:
        warnings.warn("Could not generate eot font: Unknown error!")
        return None
    return output


@ns.declare
def font_sheet(g, **kwargs):
    if not fontforge:
        raise SassMissingDependency('fontforge', 'font manipulation')

    font_sheets = _get_cache('font_sheets')

    now_time = time.time()

    globs = String(g, quotes=None).value
    globs = sorted(g.strip() for g in globs.split(','))

    _k_ = ','.join(globs)

    files = None
    rfiles = None
    tfiles = None
    base_name = None
    glob_path = None
    glyph_name = None

    if _k_ in font_sheets:
        font_sheets[_k_]['*'] = now_time
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
                    base_name = os.path.basename(os.path.dirname(_glob))
                    _glyph_name, _, _glyph_type = base_name.partition('.')
                    if _glyph_type:
                        _glyph_type += '-'
                    if not glyph_name:
                        glyph_name = _glyph_name
                    tfiles.extend([_glyph_type] * len(_files))
                else:
                    glob_path = _glob_path

    if files is not None:
        if not files:
            log.error("Nothing found at '%s'", glob_path)
            return String.unquoted('')

        key = [f for (f, s) in files] + [repr(kwargs), config.ASSETS_URL]
        key = glyph_name + '-' + make_filename_hash(key)
        asset_files = {
            'eot': key + '.eot',
            'woff': key + '.woff',
            'ttf': key + '.ttf',
            'svg': key + '.svg',
        }
        ASSETS_ROOT = _assets_root()
        asset_paths = dict((type_, os.path.join(ASSETS_ROOT, asset_file)) for type_, asset_file in asset_files.items())
        cache_path = os.path.join(config.CACHE_ROOT or ASSETS_ROOT, key + '.cache')

        inline = Boolean(kwargs.get('inline', False))

        font_sheet = None
        asset = None
        file_assets = {}
        inline_assets = {}
        if all(os.path.exists(asset_path) for asset_path in asset_paths.values()) or inline:
            try:
                save_time, file_assets, inline_assets, font_sheet, codepoints = pickle.load(open(cache_path))
                if file_assets:
                    file_asset = List([file_asset for file_asset in file_assets.values()], separator=",")
                    font_sheets[file_asset.render()] = font_sheet
                if inline_assets:
                    inline_asset = List([inline_asset for inline_asset in inline_assets.values()], separator=",")
                    font_sheets[inline_asset.render()] = font_sheet
                if inline:
                    asset = inline_asset
                else:
                    asset = file_asset
            except:
                pass

            if font_sheet:
                for file_, storage in files:
                    _time = getmtime(file_, storage)
                    if save_time < _time:
                        if _time > now_time:
                            log.warning("File '%s' has a date in the future (cache ignored)" % file_)
                        font_sheet = None  # Invalidate cached custom font
                        break

        if font_sheet is None or asset is None:
            cache_buster = Boolean(kwargs.get('cache_buster', True))
            autowidth = Boolean(kwargs.get('autowidth', False))
            autohint = Boolean(kwargs.get('autohint', True))

            font = fontforge.font()
            font.encoding = 'UnicodeFull'
            font.design_size = 16
            font.em = GLYPH_HEIGHT
            font.ascent = GLYPH_ASCENT
            font.descent = GLYPH_DESCENT
            font.fontname = glyph_name
            font.familyname = glyph_name
            font.fullname = glyph_name

            def glyphs(f=lambda x: x):
                for file_, storage in f(files):
                    if storage is not None:
                        _file = storage.open(file_)
                    else:
                        _file = open(file_)
                    svgtext = _file.read()
                    svgtext = svgtext.replace('<switch>', '')
                    svgtext = svgtext.replace('</switch>', '')
                    svgtext = svgtext.replace('<svg>', '<svg xmlns="http://www.w3.org/2000/svg">')
                    m = GLYPH_WIDTH_RE.search(svgtext)
                    if m:
                        width = float(m.group(1))
                    else:
                        width = None
                    m = GLYPH_HEIGHT_RE.search(svgtext)
                    if m:
                        height = float(m.group(1))
                    else:
                        height = None
                    _glyph = tempfile.NamedTemporaryFile(delete=False, suffix=".svg", mode='w')
                    _glyph.file.write(svgtext)
                    _glyph.file.close()
                    yield _glyph.name, width, height

            names = tuple(os.path.splitext(os.path.basename(file_))[0] for file_, storage in files)
            tnames = tuple(tfiles[i] + n for i, n in enumerate(names))

            codepoints = []
            for i, (glyph_filename, glyph_width, glyph_height) in enumerate(glyphs()):
                if glyph_height and glyph_height != GLYPH_HEIGHT:
                    warnings.warn("Glyphs should be %spx-high" % GLYPH_HEIGHT)
                codepoint = i + GLYPH_START
                name = names[i]
                codepoints.append(codepoint)
                glyph = font.createChar(codepoint, name)
                glyph.importOutlines(glyph_filename)
                os.unlink(glyph_filename)
                glyph.width = glyph_width or GLYPH_WIDTH
                if autowidth:
                    # Autowidth removes side bearings
                    glyph.left_side_bearing = glyph.right_side_bearing = 0
                glyph.round()

            filetime = int(now_time)

            # Generate font files
            if not inline:
                urls = {}
                for type_ in reversed(FONT_TYPES):
                    asset_path = asset_paths[type_]
                    try:
                        if type_ == 'eot':
                            ttf_path = asset_paths['ttf']
                            with open(ttf_path, 'rb') as ttf_fh:
                                contents = ttf2eot(ttf_fh.read())
                                if contents is not None:
                                    with open(asset_path, 'wb') as asset_fh:
                                        asset_fh.write(contents)
                        else:
                            font.generate(asset_path)
                            if type_ == 'ttf':
                                contents = None
                                if autohint:
                                    with open(asset_path, 'rb') as asset_fh:
                                        contents = ttfautohint(asset_fh.read())
                                if contents is not None:
                                    with open(asset_path, 'wb') as asset_fh:
                                        asset_fh.write(contents)
                        asset_file = asset_files[type_]
                        url = '%s%s' % (config.ASSETS_URL, asset_file)
                        params = []
                        if not urls:
                            params.append('#iefix')
                        if cache_buster:
                            params.append('v=%s' % filetime)
                        if type_ == 'svg':
                            params.append('#' + glyph_name)
                        if params:
                            url += '?' + '&'.join(params)
                        urls[type_] = url
                    except IOError:
                        inline = False

            if inline:
                urls = {}
                for type_ in reversed(FONT_TYPES):
                    contents = None
                    if type_ == 'eot':
                        ttf_path = asset_paths['ttf']
                        with open(ttf_path, 'rb') as ttf_fh:
                            contents = ttf2eot(ttf_fh.read())
                            if contents is None:
                                continue
                    else:
                        _tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.' + type_)
                        _tmp.file.close()
                        font.generate(_tmp.name)
                        with open(_tmp.name, 'rb') as asset_fh:
                            if autohint:
                                if type_ == 'ttf':
                                    _contents = asset_fh.read()
                                    contents = ttfautohint(_contents)
                            if contents is None:
                                contents = _contents
                    os.unlink(_tmp.name)
                    mime_type = FONT_MIME_TYPES[type_]
                    url = make_data_url(mime_type, contents)
                    urls[type_] = url

            assets = {}
            for type_, url in urls.items():
                format_ = FONT_FORMATS[type_]
                if inline:
                    assets[type_] = inline_assets[type_] = List([Url.unquoted(url), String.unquoted(format_)])
                else:
                    assets[type_] = file_assets[type_] = List([Url.unquoted(url), String.unquoted(format_)])
            asset = List([assets[type_] for type_ in FONT_TYPES if type_ in assets], separator=",")

            # Add the new object:
            font_sheet = dict(zip(tnames, zip(rfiles, codepoints)))
            font_sheet['*'] = now_time
            font_sheet['*f*'] = asset_files
            font_sheet['*k*'] = key
            font_sheet['*n*'] = glyph_name
            font_sheet['*t*'] = filetime

            codepoints = zip(files, codepoints)
            cache_tmp = tempfile.NamedTemporaryFile(delete=False, dir=ASSETS_ROOT)
            pickle.dump((now_time, file_assets, inline_assets, font_sheet, codepoints), cache_tmp)
            cache_tmp.close()
            os.rename(cache_tmp.name, cache_path)

            # Use the sorted list to remove older elements (keep only 500 objects):
            if len(font_sheets) > MAX_FONT_SHEETS:
                for a in sorted(font_sheets, key=lambda a: font_sheets[a]['*'], reverse=True)[KEEP_FONT_SHEETS:]:
                    del font_sheets[a]
                log.warning("Exceeded maximum number of font sheets (%s)" % MAX_FONT_SHEETS)
            font_sheets[asset.render()] = font_sheet
        font_sheet_cache = _get_cache('font_sheet_cache')
        for file_, codepoint in codepoints:
            font_sheet_cache[file_] = codepoint
    # TODO this sometimes returns an empty list, or is never assigned to
    return asset


@ns.declare_alias('glyph-names')
@ns.declare
def glyphs(sheet, remove_suffix=False):
    sheet = sheet.render()
    font_sheets = _get_cache('font_sheets')
    font_sheet = font_sheets.get(sheet, {})
    return List([String.unquoted(f) for f in sorted(set(f.rsplit('-', 1)[0] if remove_suffix else f for f in font_sheet if not f.startswith('*')))])


@ns.declare
def glyph_classes(sheet):
    return glyphs(sheet, True)


@ns.declare
def font_url(sheet, type_, only_path=False, cache_buster=True):
    font_sheets = _get_cache('font_sheets')
    font_sheet = font_sheets.get(sheet.render())
    type_ = String.unquoted(type_).render()
    if font_sheet:
        asset_files = font_sheet['*f*']
        asset_file = asset_files.get(type_)
        if asset_file:
            url = '%s%s' % (config.ASSETS_URL, asset_file)
            params = []
            # if type_ == 'eot':
            #     params.append('#iefix')
            if cache_buster:
                params.append('v=%s' % font_sheet['*t*'])
            if type_ == 'svg':
                params.append('#' + font_sheet['*n*'])
            if params:
                url += '?' + '&'.join(params)
            if only_path:
                return String.unquoted(url)
            else:
                return Url.unquoted(url)
    return String.unquoted('')


@ns.declare
def font_format(type_):
    type_ = type_.render()
    if type_ in FONT_FORMATS:
            return String.unquoted(FONT_FORMATS[type_])
    return String.unquoted('')


@ns.declare
def has_glyph(sheet, glyph):
    sheet = sheet.render()
    font_sheets = _get_cache('font_sheets')
    font_sheet = font_sheets.get(sheet)
    glyph_name = String.unquoted(glyph).value
    glyph = font_sheet and font_sheet.get(glyph_name)
    if not font_sheet:
        log.error("No font sheet found: %s", sheet, extra={'stack': True})
    return Boolean(bool(glyph))


@ns.declare
def glyph_code(sheet, glyph):
    sheet = sheet.render()
    font_sheets = _get_cache('font_sheets')
    font_sheet = font_sheets.get(sheet)
    glyph_name = String.unquoted(glyph).value
    glyph = font_sheet and font_sheet.get(glyph_name)
    if not font_sheet:
        log.error("No font sheet found: %s", sheet, extra={'stack': True})
    elif not glyph:
        log.error("No glyph found: %s in %s", glyph_name, font_sheet['*n*'], extra={'stack': True})
    return String(six.unichr(glyph[1]))
