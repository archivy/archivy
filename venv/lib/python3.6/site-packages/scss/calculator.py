from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import sys
import logging
from warnings import warn

import six

from scss.ast import Literal
from scss.cssdefs import _expr_glob_re, _interpolate_re
from scss.errors import SassError, SassEvaluationError, SassParseError
from scss.grammar.expression import SassExpression, SassExpressionScanner
from scss.rule import Namespace
from scss.types import String
from scss.types import Value
from scss.util import dequote


log = logging.getLogger(__name__)


class Calculator(object):
    """Expression evaluator."""

    ast_cache = {}

    def __init__(
            self, namespace=None,
            ignore_parse_errors=False,
            undefined_variables_fatal=True,
            ):
        if namespace is None:
            self.namespace = Namespace()
        else:
            self.namespace = namespace

        self.ignore_parse_errors = ignore_parse_errors
        self.undefined_variables_fatal = undefined_variables_fatal

    def _pound_substitute(self, result):
        expr = result.group(1)
        value = self.evaluate_expression(expr)

        if value is None:
            return self.apply_vars(expr)
        elif value.is_null:
            return ""
        else:
            return dequote(value.render())

    def do_glob_math(self, cont):
        """Performs #{}-interpolation.  The result is always treated as a fixed
        syntactic unit and will not be re-evaluated.
        """
        # TODO that's a lie!  this should be in the parser for most cases.
        if not isinstance(cont, six.string_types):
            warn(FutureWarning(
                "do_glob_math was passed a non-string {0!r} "
                "-- this will no longer be supported in pyScss 2.0"
                .format(cont)
            ))
            cont = six.text_type(cont)
        if '#{' not in cont:
            return cont
        cont = _expr_glob_re.sub(self._pound_substitute, cont)
        return cont

    def apply_vars(self, cont):
        # TODO this is very complicated.  it should go away once everything
        # valid is actually parseable.
        if isinstance(cont, six.string_types) and '$' in cont:
            try:
                # Optimization: the full cont is a variable in the context,
                cont = self.namespace.variable(cont)
            except KeyError:
                # Interpolate variables:
                def _av(m):
                    v = None
                    n = m.group(2)
                    try:
                        v = self.namespace.variable(n)
                    except KeyError:
                        if self.undefined_variables_fatal:
                            raise SyntaxError("Undefined variable: '%s'." % n)
                        else:
                            log.error("Undefined variable '%s'", n, extra={'stack': True})
                            return n
                    else:
                        if v:
                            if not isinstance(v, Value):
                                raise TypeError(
                                    "Somehow got a variable {0!r} "
                                    "with a non-Sass value: {1!r}"
                                    .format(n, v)
                                )
                            v = v.render()
                            # TODO this used to test for _dequote
                            if m.group(1):
                                v = dequote(v)
                        else:
                            v = m.group(0)
                        return v

                cont = _interpolate_re.sub(_av, cont)

            else:
                # Variable succeeded, so we need to render it
                cont = cont.render()
        # TODO this is surprising and shouldn't be here
        cont = self.do_glob_math(cont)
        return cont

    def calculate(self, expression, divide=False):
        result = self.evaluate_expression(expression, divide=divide)

        if result is None:
            return String.unquoted(self.apply_vars(expression))

        return result

    # TODO only used by magic-import...?
    def interpolate(self, var):
        value = self.namespace.variable(var)
        if var != value and isinstance(value, six.string_types):
            _vi = self.evaluate_expression(value)
            if _vi is not None:
                value = _vi
        return value

    def evaluate_expression(self, expr, divide=False):
        try:
            ast = self.parse_expression(expr)
        except SassError as e:
            if self.ignore_parse_errors:
                return None
            raise

        try:
            return ast.evaluate(self, divide=divide)
        except Exception as e:
            six.reraise(SassEvaluationError, SassEvaluationError(e, expression=expr), sys.exc_info()[2])

    def parse_expression(self, expr, target='goal'):
        if isinstance(expr, six.text_type):
            # OK
            pass
        elif isinstance(expr, six.binary_type):
            # Dubious
            warn(FutureWarning(
                "parse_expression was passed binary data {0!r} "
                "-- this will no longer be supported in pyScss 2.0"
                .format(expr)
            ))
            # Don't guess an encoding; you reap what you sow
            expr = six.text_type(expr)
        else:
            raise TypeError("Expected string, got %r" % (expr,))

        key = (target, expr)
        if key in self.ast_cache:
            return self.ast_cache[key]

        try:
            parser = SassExpression(SassExpressionScanner(expr))
            ast = getattr(parser, target)()
        except SyntaxError as e:
            raise SassParseError(e, expression=expr, expression_pos=parser._char_pos)

        self.ast_cache[key] = ast
        return ast

    def parse_interpolations(self, string):
        """Parse a string for interpolations, but don't treat anything else as
        Sass syntax.  Returns an AST node.
        """
        # Shortcut: if there are no #s in the string in the first place, it
        # must not have any interpolations, right?
        if '#' not in string:
            return Literal(String.unquoted(string))
        return self.parse_expression(string, 'goal_interpolated_literal')

    def parse_vars_and_interpolations(self, string):
        """Parse a string for variables and interpolations, but don't treat
        anything else as Sass syntax.  Returns an AST node.
        """
        # Shortcut: if there are no #s or $s in the string in the first place,
        # it must not have anything of interest.
        if '#' not in string and '$' not in string:
            return Literal(String.unquoted(string))
        return self.parse_expression(
            string, 'goal_interpolated_literal_with_vars')


__all__ = ('Calculator',)
