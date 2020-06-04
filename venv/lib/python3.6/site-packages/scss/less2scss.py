# -*- coding: utf-8 -*-
"""
Tool for converting Less files to Scss

Usage: python -m scss.less2scss [file]

"""
# http://stackoverflow.com/questions/14970224/anyone-know-of-a-good-way-to-convert-from-less-to-sass
from __future__ import unicode_literals, absolute_import, print_function

import re
import os
import sys


class Less2Scss(object):
    at_re = re.compile(r'@(?!(media|import|mixin|font-face)(\s|\())')
    mixin_re = re.compile(r'\.([\w\-]*)\s*\((.*)\)\s*\{')
    include_re = re.compile(r'(\s|^)\.([\w\-]*\(?.*\)?;)')
    functions_map = {
        'spin': 'adjust-hue',
    }
    functions_re = re.compile(r'(%s)\(' % '|'.join(functions_map))

    def convert(self, content):
        content = self.convertVariables(content)
        content = self.convertMixins(content)
        content = self.includeMixins(content)
        content = self.convertFunctions(content)
        return content

    def convertVariables(self, content):
        # Matches any @ that doesn't have 'media ' or 'import ' after it.
        content = self.at_re.sub('$', content)
        return content

    def convertMixins(self, content):
        content = self.mixin_re.sub('@mixin \1(\2) {', content)
        return content

    def includeMixins(self, content):
        content = self.mixin_re.sub('\1@include \2', content)
        return content

    def convertFunctions(self, content):
        content = self.functions_re.sub(lambda m: '%s(' % self.functions_map[m.group(0)], content)
        return content


def less2scss(options, args):
    if not args:
        args = ['-']

    less2scss = Less2Scss()

    for source_path in args:
        if source_path == '-':
            source = sys.stdin
            destiny = sys.stdout
        else:
            try:
                source = open(source_path)
                destiny_path, ext = os.path.splitext(source_path)
                destiny_path += '.scss'
                if not options.force and os.path.exists(destiny_path):
                    raise IOError("File already exists: %s" % destiny_path)
                destiny = open(destiny_path, 'w')
            except Exception as e:
                error = "%s" % e
                if destiny_path in error:
                    ignoring = "Ignoring"
                else:
                    ignoring = "Ignoring %s" % destiny_path
                print("WARNING -- %s. %s" % (ignoring, error), file=sys.stderr)
                continue
        content = source.read()
        content = less2scss.convert(content)
        destiny.write(content)


def main():
    from optparse import OptionParser, SUPPRESS_HELP

    parser = OptionParser(usage="Usage: %prog [file]",
                          description="Converts Less files to Scss.",
                          add_help_option=False)
    parser.add_option("-f", "--force", action="store_true",
                      dest="force", default=False,
                      help="Forces overwriting output file if it already exists")
    parser.add_option("-?", action="help", help=SUPPRESS_HELP)
    parser.add_option("-h", "--help", action="help",
                      help="Show this message and exit")
    parser.add_option("-v", "--version", action="store_true",
                      help="Print version and exit")

    options, args = parser.parse_args()

    if options.version:
        from scss.tool import print_version
        print_version()
    else:
        less2scss(options, args)


if __name__ == "__main__":
    main()
