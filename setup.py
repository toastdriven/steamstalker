#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

setup(
    name='steamstalker',
    version='0.2.0',
    description='Historical data capture on when your Steam friends are playing games.',
    author='Daniel Lindsley',
    author_email='daniel@toastdriven.com',
    url='http://github.com/toastdriven/steamstalker',
    long_description=open('README.rst', 'r').read(),
    packages=[
        'steamstalker',
        'steamstalker.management',
        'steamstalker.management.commands',
        'steamstalker.migrations',
    ],
    package_data={
        'steamstalker': [
            'templates/steamstalker/*',
            'static/js/*',
        ],
    },
    zip_safe=False,
    requires=[
        'dateutil(>2.0)',
    ],
    install_requires=[
        'python_dateutil > 2.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ],
)
