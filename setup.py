#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SchemaPilot - Setup Configuration
"""

from setuptools import setup, find_packages
import os

# Read README file
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

setup(
    name="schemapilot",
    version="1.0.0",
    author="SchemaPilot Team",
    author_email="hello@schemapilot.dev",
    description="Lightweight JSON Schema Intelligent Validation & Testing Engine",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/gitstq/SchemaPilot",
    py_modules=["schemapilot"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "schemapilot=schemapilot:main",
        ],
    },
    keywords="json schema validation api testing cli tool",
    project_urls={
        "Bug Reports": "https://github.com/gitstq/SchemaPilot/issues",
        "Source": "https://github.com/gitstq/SchemaPilot",
        "Documentation": "https://github.com/gitstq/SchemaPilot#readme",
    },
)
