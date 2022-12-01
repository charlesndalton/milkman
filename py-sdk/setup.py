from setuptools import setup, find_packages
import codecs
import os

VERSION = '0.0.1'
DESCRIPTION = 'Milkman smart contract SDK'
LONG_DESCRIPTION = 'A package for interacting with the Milkman smart contract system, a mechanism for smart contracts to route their order flow through the CoW protocol.'

# Setting up
setup(
    name="milkman_py",
    version=VERSION,
    author="charlesndalton (Charles Dalton)",
    author_email="<charles.n.dalton@gmail.com>",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[],
    keywords=['python', 'video', 'stream', 'video stream', 'camera stream', 'sockets'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)