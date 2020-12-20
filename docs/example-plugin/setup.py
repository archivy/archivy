from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='archivy_extra_metadata',
    version='0.1.0',
    author="Uzay-G",
    description=(
        "Archivy extension to add some metadata at the end of your notes / bookmarks."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    packages=find_packages(),
    entry_points='''
        [archivy.plugins]
        extra-metadata=archivy_extra_metadata:extra_metadata
    '''
)
