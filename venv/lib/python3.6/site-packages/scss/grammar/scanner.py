"""Pure-Python scanner and parser, used if the C module is not available."""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from collections import deque
import re

from scss.errors import SassSyntaxError


DEBUG = False


try:
    from ._scanner import locate_blocks
except ImportError:
    # Regex for finding a minimum set of characters that might affect where a
    # block starts or ends
    _blocks_re = re.compile(r'[{},;()\'"\n]|\\.', re.DOTALL)

    def locate_blocks(codestr):
        """
        For processing CSS like strings.

        Either returns all selectors (that can be "smart" multi-lined, as
        long as it's joined by `,`, or enclosed in `(` and `)`) with its code block
        (the one between `{` and `}`, which can be nested), or the "lose" code
        (properties) that doesn't have any blocks.
        """
        lineno = 1

        par = 0
        instr = None
        depth = 0
        skip = False
        i = init = lose = 0
        start = end = None
        lineno_stack = deque()

        for m in _blocks_re.finditer(codestr):
            i = m.start(0)
            c = codestr[i]
            if c == '\n':
                lineno += 1

            if c == '\\':
                # Escape, also consumes the next character
                pass
            elif instr is not None:
                if c == instr:
                    instr = None  # A string ends (FIXME: needs to accept escaped characters)
            elif c in ('"', "'"):
                instr = c  # A string starts
            elif c == '(':  # parenthesis begins:
                par += 1
            elif c == ')':  # parenthesis ends:
                par -= 1
            elif not par and not instr:
                if c == '{':  # block begins:
                    if depth == 0:
                        if i > 0 and codestr[i - 1] == '#':  # Do not process #{...} as blocks!
                            skip = True
                        else:
                            lineno_stack.append(lineno)
                            start = i
                            if lose < init:
                                _property = codestr[lose:init].strip()
                                if _property:
                                    yield lineno, _property, None
                                lose = init
                    depth += 1
                elif c == '}':  # block ends:
                    if depth <= 0:
                        raise SyntaxError("Unexpected closing brace on line {0}".format(lineno))
                    else:
                        depth -= 1
                        if depth == 0:
                            if not skip:
                                end = i
                                _selectors = codestr[init:start].strip()
                                _codestr = codestr[start + 1:end].strip()
                                if _selectors:
                                    yield lineno_stack.pop(), _selectors, _codestr
                                init = lose = end + 1
                            skip = False
                elif depth == 0:
                    if c == ';':  # End of property (or block):
                        init = i
                        if lose < init:
                            _property = codestr[lose:init].strip()
                            if _property:
                                yield lineno, _property, None
                            init = lose = i + 1
        if depth > 0:
            if not skip:
                _selectors = codestr[init:start].strip()
                _codestr = codestr[start + 1:].strip()
                if _selectors:
                    yield lineno, _selectors, _codestr
                if par:
                    error = "Parentheses never closed"
                elif instr:
                    error = "String literal never terminated"
                else:
                    error = "Block never closed"
                # TODO should remember the line + position of the actual
                # problem, and show it in a SassError
                raise SyntaxError(
                    "Couldn't parse block starting on line {0}: {1}"
                    .format(lineno, error)
                )
        losestr = codestr[lose:]
        for _property in losestr.split(';'):
            _property = _property.strip()
            lineno += _property.count('\n')
            if _property:
                yield lineno, _property, None


################################################################################
# Parser

# NOTE: This class has no C equivalent
class Parser(object):
    def __init__(self, scanner):
        self._scanner = scanner
        self._pos = 0
        self._char_pos = 0

    def reset(self, input):
        self._scanner.reset(input)
        self._pos = 0
        self._char_pos = 0

    def _peek(self, types):
        """
        Returns the token type for lookahead; if there are any args
        then the list of args is the set of token types to allow
        """
        tok = self._scanner.token(self._pos, types)
        return tok[2]

    def _scan(self, type):
        """
        Returns the matched text, and moves to the next token
        """
        tok = self._scanner.token(self._pos, frozenset([type]))
        self._char_pos = tok[0]
        if tok[2] != type:
            raise SyntaxError("SyntaxError[@ char %s: %s]" % (repr(tok[0]), "Trying to find " + type))
        self._pos += 1
        return tok[3]


try:
    from ._scanner import NoMoreTokens
except ImportError:
    class NoMoreTokens(Exception):
        """
        Another exception object, for when we run out of tokens
        """
        pass


try:
    from ._scanner import Scanner
except ImportError:
    class Scanner(object):
        def __init__(self, patterns, ignore, input=None):
            """
            Patterns is [(terminal,regex)...]
            Ignore is [terminal,...];
            Input is a string
            """
            self.reset(input)
            self.ignore = ignore
            # The stored patterns are a pair (compiled regex,source
            # regex).  If the patterns variable passed in to the
            # constructor is None, we assume that the class already has a
            # proper .patterns list constructed
            if patterns is not None:
                self.patterns = []
                for k, r in patterns:
                    self.patterns.append((k, re.compile(r)))

        def reset(self, input):
            self.tokens = []
            self.restrictions = []
            self.input = input
            self.pos = 0

        def __repr__(self):
            """
            Print the last 10 tokens that have been scanned in
            """
            output = ''
            for t in self.tokens[-10:]:
                output = "%s\n  (@%s)  %s  =  %s" % (output, t[0], t[2], repr(t[3]))
            return output

        def _scan(self, restrict):
            """
            Should scan another token and add it to the list, self.tokens,
            and add the restriction to self.restrictions
            """
            # Keep looking for a token, ignoring any in self.ignore
            if DEBUG:
                print()
                print("Being asked to match with restriction:", repr(restrict))
            token = None
            while True:
                best_pat = None
                # Search the patterns for a match, with earlier
                # tokens in the list having preference
                best_pat_len = 0
                for tok, regex in self.patterns:
                    if DEBUG:
                        print("\tTrying %s: %s at pos %d -> %s" % (repr(tok), repr(regex.pattern), self.pos, repr(self.input)))
                    # First check to see if we're restricting to this token
                    if restrict and tok not in restrict and tok not in self.ignore:
                        if DEBUG:
                            print("\tSkipping %r!" % (tok,))
                        continue
                    m = regex.match(self.input, self.pos)
                    if m:
                        # We got a match
                        best_pat = tok
                        best_pat_len = len(m.group(0))
                        if DEBUG:
                            print("Match OK! %s: %s at pos %d" % (repr(tok), repr(regex.pattern), self.pos))
                        break

                # If we didn't find anything, raise an error
                if best_pat is None:
                    raise SassSyntaxError(self.input, self.pos, restrict)

                # If we found something that isn't to be ignored, return it
                if best_pat in self.ignore:
                    # This token should be ignored...
                    self.pos += best_pat_len
                else:
                    end_pos = self.pos + best_pat_len
                    # Create a token with this data
                    token = (
                        self.pos,
                        end_pos,
                        best_pat,
                        self.input[self.pos:end_pos]
                    )
                    break
            if token is not None:
                self.pos = token[1]
                # Only add this token if it's not in the list
                # (to prevent looping)
                if not self.tokens or token != self.tokens[-1]:
                    self.tokens.append(token)
                    self.restrictions.append(restrict)
                    return 1
            return 0

        def token(self, i, restrict=None):
            """
            Get the i'th token, and if i is one past the end, then scan
            for another token; restrict is a list of tokens that
            are allowed, or 0 for any token.
            """
            tokens_len = len(self.tokens)
            if i == tokens_len:  # We are at the end, get the next...
                tokens_len += self._scan(restrict)
            if i < tokens_len:
                if restrict and self.restrictions[i] and restrict > self.restrictions[i]:
                    raise NotImplementedError("Unimplemented: restriction set changed")
                return self.tokens[i]
            raise NoMoreTokens

        def rewind(self, i):
            tokens_len = len(self.tokens)
            if i <= tokens_len:
                token = self.tokens[i]
                self.tokens = self.tokens[:i]
                self.restrictions = self.restrictions[:i]
                self.pos = token[0]
