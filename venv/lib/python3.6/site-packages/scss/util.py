from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import base64
import hashlib
import os
import re
import sys
import time
from functools import wraps

import six

from scss import config

BASE_DIR = os.path.dirname(__file__)


def split_params(params):
    params = params.split(',') or []
    if params:
        final_params = []
        param = params.pop(0)
        try:
            while True:
                while param.count('(') != param.count(')'):
                    try:
                        param = param + ',' + params.pop(0)
                    except IndexError:
                        break
                final_params.append(param)
                param = params.pop(0)
        except IndexError:
            pass
        params = final_params
    return params


def dequote(s):
    if s and s[0] in ('"', "'") and s[-1] == s[0]:
        s = s[1:-1]
        s = unescape(s)
    return s


def depar(s):
    while s and s[0] == '(' and s[-1] == ')':
        s = s[1:-1]
    return s


def to_str(num):
    try:
        render = num.render
    except AttributeError:
        pass
    else:
        return render()

    if isinstance(num, dict):
        s = sorted(num.items())
        sp = num.get('_', '')
        return (sp + ' ').join(to_str(v) for n, v in s if n != '_')
    elif isinstance(num, float):
        num = ('%0.05f' % round(num, 5)).rstrip('0').rstrip('.')
        return num
    elif isinstance(num, bool):
        return 'true' if num else 'false'
    elif num is None:
        return ''
    return six.text_type(num)


def to_float(num):
    if isinstance(num, (float, int)):
        return float(num)
    num = to_str(num)
    if num and num[-1] == '%':
        return float(num[:-1]) / 100.0
    else:
        return float(num)


def escape(s):
    return re.sub(r'''(["'])''', r'\\\1', s)  # do not escape '\'


# Deprecated; use the unescape() from cssdefs instead
def unescape(s):
    return re.sub(r'''\\(['"\\])''', r'\1', s)  # do unescape '\'


def normalize_var(var):
    """Sass defines `foo_bar` and `foo-bar` as being identical, both in
    variable names and functions/mixins.  This normalizes everything to use
    dashes.
    """
    return var.replace('_', '-')


def make_data_url(mime_type, data):
    """Generate a `data:` URL from the given data and MIME type."""
    return "data:{0};base64,{1}".format(
        mime_type, base64.b64encode(data).decode('ascii'))


def make_filename_hash(key):
    """Convert the given key (a simple Python object) to a unique-ish hash
    suitable for a filename.
    """
    key_repr = repr(key).replace(BASE_DIR, '').encode('utf8')
    # This is really stupid but necessary for making the repr()s be the same on
    # Python 2 and 3 and thus allowing the test suite to run on both.
    # TODO better solutions include: not using a repr, not embedding hashes in
    # the expected test results
    if sys.platform == 'win32':
        # this is to make sure the hash is the same on win and unix platforms
        key_repr = key_repr.replace(b'\\\\', b'/')
    key_repr = re.sub(b"\\bu'", b"'", key_repr)
    key_hash = hashlib.md5(key_repr).digest()
    return base64.b64encode(key_hash, b'__').decode('ascii').rstrip('=')


################################################################################
# Function timing decorator
profiling = {}


def print_timing(level=0):
    def _print_timing(func):
        if config.VERBOSITY:
            def wrapper(*args, **kwargs):
                if config.VERBOSITY >= level:
                    t1 = time.time()
                    res = func(*args, **kwargs)
                    t2 = time.time()
                    profiling.setdefault(func.func_name, 0)
                    profiling[func.func_name] += (t2 - t1)
                    return res
                else:
                    return func(*args, **kwargs)
            return wrapper
        else:
            return func
    return _print_timing


################################################################################
# Profiler decorator
def profile(fn):
    import cProfile
    import pstats

    @wraps(fn)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        stream = six.StringIO()
        profiler.enable()
        try:
            res = fn(*args, **kwargs)
        finally:
            profiler.disable()
            stats = pstats.Stats(profiler, stream=stream)
            stats.sort_stats('time')
            print >>stream, ""
            print >>stream, "=" * 100
            print >>stream, "Stats:"
            stats.print_stats()
            print >>stream, "=" * 100
            print >>stream, "Callers:"
            stats.print_callers()
            print >>stream, "=" * 100
            print >>stream, "Callees:"
            stats.print_callees()
            print >>sys.stderr, stream.getvalue()
            stream.close()
        return res
    return wrapper


################################################################################
# http://code.activestate.com/recipes/325905-memoize-decorator-with-timeout/

class tmemoize(object):
    """
    Memoize With Timeout

    Usage:
        @tmemoize()
        def z(a,b):
            return a + b

        @tmemoize(timeout=5)
        def x(a,b):
            return a + b
    """
    _caches = {}
    _timeouts = {}
    _collected = time.time()

    def __init__(self, timeout=60, gc=3600):
        self.timeout = timeout
        self.gc = gc

    def collect(self):
        """Clear cache of results which have timed out"""
        for func in self._caches:
            cache = {}
            for key in self._caches[func]:
                if (time.time() - self._caches[func][key][1]) < self._timeouts[func]:
                    cache[key] = self._caches[func][key]
            self._caches[func] = cache

    def __call__(self, func):
        self._caches[func] = {}
        self._timeouts[func] = self.timeout

        @wraps(func)
        def wrapper(*args):
            key = args
            now = time.time()
            cache = self._caches[func]
            try:
                ret, last = cache[key]
                if now - last > self.timeout:
                    raise KeyError
            except KeyError:
                ret, last = cache[key] = (func(*args), now)
            if now - self._collected > self.gc:
                self.collect()
                self._collected = time.time()
            return ret
        return wrapper


################################################################################
# Memoized getmtime (can accept storage)
@tmemoize()
def getmtime(filename, storage=None):
    try:
        if storage:
            d_obj = storage.modified_time(filename)
            return int(time.mktime(d_obj.timetuple()))
        else:
            return int(os.path.getmtime(filename))
    except:
        pass
