from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from scss.extension import Extension
from scss.extension.compass.helpers import _font_url
from scss.extension.compass.images import _image_url
from scss.namespace import Namespace


class BootstrapExtension(Extension):
    name = 'bootstrap'
    namespace = Namespace()

ns = BootstrapExtension.namespace


@ns.declare
def twbs_font_path(path):
    return _font_url(path, False, True, False)


@ns.declare
def twbs_image_path(path):
    return _image_url(path, False, True, None, None, False, None, None, None, None)
