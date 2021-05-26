# -*- coding: utf-8 -*-
"""Installer for Searx package."""

from setuptools import setup
from setuptools import find_packages


requirements = open('requirements.txt').read().splitlines()
dev_requirements = open('requirements-dev.txt').read().splitlines()

setup(
    name='searx',
    use_scm_version={"tag_regex": r"^(?:[\w-]+-)?(?P<version>[vV]?\d+(?:\.\d+){0,2}.*)$"},
    description="A privacy-respecting, hackable metasearch engine",
    long_description=open('README.md').read(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        'License :: OSI Approved :: GNU Affero General Public License v3'
    ],
    keywords='metasearch searchengine search web http',
    author='Adam Tauber',
    author_email='asciimoo@gmail.com',
    license='GNU Affero General Public License',
    packages=find_packages(exclude=["tests*", "searx_extra"]),
    zip_safe=False,
    install_requires=requirements,
    setup_requires=["setuptools_scm"],
    extras_require={
        'test': dev_requirements
    },
    entry_points={
        'console_scripts': [
            'searx-run = searx.webapp:run',
            'searx-checker = searx.search.checker.__main__:main'
        ]
    },
    package_data={
        'searx': [
            'settings.yml',
            'data/*',
            'plugins/*/*',
            'static/*.*',
            'static/*/*.*',
            'static/*/*/*.*',
            'static/*/*/*/*.*',
            'static/*/*/*/*/*.*',
            'templates/*/*.*',
            'templates/*/*/*.*',
            'translations/*/*/*'
        ],
    },
)
