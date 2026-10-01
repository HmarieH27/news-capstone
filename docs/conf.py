"""Load Django before Sphinx imports the documented application modules."""

import django
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "news_site.settings")
django.setup()
project = "News capstone"
extensions = ["sphinx.ext.autodoc", "sphinx.ext.viewcode"]
html_theme = "alabaster"
exclude_patterns = ["_build"]
