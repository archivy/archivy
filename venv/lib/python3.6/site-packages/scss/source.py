from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import hashlib
import logging
from pathlib import Path
import re

import six

from scss.cssdefs import (
    _ml_comment_re, _sl_comment_re,
    _collapse_properties_space_re,
    _strings_re, _urls_re,
)
from scss.cssdefs import determine_encoding


log = logging.getLogger(__name__)


_safe_strings = {
    '^doubleslash^': '//',
    '^bigcopen^': '/*',
    '^bigcclose^': '*/',
    '^doubledot^': ':',
    '^semicolon^': ';',
    '^curlybracketopen^': '{',
    '^curlybracketclosed^': '}',
}
_reverse_safe_strings = dict((v, k) for k, v in _safe_strings.items())
_safe_strings_re = re.compile('|'.join(map(re.escape, _safe_strings)))
_reverse_safe_strings_re = re.compile('|'.join(
    map(re.escape, _reverse_safe_strings)))


class MISSING(object):
    def __repr__(self):
        return "<MISSING>"
MISSING = MISSING()


# TODO i'm still not entirely happy with this, nor with the concept of an
# "origin".  it should really be a "loader", with a defined API.  also, even
# with all these helpful classmethods, i'm still having to do a lot of manual
# mucking around in django-pyscss, where all i'm given is a file path and a
# string of the contents, and i want to /not/ re-read the file.
class SourceFile(object):
    """A single input file to be fed to the compiler.  Detects the encoding
    (according to CSS spec rules) and performs some light pre-processing.

    This class is mostly internal and you shouldn't have to worry about it.

    Source files are uniquely identified by their ``.key``, a 2-tuple of
    ``(origin, relpath)``.

    ``origin`` is an object from the compiler's search
    path, most often a directory represented by a :class:`pathlib.Path`.
    ``relpath`` is a relative path from there to the actual file, again usually
    a ``Path``.

    The idea here is that source files don't always actually come from the
    filesystem, yet import semantics are expressed in terms of paths.  By
    keeping the origin and relative path separate, it's possible for e.g.
    Django to swap in an object that has the ``Path`` interface, but actually
    looks for files in an arbitrary storage backend.  In that case it would
    make no sense to key files by their absolute path, as they may not exist on
    disk or even on the same machine.  Also, relative imports can then continue
    to work, because they're guaranteed to only try the same origin.

    The ``origin`` may thus be anything that implements a minimal ``Path``ish
    interface (division operator, ``.parent``, ``.resolve()``).  It may also be
    ``None``, indicating that the file came from a string or some other origin
    that can't usefully produce other files.

    ``relpath``, however, should always be a ``Path``. or string.  XXX only when origin  (There's little
    advantage to making it anything else.)  A ``relpath`` may **never** contain
    ".."; there is nothing above the origin.

    Note that one minor caveat of this setup is that it's possible for the same
    file on disk to be imported under two different names (even though symlinks
    are always resolved), if directories in the search path happen to overlap.
    """

    key = None
    """A 2-tuple of ``(origin, relpath)`` that uniquely identifies where the
    file came from and how to find its siblings.
    """

    def __init__(
            self, origin, relpath, contents, encoding=None,
            is_sass=None):
        """Not normally used.  See the three alternative constructors:
        :func:`SourceFile.from_file`, :func:`SourceFile.from_path`, and
        :func:`SourceFile.from_string`.
        """
        if not isinstance(contents, six.text_type):
            raise TypeError(
                "Expected text for 'contents', got {0}"
                .format(type(contents)))

        if origin and '..' in relpath.parts:
            raise ValueError(
                "relpath cannot contain ..: {0!r}".format(relpath))

        self.origin = origin
        self.relpath = relpath
        self.key = origin, relpath

        self.encoding = encoding
        if is_sass is None:
            # TODO autodetect from the contents if the extension is bogus
            # or missing?
            if origin:
                self.is_sass = relpath.suffix == '.sass'
            else:
                self.is_sass = False
        else:
            self.is_sass = is_sass
        self.contents = self.prepare_source(contents)

    @property
    def path(self):
        """Concatenation of ``origin`` and ``relpath``, as a string.  Used in
        stack traces and other debugging places.
        """
        if self.origin:
            return six.text_type(self.origin / self.relpath)
        else:
            return six.text_type(self.relpath)

    def __repr__(self):
        return "<{0} {1!r} from {2!r}>".format(
            type(self).__name__, self.relpath, self.origin)

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        if self is other:
            return True

        if not isinstance(other, SourceFile):
            return NotImplemented

        return self.key == other.key

    def __ne__(self, other):
        return not self == other

    @classmethod
    def _key_from_path(cls, path, origin=MISSING):
        # Given an origin (which may be MISSING) and an absolute path,
        # return a key.
        if origin is MISSING:
            # Resolve only the parent, in case the file itself is a symlink
            origin = path.parent.resolve()
            relpath = Path(path.name)
        else:
            # Again, resolving the origin is fine; we just don't want to
            # resolve anything inside it, lest we ruin some intended symlink
            # structure
            origin = origin.resolve()
            # pathlib balks if this requires lexically ascending  <3
            relpath = path.relative_to(origin)

        return origin, relpath

    @classmethod
    def read(cls, origin, relpath, **kwargs):
        """Read a source file from an ``(origin, relpath)`` tuple, as would
        happen from an ``@import`` statement.
        """
        path = origin / relpath
        with path.open('rb') as f:
            return cls.from_file(f, origin, relpath, **kwargs)

    @classmethod
    def from_path(cls, path, origin=MISSING, **kwargs):
        """Read Sass source from a :class:`pathlib.Path`.

        If no origin is given, it's assumed to be the file's parent directory.
        """
        origin, relpath = cls._key_from_path(path, origin)

        # Open in binary mode so we can reliably detect the encoding
        with path.open('rb') as f:
            return cls.from_file(f, origin, relpath, **kwargs)

    # back-compat
    @classmethod
    def from_filename(cls, path_string, origin=MISSING, **kwargs):
        """ Read Sass source from a String specifying the path
        """
        path = Path(path_string)
        return cls.from_path(path, origin, **kwargs)

    @classmethod
    def from_file(cls, f, origin=MISSING, relpath=MISSING, **kwargs):
        """Read Sass source from a file or file-like object.

        If `origin` or `relpath` are missing, they are derived from the file's
        ``.name`` attribute as with `from_path`.  If it doesn't have one, the
        origin becomes None and the relpath becomes the file's repr.
        """
        contents = f.read()
        encoding = determine_encoding(contents)
        if isinstance(contents, six.binary_type):
            contents = contents.decode(encoding)

        if origin is MISSING or relpath is MISSING:
            filename = getattr(f, 'name', None)
            if filename is None:
                origin = None
                relpath = repr(f)
            else:
                origin, relpath = cls._key_from_path(Path(filename), origin)

        return cls(origin, relpath, contents, encoding=encoding, **kwargs)

    @classmethod
    def from_string(cls, string, relpath=None, encoding=None, is_sass=None):
        """Read Sass source from the contents of a string.

        The origin is always None.  `relpath` defaults to "string:...".
        """
        if isinstance(string, six.text_type):
            # Already decoded; we don't know what encoding to use for output,
            # though, so still check for a @charset.
            # TODO what if the given encoding conflicts with the one in the
            # file?  do we care?
            if encoding is None:
                encoding = determine_encoding(string)

            byte_contents = string.encode(encoding)
            text_contents = string
        elif isinstance(string, six.binary_type):
            encoding = determine_encoding(string)
            byte_contents = string
            text_contents = string.decode(encoding)
        else:
            raise TypeError("Expected text or bytes, got {0!r}".format(string))

        origin = None
        if relpath is None:
            m = hashlib.sha256()
            m.update(byte_contents)
            relpath = repr("string:{0}:{1}".format(
                m.hexdigest()[:16], text_contents[:100]))

        return cls(
            origin, relpath, text_contents, encoding=encoding,
            is_sass=is_sass,
        )

    def parse_scss_line(self, line, state):
        ret = ''

        if line is None:
            line = ''

        line = state['line_buffer'] + line

        if line and line[-1] == '\\':
            state['line_buffer'] = line[:-1]
            return ''
        else:
            state['line_buffer'] = ''

        output = state['prev_line']
        output = output.strip()

        state['prev_line'] = line

        ret += output
        ret += '\n'
        return ret

    def parse_sass_line(self, line, state):
        ret = ''

        if line is None:
            line = ''

        line = state['line_buffer'] + line

        if line and line[-1] == '\\':
            state['line_buffer'] = line[:-1]
            return ret
        else:
            state['line_buffer'] = ''

        indent = len(line) - len(line.lstrip())

        # make sure we support multi-space indent as long as indent is
        # consistent
        if indent and not state['indent_marker']:
            state['indent_marker'] = indent

        if state['indent_marker']:
            indent //= state['indent_marker']

        if indent == state['prev_indent']:
            # same indentation as previous line
            if state['prev_line']:
                state['prev_line'] += ';'
        elif indent > state['prev_indent']:
            # new indentation is greater than previous, we just entered a new
            # block
            state['prev_line'] += ' {'
            state['nested_blocks'] += 1
        else:
            # indentation is reset, we exited a block
            block_diff = state['prev_indent'] - indent
            if state['prev_line']:
                state['prev_line'] += ';'
            state['prev_line'] += ' }' * block_diff
            state['nested_blocks'] -= block_diff

        output = state['prev_line']
        output = output.strip()

        state['prev_indent'] = indent
        state['prev_line'] = line

        ret += output
        ret += '\n'
        return ret

    def prepare_source(self, codestr, sass=False):
        state = {
            'line_buffer': '',
            'prev_line': '',
            'prev_indent': 0,
            'nested_blocks': 0,
            'indent_marker': 0,
        }
        if self.is_sass:
            parse_line = self.parse_sass_line
        else:
            parse_line = self.parse_scss_line
        _codestr = codestr
        codestr = ''
        for line in _codestr.splitlines():
            codestr += parse_line(line, state)
        # parse the last line stored in prev_line buffer
        codestr += parse_line(None, state)

        # pop off the extra \n parse_line puts at the beginning
        codestr = codestr[1:]

        # protects codestr: "..." strings
        codestr = _strings_re.sub(
            lambda m: _reverse_safe_strings_re.sub(
                lambda n: _reverse_safe_strings[n.group(0)], m.group(0)),
            codestr)
        codestr = _urls_re.sub(
            lambda m: _reverse_safe_strings_re.sub(
                lambda n: _reverse_safe_strings[n.group(0)], m.group(0)),
            codestr)

        # removes multiple line comments
        codestr = _ml_comment_re.sub('', codestr)

        # removes inline comments, but not :// (protocol)
        codestr = _sl_comment_re.sub('', codestr)

        codestr = _safe_strings_re.sub(
            lambda m: _safe_strings[m.group(0)], codestr)

        # collapse the space in properties blocks
        codestr = _collapse_properties_space_re.sub(r'\1{', codestr)

        return codestr
