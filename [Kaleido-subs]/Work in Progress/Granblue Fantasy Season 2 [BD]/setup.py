#!/usr/bin/env python3

import setuptools

with open("requirements.txt") as fh:
    install_requires = fh.read()

name = "gbf2_filters_common"
version = "0.0.1"
release = "0.0.1"

setuptools.setup(
    name=name,
    version=release,
    author="LightArrowsEXE",
    author_email="Lightarrowsreboot@gmail.com",
    description="Filtering functions for Granblue Fantasy 2's BDs",
    packages=["gbf2_filters_common"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_data={
        'gbf2_filters_common': ['py.typed'],
    },
    install_requires=install_requires,
    python_requires='>=3.9',
)
