from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import logging
import re

from scss.namespace import Namespace

log = logging.getLogger(__name__)

SORTED_SELECTORS = False

sort = sorted if SORTED_SELECTORS else lambda it: it


def extend_unique(seq, more):
    """Return a new sequence containing the items in `seq` plus any items in
    `more` that aren't already in `seq`, preserving the order of both.
    """
    seen = set(seq)
    new = []
    for item in more:
        if item not in seen:
            seen.add(item)
            new.append(item)

    return seq + type(seq)(new)


class SassRule(object):
    """At its heart, a CSS rule: combination of a selector and zero or more
    properties.  But this is Sass, so it also tracks some Sass-flavored
    metadata, like `@extend` rules and `@media` nesting.
    """

    def __init__(
            self, source_file, import_key=None, unparsed_contents=None,
            num_header_lines=0,
            options=None, legacy_compiler_options=None, properties=None,
            namespace=None,
            lineno=0, extends_selectors=frozenset(),
            ancestry=None,
            nested=0,
            from_source_file=None, from_lineno=0):

        self.from_source_file = from_source_file
        self.from_lineno = from_lineno

        self.source_file = source_file
        self.import_key = import_key
        self.lineno = lineno

        self.num_header_lines = num_header_lines
        self.unparsed_contents = unparsed_contents
        self.legacy_compiler_options = legacy_compiler_options or {}
        self.options = options or {}
        self.extends_selectors = extends_selectors

        if namespace is None:
            assert False
            self.namespace = Namespace()
        else:
            self.namespace = namespace

        if properties is None:
            self.properties = []
        else:
            self.properties = properties

        if ancestry is None:
            self.ancestry = RuleAncestry()
        else:
            self.ancestry = ancestry

        self.nested = nested

        self.descendants = 0

    def __repr__(self):
        # TODO probably want to encode this with string_escape on python 2, and
        # similar elsewhere, especially since this file has unicode_literals
        return "<SassRule %s, %d props>" % (
            self.ancestry,
            len(self.properties),
        )

    @property
    def selectors(self):
        # TEMPORARY
        if self.ancestry.headers and self.ancestry.headers[-1].is_selector:
            return self.ancestry.headers[-1].selectors
        else:
            return ()

    @property
    def file_and_line(self):
        """Return the filename and line number where this rule originally
        appears, in the form "foo.scss:3".  Used for error messages.
        """
        ret = "%s:%d" % (self.source_file.path, self.lineno)
        if self.from_source_file:
            ret += " (%s:%d)" % (self.from_source_file.path, self.from_lineno)
        return ret

    @property
    def is_empty(self):
        """Return whether this rule is considered "empty" -- i.e., has no
        contents that should end up in the final CSS.
        """
        if self.properties:
            # Rules containing CSS properties are never empty
            return False

        if not self.descendants:
            for header in self.ancestry.headers:
                if header.is_atrule and header.directive != '@media':
                    # At-rules should always be preserved, UNLESS they are @media
                    # blocks, which are known to be noise if they don't have any
                    # contents of their own
                    return False

        return True

    @property
    def is_pure_placeholder(self):
        selectors = self.selectors
        if not selectors:
            return False
        for s in selectors:
            if not s.has_placeholder:
                return False
        return True


    def copy(self):
        return type(self)(
            source_file=self.source_file,
            lineno=self.lineno,

            from_source_file=self.from_source_file,
            from_lineno=self.from_lineno,

            unparsed_contents=self.unparsed_contents,

            legacy_compiler_options=self.legacy_compiler_options,
            options=self.options,
            #properties=list(self.properties),
            properties=self.properties,
            extends_selectors=self.extends_selectors,
            #ancestry=list(self.ancestry),
            ancestry=self.ancestry,

            namespace=self.namespace.derive(),
            nested=self.nested,
        )


class RuleAncestry(object):
    def __init__(self, headers=()):
        self.headers = tuple(headers)

    def __repr__(self):
        return "<%s %r>" % (type(self).__name__, self.headers)

    def __len__(self):
        return len(self.headers)

    def with_nested_selectors(self, c_selectors):
        if self.headers and self.headers[-1].is_selector:
            # Need to merge with parent selectors
            p_selectors = self.headers[-1].selectors

            new_selectors = []
            for p_selector in p_selectors:
                for c_selector in c_selectors:
                    new_selectors.append(c_selector.with_parent(p_selector))

            # Replace the last header with the new merged selectors
            new_headers = self.headers[:-1] + (BlockSelectorHeader(new_selectors),)
            return RuleAncestry(new_headers)

        else:
            # Whoops, no parent selectors.  Just need to double-check that
            # there are no uses of `&`.
            for c_selector in c_selectors:
                if c_selector.has_parent_reference:
                    raise ValueError("Can't use parent selector '&' in top-level rules")

            # Add the children as a new header
            new_headers = self.headers + (BlockSelectorHeader(c_selectors),)
            return RuleAncestry(new_headers)

    def with_more_selectors(self, selectors):
        """Return a new ancestry that also matches the given selectors.  No
        nesting is done.
        """
        if self.headers and self.headers[-1].is_selector:
            new_selectors = extend_unique(
                self.headers[-1].selectors,
                selectors)
            new_headers = self.headers[:-1] + (
                BlockSelectorHeader(new_selectors),)
            return RuleAncestry(new_headers)
        else:
            new_headers = self.headers + (BlockSelectorHeader(selectors),)
            return RuleAncestry(new_headers)


class BlockHeader(object):
    """..."""
    # TODO doc me depending on how UnparsedBlock is handled...

    is_atrule = False
    is_scope = False
    is_selector = False

    @classmethod
    def parse(cls, prop, has_contents=False):
        num_lines = prop.count('\n')
        prop = prop.strip()

        # Simple pre-processing
        if prop.startswith('+') and not has_contents:
            # Expand '+' at the beginning of a rule as @include.  But not if
            # there's a block, because that's probably a CSS selector.
            # DEVIATION: this is some semi hybrid of Sass and xCSS syntax
            prop = '@include ' + prop[1:]
            try:
                if '(' not in prop or prop.index(':') < prop.index('('):
                    prop = prop.replace(':', '(', 1)
                    if '(' in prop:
                        prop += ')'
            except ValueError:
                pass
        elif prop.startswith('='):
            # Expand '=' at the beginning of a rule as @mixin
            prop = '@mixin ' + prop[1:]
        elif prop.startswith('@prototype '):
            # Remove '@prototype '
            # TODO what is @prototype??
            prop = prop[11:]

        # Minor parsing
        if prop.startswith('@'):
            # This pattern MUST NOT BE ABLE TO FAIL!
            # This is slightly more lax than the CSS syntax technically allows,
            # e.g. identifiers aren't supposed to begin with three hyphens.
            # But we don't care, and will just spit it back out anyway.
            m = re.match(
                '@(else if|[-_a-zA-Z0-9\U00000080-\U0010FFFF]*)\\b',
                prop, re.I)
            directive = m.group(0).lower()
            argument = prop[len(directive):].strip()
            if not argument:
                argument = None
            return BlockAtRuleHeader(directive, argument, num_lines)
        elif prop.split(None, 1)[0].endswith(':'):
            # Syntax is "<scope>: [prop]" -- if the optional prop exists, it
            # becomes the first rule with no suffix
            scope, unscoped_value = prop.split(':', 1)
            scope = scope.rstrip()
            unscoped_value = unscoped_value.lstrip()
            return BlockScopeHeader(scope, unscoped_value, num_lines)
        else:
            return BlockSelectorHeader(prop, num_lines)


class BlockAtRuleHeader(BlockHeader):
    is_atrule = True

    def __init__(self, directive, argument, num_lines=0):
        self.directive = directive
        self.argument = argument

        self.num_lines = num_lines

    def __repr__(self):
        return "<%s %r %r>" % (type(self).__name__, self.directive, self.argument)

    def render(self):
        if self.argument:
            return "%s %s" % (self.directive, self.argument)
        else:
            return self.directive


class BlockSelectorHeader(BlockHeader):
    is_selector = True

    def __init__(self, selectors, num_lines=0):
        self.selectors = tuple(selectors)

        self.num_lines = num_lines

    def __repr__(self):
        return "<%s %r>" % (type(self).__name__, self.selectors)

    def render(self, sep=', ', super_selector=''):
        return sep.join(sort(
            super_selector + s.render()
            for s in self.selectors
            if not s.has_placeholder))


class BlockScopeHeader(BlockHeader):
    is_scope = True

    def __init__(self, scope, unscoped_value, num_lines=0):
        self.scope = scope

        if unscoped_value:
            self.unscoped_value = unscoped_value
        else:
            self.unscoped_value = None

        self.num_lines = num_lines


class UnparsedBlock(object):
    """A Sass block whose contents have not yet been parsed.

    At the top level, CSS (and Sass) documents consist of a sequence of blocks.
    A block may be a ruleset:

        selector { block; block; block... }

    Or it may be an @-rule:

        @rule arguments { block; block; block... }

    Or it may be only a single property declaration:

        property: value

    pyScss's first parsing pass breaks the document into these blocks, and each
    block becomes an instance of this class.
    """

    def __init__(self, parent_rule, lineno, prop, unparsed_contents):
        self.parent_rule = parent_rule
        self.header = BlockHeader.parse(prop, has_contents=bool(unparsed_contents))

        # Basic properties
        self.lineno = (
            parent_rule.lineno - parent_rule.num_header_lines + lineno - 1)
        self.prop = prop
        self.unparsed_contents = unparsed_contents

    @property
    def directive(self):
        return self.header.directive

    @property
    def argument(self):
        return self.header.argument

    ### What kind of thing is this?

    @property
    def is_atrule(self):
        return self.header.is_atrule

    @property
    def is_scope(self):
        return self.header.is_scope
