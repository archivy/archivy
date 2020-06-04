"""Support for compiler extensions, which can affect the compile process and
inject their own functions and values.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# Re-export
from .api import Cache
from .api import Extension
from .api import NamespaceAdapterExtension


__all__ = ['Cache', 'Extension', 'NamespaceAdapterExtension']
