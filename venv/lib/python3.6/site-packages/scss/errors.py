from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import six

import sys
import traceback


BROWSER_ERROR_TEMPLATE = """\
body:before {{
    content: {0};

    display: block;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;

    font-size: 14px;
    margin: 1em;
    padding: 1em;
    border: 3px double red;

    white-space: pre;
    font-family: monospace;
    background: #fcebeb;
    color: black;
}}
"""


def add_error_marker(text, position, start_line=1):
    """Add a caret marking a given position in a string of input.

    Returns (new_text, caret_line).
    """
    indent = "    "
    lines = []
    caret_line = start_line
    for line in text.split("\n"):
        lines.append(indent + line)

        if 0 <= position <= len(line):
            lines.append(indent + (" " * position) + "^")
            caret_line = start_line

        position -= len(line)
        position -= 1  # for the newline
        start_line += 1

    return "\n".join(lines), caret_line


class SassBaseError(Exception):
    """Base class for all errors caused by Sass code.

    Shouldn't be raising this directly; use or create a subclass instead.
    """

    def __init__(self, rule=None):
        super(SassBaseError, self).__init__()

        self.rule_stack = []
        if rule is not None:
            self.add_rule(rule)

    def add_rule(self, rule):
        """Add a new rule to the "stack" of rules -- this is used to track,
        e.g., how a file was ultimately imported.
        """
        self.rule_stack.append(rule)

    def format_file_and_line(self, rule):
        return "line {rule.lineno} of {rule.source_file.path}".format(
            rule=rule,
        )

    def format_sass_stack(self):
        """Return a "traceback" of Sass imports."""
        if not self.rule_stack:
            return ""

        ret = ["on ", self.format_file_and_line(self.rule_stack[0]), "\n"]
        last_file = self.rule_stack[0].source_file

        # TODO this could go away if rules knew their import chains...
        # TODO this doesn't mention mixins or function calls.  really need to
        # track the call stack better.  atm we skip other calls in the same
        # file because most of them are just nesting, but they might not be!
        # TODO the line number is wrong here for @imports, because we don't
        # have access to the UnparsedBlock representing the import!
        # TODO @content is completely broken; it's basically textual inclusion
        for rule in self.rule_stack[1:]:
            if rule.source_file is not last_file:
                ret.extend((
                    "imported from ", self.format_file_and_line(rule), "\n"))
            last_file = rule.source_file

        return "".join(ret)

    def format_message(self):
        return ""

    def __str__(self):
        return "{message}\n{sass_stack}".format(
            message=self.format_message(),
            sass_stack=self.format_sass_stack(),
        )


class SassSyntaxError(SassBaseError):
    """Generic syntax error thrown by the guts of the expression parser;
    usually caught and wrapped later on.
    """
    def __init__(self, input_string, position, desired_tokens):
        super(SassSyntaxError, self).__init__()

        self.input_string = input_string
        self.position = position
        self.desired_tokens = desired_tokens

    def __str__(self):
        # TODO this doesn't show the rule stack; should inherit from SassError
        # instead?
        if self.position == 0:
            after = "Syntax error"
        else:
            after = "Syntax error after {0!r}".format(
                self.input_string[max(0, self.position - 20):self.position])

        found = "Found {0!r}".format(
            self.input_string[self.position:self.position + 10])

        if not self.desired_tokens:
            expected = "but can't figure out what that means"
        elif len(self.desired_tokens) == 1:
            expected = "but expected {0}".format(
                ''.join(self.desired_tokens))
        else:
            expected = "but expected one of {0}".format(
                ', '.join(sorted(self.desired_tokens)))

        return "{after}: {found} {expected}".format(
            after=after,
            found=found,
            expected=expected,
        )


class SassImportError(SassBaseError):
    """Error raised when unable to resolve an @import."""

    def __init__(self, bad_name, compiler, **kwargs):
        super(SassImportError, self).__init__(**kwargs)

        self.bad_name = bad_name
        self.compiler = compiler

    def format_message(self):
        return (
            "Couldn't find anything to import: {0}\n"
            "Extensions: {1}\n"
            "Search path:\n  {2}"
            .format(
                self.bad_name,
                ", ".join(repr(ext) for ext in self.compiler.extensions),
                "\n  ".join(str(path) for path in self.compiler.search_path),
            )
        )


class SassMissingDependency(SassBaseError):
    """Error raised when an optional library (e.g., PIL or fontforge) is
    missing.
    """

    def __init__(self, library, activity, **kwargs):
        super(SassMissingDependency, self).__init__(**kwargs)

        self.library = library
        self.activity = activity

    def format_message(self):
        return "{0} requires {1}, which is not installed".format(
            self.activity, self.library)


class SassError(SassBaseError):
    """Error class that wraps another exception and attempts to bolt on some
    useful context.
    """
    def __init__(self, exc, expression=None, expression_pos=None, **kwargs):
        super(SassError, self).__init__(**kwargs)

        self.exc = exc
        self.expression = expression
        self.expression_pos = expression_pos

        _, _, self.original_traceback = sys.exc_info()

    def format_prefix(self):
        """Return the general name of the error and the contents of the rule or
        property that caused the failure.  This is the initial part of the
        error message and should be error-specific.
        """
        # TODO this contains NULs and line numbers; could be much prettier
        if self.rule_stack:
            return (
                "Error parsing block:\n" +
                "    " + self.rule_stack[0].unparsed_contents + "\n"
            )
        else:
            return "Unknown error\n"

    def format_python_stack(self):
        """Return a traceback of Python frames, from where the error occurred
        to where it was first caught and wrapped.
        """
        ret = ["Traceback:\n"]
        ret.extend(traceback.format_tb(self.original_traceback))
        return "".join(ret)

    def format_original_error(self):
        """Return the typical "TypeError: blah blah" for the original wrapped
        error.
        """
        # TODO eventually we'll have sass-specific errors that will want nicer
        # "names" in browser display and stderr
        return "".join((
            type(self.exc).__name__, ": ", six.text_type(self.exc), "\n",
        ))

    def __str__(self):
        try:
            prefix = self.format_prefix()
            sass_stack = self.format_sass_stack()
            python_stack = self.format_python_stack()
            original_error = self.format_original_error()

            # TODO not very well-specified whether these parts should already
            # end in newlines, or how many
            return prefix + "\n" + sass_stack + python_stack + original_error
        except Exception:
            # "unprintable error" is not helpful
            return six.text_type(self.exc)

    def to_css(self):
        """Return a stylesheet that will show the wrapped error at the top of
        the browser window.
        """
        # TODO should this include the traceback?  any security concerns?
        prefix = self.format_prefix()
        original_error = self.format_original_error()
        sass_stack = self.format_sass_stack()

        message = prefix + "\n" + sass_stack + original_error

        # Super simple escaping: only quotes and newlines are illegal in css
        # strings
        message = message.replace('\\', '\\\\')
        message = message.replace('"', '\\"')
        # use the maximum six digits here so it doesn't eat any following
        # characters that happen to look like hex
        message = message.replace('\n', '\\00000A')

        return BROWSER_ERROR_TEMPLATE.format('"' + message + '"')


class SassParseError(SassError):
    """Error raised when parsing a Sass expression fails."""

    def format_prefix(self):
        decorated_expr, line = add_error_marker(self.expression, self.expression_pos or -1)
        return """Error parsing expression at {1}:\n{0}\n""".format(decorated_expr, self.expression_pos)


class SassEvaluationError(SassError):
    """Error raised when evaluating a parsed expression fails."""

    def format_prefix(self):
        # TODO boy this is getting repeated a lot
        # TODO would be nice for the AST to have position information
        # TODO might be nice to print the AST and indicate where the failure
        # was?
        decorated_expr, line = add_error_marker(self.expression, self.expression_pos or -1)
        return """Error evaluating expression:\n{0}\n""".format(decorated_expr)
