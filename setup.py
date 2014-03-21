#!/usr/bin/env python
import os
from setuptools import setup
from glob import glob

# Utility function so that we can share documentation with Sphinx politely.
def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()
def requirements():
    """
    Halfheartedly parses ./requirements.txt for dependency information.
    """
    # Read requirements spec
    requirements = [x.strip() for x in read('requirements.txt').split("\n")]
    # Remove blank and comment lines
    requirements = [x for x in requirements if len(x) > 0 and x[0] != '#']
    # Return
    return requirements
def scripts():
    """
    Reads all *.py filenames in ./bin for use as setup(scripts=) argument.
    """
    setup_dir = os.path.dirname(__file__)
    script_dir = os.path.join(setup_dir, 'bin')
    scripts = glob(os.path.join(script_dir,'*'))
    scripts = [os.path.relpath(p, setup_dir) for p in scripts]
    scripts = [s for s in scripts if s not in ['.', '..']]
    return scripts

setup(
    name = "gitzebo",
    # TODO: How do we make this and version.py play nicely together without
    #       a MAJOR hack that winds up breaking automated build frameworks?
    #       (For example, we don't want to break fpm compatibility.)
    version="0.0.9",
    author="John Gilik",
    author_email="john@jgilik.com",
    description=("A minimal git management web application."),
    license="2-Clause BSD License",
    keywords="git",
    url="http://jgilik.com/gitzebo/",
    packages=['gitzebo'],
    include_package_data=True, # include templates, static, etc
    long_description=read('README.rst'),
    scripts=scripts(),
    install_requires=requirements(),
    # TODO: Probably should add some classifiers.
    classifiers=[
        "Development Status :: 3 - Alpha",
    ],
)

