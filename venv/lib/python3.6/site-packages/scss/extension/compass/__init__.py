"""Extension providing Compass support."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import glob
import os.path

import scss.config as config
from scss.extension import Extension
from scss.namespace import Namespace
from scss.source import SourceFile
from scss.types import Boolean
from scss.types import Number
from scss.types import String


class CompassExtension(Extension):
    name = 'compass'
    namespace = Namespace()

    def handle_import(self, name, compilation, rule):
        """Implementation of Compass's "magic" imports, which generate
        spritesheets on the fly, given either a wildcard or the name of a
        directory.
        """
        from .sprites import sprite_map

        # TODO check that the found file is actually under the root
        if callable(config.STATIC_ROOT):
            files = sorted(config.STATIC_ROOT(name))
        else:
            glob_path = os.path.join(config.STATIC_ROOT, name)
            files = glob.glob(glob_path)
            files = sorted((fn[len(config.STATIC_ROOT):], None) for fn in files)

        if not files:
            return

        # Build magic context
        calculator = compilation._make_calculator(rule.namespace)
        map_name = os.path.normpath(os.path.dirname(name)).replace('\\', '_').replace('/', '_')
        kwargs = {}

        # TODO this is all kinds of busted.  rule.context hasn't existed for
        # ages.
        def setdefault(var, val):
            _var = '$' + map_name + '-' + var
            if _var in rule.context:
                kwargs[var] = calculator.interpolate(rule.context[_var], rule, self._library)
            else:
                rule.context[_var] = val
                kwargs[var] = calculator.interpolate(val, rule, self._library)
            return rule.context[_var]

        setdefault('sprite-base-class', String('.' + map_name + '-sprite', quotes=None))
        setdefault('sprite-dimensions', Boolean(False))
        position = setdefault('position', Number(0, '%'))
        spacing = setdefault('spacing', Number(0))
        repeat = setdefault('repeat', String('no-repeat', quotes=None))
        names = tuple(os.path.splitext(os.path.basename(file))[0] for file, storage in files)
        for n in names:
            setdefault(n + '-position', position)
            setdefault(n + '-spacing', spacing)
            setdefault(n + '-repeat', repeat)
        rule.context['$' + map_name + '-' + 'sprites'] = sprite_map(name, **kwargs)
        generated_code = '''
            @import "compass/utilities/sprites/base";

            // All sprites should extend this class
            // The %(map_name)s-sprite mixin will do so for you.
            #{$%(map_name)s-sprite-base-class} {
                background: $%(map_name)s-sprites;
            }

            // Use this to set the dimensions of an element
            // based on the size of the original image.
            @mixin %(map_name)s-sprite-dimensions($name) {
                @include sprite-dimensions($%(map_name)s-sprites, $name);
            }

            // Move the background position to display the sprite.
            @mixin %(map_name)s-sprite-position($name, $offset-x: 0, $offset-y: 0) {
                @include sprite-position($%(map_name)s-sprites, $name, $offset-x, $offset-y);
            }

            // Extends the sprite base class and set the background position for the desired sprite.
            // It will also apply the image dimensions if $dimensions is true.
            @mixin %(map_name)s-sprite($name, $dimensions: $%(map_name)s-sprite-dimensions, $offset-x: 0, $offset-y: 0) {
                @extend #{$%(map_name)s-sprite-base-class};
                @include sprite($%(map_name)s-sprites, $name, $dimensions, $offset-x, $offset-y);
            }

            @mixin %(map_name)s-sprites($sprite-names, $dimensions: $%(map_name)s-sprite-dimensions) {
                @include sprites($%(map_name)s-sprites, $sprite-names, $%(map_name)s-sprite-base-class, $dimensions);
            }

            // Generates a class for each sprited image.
            @mixin all-%(map_name)s-sprites($dimensions: $%(map_name)s-sprite-dimensions) {
                @include %(map_name)s-sprites(%(sprites)s, $dimensions);
            }
        ''' % {'map_name': map_name, 'sprites': ' '.join(names)}

        return SourceFile.from_string(generated_code)


__all__ = ['CompassExtension']

# Import child modules LAST, so they can in turn import CompassExtension from
# us
import scss.extension.compass.gradients
import scss.extension.compass.helpers
import scss.extension.compass.images
import scss.extension.compass.sprites  # NOQA
