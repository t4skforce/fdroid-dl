#!/usr/bin/env python
# coding: utf-8
import os.path
import warnings
import sys
import setuptools
import fdroid_dl

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name=fdroid_dl.NAME,
    version=fdroid_dl.__version__,
    author=fdroid_dl.AUTHOR,
    author_email=fdroid_dl.AUTHOR_MAIL,
    description="fdroid-dl is a f-droid (offline) mirror generation and update utility",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/t4skforce/fdroid-dl",
    entry_points={'console_scripts': ['fdroid-dl=fdroid_dl.__main__:main']},
    packages=setuptools.find_packages(),
    install_requires=[
        'requests-futures>=0.9.7',
        'PyYAML>=3.13',
        'click>=6.7'
    ],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4',
    classifiers=(
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
