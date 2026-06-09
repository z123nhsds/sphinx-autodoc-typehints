import os
import sys

sys.path.insert(0, os.path.abspath("."))

project = "My Project"
author = "Author"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "alabaster"

autodoc_typehints = "none"
napoleon_use_rtype = False
typehints_use_rtype = False
always_use_bars_union = True
simplify_optional_unions = False
typehints_use_signature = True
typehints_use_signature_return = True
typehints_defaults = "braces-after"
typehints_document_rtype_none = False
