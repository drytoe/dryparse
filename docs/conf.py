import glob
import os
import sys

from sphinx.application import Sphinx
from sphinx.domains import std

# ┏━━━━━━━━━━━━━━┓
# ┃ Project info ┃
# ┗━━━━━━━━━━━━━━┛
project = "dryparse"
copyright = "2021, Haris Gušić"
author = "Haris Gušić"

sys.path.insert(0, os.path.dirname(__file__) + "/..")
import tem

release = tem.__version__

# ┏━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ General configuration ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━┛
extensions = [
    "sphinx.ext.todo",
    "sphinx.ext.autodoc",
    "sphinx_codeautolink",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx_rtd_dark_mode",
    "sphinx_copybutton",
    "sphinx-prompt",
    "sphinx_toolbox.source",
]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
todo_include_todos = True

default_role = "envvar"  # Like :code: role, but the text is black

sys.path.insert(0, os.path.abspath(".."))
# ┏━━━━━━┓
# ┃ HTML ┃
# ┗━━━━━━┛
html_theme = "sphinx_rtd_theme"
default_dark_mode = False
html_static_path = ["static"]
html_css_files = [
    "custom.css",
]

# ┏━━━━━━━━━━━━┓
# ┃ Python doc ┃
# ┗━━━━━━━━━━━━┛
autodoc_member_order = "bysource"
autodoc_typehints_format = "short"
add_module_names = False
autosummary_generate = True
napoleon_custom_sections = ["Constants", "Attributes", "Returns", "Methods"]

# ┏━━━━━━━━━━━━━━━━┓
# ┃ Sphinx toolbox ┃
# ┗━━━━━━━━━━━━━━━━┛
github_username = "veracioux"
github_repository = "dryparse"
source_link_target = "GitHub"

# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ Specific steps for ReadTheDocs ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

# ReadTheDocs doesn't use make -- it builds directly using sphinx and this file
if os.environ.get("READTHEDOCS", False):
    from subprocess import call

    # Scripts must be made executable on ReadTheDocs, but we just give full
    # permissions to all files to prevent future headaches
    call("chmod -R 777 ./", shell=True)
    call("umask 000", shell=True)

    # Add a tag so we can customize some rst files for ReadTheDocs
    tags.add("ReadTheDocs")
    # Confer [*]
    exclude_patterns.remove("man")

    # Move them to man/ so the resulting URL looks nicer [*]
    call("mv _intermediate/man/* man/", shell=True)

    # ┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    # ┃ Debugging on ReadTheDocs ┃
    # ┗━━━━━━━━━━━━━━━━━━━━━━━━━━┛

    # Only uncomment this section if something is going wrong on ReadTheDocs

    """
    # In the Sphinx documentation, this function is said to require three arguments.
    # But when the third one is positional, an exception is raised.
    # We don't use it anyway, so set its default value to None.
    def build_finished_handler(app, docname, source=None):
        # Check if the correct files have been generated
        call('ls -Rl', shell=True)

    def setup(app):
        app.connect('build-finished', build_finished_handler)
    """
