#!/usr/bin/env python3.6
"""Distribution and installation of Astrality."""

from setuptools import find_packages, setup

setup(
    name='astrality',
    version='0.0.7',
    packages=find_packages(),
    install_requires=[
        'astral',
        'pyyaml',
        'Jinja2',
    ],
    python_requires='>=3.6',
    scripts=['astrality'],

    # metadata for upload to PyPI
    author='Jakob Gerhard Martinussen',
    author_email='jakobgm@gmail.com',
    description='A dynamic configuration file manager.',
    long_description='See documentation at: https://github.com/JakobGM/astrality',
    license="MIT",
    keywords="unix configuration management",
    url="http://github.com/JakobGM/astrality",

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.6',
        'Topic :: Desktop Environment :: File Managers',
        'Topic :: Text Processing',
    ]
)
