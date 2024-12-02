"""Configuration file for the Sphinx documentation builder.
For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

# pylint: disable=redefined-builtin
# pylint: disable=invalid-name

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "data-access-layer"
copyright = "2024, Backend"
author = "Backend"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # Include documentation from docstrings
    "sphinx.ext.napoleon",  # Add support for Google style docstrings
    "sphinx.ext.todo",  # Catch and show TODOs within docstrings
    "sphinx_mdinclude",  # Markdown to rst
    "sphinx.ext.inheritance_diagram",  # Classes inheritance diagram
]

# display TODOs
todo_include_todos = True

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
