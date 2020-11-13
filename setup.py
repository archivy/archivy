import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt', encoding='utf-8') as f:
    all_reqs = f.read().split('\n')
    install_requires = [x.strip() for x in all_reqs if not x.startswith('#')
                        and not x.startswith("-e git")]

setuptools.setup(
    name="archivy",
    version="0.7.3",
    author="Uzay-G",
    author_email="uzgirit@gmail.com",
    description=(
        "Minimalist knowledge base focused on digital preservation"
        " and building your second brain."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Uzay-G/archivy",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ],
    entry_points={
        "console_scripts": [
            "archivy = archivy.cli:cli",
        ]
    },
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    python_requires='>=3.6',
)
