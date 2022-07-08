from setuptools import setup, find_packages

import dryparse

setup(
    name="dryparse",
    version=dryparse.__version__,
    description="DRY command line parser",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/drytoe/dryparse",
    author="Haris Gušić",
    author_email="harisgusic.dev@gmail.com",
    classifiers=["Programming Language :: Python :: 3.7"],
    packages=find_packages(),
    install_requires=["docstring-parser"],
)
