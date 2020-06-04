from __future__ import with_statement
from __future__ import absolute_import
import os.path as op
import os
from scss.compiler import Compiler
import fnmatch
import codecs


class Scss(object):
    '''
    Main and only class for Flask-Scss. It is in charge on the discovery of
    .scss files and compiles them every time they are modified.

    Any application that wants to use Flask-Scss must create a instance of this class
    '''

    def __init__(self, app, static_dir=None, asset_dir=None, load_paths=None):
        '''

        See :ref:`scss_discovery_rules`
        and :ref:`static_discovery_rules`
        for more information about the impact of ``static_dir`` and
        ``asset_dir`` parameters.

        Parameters here has preedence over Parameters found in the application
        config.

        :param app: Your Flask Application
        :param static_dir: The path to the ``static`` directory of your
                           application (optional)
        :param asset_dir: The path to the ``assets`` directory where Flask-Scss
                          will search ``.scss`` files (optional)
        :param load_paths: A list of folders to add to pyScss load_paths
                           (for ex., the path to a library like Compass)
        '''
        if not load_paths:
            load_paths = []

        self.app = app
        self.asset_dir = self.set_asset_dir(asset_dir)
        self.static_dir = self.set_static_dir(static_dir)
        self.assets = {}
        self.partials = {}

        load_path_list = ([self.asset_dir] if self.asset_dir else []) \
                       + (load_paths or app.config.get('SCSS_LOAD_PATHS', []))

        # pyScss.log = app.logger
        self.compiler = Compiler(search_path=load_path_list)
        if self.app.testing or self.app.debug:
            self.set_hooks()

    def set_asset_dir(self, asset_dir):
        asset_dir = asset_dir \
                    or self.app.config.get('SCSS_ASSET_DIR', None) \
                    or op.join(self.app.root_path, 'assets')
        if op.exists(op.join(asset_dir, 'scss')):
            return op.join(asset_dir, 'scss')
        if op.exists(asset_dir):
            return asset_dir
        return None

    def set_static_dir(self, static_dir):
        static_dir = static_dir  \
                        or self.app.config.get('SCSS_STATIC_DIR', None) \
                        or op.join(self.app.root_path, self.app.static_folder)
        if op.exists(op.join(static_dir, 'css')):
            return op.join(static_dir, 'css')
        if op.exists(static_dir):
            return static_dir
        return None

    def set_hooks(self):
        if self.asset_dir is None:
            self.app.logger.warning("The asset directory cannot be found."
                                    "Flask-Scss extension has been disabled")
            return
        if self.static_dir is None:
            self.app.logger.warning("The static directory cannot be found."
                                    "Flask-Scss extension has been disabled")
            return
        self.app.logger.info("Pyscss loaded!")
        self.app.before_request(self.update_scss)

    def discover_scss(self):
        for folder, _, files in os.walk(self.asset_dir):
            for filename in fnmatch.filter(files, '*.scss'):
                src_path = op.join(folder, filename)
                if filename.startswith('_') and src_path not in self.partials:
                    self.partials[src_path] = op.getmtime(src_path)
                elif src_path not in self.partials and src_path not in self.assets:
                    dest_path = src_path.replace(
                                    self.asset_dir,
                                    self.static_dir
                                ).replace('.scss', '.css')
                    self.assets[src_path] = dest_path

    def partials_have_changed(self):
        res = False
        for partial, old_mtime in self.partials.items():
            cur_mtime = op.getmtime(partial)
            if cur_mtime > old_mtime:
                res = True
                self.partials[partial] = cur_mtime
        return res

    def update_scss(self):
        self.discover_scss()
        if self.partials_have_changed():
            for asset, dest_path in self.assets.items():
                self.compile_scss(asset, dest_path)
            return
        for asset, dest_path in self.assets.items():
            dest_mtime = op.getmtime(dest_path) \
                             if op.exists(dest_path) \
                             else -1
            if op.getmtime(asset) > dest_mtime:
                self.compile_scss(asset, dest_path)

    def compile_scss(self, asset, dest_path):
        self.app.logger.info("[flask-pyscss] refreshing %s" % (dest_path,))
        if not os.path.exists(op.dirname(dest_path)):
            os.makedirs(op.dirname(dest_path))
        with codecs.open(dest_path, 'w', 'utf-8') as file_out:
            with open(asset) as file_in:
                file_out.write(self.compiler.compile_string(file_in.read()))
