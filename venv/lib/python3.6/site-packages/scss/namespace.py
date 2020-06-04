"""Support for Sass's namespacing rules."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import inspect
import logging

import six

from scss.types import Undefined
from scss.types import Value


log = logging.getLogger(__name__)


def normalize_var(name):
    assert isinstance(name, six.string_types)
    return name.replace('_', '-')


class Scope(object):
    """Implements Sass variable scoping.

    Similar to `ChainMap`, except that assigning a new value will replace an
    existing value, not mask it.
    """
    def __init__(self, maps=()):
        maps = list(maps)
        self.maps = [dict()] + maps

    def __repr__(self):
        return "<%s(%s) at 0x%x>" % (type(self).__name__, ', '.join(repr(map) for map in self.maps), id(self))

    def __getitem__(self, key):
        for map in self.maps:
            if key in map:
                return map[key]

        raise KeyError(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __contains__(self, key):
        for map in self.maps:
            if key in map:
                return True
        return False

    def keys(self):
        # For mapping interface
        keys = set()
        for map in self.maps:
            keys.update(map.keys())
        return list(keys)

    def set(self, key, value, force_local=False):
        if not force_local:
            for map in self.maps:
                if key in map:
                    if isinstance(map[key], Undefined):
                        break
                    map[key] = value
                    return

        self.maps[0][key] = value

    def new_child(self):
        return type(self)(self.maps)


class VariableScope(Scope):
    pass


class FunctionScope(Scope):
    def __repr__(self):
        return "<%s(%s) at 0x%x>" % (type(self).__name__, ', '.join('[%s]' % ', '.join('%s:%s' % (f, n) for f, n in sorted(map.keys())) for map in self.maps), id(self))


class MixinScope(Scope):
    def __repr__(self):
        return "<%s(%s) at 0x%x>" % (type(self).__name__, ', '.join('[%s]' % ', '.join('%s:%s' % (f, n) for f, n in sorted(map.keys())) for map in self.maps), id(self))


class ImportScope(Scope):
    pass


class Namespace(object):
    """..."""
    _mutable = True

    def __init__(self, variables=None, functions=None, mixins=None, mutable=True):
        self._mutable = mutable

        if variables is None:
            self._variables = VariableScope()
        else:
            # TODO parse into sass values once that's a thing, or require them
            # all to be
            self._variables = VariableScope([variables])

        if functions is None:
            self._functions = FunctionScope()
        else:
            self._functions = FunctionScope([functions._functions])

        self._mixins = MixinScope()

        self._imports = ImportScope()

    def _assert_mutable(self):
        if not self._mutable:
            raise AttributeError("This Namespace instance is immutable")

    @classmethod
    def derive_from(cls, *others):
        self = cls()
        if len(others) == 1:
            self._variables = others[0]._variables.new_child()
            self._functions = others[0]._functions.new_child()
            self._mixins = others[0]._mixins.new_child()
            self._imports = others[0]._imports.new_child()
        else:
            # Note that this will create a 2-dimensional scope where each of
            # these scopes is checked first in order.  TODO is this right?
            self._variables = VariableScope(other._variables for other in others)
            self._functions = FunctionScope(other._functions for other in others)
            self._mixins = MixinScope(other._mixins for other in others)
            self._imports = ImportScope(other._imports for other in others)
        return self

    def derive(self):
        """Return a new child namespace.  All existing variables are still
        readable and writeable, but any new variables will only exist within a
        new scope.
        """
        return type(self).derive_from(self)

    def declare(self, function):
        """Insert a Python function into this Namespace, detecting its name and
        argument count automatically.
        """
        self._auto_register_function(function, function.__name__)
        return function

    def declare_alias(self, name):
        """Insert a Python function into this Namespace with an
        explicitly-given name, but detect its argument count automatically.
        """
        def decorator(f):
            self._auto_register_function(f, name)
            return f

        return decorator

    def declare_internal(self, function):
        """Like declare(), but the registered function will also receive the
        current namespace as its first argument.  Useful for functions that
        inspect the state of the compilation, like ``variable-exists()``.
        Probably not so useful for anything else.
        """
        function._pyscss_needs_namespace = True
        self._auto_register_function(function, function.__name__, 1)
        return function

    def _auto_register_function(self, function, name, ignore_args=0):
        name = name.replace('_', '-').rstrip('-')
        argspec = inspect.getargspec(function)

        if argspec.varargs or argspec.keywords:
            # Accepts some arbitrary number of arguments
            arities = [None]
        else:
            # Accepts a fixed range of arguments
            if argspec.defaults:
                num_optional = len(argspec.defaults)
            else:
                num_optional = 0
            num_args = len(argspec.args) - ignore_args
            arities = range(num_args - num_optional, num_args + 1)

        for arity in arities:
            self.set_function(name, arity, function)

    @property
    def variables(self):
        return dict((k, self._variables[k]) for k in self._variables.keys())

    def variable(self, name, throw=False):
        name = normalize_var(name)
        return self._variables[name]

    def set_variable(self, name, value, local_only=False):
        self._assert_mutable()
        name = normalize_var(name)
        if not isinstance(value, Value):
            raise TypeError("Expected a Sass type, while setting %s got %r" % (name, value,))
        self._variables.set(name, value, force_local=local_only)

    def has_import(self, source):
        return source.path in self._imports

    def add_import(self, source, parent_rule):
        self._assert_mutable()
        self._imports[source.path] = [
            0,
            parent_rule.source_file.path,
            parent_rule.file_and_line,
        ]

    def use_import(self, import_key):
        self._assert_mutable()
        if import_key and import_key in self._imports:
            imports = self._imports[import_key]
            imports[0] += 1
            self.use_import(imports[1])

    def unused_imports(self):
        unused = []
        for import_key in self._imports.keys():
            imports = self._imports[import_key]
            if not imports[0]:
                unused.append((import_key[0], imports[2]))
        return unused

    def _get_callable(self, chainmap, name, arity):
        name = normalize_var(name)
        if arity is not None:
            # With explicit arity, try the particular arity before falling back
            # to the general case (None)
            try:
                return chainmap[name, arity]
            except KeyError:
                pass

        return chainmap[name, None]

    def _set_callable(self, chainmap, name, arity, cb):
        name = normalize_var(name)
        chainmap[name, arity] = cb

    def mixin(self, name, arity):
        return self._get_callable(self._mixins, name, arity)

    def set_mixin(self, name, arity, cb):
        self._assert_mutable()
        self._set_callable(self._mixins, name, arity, cb)

    def function(self, name, arity):
        return self._get_callable(self._functions, name, arity)

    def set_function(self, name, arity, cb):
        self._assert_mutable()
        self._set_callable(self._functions, name, arity, cb)
