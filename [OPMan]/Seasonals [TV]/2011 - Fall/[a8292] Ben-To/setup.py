#!/usr/bin/env python3

import setuptools

with open("requirements.txt") as fh:
    install_requires = fh.read()

name = "bento_filters"
version = "1.0.0"
release = "1.0.0"

setuptools.setup(
    name=name,
    version=release,
    author="LightArrowsEXE",
    author_email="Lightarrowsreboot@gmail.com",
    description="Filtering functions for [◯PMan] Ben-To!",
    packages=["bento_filters"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_data={
        'trdr_filters': ['py.typed'],
    },
    install_requires=install_requires,
    python_requires='>=3.9',
)
