from setuptools import setup

import tem

setup(
    name="dryparse",
    version=dryparse.__version__,
    description="DRY parser",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="{<>}",
    author="{<>}",
    author_email="{<>}",
    classifiers=["Programming Language :: Python :: {<>}"],
    packages=[],
    entry_points={"console_scripts": ["{<name>}={<name>}.__main__:main"]},
)
