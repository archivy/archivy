
from setuptools import setup


setup(
    name='plugins2',
    version='0.1dev0',
    py_modules=['plugin'],
    entry_points='''
        [archivy.plugins]
        test_plugin=plugin:test_plugin
    '''
)
