# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('../histopath_bim_des'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'histopath-bim-des'
copyright = '2024, Yin-Chi Chan, Nicola Moretti'
author = 'Yin-Chi Chan, Nicola Moretti'
release = '0.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.napoleon', 'sphinx.ext.autodoc', 'sphinx.ext.viewcode', 'myst_parser',
              'sphinx.ext.githubpages', 'sphinx.ext.intersphinx']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


autodoc_default_options = {
    'members': None,
    'undoc-members': True,
    'special-members': '__core__',
    'member-order': 'bysource',
    'exclude-members': '__dict__,__weakref__,__module__,model_computed_fields,model_config,model_fields'
}

myst_enable_extensions = ["colon_fence","attrs_inline"]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'openpyxl': ('https://openpyxl.readthedocs.io/en/stable/', None),
    'ifcopenshell':  ('https://docs.ifcopenshell.org/', None),
    'shapely': ('https://shapely.readthedocs.io/en/stable/', None),
    'networkx': ('https://networkx.org/documentation/stable/', None),
    'pydantic': ('https://docs.pydantic.dev/latest/', None),
    'salabim': ('https://www.salabim.org/manual/', None)
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

html_context = {
    'display_github': True,
    'github_user': 'yinchi',
    'github_repo': 'histopath-bim-des',
    'github_version': 'main',
    'conf_py_path': '/docs/',
}
