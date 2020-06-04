"""Support for extending the Sass compiler."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


_no_default = object()


class Cache(object):
    """Serves as a local memory cache storage for extensions usage.
    """
    _cache = {}

    def __init__(self, prefix=None):
        self.prefix = prefix

    def get(self, key, default=None):
        try:
            return self.__class__._cache[self.prefix][key]
        except KeyError:
            if default is _no_default:
                raise
            return default

    def set(self, key, value):
        self.__class__._cache.setdefault(self.prefix, {})[key] = value

    def clear_cache(self, key=None):
        if key:
            try:
                del self.__class__._cache[self.prefix][key]
            except KeyError:
                pass
        else:
            self.__class__._cache.clear()

    def __len__(self):
        return len(self.__class__._cache.setdefault(self.prefix, {}))

    def __iter__(self):
        return iter(self.__class__._cache.setdefault(self.prefix, {}))

    def __getitem__(self, key):
        return self.get(key, _no_default)

    def __setitem__(self, key, value):
        return self.set(key, value)

    def __delitem__(self, key):
        self.clear_cache(key)


class Extension(object):
    """An extension to the Sass compile process.  Subclass to add your own
    behavior.

    Methods are hooks, called by the compiler at certain points.  Each
    extension is considered in the order it's provided.
    """

    # TODO unsure how this could work given that we'd have to load modules for
    # it to be available
    name = None
    """A unique name for this extension, which will allow it to be referenced
    from the command line.
    """

    namespace = None
    """An optional :class:`scss.namespace.Namespace` that will be injected into
    the compiler.
    """

    def __init__(self):
        pass

    def __repr__(self):
        return "<{0}>".format(type(self).__name__)

    def handle_import(self, name, compilation, rule):
        """Attempt to resolve an import.  Called once for every Sass string
        listed in an ``@import`` statement.  Imports that Sass dictates should
        be converted to plain CSS imports do NOT trigger this hook.

        So this::

            @import url(foo), "bar", "baz";

        would call `handle_import` twice: once with "bar", once with "baz".

        Return a :class:`scss.source.SourceFile` if you want to handle the
        import, or None if you don't.  (This method returns None by default, so
        if you don't care about hooking imports, just don't implement it.)
        This method is tried on every registered `Extension` in order, until
        one of them returns successfully.

        A good example is the core Sass import machinery, which is implemented
        with this hook; see the source code of the core extension.
        """
        pass


class NamespaceAdapterExtension(Extension):
    """Trivial wrapper that adapts a bare :class:`scss.namespace.Namespace`
    into a full extension.
    """

    def __init__(self, namespace):
        self.namespace = namespace
